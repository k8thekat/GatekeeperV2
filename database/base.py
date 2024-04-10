import logging
from pathlib import Path
from sqlite3 import Row

import utils.asqlite as asqlite

VERSION: str = "0.0.1"
DB_FILENAME: str = "gatekeeper.db"

VERSION_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS version (
    value TEXT COLLATE NO CASE NOT NULL
)STRICT"""


class Base():
    """
    Gatekeeper's DATABASE

    **Most tables are running STRICT**\n
    Will raise `sqlite3.IntegrityError` if value does not match column type.
    """

    def __init__(self) -> None:
        _dir: Path = Path(__file__).parent
        self._db_file_path: str = _dir.joinpath(DB_FILENAME).as_posix()
        self._logger = logging.getLogger()
        self._version: str = VERSION

    async def create_tables(self, schema: str | list[str]) -> None:
        """
        Creates the DATABASE tables. \n
        ** Please have `CREATE TABLE IF NOT EXISTS` as your first line** 

        Args:
            schema (str | list[str]): SQLITE schema setup. Supports list of schema's or single entry.
        """
        if isinstance(schema, list):
            for table in schema:
                return await self.create_tables(schema=table)
        else:
            async with asqlite.connect(self._db_file_path) as db:
                await db.execute(schema)
                await db.commit()

    async def _initialize_tables(self) -> None:
        """
        Creates the `Base` table.

        """
        tables = [
            VERSION_SETUP_SQL
        ]
        await self.create_tables(schema=tables)

    @property
    async def version(self) -> str | None:
        """
        Returns the DATABASE version if it exists.

        Returns:
            str | None: DATABASE version (Major.Minor.Revision) eg `1.0.2`
        """
        res = await self._select_column(table="version", column="value")
        if isinstance(res, str):
            return res
        else:
            return None

    async def _set_version(self):
        """
        Creates DATABASE version table and sets the version value.
        """

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""INSERT INTO version(value) VALUES(?)""", VERSION)
                await db.commit()
                await cur.close()

    async def _update_version(self) -> None:
        """
        Updates the DATABASE with the current version the script is at.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""UPDATE version SET value = ?""", VERSION)
                await db.commit()
                await cur.close()

    async def _insert_row(self, table: str, column: str, value: str | int | bool) -> None:
        """
        A generic SQL insert method.

        Args:
            table (str): The TABLE to be used.
            column (str): The COLUMN to insert into.
            value (str | int | bool): The VALUE to be inserted into the SQL table column specified.
        Raises:
            sqlite3.OperationalError: If the `column` or `table` does not exists.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute(f"""INSERT INTO {table}({column}) VALUES(?) ON CONFLICT({column}) DO NOTHING RETURNING *""", value)
                await db.commit()
                await cur.close()

    async def _update_row(self, table: str, column: str, where: str | None, value: str | int | bool) -> None:
        """
        A generic SQL update method with a WHERE clause.

        Args:
            table (str): The TABLE to be used.
            column (str): The COLUMN to be updated.
            where (str | int | bool): The VALUE to match in the COLUMN. `WHERE {where} = ?`
            value (str | int | bool): The VALUE to be updated in the SQL table column specified.

        Raises:
            sqlite3.OperationalError: If `column`or `table` does not exist.
        """

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                if where is None:
                    await cur.execute(f"""UPDATE {table} SET {column} = ?""", value)
                else:
                    await cur.execute(f"""UPDATE {table} SET {column} = ? WHERE {where} = ?""", value)
                await db.commit()
                await cur.close()

    async def _update_column(self, table: str, column: str, value: str | int | bool) -> None:
        """
        A generic SQL update method.

        Args:
            table (str): The TABLE to be used.
            column (str): The COLUMN to be updated.
            value (str | int | bool): The VALUE to be updated in the SQL table column specified.

        Raises:
            sqlite3.OperationalError: If `column`or `table` does not exist.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute(f"""UPDATE {table} SET {column} = ?""", value)
                await db.commit()
                await cur.close()

    async def _select_column(self, table: str, column: str) -> str | int | bool | None:
        """
        A generic SQL select method.

        Args:
            table (str): The TABLE to be used.
            column (str): The COLUMN to be selected.

        Raises:
            sqlite3.OperationalError: If `column`or `table` does not exist.

        Returns:
            str | int | bool | None: Returns the value of the column provided.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute(f"""SELECT {column} FROM {table}""")
                res = await cur.fetchone()
                await cur.close()
                # return res[f"{column}"] if not None else None
                return res[column] if not None else None

    async def _select_row_where(self, table: str, column: str, where: str, value: str | int | bool):
        """
        A generic SQL select method with a WHERE clause. 

        Args:
            table (str): The TABLE to be used.
            column (str): The COLUMN to be selected. Supports wildcard.
            where (str): The VALUE to match in the COLUMN. `WHERE {where} = ?`
            value (str | int | bool): The VALUE to search for.

        Raises:
            sqlite3.OperationalError: If `column`or `table` does not exist.

        Returns:
            str | int | bool | None: Returns the value of the column provided.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute(f"""SELECT {column} FROM {table} WHERE {where} = ?""", value)
                res = await cur.fetchone()
                await cur.close()
                # if res == None:
                #     return res

                if column == "*":
                    return res if not None else None
                else:
                    # return None if res is None else res[f"{column}"]
                    return None if res is None else res[column]
