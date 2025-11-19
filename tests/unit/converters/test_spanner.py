from recap.converters.spanner import SpannerConverter
from recap.types import (
    BoolType,
    BytesType,
    FloatType,
    IntType,
    ListType,
    NullType,
    StringType,
    UnionType,
)


def test_spanner_converter():
    converter = SpannerConverter()

    # Test base types
    assert isinstance(
        converter._parse_type({"SPANNER_TYPE": "BOOL", "IS_NULLABLE": "NO"}), BoolType
    )
    assert isinstance(
        converter._parse_type({"SPANNER_TYPE": "INT64", "IS_NULLABLE": "NO"}), IntType
    )
    assert isinstance(
        converter._parse_type({"SPANNER_TYPE": "FLOAT64", "IS_NULLABLE": "NO"}),
        FloatType,
    )
    assert isinstance(
        converter._parse_type({"SPANNER_TYPE": "STRING(MAX)", "IS_NULLABLE": "NO"}),
        StringType,
    )
    assert isinstance(
        converter._parse_type({"SPANNER_TYPE": "BYTES(MAX)", "IS_NULLABLE": "NO"}),
        BytesType,
    )

    # Test logical types
    timestamp_type = converter._parse_type(
        {"SPANNER_TYPE": "TIMESTAMP", "IS_NULLABLE": "NO"}
    )
    assert isinstance(timestamp_type, IntType)
    assert timestamp_type.logical == "build.recap.Timestamp"

    date_type = converter._parse_type({"SPANNER_TYPE": "DATE", "IS_NULLABLE": "NO"})
    assert isinstance(date_type, IntType)
    assert date_type.logical == "build.recap.Date"

    numeric_type = converter._parse_type(
        {"SPANNER_TYPE": "NUMERIC", "IS_NULLABLE": "NO"}
    )
    assert isinstance(numeric_type, BytesType)
    assert numeric_type.logical == "build.recap.Decimal"

    json_type = converter._parse_type({"SPANNER_TYPE": "JSON", "IS_NULLABLE": "NO"})
    assert isinstance(json_type, StringType)
    assert json_type.logical == "build.recap.JSON"

    # Test array type
    array_type = converter._parse_type(
        {"SPANNER_TYPE": "ARRAY<STRING(MAX)>", "IS_NULLABLE": "NO"}
    )
    assert isinstance(array_type, ListType)
    assert isinstance(array_type.values, UnionType)
    assert any(isinstance(t, StringType) for t in array_type.values.types)

    # Test nullable type
    nullable_type = converter._parse_type(
        {"SPANNER_TYPE": "BOOL", "IS_NULLABLE": "YES"}
    )
    assert isinstance(nullable_type, UnionType)
    assert any(isinstance(t, NullType) for t in nullable_type.types)
    assert any(isinstance(t, BoolType) for t in nullable_type.types)
