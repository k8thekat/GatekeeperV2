from db import Database
import utils.asqlite as asqlite

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
CREATE TABLE IF NOT EXISTS prefix (
    id INTEGER PRIMARY KEY NOT NULL,
    prefix TEXT
)STRICT"""


class DB_Settings(Database):
    """
        Gatekeepers Database/Bot Settings class.

        Has access to `SETTINGS, OWNERS, PREFIX` tables.
    """

    async def _initlize_tables(self) -> None:
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
    async def prefixs(self) -> list[str] | None:
        """Returns a list of prefix's the bot will listen for."""
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT prefix FROM prefix""")
                res = await cur.fetchall()
                if res is not None:
                    return [entry['prefix'] for entry in res]

    async def update_guild_id(self, guild_id: int) -> None:
        """
        Update the Guild ID value in the DATABASE.

        Args:
            guild_id (int): The Discord Guild ID. eg `602285328320954378`

        Raises:
            ValueError: If the Guild ID value is to short we raise an exception.
        """
        if len(str(guild_id)) < 18:
            raise ValueError("Your Guild ID value is to short.")
        await self._update_column(table="settings", column="guild_id", value=guild_id)

    async def update_role_id(self, role: str, role_id: int) -> None:
        """
        Update any Role specific column value in the DATABASE.

        Args:
            role (str): The column to be updated.
            role_id (int): The Discord Role ID.  eg `617967701381611520`

        Raises:
            ValueError: If the Role ID value is to short we raise an exception.
        """
        if len(str(role_id)) < 18:
            raise ValueError("Your Role ID value is to short.")
        await self._update_column(table="settings", column=role, value=role_id)

    async def update_message_timeout(self, timeout: int = 120) -> None:
        """
        Updates the Message Timeout aka time till the message is auto-deleted after a the bot sends a message.

        Args:
            timeout (int): seconds. Default is `120` seconds.
        """
        await self._update_column(table="settings", column="msg_timeout", value=timeout)

    async def add_owner(self, user_id: int) -> None:
        """
        Add a Discord User ID to the owners table. \n

        Args:
            user_id (int): Discord User ID.
        """
        await self._insert_column(table="owners", column="id", value=user_id)

    async def remove_owner(self, user_id: int) -> None:
        """
        Remove a Discord User ID from the owners table.

        Args:
            user_id (int): Discord User ID
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""DELETE FROM owners WHERE id = ?""", user_id)
                await db.commit()

    async def add_prefix(self, prefix: str) -> None:
        """
        Add a prefix to the prefix table.

        Args:
            prefix (str): A phrase or single character. eg `?` or `gatekeeper`
        """
        await self._insert_column(table="prefix", column="prefix", value=prefix)

    async def remove_prefix(self, prefix: str) -> None:
        """
        Remove a prefix from the prefix table.

        Args:
            prefix (str): The prefix to remove from the table.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""DELETE FROM prefix WHERE prefix = ?""", prefix)
                await db.commit()
