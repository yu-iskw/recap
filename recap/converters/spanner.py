from __future__ import annotations

from typing import Any

from recap.types import (
    BoolType,
    BytesType,
    FloatType,
    IntType,
    ListType,
    StringType,
    StructType,
)


class SpannerConverter:
    """
    Converter for Google Cloud Spanner data types to Recap types.
    """

    def to_recap(self, columns: list[dict[str, Any]]) -> StructType:
        """
        Convert Spanner columns to a Recap StructType.

        :param columns: List of column dictionaries from INFORMATION_SCHEMA.COLUMNS
        :return: Recap StructType representing the table schema
        """
        recap_fields = []

        for column in columns:
            column_name = column["COLUMN_NAME"]
            spanner_type = column["SPANNER_TYPE"]
            is_nullable = column["IS_NULLABLE"] == "YES"

            field_type = self._parse_type(spanner_type)

            if is_nullable:
                field_type = field_type.make_nullable()

            field_type.extra_attrs["name"] = column_name
            recap_fields.append(field_type)

        return StructType(recap_fields)

    def _parse_type(self, spanner_type: str) -> "RecapType":  # noqa: F821
        """
        Parse a Spanner type string into a Recap type.

        Spanner types come in formats like:
        - BOOL
        - INT64
        - FLOAT64
        - STRING(MAX)
        - STRING(256)
        - BYTES(MAX)
        - DATE
        - TIMESTAMP
        - NUMERIC
        - JSON
        - ARRAY<INT64>
        - ARRAY<STRING(MAX)>

        :param spanner_type: Spanner type string
        :return: Corresponding Recap type
        """
        spanner_type = spanner_type.strip()

        # Handle ARRAY types
        if spanner_type.startswith("ARRAY<"):
            # Extract the element type (e.g., "INT64" from "ARRAY<INT64>")
            element_type_str = spanner_type[6:-1]  # Remove "ARRAY<" and ">"
            element_type = self._parse_type(element_type_str)
            return ListType(values=element_type)

        # Handle STRING with length
        if spanner_type.startswith("STRING("):
            # Extract length (e.g., "256" from "STRING(256)" or "MAX" from "STRING(MAX)")
            length_str = spanner_type[7:-1]  # Remove "STRING(" and ")"
            if length_str == "MAX":
                # Max string length in Spanner is 10 MiB = 10485760 bytes
                return StringType(bytes_=10485760, variable=True)
            else:
                # Length is specified in characters, not bytes
                # For UTF-8, max bytes = length * 4
                return StringType(bytes_=int(length_str) * 4, variable=True)

        # Handle BYTES with length
        if spanner_type.startswith("BYTES("):
            # Extract length (e.g., "256" from "BYTES(256)" or "MAX" from "BYTES(MAX)")
            length_str = spanner_type[6:-1]  # Remove "BYTES(" and ")"
            if length_str == "MAX":
                # Max bytes length in Spanner is 10 MiB = 10485760 bytes
                return BytesType(bytes_=10485760, variable=True)
            else:
                return BytesType(bytes_=int(length_str), variable=True)

        # Handle simple types
        match spanner_type:
            case "BOOL":
                return BoolType()
            case "INT64":
                return IntType(bits=64, signed=True)
            case "FLOAT64":
                return FloatType(bits=64)
            case "STRING":
                # STRING without length specification, use MAX
                return StringType(bytes_=10485760, variable=True)
            case "BYTES":
                # BYTES without length specification, use MAX
                return BytesType(bytes_=10485760, variable=True)
            case "DATE":
                return IntType(
                    logical="build.recap.Date",
                    bits=32,
                    unit="day",
                )
            case "TIMESTAMP":
                return IntType(
                    logical="build.recap.Timestamp",
                    bits=64,
                    unit="nanosecond",
                )
            case "NUMERIC":
                # Spanner NUMERIC supports up to 38 digits precision and 9 digits scale
                return BytesType(
                    logical="build.recap.Decimal",
                    bytes_=16,
                    variable=False,
                    precision=38,
                    scale=9,
                )
            case "JSON":
                # JSON is stored as a string with special validation
                return StringType(
                    logical="build.recap.JSON",
                    bytes_=10485760,
                    variable=True,
                )
            case _:
                raise ValueError(f"Unknown Spanner type: {spanner_type}")
