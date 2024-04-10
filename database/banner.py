from dataclasses import fields
from typing import Literal

from utils import asqlite

from .base import Base
from .types import BannerSettings

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
    guild_id INTEGER,
    channel_id INTEGER,
    group_id INTEGER NOT NULL,
    foreign key (group_id) REFERENCES banner_group(id)
    UNIQUE(guild_id, channel_id, group_id)
)STRICT"""

BANNER_GROUP_MESSAGES_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS banner_group_messages (
    group_channel_id INTEGER NOT NULL,
    message_id INTEGER,
    foreign key (group_channel_id) REFERENCES banner_group_channels(id)
    UNIQUE(group_channel_id, message_id)
)STRICT"""

SERVER_BANNERS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS banner_settings (
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


class DBBanner(Base):
    def __init__(self) -> None:
        super().__init__()

    async def _initialize_tables(self) -> None:
        """
        Creates the `Banner` tables.

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
                    raise ValueError(f"The Server ID provided is not apart of the Banner Group. {server_id}")

    async def add_channel_to_banner_group(self, name: str, channel_id: int, guild_id: int) -> Literal[True]:
        """
        Add a Discord Channel to a Banner Group. 

        *Validate channel_id and guild_id prior to use.*

        Args:
            name (str): The name of the Banner Group.
            guild_id (int): The Discord Guild ID.
            channel_id (int): The Discord Channel ID.
        """

        _group = await self._select_row_where(table="banner_group", column="*", where="name", value=name)
        if _group is None:
            raise ValueError(f"The Banner Group Name provided doesn't exists in the Database. {name}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                res = await cur.execute("""SELECT * FROM banner_group_channels WHERE channel_id = ? AND guild_id = ? AND group_id = ?""", channel_id, guild_id, _group["ID"])
                if res is None:
                    await cur.execute("""INSERT INTO banner_group_channels(channel_id, guild_id, group_id) VALUES(?, ?, ?)""", channel_id, guild_id, _group["ID"])
                    await db.commit()
                    return True
                else:
                    raise ValueError(f"The Channel ID and Guild ID provided is already in the Banner Group. {channel_id} {guild_id}")

    async def remove_channel_from_banner_group(self, name: str, channel_id: int, guild_id: int) -> Literal[True]:
        """
        remove_channel_from_banner_group _summary_

        Args:
            name (str): The name of the Banner Group.
            channel_id (int): The Discord Channel ID.
            guild_id (int): The Discord Guild ID.
        """

        _group = await self._select_row_where(table="banner_group", column="*", where="name", value=name)
        if _group is None:
            raise ValueError(f"The Banner Group Name provided doesn't exists in the Database. {name}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                res = await cur.execute("""SELECT * FROM banner_group_channels WHERE channel_id = ? AND guild_id = ? AND group_id = ?""", channel_id, guild_id, _group["ID"])
                if res is not None:
                    await cur.execute("""DELETE FROM banner_group_channels WHERE channel_id = ? AND guild_id = ? AND group_id = ?""", channel_id, guild_id, _group["ID"])
                    await db.commit()
                    return True
                else:
                    raise ValueError(f"The Channel ID and Guild ID provided isn't apart of the Banner Group. {channel_id} {guild_id}")

    async def add_message_to_banner_group(self, name: str, message_id: int) -> Literal[True]:
        """
        Add a Discord Message ID to a Banner Group.

        Args:
            name (str): The name of the Banner Group.
            message_id (int): The Discord Message ID.
        """

        # Get our banner group info
        _group = await self._select_row_where(table="banner_group", column="*", where="name", value=name)
        if _group is None:
            raise ValueError(f"The Banner Group Name provided doesn't exists in the Database. {name}")

        # Get the banner group channel info
        _group_channel = await self._select_row_where(table="banner_group_channels", column="*", where="group_id", value=_group["id"])
        if _group_channel is None:
            raise ValueError(f"The Banner Group doesn't have any channels. {name}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                # See if the message id and group channel id are already in the banner group.
                res = await cur.execute("""SELECT * FROM banner_group_messages WHERE message_id = ? AND group_channel_id = ?""", message_id, _group_channel["id"])
                if res is None:
                    await cur.execute("""INSERT INTO banner_group_messages(message_id, group_id) VALUES(?, ?)""", message_id, _group_channel["id"])
                    await db.commit()
                    return True
                else:
                    raise ValueError(f"The Message ID provided is already in the Banner Group. {message_id}")

    async def update_banner_setting(self, server_id: int, setting: str, value: str | int):
        """
        Update a Banner Group Setting.

        Args:
            name (str): The name of the Banner Group.
            setting (str): The setting to update.
            value (str | int): The value to update the setting to.
        """

        _fields = [entry.name for entry in fields(BannerSettings)]

        _server = await self._select_row_where(table="servers", column="*", where="id", value=server_id)
        if _server is None:
            raise ValueError(f"The Server ID provided doesn't exists in the Database. {server_id}")

        if setting not in _fields:
            raise ValueError(f"The setting provided is not a Banner Setting. {setting}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute(f"""UPDATE banner_settings SET {setting} = ? WHERE server_id = ?""", value, _server["ID"])
