from op_coreutils.logger import bind_contextvars, clear_contextvars, structlog
from op_coreutils.partitioned import DataLocation
from op_coreutils.duckdb_inmem import init_client

from .construct import construct_tasks
from .registry import REGISTERED_INTERMEDIATE_MODELS, load_model_definitions
from .task import IntermediateModelsTask
from .types import NamedRelations
from .udfs import create_duckdb_macros

log = structlog.get_logger()


def compute_intermediate(
    chains: list[str],
    models: list[str],
    range_spec: str,
    read_from: DataLocation,
    write_to: list[DataLocation],
    dryrun: bool,
    force: bool = False,
):
    clear_contextvars()

    # Load python functions that define registered data models.
    load_model_definitions()

    for model in models:
        should_exit = False
        if model not in REGISTERED_INTERMEDIATE_MODELS:
            should_exit = True
            log.error("Model is not registered: {model}")
        if should_exit:
            log.error("Cannot run on unregistered models. Will exit.")
            exit(1)

    tasks = construct_tasks(chains, models, range_spec, read_from, write_to)

    if dryrun:
        log.info("DRYRUN: No work will be done.")
        return

    for i, task in enumerate(tasks):
        bind_contextvars(
            task=f"{i+1}/{len(tasks)}",
            **task.data_reader.contextvars,
        )

        # Check output/input status for the task.
        checker(task)

        # Decide if we can run this task.
        if not task.data_reader.inputs_ready:
            log.warning("Task inputs are not ready. Skipping this task.")
            continue

        # Decide if we need to run this task.
        if task.data_writer.is_complete and not force:
            continue
        if force:
            log.info("Force flag detected. Forcing execution.")
            task.data_writer.force = True

        executor(task)

        writer(task)


def executor(task: IntermediateModelsTask) -> None:
    """Execute the model computations."""

    # Load shared DuckDB UDFs.
    client = init_client()
    create_duckdb_macros(client)

    for model in task.models:
        # Get the model.
        im_model = REGISTERED_INTERMEDIATE_MODELS[model]

        # Prepare input data.
        input_tables: NamedRelations = {}
        for dataset in im_model.input_datasets:
            input_tables[dataset] = task.data_reader.duckdb_relation(dataset)

        # Execute the model.
        model_results = im_model.func(
            duckdb_client=client,
            input_tables=input_tables,
        )

        # Store outputs produced by the model.
        for output_name, output in model_results.items():
            task.store_output(output_name, output)

        produced_datasets = set(task.output_duckdb_relations.keys())
        if produced_datasets != set(im_model.expected_output_datasets):
            raise RuntimeError(f"model {model!r} produced unexpected datasets: {produced_datasets}")


def writer(task: IntermediateModelsTask):
    # TODO: implementt writing
    pass
    # marker_kwargs = dict(
    #     process_name="default",
    #     additional_columns=dict(
    #         model_name=...,
    #     ),
    #     additional_columns_schema=[
    #         pa.field("chain", pa.string()),
    #         pa.field("dt", pa.date32()),
    #         pa.field("model_name", pa.string()),
    #     ],
    # )

    # task.data_writer.write_all(
    #     dataframes=task.output_duckdb_relations,
    #     basename=task.block_batch.construct_parquet_filename(),
    #     marker_kwargs=marker_kwargs,
    # )


def checker(task: IntermediateModelsTask) -> None:
    if task.data_writer.all_complete():
        task.data_writer.is_complete = True
        task.data_reader.inputs_ready = True
        return
