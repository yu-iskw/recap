from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from recap.clients.dbapi import Connection, DbapiClient
from recap.converters.spanner import SpannerConverter
from recap.types import StructType

SPANNER_CONNECT_ARGS = {
    "instance_id",
    "database_id",
    "project",
    "credentials_path",
    "credentials_base64",
    "pool",
    "user_agent",
}


class SpannerClient(DbapiClient):
    def __init__(
        self,
        connection: Connection,
        converter: SpannerConverter = SpannerConverter(),
    ) -> None:
        super().__init__(connection, converter)

    @staticmethod
    @contextmanager
    def create(
        paths: list[str] | None = None,
        **url_args,
    ) -> Generator[SpannerClient, None, None]:
        from google.cloud import spanner_dbapi

        # Filter kwargs to only include valid ones for spanner_dbapi.connect()
        url_args = {k: v for k, v in url_args.items() if k in SPANNER_CONNECT_ARGS}

        with spanner_dbapi.connect(**url_args) as connection:
            yield SpannerClient(connection)

    def ls_catalogs(self) -> list[str]:
        return []

    def ls_schemas(self, catalog: str) -> list[str]:
        return [""]

    def ls_tables(self, catalog: str, schema: str) -> list[str]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = ''
            """
        )
        return [row[0] for row in cursor.fetchall()]

    def schema(self, catalog: str, schema: str, table: str) -> StructType:
        cursor = self.connection.cursor()
        cursor.execute(
            f"""
            SELECT
                column_name,
                spanner_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = {self.param_style}
            AND table_schema = ''
            """,
            (table,),
        )
        names = [name[0].upper() for name in cursor.description]
        return self.converter.to_recap(
            [dict(zip(names, row)) for row in cursor.fetchall()]
        )
