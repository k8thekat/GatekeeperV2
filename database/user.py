from dataclasses import dataclass
from sqlite3 import Row

from utils import asqlite

from .base import Base
from .types import ServerTypes

USERS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY NOT NULL,
    discord_id INTEGER UNIQUE NOT NULL
)STRICT"""

IGN_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS ign (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    user_id INTEGER,
    type_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(name, type_id, user_id)
)STRICT"""

# This was apart of ign table.
# FOREIGN KEY (type_id) REFERENCES ign_types(id)

# IGN_TYPES_SETUP_SQL = """
# CREATE TABLE IF NOT EXISTS ign_types (
#     id INTEGER PRIMARY KEY NOT NULL,
#     type TEXT NOCASE UNIQUE NOT NULL
# )STRICT"""

METRICS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS user_metrics (
    ign_id INTEGER,
    server_id INTEGER,
    last_login TEXT NO CASE,
    playtime INTEGER,
    created TEXT NO CASE,
    FOREIGN KEY (server_id) REFERENCES servers(id)
    FOREIGN KEY (ign_id) REFERENCES ign(id)
    UNIQUE(server_id, ign_id)
)STRICT"""


@dataclass()
class IGN(Base):
    id: int  # id column from ign table.
    name: str  # name from ign table.
    user_id: int  # id from users table.
    type_id: ServerTypes  # id from ign_types table.

    @property
    async def owner(self) -> int | None:
        """
        Returns the Discord ID associated with the IGN if it exists.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT discord_id FROM users WHERE id = ?""", self.user_id)
                res = await cur.fetchone()
                return res["discord_id"] if not None else None

    @property
    async def servers(self) -> list[int] | None:
        """
        Returns a list of Server IDs that the IGN has been on.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT server_id from user_metrics WHERE ign_id = ?""", self.id)
                res = await cur.fetchall()
                if res is not None:
                    # TODO - Call DB servers table lookup with IDs and return a list of Server names?
                    return [entry["server_id"] for entry in res] if not None else None
                else:
                    return res

    async def get_playtime(self, server_id: int) -> int | None:
        """
        Returns the playtime for a specific Server ID

        Args:
            server_id (int): The sever(ID) value from the `server` table.

        Returns:
            int | None: Time in seconds.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT playtime FROM user_metrics WHERE ign_id = ? and server_id = ?""", self.id, server_id)
                res = await cur.fetchone()
                return res["playtime"] if not None else None

    async def get_global_playtime(self) -> list[tuple[int, int]]:
        """
        Returns the total playtime across all servers.

        Returns:
            list[tuple[int, int]]: A list of time in seconds per server. `tuple=(server_id, playtime)`
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT server_id,playtime FROM user_metrics WHERE ign_id = ?""", self.id)
                res = await cur.fetchall()
                return [(entry["server_id"], entry["playtime"]) for entry in res]

    async def get_last_login(self, server_id: int) -> str | None:
        """
       Returns the last time the IGN logged into a server as a `unix timestamp`.

        Args:
            server_id (int): The sever(ID) value from the `server` table.

        Returns:
            str | None: A `unix timestamp`.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT last_login FROM user_metrics WHERE ign_id = ? and server_id = ?""", self.id, server_id)
                res = await cur.fetchone()
                return res["last_login"] if not None else None

    @property
    async def type(self) -> str:
        """
        Returns the type of server this IGN belongs to. \n
        eg `Minecraft, Ark, Source/Valve`
        """
        return ServerTypes(self.type_id).name
        # async with asqlite.connect(self._db_file_path) as db:
        #     async with db.cursor() as cur:
        #         await cur.execute("""SELECT typeid FROM ign_types WHERE id = ?""", self.type_id)
        #         res = await cur.fetchone()
        #         return res["type"] if not None else None


class DBuser(Base):
    def __init__(self) -> None:
        print()

    async def _initialize_tables(self) -> None:
        """
        Creates the `DBuser` tables.
        """
        tables: list[str] = [USERS_SETUP_SQL, IGN_SETUP_SQL, METRICS_SETUP_SQL]
        await self.create_tables(schema=tables)

    async def add_user(self, discord_id: int) -> None | bool:
        """
        Add a Discord ID to the `users` table.

        Args:
            discord_id(int): Discord ID

        Raises:
            ValueError: If the Discord ID already exists in the Database.
        """
        _exists = await self._select_row_where(table="user", column="discord_id", where="discord_id", value=discord_id)
        if _exists == None:
            await self._insert_row(table="users", column="discord_id", value=discord_id)
            return True
        else:
            raise ValueError(f"The Discord ID provided already exists in the Database. {discord_id}")

    async def update_user(self, discord_id: int, old_discord_id: int) -> None | bool:
        """
        Update an existing Discord ID in the `users` table.\n

        Typically this method will not be used; simply use `update_ign` and change the IGN's `user_id`.

        Args:
            discord_id (int): New Discord ID to replace the existing entry with.
            old_discord_id (int): Existing entry in the `users` table.

        Raises:
            ValueError: If the existing Discord ID is not in the Database or if the new Discord ID is already in the Database.
        """
        _exists = await self._select_row_where(table="users", column="discord_id", where="discord_id", value=old_discord_id)
        if _exists == None:
            raise ValueError(f"The Discord ID provided does not exist in the Database. {old_discord_id}")

        _new_exists = await self._select_row_where(table="users", column="discord_id", where="discord_id", value=discord_id)
        if _new_exists != None:
            raise ValueError(f"The Discord ID provided already exists in the Database. {discord_id}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""UPDATE users SET discord_id = ? WHERE discord_id = ?""", discord_id, old_discord_id)
                await db.commit()
                return True

    async def get_ign(self, ign: str | None = None, discord_id: int | None = None) -> list[IGN] | None:
        """
        Returns an IGN class object if the IGN exists or their is a Discord ID tied to an IGN.\n
        This can return multiple IGN class objects.

        Args:
            ign (str | None): IGN to search for. Defaults to None.
            discord_id (int | None): Discord ID to search for. Defaults to None.

        Returns:
            list[IGN] | None: Returns all matches to the IGN or Discord ID provided.
        """
        if ign == None and discord_id == None:
            raise ValueError(f"You must provided at least one value, ign and discord_id cannot be None.")

        if ign != None and discord_id == None:
            query = ign
        else:
            query = discord_id

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute(f"""SELECT * FROM ign WHERE {query} = ?""", query)
                res = await cur.fetchall()
                if res is not None:
                    return [IGN(**entry) for entry in res]

    async def add_ign(self, ign: str, type_id: ServerTypes = ServerTypes.GENERAL, user_id: int | None = None) -> IGN | None:
        """
        Adds an IGN to the DATABASE, has a unique constraint of `ign` and `type_id` to prevent duplicates.\n
        `user_id` is Optional to set a Discord ID as an owner of the IGN.

        Args:
            ign (str): The IGN to be added to the DATABASE.
            type_id (int): The IGN type ID. See `db_types` -> ServerTypes.
            user_id (int | None, optional): The Discord ID that the IGN will belong to. Defaults to None.

        Raises:
            ValueError: If the `typeid` does not exist in the DATABASE.

        Returns:
            IGN | None: Returns an IGN class object or None if `fetch()` fails.
        """
        # _type = await self._select_row(table="ign_types", column="id", where="id", value=type_id)
        # if _type == None:
        #     raise ValueError(f"The Type ID provided does not exists. {type_id}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT * FROM ign WHERE name = ? and type_id = ?""", ign, type_id)
                res = await cur.fetchone()
                if res is not None:
                    return IGN(**res)

                else:
                    await cur.execute("""INSERT INTO ign(name, type_id, user_id) VALUES(?, ?, ?)""", ign, type_id, user_id)
                    res = await cur.fetchone()
                    await db.commit()
                    return IGN(**res) if res is not None else None

    async def update_ign(self, ign: str, new_ign: str | None = None, user_id: int | None = None, type_id: ServerTypes = ServerTypes.GENERAL) -> IGN | None:
        """
        Update an IGN with either a new `IGN`, `type_id` or set the `user_id` aka Discord ID which correlates to who "owns" the IGN.

        Args:
            ign (str): The IGN to update.
            new_ign (str | None, optional): The new IGN to replace `ign`. Defaults to None.
            user_id (int | None, optional): The ID value to correlate a Discord ID as owner from `users` table. Defaults to None.
            type_id (ServerTypes, optional): The IGN type ID. Defaults to ServerTypes.GENERAL. See `db_types` -> ServerTypes.

        Raises:
            ValueError: If the IGN provided does not exist in the Database.
            ValueError: if the IGN provided has multiple matches in the Database.

        Returns:
            IGN | None: Returns an IGN class on success or `None` if it fails to update.
        """

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""UPDATE ign SET name = COALESCE(?, name), user_id = COALESCE(?, user_id), type_id = COALESCE(?, type_id) WHERE name = ?""", new_ign, user_id, type_id.value, ign)
                await db.commit()
                res = await cur.fetchone()
                return IGN(**res) if not None else None

    async def _delete_ign(self, ign: str) -> int | None:
        """
        Removes all entries of an IGN from the `ign` table and the `user_metrics` table. Regardless of Server

        Args:
            ign (str): The IGN to delete from the `ign` table.

        Raises:
            ValueError: If the IGN provided does not exist in the Database.

        Returns:
            int | None: Row count of removed entries.
        """
        _exist = self._select_row_where(table="ign", column="name", where="name", value=ign)
        if _exist == None:
            raise ValueError(f"The ign provided does not exist in the Database. {ign}")

        async with asqlite.connect(self._db_file_path)as db:
            async with db.cursor() as cur:
                res = await cur.execute("""SELECT id FROM ign WHERE name = ?""", ign)
                if isinstance(res, Row) and res["id"] is not None:
                    await cur.execute("""DELETE FROM user_metrics WHERE ign_id = ?""", res["id"])
                    await cur.execute("""DELETE FROM ign WHERE name = ?""", ign)
                    await db.commit()
                    return cur.get_cursor().rowcount

    # async def add_ign_type(self, type: str) -> None:
    #     """
    #     Add a Server Type to the Database.

    #     Args:
    #         type (str): The Server Type to add to the Database.

    #     Raises:
    #         ValueError: If the type you provided already exists.
    #     """
    #
    #     # Need to pass that value along to our `ign_types` table to populate it.
    #     _exists = await self._select_row(table="ign_types", column="type", where="type", value=type)
    #     if _exists == None:
    #         await self._insert_row(table="ign_types", column="type", value=type)
    #     else:
    #         raise ValueError(f"The type you provided already exists in the database. {type}")

    # async def update_ign_type(self, type: str, new_type: str) -> None:
    #     """
    #     Update an existing `type` entry in the Database.

    #     Args:
    #         type (str): The existing type in the Database.
    #         new_type (str): The type to replace the existing Database entry.

    #     Raises:
    #         ValueError: If the `type` provided does not exist or the `new_type` already exists.
    #     """
    #     _exists = await self._select_row(table="ign_types", column="type", where="type", value=type)
    #     _new_exists = await self._select_row(table="ign_types", column="type", where="type", value=new_type)
    #     if _exists == None:
    #         raise ValueError(f"The type provided does not exist in the Database. {type}")
    #     if _new_exists != None:
    #         raise ValueError(f"The new_type provided already exists in the Database. {new_type}")

    #     await self._update_row(table="ign_types", column="type", where=type, value=new_type)

    # async def _delete_ign_type(self, type: str):
    #     """
    #     Removes a `type` from the `ign_types` table. There is a FOREIGN KEY reference for this table tied to IGNs.

    #     **Warning** This will raise a `sqlite3.IntegrityError` if the `ign_types(id)` value is already in use for an `ign`. \n
    #     Recommended using `update_ign_type` at the very least first.

    #     Args:
    #         type (str): The `type` to be removed from the table.

    #     Raises:
    #         ValueError: If the provided `type` does not exist in the Database.
    #     """
    #     _exists = await self._select_row(table="ign_types", column="type", where="type", value=type)
    #     if _exists == None:
    #         raise ValueError(f"The type provided does not exist in the Database. {type}")

    #     async with asqlite.connect(self._db_file_path) as db:
    #         async with db.cursor() as cur:
    #             await cur.execute("""DELETE FROM ign_types WHERE type = ?""", type)
    #             await db.commit()
    #             return cur.get_cursor().rowcount

    async def transfer_ign_metrics(self, ign: str, to_ign: str, server_id: int) -> int:
        """
        Move existing metrics data from one IGN to another IGN. \n 
        Typical use case is when someone changes there IGN.


       **This will update the table entries for `to_ign` and `DELETE` the `ign` row and `user_metrics` row.**

        Args:
            ign (str): The IGN metrics to move/combine to `to_ign`
            to_ign (str): The destination IGN metrics to update.

        Returns:
            int : The amount of Rows deleted from the Database.
        """
        _exists = await self._select_row_where(table="ign", column="name", where="name", value=ign)
        if _exists == None:
            raise ValueError(f"The ign provided does not exist in the Database. {ign}")

        _to_exists = await self._select_row_where(table="ign", column="name", where="name", value=to_ign)
        if _to_exists == None:
            raise ValueError(f"The to_ign provided does not exist in the Database. {to_ign}")

        # TODO - This select statement will be need to validated when setting up my `servers` table.
        _server_exists = await self._select_row_where(table="servers", column="id", where="id", value=server_id)
        if _server_exists == None:
            raise ValueError(f"The server_id provided does not exist in the Database. {server_id}")

        # ign IDs to update our tables.
        _ign_id = await self._select_row_where(table="ign", column="id", where="name", value=ign)
        _to_ign_id = await self._select_row_where(table="ign", column="id", where="name", value=to_ign)

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT last_login,playtime FROM user_metrics WHERE ign_id = ? and server_id = ?""", _ign_id, server_id)
                res = await cur.fetchone()  # this is the old IGN metrics information.

                await cur.execute("""SELECT last_login,playtime FROM user_metrics WHERE ign_id = ? and server_id = ?""", _to_ign_id, server_id)
                to_res = await cur.fetchone()  # this is the new IGN metrics information.
                _last_login = to_res["last_login"]
                _playtime = res["playtime"] + to_res["playtime"]
                # update the NEW IGN with the combined playtime and most recent login data.
                await cur.execute("""UPDATE user_metrics SET last_login = ? and playtime = ? WHERE ign_id = ? and server_id = ?""", _last_login, _playtime, _to_ign_id, server_id)
                # remove the old user metrics information tied to the ign and remove the ign from the table.
                await cur.execute("""DELETE FROM user_metrics WHERE ign_id = ? and server_id = ?""", _ign_id, server_id)
                await cur.execute("""DELETE FROM ign WHERE ign_id = ?""", _ign_id)
                await db.commit()
                return cur.get_cursor().rowcount
