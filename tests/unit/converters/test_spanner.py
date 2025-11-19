import pytest

from recap.converters.spanner import SpannerConverter
from recap.types import (
    BoolType,
    BytesType,
    FloatType,
    IntType,
    ListType,
    StringType,
    StructType,
)


@pytest.mark.parametrize(
    "spanner_type,expected",
    [
        ("BOOL", BoolType()),
        ("INT64", IntType(bits=64, signed=True)),
        ("FLOAT64", FloatType(bits=64)),
        ("STRING(MAX)", StringType(bytes_=10485760, variable=True)),
        ("STRING(256)", StringType(bytes_=256 * 4, variable=True)),
        ("BYTES(MAX)", BytesType(bytes_=10485760, variable=True)),
        ("BYTES(1024)", BytesType(bytes_=1024, variable=True)),
        (
            "DATE",
            IntType(
                logical="build.recap.Date",
                bits=32,
                unit="day",
            ),
        ),
        (
            "TIMESTAMP",
            IntType(
                logical="build.recap.Timestamp",
                bits=64,
                unit="nanosecond",
            ),
        ),
        (
            "NUMERIC",
            BytesType(
                logical="build.recap.Decimal",
                bytes_=16,
                variable=False,
                precision=38,
                scale=9,
            ),
        ),
        (
            "JSON",
            StringType(
                logical="build.recap.JSON",
                bytes_=10485760,
                variable=True,
            ),
        ),
    ],
)
def test_spanner_type_conversion(spanner_type, expected):
    """Test conversion of Spanner types to Recap types."""
    converter = SpannerConverter()
    result = converter._parse_type(spanner_type)
    assert result == expected


def test_array_type():
    """Test conversion of ARRAY types."""
    converter = SpannerConverter()
    result = converter._parse_type("ARRAY<INT64>")
    expected = ListType(values=IntType(bits=64, signed=True))
    assert result == expected


def test_nested_array_type():
    """Test conversion of nested ARRAY types."""
    converter = SpannerConverter()
    result = converter._parse_type("ARRAY<STRING(MAX)>")
    expected = ListType(values=StringType(bytes_=10485760, variable=True))
    assert result == expected


def test_to_recap():
    """Test conversion of column metadata to StructType."""
    converter = SpannerConverter()
    columns = [
        {
            "COLUMN_NAME": "id",
            "SPANNER_TYPE": "INT64",
            "IS_NULLABLE": "NO",
            "ORDINAL_POSITION": 1,
        },
        {
            "COLUMN_NAME": "name",
            "SPANNER_TYPE": "STRING(100)",
            "IS_NULLABLE": "YES",
            "ORDINAL_POSITION": 2,
        },
        {
            "COLUMN_NAME": "created_at",
            "SPANNER_TYPE": "TIMESTAMP",
            "IS_NULLABLE": "NO",
            "ORDINAL_POSITION": 3,
        },
    ]

    result = converter.to_recap(columns)

    assert isinstance(result, StructType)
    assert len(result.fields) == 3

    # Check first field (id - not nullable)
    assert result.fields[0].extra_attrs["name"] == "id"
    assert isinstance(result.fields[0], IntType)
    assert result.fields[0].bits == 64

    # Check second field (name - nullable)
    assert result.fields[1].extra_attrs["name"] == "name"
    # Should be a Union type due to nullable
    assert result.fields[1].is_nullable()

    # Check third field (created_at - not nullable)
    assert result.fields[2].extra_attrs["name"] == "created_at"
    assert isinstance(result.fields[2], IntType)
    assert result.fields[2].logical == "build.recap.Timestamp"


def test_unknown_type():
    """Test that unknown types raise ValueError."""
    converter = SpannerConverter()
    with pytest.raises(ValueError, match="Unknown Spanner type"):
        converter._parse_type("UNKNOWN_TYPE")
