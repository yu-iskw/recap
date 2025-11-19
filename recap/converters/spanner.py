from typing import Any

from recap.converters.dbapi import DbapiConverter
from recap.types import (
    BoolType,
    BytesType,
    FloatType,
    IntType,
    ListType,
    NullType,
    RecapType,
    StringType,
    StructType,
    UnionType,
)


class SpannerConverter(DbapiConverter):
    def _parse_type(self, column_props: dict[str, Any]) -> RecapType:
        data_type = column_props["SPANNER_TYPE"].upper()
        is_nullable = column_props["IS_NULLABLE"].upper() == "YES"
        base_type = None

        if data_type == "BOOL":
            base_type = BoolType()
        elif data_type == "INT64":
            base_type = IntType(bits=64, signed=True)
        elif data_type == "FLOAT64":
            base_type = FloatType(bits=64)
        elif data_type.startswith("STRING"):
            base_type = StringType()
        elif data_type.startswith("BYTES"):
            base_type = BytesType()
        elif data_type == "TIMESTAMP":
            base_type = IntType(
                bits=64,
                logical="build.recap.Timestamp",
                unit="nanosecond",
            )
        elif data_type == "DATE":
            base_type = IntType(
                bits=32,
                logical="build.recap.Date",
                unit="day",
            )
        elif data_type == "NUMERIC":
            base_type = BytesType(
                logical="build.recap.Decimal",
                bytes_=32,
                variable=False,
                precision=38,
                scale=9,
            )
        elif data_type == "JSON":
            base_type = StringType(logical="build.recap.JSON")
        elif data_type.startswith("ARRAY"):
            # Ex: ARRAY<STRING(MAX)> -> STRING(MAX)
            nested_type_str = data_type[6:-1]
            nested_type = self._parse_type(
                {
                    "SPANNER_TYPE": nested_type_str,
                    "IS_NULLABLE": "YES",
                }
            )
            base_type = ListType(values=nested_type)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

        if is_nullable:
            return UnionType(types=[NullType(), base_type])

        return base_type

    def to_recap(self, columns: list[dict[str, Any]]) -> StructType:
        fields = []
        for column in columns:
            field_type = self._parse_type(column)
            type_args = {
                "name": column["COLUMN_NAME"],
                "default": column["COLUMN_DEFAULT"],
            }
            if isinstance(field_type, UnionType):
                type_args["types"] = field_type.types
            elif isinstance(field_type, ListType):
                type_args["values"] = field_type.values
            else:
                # Unpack field_type's attributes into type_args.
                # field_type is a pydantic model, so we can use .dict()
                type_args.update(field_type.dict())
            field_instance = type(field_type)(**type_args)
            fields.append(field_instance)
        return StructType(fields=fields)
