from unittest.mock import MagicMock, patch

from recap.clients.spanner import SpannerClient
from recap.types import IntType, ListType, NullType, StringType, StructType, UnionType


@patch("google.cloud.spanner_dbapi.connect")
def test_spanner_schema(mock_spanner_connect):
    # Mock the DBAPI connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_spanner_connect.return_value.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value = mock_cursor

    # Mock the return value of cursor.description
    mock_cursor.description = [
        ("COLUMN_NAME",),
        ("SPANNER_TYPE",),
        ("IS_NULLABLE",),
        ("COLUMN_DEFAULT",),
    ]

    # Mock the return value of cursor.fetchall()
    mock_cursor.fetchall.return_value = [
        ("test_column", "STRING(MAX)", "YES", None),
        ("test_column2", "ARRAY<INT64>", "NO", None),
    ]

    # Call the schema method
    with SpannerClient.create(
        instance_id="test-instance", database_id="test-database"
    ) as client:
        schema = client.schema("test-catalog", "test-schema", "test-table")

        # Assert that the schema is correct
        assert schema == StructType(
            fields=[
                UnionType(
                    types=[
                        NullType(),
                        StringType(),
                    ],
                    name="test_column",
                    default=None,
                ),
                ListType(
                    values=UnionType(
                        types=[
                            NullType(),
                            IntType(
                                bits=64,
                                signed=True,
                            ),
                        ]
                    ),
                    name="test_column2",
                    default=None,
                ),
            ]
        )
