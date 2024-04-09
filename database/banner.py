from dataclasses import dataclass
from typing import Literal

from database.db import Database
from utils import asqlite

BANNER_GROUP_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS banner_group (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE
)STRICT"""

BANNER_GROUP_SERVER_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS banner_group_servers (
    server_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    foreign key (server_id) REFERENCES servers(id),
    foreign key (group_id) REFERENCES banner_group(id)
)STRICT"""

BANNER_GROUP_CHANNELS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS banner_group_channels (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER,
    guild_id INTEGER,
    group_id INTEGER NOT NULL,
    foreign key (group_id) REFERENCES banner_group(id)
)STRICT"""

BANNER_GROUP_MESSAGES_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS banner_group_messages (
    channel_id INTEGER NOT NULL,
    message_id INTEGER,
    foreign key (channel_id) REFERENCES banner_group_channels(id)
)STRICT"""

SERVER_BANNERS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS banners (
    server_id INTEGER NOT NULL,
    background_path TEXT,
    blur_background_amount INTEGER,
    color_header TEXT,
    color_body TEXT,
    color_host TEXT,
    color_whitelist_open TEXT,
    color_whitelist_closed TEXT,
    color_donator TEXT,
    color_status_online TEXT,
    color_status_offline TEXT,
    color_player_limit_min TEXT,
    color_player_limit_max TEXT,
    color_player_online TEXT,
    foreign key(server_id) REFERENCES servers(ID)
)STRICT"""


@dataclass
class Banner():
    """
    Represents the data from the Database table banners.
    """

    server_id: int
    background_path: str
    blur_background_amount: int
    color_header: str
    color_body: str
    color_host: str
    color_whitelist_open: str
    color_whitelist_closed: str
    color_donator: str
    color_status_online: str
    color_status_offline: str
    color_player_limit_min: str
    color_player_limit_max: str
    color_player_online: str


class DBBanner(Database):
    def __init__(self) -> None:
        super().__init__()

    async def _initialize_tables(self) -> None:
        """
        Creates the `DBBanner` tables.

        """
        tables = [
            BANNER_GROUP_SETUP_SQL,
            BANNER_GROUP_SERVER_SETUP_SQL,
            BANNER_GROUP_CHANNELS_SETUP_SQL,
            BANNER_GROUP_MESSAGES_SETUP_SQL,
            SERVER_BANNERS_SETUP_SQL
        ]
        await self.create_tables(schema=tables)

    async def add_banner_group(self, name: str) -> Literal[True]:
        """
        Creates a Banner Group Table with the provided `name`

        Args:
            name (str): Name of the Banner Group.

        Raises:
            ValueError: If the name provided already exists in the Database.

        """
        res = await self._select_row_where(table="banner_group", column="name", where="name", value=name)
        if res is None:
            await self._insert_row(table="banner_group", column="name", value=name)
            return True

        raise ValueError(f"The name provided already exists in the Database. {name}")

    async def remove_banner_group(self, name: str) -> Literal[True]:
        """
        Removes a Banner Group Table with the provided `name`

        Args:
            name (str): Name of the Banner Group.

        Raises:
            ValueError: If the name provided already exists in the Database.

        """
        res = await self._select_row_where(table="banner_group", column="name", where="name", value=name)
        if res is None:
            raise ValueError(f"The name provided doesn't exists in the Database. {name}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""DELETE FROM banner_group WHERE name = ?""", name)
                await db.commit()
                return True

    async def add_server_to_banner_group(self, name: str, server_id: int) -> Literal[True]:
        """
        Adds a Server to a Banner Group.

        Args:
            name (str): The name of the Banner Group.
            server_id (int): ID of the Server.

        Raises:
            ValueError: If the server_id provided already exists in the Banner Group.
            ValueError: If the name provided doesn't exists in the Database.
            ValueError: If the server_id provided doesn't exists in the Database.

        Returns:
            Literal[True]: If the Server was added to the Banner Group.

        """
        # Check if the group exists.
        group = await self._select_row_where(table="banner_group", column="*", where="name", value=name)
        if group is None:
            raise ValueError(f"The Banner Group Name provided doesn't exists in the Database. {name}")

        # Check if the server exists.
        server = await self._select_row_where(table="servers", column="id", where="id", value=server_id)
        if server is None:
            raise ValueError(f"The Server ID provided doesn't exists in the Database. {server_id}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                # See if the server is already in the group.
                res = await cur.execute("""SELECT * FROM banner_group_servers WHERE server_id = ? AND group_id = ?""", server_id, group["ID"])
                if res is None:
                    await cur.execute("""INSERT INTO banner_group_servers(server_id, group_id) VALUES(?, ?)""", server_id, group["ID"])
                    await db.commit()
                    return True
                else:
                    raise ValueError(f"The Server ID provided already exists in the Banner Group. {server_id}")

    async def remove_server_from_banner_group(self, name: str, server_id: int) -> Literal[True]:
        """
        Remove a Server from a Banner Group.

        Args:
            name (str): The name of the Banner Group.
            server_id (int): ID of the Server.

        Raises:
            ValueError: If the server_id provided already exists in the Banner Group.
            ValueError: If the name provided doesn't exists in the Database.
            ValueError: If the server_id provided doesn't exists in the Database.

        Returns:
            Literal[True]: If the Server was removed from the Banner Group.

        """
        # Check if the group exists.
        _group = await self._select_row_where(table="banner_group", column="*", where="name", value=name)
        if _group is None:
            raise ValueError(f"The Banner Group Name provided doesn't exists in the Database. {name}")

        # Check if the server exists.
        _server = await self._select_row_where(table="servers", column="id", where="id", value=server_id)
        if _server is None:
            raise ValueError(f"The Server ID provided doesn't exists in the Database. {server_id}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                # See if the server is not in the group.
                res = await cur.execute("""SELECT * FROM banner_group_servers WHERE server_id = ? AND group_id = ?""", server_id, _group["ID"])
                if res is not None:
                    await cur.execute("""DELETE FROM banner_group_servers WHERE server_id = ? AND group_id = ?""", server_id, _group["ID"])
                    await db.commit()
                    return True
                else:
                    raise ValueError(f"The Server ID provided doesn't exists in the Banner Group. {server_id}")
