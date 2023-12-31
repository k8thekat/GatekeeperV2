from dataclasses import dataclass
from database.db import Database
from utils import asqlite
from sqlite3 import Row


USERS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY NOT NULL,
    discordid INTEGER UNIQUE NOT NULL
)STRICT"""

IGN_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS ign (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    userid INTEGER,
    typeid INTEGER NOT NULL,
    FOREIGN KEY (userid) REFERENCES users(id),
    FOREIGN KEY (typeid) REFERENCES igntypes(id)
    UNIQUE(name, typeid)
)STRICT"""

IGN_TYPES_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS igntypes (
    id INTEGER PRIMARY KEY NOT NULL,
    type TEXT NOCASE UNIQUE NOT NULL
)STRICT"""

METRICS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS usermetrics (
    ignid INTEGER,
    serverid INTEGER,
    lastlogin TEXT NO CASE,
    playtime INTEGER,
    FOREIGN KEY (serverid) REFERENCES servers(id)
    FOREIGN KEY (ignid) REFERENCES ign(id)
    UNIQUE(serverid, ignid)
)STRICT"""


@dataclass()
class IGN(Database):
    id: int  # id column from ign table.
    name: str  # name from ign table.
    userid: int  # id from users table.
    typeid: int  # id from igntypes table.

    @property
    async def owner(self) -> int | None:
        """
        Returns the Discord ID associated with the IGN if it exists.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT discordid FROM users WHERE id = ?""", self.userid)
                res = await cur.fetchone()
                return res["discordid"] if not None else None

    @property
    async def servers(self) -> list[int] | None:
        """
        Returns a list of Server IDs that the IGN has been on.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT serverid from usermetrics WHERE ignid = ?""", self.id)
                res = await cur.fetchall()
                if res is not None:
                    # TODO - Call DB servers table lookup with IDs and return a list of Server names?
                    return [entry["serverid"] for entry in res] if not None else None
                else:
                    return res

    async def get_playtime(self, serverid: int) -> int | None:
        """
        Returns the playtime for a specific Server ID

        Args:
            serverid (int): The sever(ID) value from the `server` table.

        Returns:
            int | None: Time in seconds.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT playtime FROM usermetrics WHERE ignid = ? and serverid = ?""", self.id, serverid)
                res = await cur.fetchone()
                return res["playtime"] if not None else None

    async def get_global_playtime(self) -> list[tuple[int, int]]:
        """
        Returns the total playtime accross all servers.

        Returns:
            list[tuple[int, int]]: A list of time in seconds per server. `tuple=(serverid, playtime)`
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT serverid,playtime FROM usermetrics WHERE ignid = ?""", self.id)
                res = await cur.fetchall()
                return [(entry["serverid"], entry["playtime"]) for entry in res]

    async def get_lastlogin(self, serverid: int) -> str | None:
        """
       Returns the last time the IGN logged into a server as a `unix timestamp`.

        Args:
            serverid (int): The sever(ID) value from the `server` table.

        Returns:
            str | None: A `unix timestamp`.
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT lastlogin FROM usermetrics WHERE ignid = ? and serverid = ?""", self.id, serverid)
                res = await cur.fetchone()
                return res["lastlogin"] if not None else None

    @property
    async def type(self):
        """
        Returns the type of server this IGN belongs to. \n
        eg `Minecraft, Ark, Source/Valve`
        """
        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT typeid FROM igntypes WHERE id = ?""", self.typeid)
                res = await cur.fetchone()
                return res["type"] if not None else None


class DBuser(Database):
    def __init__(self) -> None:
        print()

    async def _initialize_tables(self) -> None:
        """
        Creates the `DBuser` tables.
        """
        tables: list[str] = [USERS_SETUP_SQL, IGN_TYPES_SETUP_SQL, IGN_SETUP_SQL, METRICS_SETUP_SQL]
        await self.create_tables(schema=tables)

    async def add_user(self, discord_id: int) -> None | bool:
        """
        Add a Discord ID to the `users` table.

        Args:
            discord_id (int): Discord ID

        Raises:
            ValueError: If the Discord ID already exists in the Database.
        """
        _exists = await self._select_row(table="user", column="discordid", where="discordid", value=discord_id)
        if _exists == None:
            await self._insert_row(table="users", column="discordid", value=discord_id)
            return True
        else:
            raise ValueError(f"The Discord ID provided already exists in the Database. {discord_id}")

    async def update_user(self, discord_id: int, old_discord_id: int) -> None | bool:
        """
        Update an existing Discord ID in the `users` table.\n

        Typically this method will not be used; simply use `update_ign` and change the IGN's `userid`.

        Args:
            discord_id (int): New Discord ID to replace the existing entry with.
            old_discord_id (int): Existing entry in the `users` table.

        Raises:
            ValueError: If the existing Discord ID is not in the Database or if the new Discord ID is already in the Database.
        """
        _exists = await self._select_row(table="users", column="discordid", where="discordid", value=old_discord_id)
        if _exists == None:
            raise ValueError(f"The Discord ID provided does not exist in the Database. {old_discord_id}")

        _new_exists = await self._select_row(table="users", column="discordid", where="discordid", value=discord_id)
        if _new_exists != None:
            raise ValueError(f"The Discord ID provided already exists in the Database. {discord_id}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""UPDATE users SET discordid = ? WHERE discordid = ?""", discord_id, old_discord_id)
                await db.commit()
                return True

    async def get_ign(self, ign: str | None, discord_id: int | None) -> list[IGN] | None:
        """
        Returns an IGN class object if the IGN exists or their is a Discord ID tied to an IGN.\n
        This can return multiple IGN class objects.

        Args:
            ign (str | None): IGN to search for.
            discord_id (int | None): Discord ID to search for.

        Returns:
            list[IGN] | None: Returns all matches to the IGN or Discord ID provided.
        """
        if ign == None and discord_id == None:
            raise ValueError(f"You must provided atleast one value, ign and discord_id cannot be None.")

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

    async def add_ign(self, ign: str, typeid: int, userid: int | None = None) -> IGN | None:
        """
        Adds an IGN to the DATABASE, has a unique constraint of `ign` and `typeid` to prevent duplicates.\n
        `userid` is Optional to set a Discord ID as an owner of the IGN.

        Args:
            ign (str): The IGN to be added to the DATABASE.
            typeid (int): The IGN type ID, see `igntypes` table.
            userid (int | None, optional): The Discord ID that the IGN will belong to. Defaults to None.

        Raises:
            ValueError: If the `typeid` does not exist in the DATABASE.

        Returns:
            IGN | None: Returns an IGN class object or None if `fetch()` fails.
        """
        _type = await self._select_row(table="igntypes", column="id", where="id", value=typeid)
        if _type == None:
            raise ValueError(f"The typeid provided does not exists. {typeid}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT * FROM ign WHERE name = ? and typeid = ?""", ign, typeid)
                res = await cur.fetchone()
                if res is not None:
                    return IGN(**res)

                else:
                    await cur.execute("""INSERT INTO ign(name, typeid, userid) VALUES(?, ?, ?)""", ign, typeid, userid)
                    res = await cur.fetchone()
                    await db.commit()
                    return IGN(**res) if res is not None else None

    async def update_ign(self, ign: str, new_ign: str | None = None, userid: int | None = None) -> IGN | None:
        """
        Update an IGN with either a new IGN and or set the `userid` aka Discord ID which correlates to who "owns" the IGN.

        Args:
            ign (str): The IGN to update.
            new_ign (str | None, optional): The new IGN to replace `ign`. Defaults to None.
            userid (int | None, optional): The ID value to correlate a Discord ID as owner from `users` table. Defaults to None.

        Raises:
            ValueError: If the IGN provided does not exist in the Database.

        Returns:
            IGN | None: Returns an IGN class on success or `None` if it fails to update.
        """
        # TODO - See about allowing `typeid` to be changed?
        # Grab the userid and name.
        # This allows us to use the existing value in the DB if None is provided.
        _name = await self._select_row(table="ign", column="name", where="name", value=ign)
        if _name == None:
            raise ValueError(f"The ign provided does not exist in the Database. {ign}")

        if isinstance(_name, str) and new_ign == None:
            new_ign = _name

        _userid = await self._select_row(table="ign", column="userid", where="name", value=ign)
        if isinstance(_userid, int) and userid == None:
            userid = _userid

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""UPDATE ign SET name = ? AND userid = ? WHERE name = ?""", new_ign, userid, ign)
                await db.commit()
                res = await cur.fetchone()
                return IGN(**res) if not None else None

    async def _delete_ign(self, ign: str) -> int | None:
        """
        Removes all entries of an IGN from the `ign` table and the `usermetrics` table. Regardless of Server

        Args:
            ign (str): The IGN to delete from the `ign` table.

        Raises:
            ValueError: If the IGN provided does not exist in the Database.

        Returns:
            int | None: Row count of removed entries.
        """
        _exist = self._select_row(table="ign", column="name", where="name", value=ign)
        if _exist == None:
            raise ValueError(f"The ign provided does not exist in the Database. {ign}")

        async with asqlite.connect(self._db_file_path)as db:
            async with db.cursor() as cur:
                res = await cur.execute("""SELECT id FROM ign WHERE name = ?""", ign)
                if isinstance(res, Row) and res["id"] is not None:
                    await cur.execute("""DELETE FROM usermetrics WHERE ignid = ?""", res["id"])
                    await cur.execute("""DELETE FROM ign WHERE name = ?""", ign)
                    await db.commit()
                    return cur.get_cursor().rowcount

    async def add_igntype(self, type: str) -> None:
        """
        Add a Server Type to the Database.

        Args:
            type (str): The Server Type to add to the Database.

        Raises:
            ValueError: If the type you provided already exists.
        """
        # TODO -- See about figuring out the server type from AMP API calls.
        # Need to pass that value along to our `igntypes` table to populate it.
        _exists = await self._select_row(table="igntypes", column="type", where="type", value=type)
        if _exists == None:
            await self._insert_row(table="igntypes", column="type", value=type)
        else:
            raise ValueError(f"The type you provided already exists in the database. {type}")

    async def update_igntype(self, type: str, new_type: str) -> None:
        """
        Update an existing `type` entry in the Database.

        Args:
            type (str): The existing type in the Database.
            new_type (str): The type to replace the existing Database entry.

        Raises:
            ValueError: If the `type` provided does not exist or the `new_type` already exists.
        """
        _exists = await self._select_row(table="igntypes", column="type", where="type", value=type)
        _new_exists = await self._select_row(table="igntypes", column="type", where="type", value=new_type)
        if _exists == None:
            raise ValueError(f"The type provided does not exist in the Database. {type}")
        if _new_exists != None:
            raise ValueError(f"The new_type provided already exists in the Database. {new_type}")

        await self._update_row(table="igntypes", column="type", where=type, value=new_type)

    async def _delete_igntype(self, type: str):
        """
        Removes a `type` from the `igntypes` table. There is a FOREIGN KEY reference for this table tied to IGNs.

        **Warning** This will raise a `sqlite3.IntegrityError` if the `igntypes(id)` value is already in use for an `ign`. \n
        Recommended using `update_igntype` at the very least first.

        Args:
            type (str): The `type` to be removed from the table.

        Raises:
            ValueError: If the provided `type` does not exist in the Database.
        """
        _exists = await self._select_row(table="igntypes", column="type", where="type", value=type)
        if _exists == None:
            raise ValueError(f"The type provided does not exist in the Database. {type}")

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""DELETE FROM igntypes WHERE type = ?""", type)
                await db.commit()
                return cur.get_cursor().rowcount

    async def transfer_ign_metrics(self, ign: str, to_ign: str, serverid: int) -> int:
        """
        Move existing metrics data from one IGN to another IGN. \n 
        Typical use case is when someone changes there IGN.


       **This will update the table entries for `to_ign` and `DELETE` the `ign` row and `usermetrics` row.**

        Args:
            ign (str): The IGN metrics to move/combine to `to_ign`
            to_ign (str): The destination IGN metrics to update.

        Returns:
            int : The amount of Rows deleted from the Database.
        """
        _exists = await self._select_row(table="ign", column="name", where="name", value=ign)
        if _exists == None:
            raise ValueError(f"The ign provided does not exist in the Database. {ign}")

        _to_exists = await self._select_row(table="ign", column="name", where="name", value=to_ign)
        if _to_exists == None:
            raise ValueError(f"The to_ign provided does not exist in the Database. {to_ign}")

        # TODO - This select statement will be need to validated when setting up my `servers` table.
        _server_exists = await self._select_row(table="servers", column="id", where="id", value=serverid)
        if _server_exists == None:
            raise ValueError(f"The serverid provided does not exist in the Database. {serverid}")

        # ign IDs to update our tables.
        _ignid = await self._select_row(table="ign", column="id", where="name", value=ign)
        _to_ignid = await self._select_row(table="ign", column="id", where="name", value=to_ign)

        async with asqlite.connect(self._db_file_path) as db:
            async with db.cursor() as cur:
                await cur.execute("""SELECT lastlogin,playtime FROM usermetrics WHERE ignid = ? and serverid = ?""", _ignid, serverid)
                res = await cur.fetchone()  # this is the old IGN metrics information.

                await cur.execute("""SELECT lastlogin,playtime FROM usermetrics WHERE ignid = ? and serverid = ?""", _to_ignid, serverid)
                to_res = await cur.fetchone()  # this is the new IGN metrics information.
                _lastlogin = to_res["lastlogin"]
                _playtime = res["playtime"] + to_res["playtime"]
                # update the NEW IGN with the combined playtime and most recent login data.
                await cur.execute("""UPDATE usermetrics SET lastlogin = ? and playtime = ? WHERE ignid = ? and serverid = ?""", _lastlogin, _playtime, _to_ignid, serverid)
                # remove the old user metrics information tied to the ign and remove the ign from the table.
                await cur.execute("""DELETE FROM usermetrics WHERE ignid = ? and serverid = ?""", _ignid, serverid)
                await cur.execute("""DELETE FROM ign WHERE ignid = ?""", _ignid)
                await db.commit()
                return cur.get_cursor().rowcount
