import logging
from pathlib import Path
from sqlite3 import Cursor, Row
from typing import Any

import utils.asqlite as asqlite

VERSION: str = "0.0.1"
DB_FILENAME: str = "gatekeeper.db"
dir: Path = Path(__file__).parent
# DB_FILE_PATH: str = dir.joinpath(DB_FILENAME).as_posix()
DB_FILE_PATH: str = Path("/home/k8thekat/").joinpath(DB_FILENAME).as_posix()
SCHEMA_FILE_PATH: str = Path(__file__).parent.joinpath("schema.sql").as_posix()


class Base:
    """
    Gatekeeper's DATABASE

    **Most tables are running STRICT**\n
    Will raise `sqlite3.IntegrityError` if value does not match column type.
    """
    _logger: logging.Logger = logging.getLogger()
    _pool: asqlite.Pool | None

    def __init__(self, pool: asqlite.Pool | None = None) -> None:
        self._pool = pool

    @property
    def pool(self) -> asqlite.Pool:
        if self._pool is None:
            self._logger.error(msg="Database Pool has not been initialized")
            raise ValueError("Database Pool has not been initialized")
        return self._pool

    async def _fetchone(self, SQL: str, parameters: tuple[Any, ...] | dict[str, Any] | None = None) -> Row | None:
        """
        Query for a single Row.

        Args:
            SQL (str): The SQL query statement.

        Returns:
            Row | None: A Row.
        """
        if self._pool is None:
            self._pool = await asqlite.create_pool(database=DB_FILE_PATH)

        async with self.pool.acquire() as conn:
            if parameters is None:
                return await conn.fetchone(SQL)
            else:
                return await conn.fetchone(SQL, parameters)

    async def _fetchall(self, SQL: str, parameters: tuple[Any, ...] | dict[str, Any] | None = None) -> list[Row] | None:
        """
        Query for a list of Rows.

        Args:
            SQL (str): The SQL query statement.

        Returns:
            list[Row]: A list of Rows.
        """

        if self._pool is None:
            self._pool = await asqlite.create_pool(database=DB_FILE_PATH)

        async with self.pool.acquire() as conn:
            if parameters is None:
                return await conn.fetchall(SQL)
            else:
                return await conn.fetchall(SQL, parameters)

    async def _execute(self, SQL: str, parameters: tuple[Any, ...] | dict[str, Any] | None = None) -> Row | None:
        """
        Execute a SQL statement.

        Args:
            SQL (str): The SQL statement.
        """
        if self._pool is None:
            self._pool = await asqlite.create_pool(database=DB_FILE_PATH)

        async with self.pool.acquire() as conn:
            if parameters is None:
                res: asqlite.Cursor = await conn.execute(SQL)
            else:
                res = await conn.execute(SQL, parameters)
            return await res.fetchone()

    async def _execute_with_cursor(self, SQL: str, parameters: tuple[Any, ...] | dict[str, Any] | None = None) -> Cursor:
        """
        Execute a SQL statement.

        Args:
            SQL (str): The SQL statement.
        """
        if self._pool is None:
            self._pool = await asqlite.create_pool(database=DB_FILE_PATH)

        async with self.pool.acquire() as conn:
            if parameters is None:
                res: asqlite.Cursor = await conn.execute(SQL)
            else:
                res = await conn.execute(SQL, parameters)
            return res.get_cursor()

    async def _create_tables(self) -> None:
        """
        Creates the DATABASE tables from `SCHEMA_FILE_PATH`. \n

        """
        with open(file=SCHEMA_FILE_PATH, mode="r") as f:
            async with asqlite.connect(database=DB_FILE_PATH) as db:
                async with db.cursor() as cur:
                    await cur.executescript(sql_script=f.read())

    async def _get_version(self) -> str | None:
        """
        Returns the DATABASE version if it exists.

        Returns:
            str | None: DATABASE version (Major.Minor.Revision) eg `1.0.2`
        """
        # res: Row | None = await self._select_column(table="version", column="value")
        res: Row | None = await self._fetchone(SQL=f"""SELECT value FROM version""")
        return res["value"] if res is not None else None

    async def _set_version(self):
        """
        Creates DATABASE version table and sets the version value.
        """

        await self._execute(SQL="""INSERT INTO version(value) VALUES(?)""", parameters=(VERSION,))

    async def _update_version(self) -> None:
        """
        Updates the DATABASE with the current version the script is at.
        """
        await self._execute(SQL="""UPDATE version SET value=?""", parameters=(VERSION,))

    # async def _insert_row(self, table: str, column: str, value: str | int | bool) -> None | Row:
    #     """
    #     A generic SQL insert method.

    #     Args:
    #         table (str): The TABLE to be used.
    #         column (str): The COLUMN to insert into.
    #         value (str | int | bool): The VALUE to be inserted into the SQL table column specified.
    #     Raises:
    #         sqlite3.OperationalError: If the `column` or `table` does not exists.
    #     Returns:
    #         sqlite.Row | None: Returns Row.
    #     """
    #     res: Row | None = await self._fetchone(SQL=f"""INSERT INTO {table}({column}) VALUES(?) ON CONFLICT({column}) DO NOTHING RETURNING *""", parameters=(value,))
    #     return res if not None else None

    # async def _update_row_where(self, table: str, column: str, where: str | None, where_value: str | int | bool, value: str | int | bool) -> None | Row:
    #     """
    #     A generic SQL update method with a WHERE clause.

    #     Args:
    #         table (str): The TABLE to be used.
    #         column (str): The COLUMN to be updated.
    #         where (str | int | bool): The VALUE to match in the COLUMN. `WHERE {where} = ?`
    #         where_value (str | int | bool): The VALUE to search for with WHERE.
    #         value (str | int | bool): The VALUE to be updated in the SQL table column specified.

    #     Raises:
    #         sqlite3.OperationalError: If `column`or `table` does not exist.

    #     Returns:
    #         sqlite.Row | None: Returns Row.
    #     """
    #     if where is None:
    #         res: Row | None = await self._fetchone(SQL=f"""UPDATE {table} SET {column} = ? RETURNING *""", parameters=(value,))
    #     else:
    #         res = await self._fetchone(SQL=f"""UPDATE {table} SET {column} = ? WHERE {where} = ? RETURNING *""", parameters=(value, where_value))
    #     return res if not None else None

    # async def _select_column(self, table: str, column: str) -> Row | None:
    #     """
    #     A generic SQL select method.

    #     Args:
    #         table (str): The TABLE to be used.
    #         column (str): The COLUMN to be selected.

    #     Raises:
    #         sqlite3.OperationalError: If `column`or `table` does not exist.

    #     Returns:
    #         sqlite.Row | None: Returns Row.
    #     """

    #     res: Row | None = await self._fetchone(SQL=f"""SELECT {column} FROM {table}""")
    #     return res if not None else None

    # async def _select_row_where(self, table: str, column: str, where: str, value: str | int | bool) -> asqlite.List[Row] | None:
    #     """
    #     A generic SQL select method with a WHERE clause.

    #     Args:
    #         table (str): The TABLE to be used.
    #         column (str): The COLUMN to be selected. Supports wildcard `*`.
    #         where (str): The VALUE to match in the COLUMN. `WHERE {where} = ?`
    #         value (str | int | bool): The VALUE to search for.

    #     Raises:
    #         sqlite3.OperationalError: If `column`or `table` does not exist.

    #     Returns:
    #         sqlite.Row | None: Returns a list of Rows.
    #     """

    #     res: list[Row] | None = await self._fetchall(f"""SELECT {column} FROM {table} WHERE {where} = ?""", (value,))
    #     if res is not None and len(res) > 0:
    #         return res
    #     return None

    # async def _delete_row_where(self, table: str, where: str, value: str | int | bool) -> int:
    #     """
    #     A generic SQL delete method with a WHERE clause.

    #     Args:
    #         table (str): The TABLE to be used.
    #         where (str): The VALUE to match in the COLUMN. `WHERE {where} = ?`
    #         value (str | int | bool): The VALUE to search for.

    #     Raises:
    #         sqlite3.OperationalError: If `column`or `table` does not exist.

    #     Returns:
    #         int: Returns the amount of rows deleted.
    #     """

    #     async with asqlite.connect(database=DB_FILE_PATH) as db:
    #         async with db.cursor() as cur:
    #             await cur.execute(f"""DELETE FROM {table} WHERE {where} = ?""", value)
    #             res: int = cur.get_cursor().rowcount
    #             await cur.close()
    #             await db.commit()
    #             return res
