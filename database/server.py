
from dataclasses import dataclass
from typing import Any, Literal

from database.db import Database
from utils import asqlite

SERVER_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY NOT NULL,
    instance_id TEXT NOT NULL UNIQUE,
    instance_name TEXT NOT NULL,
    ip TEXT,
    whitelist INTEGER ,
    whitelist_disabled INTEGER,
    donator INTEGER,
    chat_channel INTEGER,
    chat_prefix TEXT,
    event_channel INTEGER,
    role INTEGER,
    avatar_url TEXT,
    hidden INTEGER
)STRICT"""


@dataclass()
class Server(Database):
    """
    Represents the data from the Database table servers.

    **THIS MUST BE UPDATED TO REPRESENT THE servers DATABASE SCHEMA AT ALL TIMES** \n
    - The dataclass is used to validate column names and column type constraints.

    """
    id: int
    instance_id: str
    instance_name: str
    ip: str = ""
    whitelist: bool = False
    whitelist_disabled: bool = False
    donator: bool = False
    chat_channel: int = 0
    chat_prefix: str = ""
    event_channel: int = 0
    role: int = 0
    avatar_url: str = ""
    hidden: bool = False

    def __setattr__(self, name: str, value: Any) -> Any:
        """
        We are overwriting setattr because SQLite returns 0 or 1 for True/False. \n
        Convert it to a `bool` for human readable.

        """
        if hasattr(Server, name) and (type(getattr(Server, name)) == bool):
            return super().__setattr__(name, bool(value))
        return super().__setattr__(name, value)


class DBServer(Database):
    def __init__(self) -> None:
        super().__init__()

    async def _initialize_tables(self) -> None:
        """
        Creates the `DBServer` tables.

        """
        tables: list[str] = [SERVER_SETUP_SQL]
        await self.create_tables(schema=tables)

    async def add_server(self, instance_id: str, instance_name: str) -> Literal[True] | None:
        """
        Add a AMP Instance ID/Name to the `servers` table.

        Args:
            instance_id (str): AMP Instance ID
            instance_name (str): AMP Instance Name

        Raises:
            ValueError: Duplicate instance_id value in the database.

        Returns:
            bool | None: Returns `True` on successful execution of Database insert; otherwise `None`.
        """
        _exists = await self._select_row_where(table="servers", column="instance_id", where="instance_id", value=instance_id)
        if _exists != None:
            raise ValueError(f"The Instance ID provided already exists in the Database. {instance_id}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""INSERT INTO servers(instance_id, instance_name) VALUES(?, ?)""", instance_id, instance_name)
                # res = await cur.fetchone()
                await db.commit()
                return True
                # return Server(**res) if res is not None else None

    async def update_server(self, instance_id: str, column: str, value: bool | str | int) -> Server | None:
        """
        Update an existing instance_id in the `servers` table.\n

        Specify the `column` (eg. "whitelist") and the value to be set for it (eg. True) to update said values.
        See `Server` dataclass for possible attributes.

        Args:
            instance_id (str): AMP Instance ID
            column (str): A column from the `servers` table. See also `Server()` dataclass. 
            value (bool | str | int): The value to be inserted into the column.  Will validate the type against the `Server()` dataclass.

        Raises:
            ValueError: If the `instance_id` is non-existent or the `value` for the specified `column` is not the correct type.

        Returns:
            Server | None: _description_
        """
        _exists = await self._select_row_where(table="servers", column="instance_id", where="instanceid", value=instance_id)
        if _exists == None:
            raise ValueError(f"The Instance ID provided doesn't exists in the Database. {instance_id}")

        _check = hasattr(Server, column)
        if _check is True:
            _type = type(getattr(Server, column))
        else:
            raise ValueError(f"The column provided does not match the Database Schema. {column}")

        if isinstance(value, _type):
            await self._update_column(table="servers", column=column, value=value)
            # Let's get the updated table values for provided instance_id and return a dataclass to be used.
            res = await self._select_row_where(table="servers", column="*", where="instance_id", value=instance_id)
            return Server(**res) if res is not None else None
        else:
            raise ValueError(f"The type of your value does not match the column constraint. {_type} | value type: {type(value)} ")

    async def _remove_server(self, instance_id: str) -> int:
        """
        Remove a instance_id from the `servers` table and any tables referencing the `servers.id`.

        Args:
            instance_id (str): AMP Instance ID

        Raises:
            ValueError: If the `instance_id` doesn't exist.

        Returns:
            int: Deleted Row count.
        """
        _exists = await self._select_row_where(table="servers", column="id", where="instance_id", value=instance_id)
        if _exists == None:
            raise ValueError(f"The Instance ID provided doesn't exists in the Database. {instance_id}")
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                # TODO - Any other tables referencing `server_id` will need to be added to this list.
                await cur.execute("DELETE FROM user_metrics WHERE server_id=?", _exists)
                await cur.execute("DELETE FROM servers WHERE id=?", _exists)
                return cur.get_cursor().rowcount

    # TODO - Transfer/Swap Server information
