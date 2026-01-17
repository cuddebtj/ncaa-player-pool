import io
import logging
import json
import os
from dataclasses import dataclass
from typing import Literal

import psycopg
from dotenv import load_dotenv
from psycopg import sql

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class DatabaseParameters:
    __slots__ = ["db_conn", "schema_name", "table_name"]
    db_conn: psycopg.Connection
    table_name: str | None
    schema_name: Literal["public"] = "public"


def get_conn_str():
    try:
        connection_string = os.getenv("POSTGRES_CONN_STR")
        db_conn = psycopg.connect(connection_string)
        return db_conn

    except psycopg.DatabaseError as connection_error:
        logger.exception(connection_error, exc_info=True, stack_info=True)
        raise connection_error

    except Exception as error:
        logger.exception(error, exc_info=True, stack_info=True)
        raise error


def data_to_db(
    resp_data: dict,
    db_conn: psycopg.Connection,
    table_name: str,
    schema_name: str = "public",
) -> None:
    columns = ["json"]
    logger.info(f"Json load to table {schema_name}.{table_name}.")
    copy_statement = """COPY {table_name} ({column_names})
    FROM STDIN"""

    file_buffer = io.StringIO()  # type: ignore
    json.dump(resp_data, file_buffer)  # type: ignore
    file_buffer.seek(0)

    # set_delete_statement = sql.SQL(
    #     "CALL public.delete_duplicate_data({schema_name}, {table_name});"
    # ).format(
    #     schema_name=sql.Literal(schema_name),
    #     table_name=sql.Literal(table_name),
    # )
    # logger.info(f"SQL Delete Statement:\n\t{set_delete_statement}")

    set_schema_statement = sql.SQL("set search_path to {};").format(
        sql.Identifier(schema_name)
    )

    column_names = sql.SQL(", ").join([sql.Identifier(col) for col in columns])
    copy_query = sql.SQL(copy_statement).format(
        table_name=sql.Identifier(table_name),
        column_names=column_names,  # type: ignore
    )

    logger.info(f"SQL Copy Statement:\n\t{copy_query}")

    try:
        curs = db_conn.cursor()
        curs.execute(set_schema_statement)

        with curs.copy(copy_query) as copy:
            copy.write(file_buffer.read())

        status_msg = curs.statusmessage
        logger.info(f"Response copied successfully.\n\t{status_msg}")

    except (Exception, psycopg.DatabaseError) as error:  # type: ignore
        logger.exception(
            f"Error with database:\n\n{error}\n\n", exc_info=True, stack_info=True
        )
        db_conn.rollback()
        logger.info("Postgres transaction rolled back.")
        raise error

    finally:
        db_conn.commit()
        logger.info("Postgres transaction commited.")
