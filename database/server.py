
from dataclasses import dataclass
from database.db import Database
from utils import asqlite
from sqlite3 import Row
from typing import Any

SERVER_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY NOT NULL,
    instanceid TEXT NOT NULL UNIQUE,
    instancename TEXT NOT NULL,
    ip TEXT,
    whitelist INTEGER ,
    whitelistdisabled INTEGER,
    donator INTEGER,
    chatchannel INTEGER,
    chatprefix TEXT,
    eventchannel INTEGER,
    role INTEGER,
    avatarurl TEXT,
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
    instanceid: str
    instancename: str
    ip: str = ""
    whitelist: bool = False
    whitelistdisabled: bool = False
    donator: bool = False
    chatchannel: int = 0
    chatprefix: str = ""
    eventchannel: int = 0
    role: int = 0
    avatarurl: str = ""
    hidden: bool = False

    def __setattr__(self, name: str, value: Any) -> Any:
        """
        We are overwritting setattr because SQLite returns 0 or 1 for True/False. \n
        Convert it to a bool for human readable.

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

    # Remove a Server (maybe?)
    # Transfer/Swap Server information

    async def add_server(self, instanceid: str, instancename: str) -> bool | None:
        """
        Add a AMP Instance ID/Name to the `servers` table.

        Args:
            instanceid (str): AMP Instance ID
            instancename (str): AMP Instance Name

        Raises:
            ValueError: Duplicate instanceid value in the database.

        Returns:
            bool | None: Returns `True` on successful execution of Database insert; otherwise `None`.
        """
        _exists = await self._select_row(table="servers", column="instanceid", where="instanceid", value=instanceid)
        if _exists != None:
            raise ValueError(f"The instanceid provided already exists in the Database. {instanceid}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""INSERT INTO servers(instanceid, instancename) VALUES(?, ?)""", instanceid, instancename)
                # res = await cur.fetchone()
                await db.commit()
                return True
                # return Server(**res) if res is not None else None

    async def update_server(self, instanceid: str, column: str, value: bool | str | int) -> Server | None:
        """
        Update an existing instanceid in the `servers` table.\n

        Specify the `column` (eg. "whitelist") and the value to be set for it (eg. True) to update said values.
        See `Server` dataclass for possible attributes.

        Args:
            instanceid (str): AMP Instance ID
            column (str): A column from the `servers` table. See also `Server()` dataclass. 
            value (bool | str | int): The value to be inserted into the column.  Will validate the type against the `Server()` dataclass.

        Raises:
            ValueError: If the `instanceid` is non-existent or the `value` for the specified `column` is not the correct type.

        Returns:
            Server | None: _description_
        """
        _exists = await self._select_row(table="servers", column="instanceid", where="instanceid", value=instanceid)
        if _exists == None:
            raise ValueError(f"The instanceid provided doesn't exists in the Database. {instanceid}")

        _check = hasattr(Server, column)
        if _check is True:
            _type = type(getattr(Server, column))
        else:
            raise ValueError(f"The column provided does not match the Database Schema. {column}")

        if isinstance(value, _type):
            await self._update_column(table="servers", column=column, value=value)
            # Let's get the updated table values for provided instanceid and return a dataclass to be used.
            res = await self._select_row(table="servers", column="*", where="instanceid", value=instanceid)
            return Server(**res) if res is not None else None
        else:
            raise ValueError(f"The type of your value does not match the column constraint. {_type} | value type: {type(value)} ")

    async def remove_server(self, instanceid: str):
        _exists = await self._select_row(table="servers", column="instanceid", where="instanceid", value=instanceid)
        if _exists == None:
            raise ValueError(f"The instanceid provided doesn't exists in the Database. {instanceid}")

        # Check if the server exists
        # Use the instanceid and check usermetrics
        # R
