import utils.asqlite as asqlite

from .base import Base

SETTINGS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    guild_id INTEGER,
    mod_role_id INTEGER,
    donator_role_id INTEGER,
    msg_timeout INTEGER
)STRICT"""

OWNERS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS owners (
    id INTEGER PRIMARY KEY NOT NULL,
    user_id INTEGER UNIQUE,
)STRICT"""

PREFIX_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS prefixes (
    id INTEGER PRIMARY KEY NOT NULL,
    prefix TEXT
)STRICT"""


class DBSettings(Base):
    """
        Gatekeepers Database/Bot Settings class.

        Has access to `SETTINGS, OWNERS, PREFIX` tables.
    """

    async def _initialize_tables(self) -> None:
        tables = [SETTINGS_SETUP_SQL, OWNERS_SETUP_SQL, PREFIX_SETUP_SQL]
        await self.create_tables(schema=tables)

    @property
    async def guild_id(self) -> int | None:
        """
        Gets the Discord Guild ID from the DATABASE.

        Returns:
            int | None: Discord Guild ID. eg `602285328320954378`
        """
        res = await self._select_column(table="settings", column="guild_id")
        if isinstance(res, int):
            return res
        else:
            return None

    @property
    async def mod_role_id(self) -> int | None:
        """
        Gets the Discord Moderator role ID from the DATABASE.

        Returns:
            int | None: Discord Moderator role ID. eg `617967701381611520`
        """
        res = await self._select_column(table="settings", column="mod_role_id")
        if isinstance(res, int):
            return res
        else:
            return None

    @property
    async def msg_timeout(self) -> int | None:
        """
        Gets the Message Timeout value from the DATABASE.

        Returns:
            int | None: Message Timeout value. Default is `120 seconds`.
        """
        res = await self._select_column(table="settings", column="msg_timeout")
        if isinstance(res, int):
            return res
        else:
            return None

    @property
    async def donator_role_id(self) -> int | None:
        """
        Gets the Discord Donator role ID from the DATABASE.

        Returns:
            int | None: Discord Role ID. eg `617967701381611520`
        """
        res = await self._select_column(table="settings", column="donator_role_id")
        if isinstance(res, int):
            return res
        else:
            return None

    @property
    async def prefixes(self) -> list[str] | None:
        """Returns a list of prefixes the bot will listen for."""
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT prefix FROM prefixes""")
                res = await cur.fetchall()
                if res is not None:
                    return [entry['prefix'] for entry in res]

    async def set_guild_id(self, guild_id: int) -> None:
        """
        Set the Guild ID value in the DATABASE.

        Args:
            guild_id (int): The Discord Guild ID. eg `602285328320954378`

        Raises:
            ValueError: If the Guild ID value is to short we raise an exception.
        """
        if len(str(guild_id)) < 18:
            raise ValueError("Your Guild ID value is to short.")

        res = await self._select_column(table="settings", column="guild_id")
        if res is None:
            await self._insert_row(table="settings", column="guild_id", value=guild_id)
        else:
            await self._update_row(table="settings", column="guild_id", value=guild_id, where=None)

    async def set_mod_role_id(self, role_id: int):
        """
        Set the Mod role id value in the DATABASE.

        Args:
            role_id (int): The Discord Role ID. eg `617967701381611520`

        Raises:
            ValueError: If the Role ID value is to short we raise an exception.
        """
        if len(str(role_id)) < 18:
            raise ValueError("Your Role ID value is to short.")

        res = await self._select_column(table="settings", column="mod_role_id")
        if res is None:
            await self._insert_row(table="settings", column="mod_role_id", value=role_id)
        else:
            await self._update_row(table="settings", column="mod_role_id", value=role_id, where=None)

    async def set_donator_role_id(self, role_id: int) -> None:
        """
        Set the Donator role id value in the DATABASE.

        Args:
            role_id (int): The Discord Role ID. eg `617967701381611520`

        Raises:
            ValueError: If the Role ID value is to short we raise an exception.
        """
        if len(str(role_id)) < 18:
            raise ValueError("Your Role ID value is to short.")

        res = await self._select_column(table="settings", column="donator_role_id")
        if res is None:
            await self._insert_row(table="settings", column="donator_role_id", value=role_id)
        else:
            await self._update_row(table="settings", column="donator_role_id", value=role_id, where=None)

    async def update_message_timeout(self, timeout: int = 120) -> None:
        """
        Updates the Message Timeout aka time till the message is auto-deleted after a the bot sends a message.

        Args:
            timeout (int): seconds. Default is `120` seconds.
        """

        res = await self._select_column(table="settings", column="msg_timeout")
        if res is None:
            await self._insert_row(table="settings", column="msg_timeout", value=timeout)
        else:
            await self._update_row(table="settings", column="msg_timeout", value=timeout, where=None)

    async def add_owner(self, user_id: int) -> None:
        """
        Add a Discord User ID to the owners table. \n

        Args:
            user_id (int): Discord User ID.

        Raises:
            ValueError: If the user_id already exists in the Database.
        """
        res = await self._select_row_where(table="owners", column="user_id", where="user_id", value=user_id)
        if res is None:
            await self._insert_row(table="owners", column="user_id", value=user_id)
        else:
            raise ValueError(f"The user_id provided already exists in the Database. {user_id}")

    async def remove_owner(self, user_id: int) -> None:
        """
        Remove a Discord User ID from the owners table.

        Args:
            user_id (int): Discord User ID
        """
        res = await self._select_row_where(table="owners", column="user_id", where="user_id", value=user_id)
        if res is None:
            raise ValueError(f"The user_id provided does not exist in the Database. {user_id}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""DELETE FROM owners WHERE user_id = ?""", user_id)
                await db.commit()

    async def add_prefix(self, prefix: str) -> None:
        """
        Add a prefix to the prefixes table.

        Args:
            prefix (str): A phrase or single character. eg `?` or `gatekeeper`

        Raises:
            ValueError: If the prefix already exists in the Database.
        """

        res = await self._select_row_where(table="prefixes", column="prefix", where="prefix", value=prefix)
        if res is None:
            await self._insert_row(table="prefixes", column="prefix", value=prefix)
        else:
            raise ValueError(f"The prefix provided already exists in the Database. {prefix}")

    async def remove_prefix(self, prefix: str) -> None:
        """
        Remove a prefix from the prefixes table.

        Args:
            prefix (str): The prefix to remove from the table.
        """

        res = await self._select_row_where(table="prefixes", column="prefix", where="prefix", value=prefix)
        if res is None:
            raise ValueError(f"The prefix provided does not exist in the Database. {prefix}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""DELETE FROM prefixes WHERE prefix = ?""", prefix)
                await db.commit()
