from sqlite3 import Row
from typing import Literal

import utils.asqlite as asqlite

from .base import Base
from .types import *

GUILDS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS guilds (
    guild_id INTEGER UNIQUE NOT NULL
)STRICT"""

SETTINGS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    guild_id INTEGER UNIQUE NOT NULL,
    mod_role_id INTEGER,
    donator_role_id INTEGER,
    msg_timeout INTEGER,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
)STRICT"""

OWNERS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS owners (
    guild_id INTEGER NOT NULL,
    user_id INTEGER UNIQUE,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id),
    UNIQUE(guild_id, user_id)
)STRICT"""

PREFIX_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS prefixes (
    id INTEGER PRIMARY KEY NOT NULL,
    guild_id INTEGER,
    prefix TEXT,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
    UNIQUE(guild_id, prefix)
)STRICT"""


class DBSettings(Base):
    """
        Gatekeepers Database/Bot Settings class.

        Has access to `SETTINGS, OWNERS, PREFIX and GUILDS` tables.
    """

    async def _initialize_tables(self) -> None:
        tables: list[str] = [SETTINGS_SETUP_SQL, OWNERS_SETUP_SQL, PREFIX_SETUP_SQL, GUILDS_SETUP_SQL]
        await self._create_tables(schema=tables)

    async def add_guild_id(self, guild_id: int) -> None | Settings:
        """
        Add a Discord Guild ID to the `guilds` table.

        Args:
            guild_id (int): The Discord Guild ID.

        Raises:
            ValueError: If the `guild_id` value is to short.

        Returns:
            Settings | None: Returns a Settings object if the Guild ID was added to the Database.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        _id: Row | None = await self._insert_row(table="guilds", column="guild_id", value=guild_id)

        if _id is not None:
            res: None | Row = await self._execute(SQL="""INSERT INTO settings (guild_id, mod_role_id, donator_role_id, msg_timeout) VALUES (?, ?, ?, ?) RETURNING *""", parameters=(_id["guild_id"], None, None, None))
            return Settings(**res) if res is not None else None
        return None

    async def get_guild_settings(self, guild_id: int) -> Settings | None:
        """
        Gets all the settings from the `settings` table for a specific Discord Guild ID.

        Args:
            guild_id (int): The Discord Guild ID.

        Raises:
            ValueError: If the `guild_id` value is to short.

        Returns:
            Settings | None: Returns a Settings dataclass object.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: asqlite.List[Row] | Row | None = await self._select_row_where(table="settings", column="*", where="guild_id", value=guild_id)
        return Settings(**res[0]) if res is not None else None

    async def set_mod_role_id(self, guild_id: int, role_id: int) -> Settings | None:
        """
        Set the `mod_role_id` value in the `settings` table.

        Args:
            guild_id (int): The Discord Guild ID.
            role_id (int): The Discord Role ID. eg `617967701381611520`

        Raises:
            ValueError: If the role_id value is to short we raise an exception.
            ValueError: If the guild_id value is to short we raise an exception.

        Returns:
            Settings | None : Returns a Settings dataclass object.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        if len(str(object=role_id)) < 15:
            raise ValueError("Your `role_id` value is to short. (<15)")

        res: None | Row = await self._update_row_where(table="settings", column="mod_role_id", value=role_id, where="guild_id", where_value=guild_id)
        return Settings(**res) if res is not None else None

    async def set_donator_role_id(self, guild_id: int, role_id: int) -> None | Settings:
        """
        Update the `donator_role_id`` value in the `settings` table.

        Args:
            guild_id (int): The Discord Guild ID.
            role_id (int): The Discord Role ID. eg `617967701381611520`

        Raises:
            ValueError: If the `role_id` value is to short we raise an exception.
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            Settings | None: Returns a Settings dataclass object.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        if len(str(object=role_id)) < 15:
            raise ValueError("Your `role_id` value is to short. (<15)")

        res: None | Row = await self._update_row_where(table="settings", column="donator_role_id", value=role_id, where="guild_id", where_value=guild_id)
        return Settings(**res) if res is not None else None

    async def set_message_timeout(self, guild_id: int, timeout: int = 120) -> None | Settings:
        """
        Updates the `msg_timeout` value in the `settings` table. \n
         *aka time till the message is auto-deleted after a the bot sends a message.*

        Args:
            guild_id (int): The Discord Guild ID.
            timeout (int): seconds. Default is `120` seconds.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            Settings | None: Returns a Settings dataclass object.
        """

        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: None | Row = await self._update_row_where(table="settings", column="msg_timeout", value=timeout, where="guild_id", where_value=guild_id)
        return Settings(**res) if res is not None else None

    async def add_owner(self, guild_id: int, user_id: int) -> Owner | None:
        """
        Add a Discord User ID to the `owners` table. \n

        Args:
            guild_id (int): The Discord Guild ID.
            user_id (int): The Discord User ID.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.
            ValueError: If the `user_id` value is to short we raise an exception.

        Returns:
            Owner | None: Returns a Owner dataclass object.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        if len(str(object=user_id)) < 15:
            raise ValueError("Your `user_id` value is to short. (<15)")

        res: None | Row = await self._execute(f"""INSERT INTO owners(guild_id, user_id) VALUES(?, ?) ON CONFLICT(guild_id, user_id) DO NOTHING RETURNING *""", (guild_id, user_id))
        return Owner(**res) if res is not None else None

    async def remove_owner(self, guild_id: int, user_id: int) -> None | Literal[True]:
        """
        Remove a Discord User ID from the `owners` table.

        Args:
            guild_id (int): The Discord Guild ID.
            user_id (int): The Discord User ID.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.
            ValueError: If the `user_id` value is to short we raise an exception.

        Returns:
            None
        """

        if len(str(object=user_id)) < 15:
            raise ValueError("Your `user_id` value is to short. (<15)")

        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: None | Row = await self._execute("""SELECT * FROM owners WHERE guild_id = ? AND user_id = ?""", (guild_id, user_id))
        if res is None:
            raise ValueError(f"The `user_id` provided does not exist in the `owners` table. user_id:{user_id}")

        await self._execute("""DELETE FROM owners WHERE guild_id = ? AND user_id = ?""", (guild_id, user_id))
        return True

    async def get_owners(self, guild_id: int) -> list[Owner] | None:
        """
        Get all the owners from the `owners` table.

        Args:
            guild_id (int): The Discord Guild ID.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            list[Owner]: Returns a list of Owner dataclass objects.
        """

        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: list[Row] | None = await self._fetchall(f"""SELECT * FROM owners WHERE guild_id = ?""", (guild_id,))
        return [Owner(**row) for row in res] if res is not None else None

    async def add_prefix(self, guild_id: int, prefix: str) -> None | str:
        """
        Add a prefix to the `prefixes` table.

        Args:
            guild_id (int): The Discord Guild ID.
            prefix(str): A phrase or single character. eg `?` or `gatekeeper`.

        Returns:
            None | str: Returns the `prefix` if it was added.

        """

        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        prefix = prefix.strip()
        res: None | Row = await self._execute("""INSERT INTO prefixes(guild_id, prefix) VALUES(?, ?) ON CONFLICT(guild_id, prefix) DO NOTHING RETURNING *""", (guild_id, prefix))
        return res["prefix"] if res is not None else None

    async def remove_prefix(self, guild_id: int, prefix: str) -> None | Literal[True]:
        """
        Remove a prefix from the `prefixes` table.

        Args:
            guild_id (int): The Discord Guild ID.
            prefix(str): The prefix to remove from the table.

        Raises:
            ValueError: If the prefix does not exist in the Database.

        Returns:
            None | Literal[True]: Returns `True` if the prefix was removed.
        """

        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: None | Row = await self._execute("""SELECT prefix FROM prefixes WHERE guild_id = ? AND prefix = ?""", (guild_id, prefix))
        if res is None:
            raise ValueError(f"The `prefix` provided does not exist in the `prefixes` table. prefix:{prefix}")

        await self._execute("""DELETE FROM prefixes WHERE guild_id = ? AND prefix = ?""", (guild_id, prefix))
        return True

    async def get_prefixes(self, guild_id: int) -> list[str] | None:
        """"
        Get all the prefixes from the `prefixes` table.

        Args:
            guild_id (int): The Discord Guild ID.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            list[str]: Returns a list of prefixes.
        """

        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: list[Row] | None = await self._fetchall(f"""SELECT prefix FROM prefixes WHERE guild_id = ?""", (guild_id,))
        return [row["prefix"] for row in res] if res is not None else None
