"""Inspect the configured schema and bootstrap a missing local MySQL database."""
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool


def inspect_startup_tables(engine, *, public_deployment):
    try:
        return set(inspect(engine).get_table_names())
    except OperationalError as error:
        url = engine.url
        missing_database = error.orig.args[:1] == (1049,)
        if (not missing_database or public_deployment or url.get_backend_name() != 'mysql'
                or url.host not in ('127.0.0.1', 'localhost', '::1') or not url.database):
            raise

    # Connect to the same instance without selecting the missing database.
    server = create_engine(url.set(database=''), poolclass=NullPool)
    try:
        name = server.dialect.identifier_preparer.quote_identifier(url.database)
        with server.begin() as connection:
            connection.exec_driver_sql(
                f'CREATE DATABASE IF NOT EXISTS {name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
            )
    finally:
        server.dispose()
    return set(inspect(engine).get_table_names())
