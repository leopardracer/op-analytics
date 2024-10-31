import time
from dataclasses import dataclass
from typing import Any, Callable

import polars as pl
from op_coreutils.bigquery.write import (
    overwrite_partition_static,
    overwrite_partitions_dynamic,
    overwrite_table,
)
from op_coreutils.logger import structlog
from op_coreutils.request import new_session
from op_coreutils.threads import run_concurrently
from op_coreutils.time import now_date

log = structlog.get_logger()

SUMMARY_ENDPOINT = "https://l2beat.com/api/scaling/summary"

BQ_DATASET = "uploads_api"

SUMMARY_TABLE = "l2beat_daily_chain_summary"

TVL_TABLE = "l2beat_daily_tvl"
TVL_SCHEMA: dict[str, type[pl.DataType]] = {
    "timestamp": pl.Int64,
    "native": pl.Float64,
    "canonical": pl.Float64,
    "external": pl.Float64,
    "ethPrice": pl.Float64,
}
TVL_QUERY_RANGE = "30d"  # use "max" for backfill


ACTIVITY_TABLE = "l2beat_daily_activity"
ACTIVITY_SCHEMA: dict[str, type[pl.DataType]] = {
    "timestamp": pl.Int64,
    "count": pl.Int64,
}
ACTIVITY_QUERY_RANGE = "30d"  # use "max" for backfill


def get_data(session, url):
    """Helper function to reuse an existing HTTP session to fetch data from a URL."""
    start = time.time()
    resp = session.request(
        method="GET",
        url=url,
        headers={"Content-Type": "application/json"},
    ).json()
    log.info(f"Fetched from {url}: {time.time() - start:.2f} seconds")
    return resp


@dataclass(frozen=True)
class L2BeatProject:
    """A single project as referenced by L2Beat."""

    id: str
    slug: str


def pull():
    """Pull data from L2Beat.

    - Fetch the L2Beat summary endpoint.
    - For each project in the L2Beat summary fetch TVL (last 30 days).
    - Write all results to BigQuery.
    """
    # Call the summary endpoint
    session = new_session()
    summary = get_data(session, SUMMARY_ENDPOINT)
    projects_summary = list(summary["data"]["projects"].values())

    # Parse the summary and store as a dataframe.
    summary_df = pl.DataFrame(projects_summary)

    # Write summary to BQ.
    dt = now_date()
    overwrite_table(summary_df, BQ_DATASET, f"{SUMMARY_TABLE}_latest")
    overwrite_partition_static(summary_df, dt, BQ_DATASET, f"{SUMMARY_TABLE}_history")

    # Collect the list of projects tracked by L2Beat
    projects = []
    for project_data in projects_summary:
        projects.append(L2BeatProject(id=project_data["id"], slug=project_data["slug"]))

    # Fetch and write TVL and ACTIVITY to BQ
    tvl_df = _process_tvl(session, projects)
    activity_df = _process_activity(session, projects)

    return {
        "summary": summary_df,
        "tvl": tvl_df,
        "activity": activity_df,
    }


def _process_tvl(session, projects: list[L2BeatProject]):
    """Pull TVL and write to BQ."""

    def fetch_tvl(p: L2BeatProject):
        url = f"https://l2beat.com/api/scaling/tvl/{p.slug}?range={TVL_QUERY_RANGE}"
        return get_data(session, url)

    tvl_df = _pull_project_data(
        projects=projects,
        fetch=fetch_tvl,
        column_schemas=TVL_SCHEMA,
    )
    overwrite_partitions_dynamic(tvl_df, BQ_DATASET, f"{TVL_TABLE}_history")
    return tvl_df


def _process_activity(session, projects: list[L2BeatProject]):
    """Pull ACTIVITY and write to BQ."""

    def fetch_activity(p: L2BeatProject):
        url = f"https://l2beat.com/api/scaling/activity/{p.slug}?range={ACTIVITY_QUERY_RANGE}"
        return get_data(session, url)

    activity_df = _pull_project_data(
        projects=projects,
        fetch=fetch_activity,
        column_schemas=ACTIVITY_SCHEMA,
    ).rename({"count": "transaction_count"})
    overwrite_partitions_dynamic(activity_df, BQ_DATASET, f"{ACTIVITY_TABLE}_history")
    return activity_df


def _pull_project_data(
    projects: list[L2BeatProject],
    fetch: Callable[[L2BeatProject], Any],
    column_schemas: dict[str, type[pl.DataType]],
) -> pl.DataFrame:
    """Pull L2Beat data for alist of projects.

    L2Beat API responses have the same structure for different endpoints. This function
    leverages that structure to turn the data feched from multiple projects into a polars
    dataframe.
    """
    # Run requests concurrenetly.
    all_data = run_concurrently(fetch, projects, max_workers=8)
    percent_success = 100.0 * sum(_["success"] for _ in all_data.values()) / len(all_data)
    if percent_success < 80:
        raise Exception("Failed to get L2Beat data for >80%% of chains")

    # Process the feched data.
    dfs = []
    for project, data in all_data.items():
        if data["success"]:
            chart_data = data["data"]["chart"]
            columns = chart_data["types"]
            values = chart_data["data"]

            # Ensure fetched data conforms to our expected schema.
            assert set(column_schemas.keys()) == set(columns)

            schema = [(col, column_schemas[col]) for col in columns]

            # Pick the last value for each date.
            project_df = (
                pl.DataFrame(values, schema=schema, orient="row")
                .with_columns(
                    id=pl.lit(project.id),
                    slug=pl.lit(project.slug),
                    dt=pl.from_epoch(pl.col("timestamp")).dt.strftime("%Y-%m-%d"),
                )
                .sort("timestamp")
                .group_by("dt", maintain_order=True)
                .last()
            )

            dfs.append(project_df)

    return pl.concat(dfs)
