from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

from google.cloud import spanner

from recap.converters.spanner import SpannerConverter
from recap.types import StructType


class SpannerClient:
    """
    Client for reading schemas from Google Cloud Spanner.
    """

    def __init__(
        self, client: spanner.Client, converter: SpannerConverter | None = None
    ):
        self.client = client
        self.converter = converter or SpannerConverter()

    @staticmethod
    @contextmanager
    def create(**_) -> Generator[SpannerClient, None, None]:
        """
        Create a Spanner client.

        :return: SpannerClient instance
        """
        with spanner.Client() as client:
            yield SpannerClient(client)

    @staticmethod
    def parse(method: str, paths: list[str], **_) -> tuple[str, list[Any]]:
        """
        Parse URL paths for Spanner operations.

        Spanner URL format: spanner://instance/database/table
        The project is determined from default credentials (GOOGLE_APPLICATION_CREDENTIALS
        or gcloud CLI configuration).

        URL components:
        - paths[0]: instance ID
        - paths[1]: database ID
        - paths[2]: table name (optional, for schema method)

        :param method: Either "ls" or "schema"
        :param paths: URL path components
        :return: Tuple of connection URL and method arguments
        """
        instance, database, table = (paths + [None, None, None])[:3]

        match method:
            case "ls" | "schema":
                return ("spanner://", [None, instance, database, table])
            case _:
                raise ValueError("Invalid method")

    def ls(
        self,
        project: str | None = None,
        instance_id: str | None = None,
        database_id: str | None = None,
    ) -> list[str]:
        """
        List Spanner resources at different levels of the hierarchy.

        :param project: Project ID (if None, lists instances in default project)
        :param instance_id: Instance ID (if provided, lists databases)
        :param database_id: Database ID (if provided, lists tables)
        :return: List of resource names
        """
        match (project, instance_id, database_id):
            case (None, None, None):
                # List instances in the default project
                return self.ls_instances()
            case (str(_), None, None):
                # List instances in specified project (not commonly needed, but supported)
                return self.ls_instances()
            case (_, str(instance_id), None):
                # List databases in instance
                return self.ls_databases(instance_id)
            case (_, str(instance_id), str(database_id)):
                # List tables in database
                return self.ls_tables(instance_id, database_id)
            case _:
                raise ValueError("Invalid arguments")

    def ls_instances(self) -> list[str]:
        """
        List all Spanner instances in the project.

        :return: List of instance IDs
        """
        return [instance.instance_id for instance in self.client.list_instances()[0]]

    def ls_databases(self, instance_id: str) -> list[str]:
        """
        List all databases in a Spanner instance.

        :param instance_id: Instance ID
        :return: List of database IDs
        """
        instance = self.client.instance(instance_id)
        return [database.database_id for database in instance.list_databases()]

    def ls_tables(self, instance_id: str, database_id: str) -> list[str]:
        """
        List all tables in a Spanner database.

        :param instance_id: Instance ID
        :param database_id: Database ID
        :return: List of table names
        """
        instance = self.client.instance(instance_id)
        database = instance.database(database_id)

        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_catalog = '' AND table_schema = ''
                ORDER BY table_name ASC
                """
            )
            return [row[0] for row in results]

    def schema(
        self,
        project: str | None,
        instance_id: str,
        database_id: str,
        table_name: str,
        **_,
    ) -> StructType:
        """
        Get the schema for a Spanner table.

        :param project: Project ID (unused, kept for API compatibility)
        :param instance_id: Instance ID
        :param database_id: Database ID
        :param table_name: Table name
        :return: Recap StructType representing the table schema
        """
        instance = self.client.instance(instance_id)
        database = instance.database(database_id)

        with database.snapshot() as snapshot:
            results = snapshot.execute_sql(
                """
                SELECT
                    column_name,
                    spanner_type,
                    is_nullable,
                    ordinal_position
                FROM information_schema.columns
                WHERE table_name = @table_name
                    AND table_catalog = ''
                    AND table_schema = ''
                ORDER BY ordinal_position ASC
                """,
                params={"table_name": table_name},
                param_types={"table_name": spanner.param_types.STRING},
            )

            columns = []
            for row in results:
                columns.append(
                    {
                        "COLUMN_NAME": row[0],
                        "SPANNER_TYPE": row[1],
                        "IS_NULLABLE": row[2],
                        "ORDINAL_POSITION": row[3],
                    }
                )

        return self.converter.to_recap(columns)
