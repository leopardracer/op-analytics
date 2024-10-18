"""
TRACES SCHEMA
"""

from textwrap import dedent

from pyiceberg.types import LongType, StringType, TimestampType

from op_datasets.schemas import shared
from op_datasets.schemas.core import Column, CoreDataset

TRACES_V1_SCHEMA = CoreDataset(
    name="traces",
    versioned_location="ingestion/traces",
    goldsky_table_suffix="traces",
    block_number_col="block_number",
    doc=dedent("""Indexed Traces."""),
    columns=[
        shared.METADATA,
        shared.CHAIN,
        shared.NETWORK,
        shared.CHAIN_ID,
        # Block
        Column(
            name="dt",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr=None,
            raw_goldsky_pipeline_type=None,
            op_analytics_clickhouse_expr="formatDateTime(block_timestamp, '%Y-%m-%d') AS dt",
        ),
        Column(
            name="block_timestamp",
            field_type=TimestampType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="block_timestamp",
            raw_goldsky_pipeline_type="long",
            op_analytics_clickhouse_expr="block_timestamp",
        ),
        Column(
            name="block_number",
            field_type=LongType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="block_number",
            raw_goldsky_pipeline_type="long",
            op_analytics_clickhouse_expr="accurateCast(block_number, 'Int64') AS block_number",
        ),
        Column(
            name="block_hash",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="block_hash",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(block_hash, 'String') AS block_hash",
        ),
        # Transaction
        Column(
            name="transaction_hash",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="transaction_hash",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(transaction_hash, 'String') AS transaction_hash",
        ),
        Column(
            name="transaction_index",
            field_type=LongType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="transaction_index",
            raw_goldsky_pipeline_type="long",
            op_analytics_clickhouse_expr="accurateCast(transaction_index, 'Int64') AS transaction_index",
        ),
        Column(
            name="from_address",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="from_address",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(from_address, 'String') AS from_address",
        ),
        Column(
            name="to_address",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="to_address",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(to_address, 'String') AS to_address",
        ),
        Column(
            name="value_64",
            field_type=LongType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="value",
            raw_goldsky_pipeline_type="decimal",
            op_analytics_clickhouse_expr="accurateCastOrNull(value, 'Int64') AS value_64",
            doc="Lossy value downcasted to Int64 to be compatible with BigQuery data types.",
        ),
        Column(
            name="value_lossless",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="value",
            raw_goldsky_pipeline_type="decimal",
            op_analytics_clickhouse_expr="cast(value, 'String') AS value_lossless",
        ),
        Column(
            name="input",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="input",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="input",
        ),
        Column(
            name="output",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="output",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="output",
        ),
        # Trace
        Column(
            name="trace_type",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="trace_type",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(trace_type, 'String') AS trace_type",
        ),
        Column(
            name="call_type",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="call_type",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(call_type, 'String') AS call_type",
        ),
        Column(
            name="reward_type",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="reward_type",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(reward_type, 'String') AS reward_type",
        ),
        Column(
            name="gas",
            field_type=LongType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="gas",
            raw_goldsky_pipeline_type="long",
            op_analytics_clickhouse_expr="accurateCast(gas, 'Int64') AS gas",
        ),
        Column(
            name="gas_used",
            field_type=LongType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="gas_used",
            raw_goldsky_pipeline_type="long",
            op_analytics_clickhouse_expr="accurateCast(gas_used, 'Int64') AS gas_used",
        ),
        Column(
            name="subtraces",
            field_type=LongType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="subtraces",
            raw_goldsky_pipeline_type="long",
            op_analytics_clickhouse_expr="accurateCast(subtraces, 'Int64') AS subtraces",
        ),
        Column(
            name="trace_address",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="trace_address",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(trace_address, 'String') AS trace_address",
        ),
        Column(
            name="error",
            field_type=StringType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="error",
            raw_goldsky_pipeline_type="string",
            op_analytics_clickhouse_expr="cast(error, 'String') AS error",
        ),
        Column(
            name="status",
            field_type=LongType(),
            required=True,
            json_rpc_method=None,
            json_rpc_field_name=None,
            raw_goldsky_pipeline_expr="status",
            raw_goldsky_pipeline_type="long",
            op_analytics_clickhouse_expr="accurateCast(status, 'Int64') AS status",
        ),
    ],
)
