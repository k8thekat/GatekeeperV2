from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from sqlite3 import Cursor, IntegrityError, Row
from typing import List, Literal, Self

import utils.asqlite as asqlite

from .base import Base
from .types import *

USERS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER UNIQUE NOT NULL
)STRICT"""

IGN_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS ign (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    type_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(name, type_id),
    UNIQUE(type_id, user_id)
)STRICT"""

METRICS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS ign_metrics (
    ign_id INTEGER NOT NULL,
    instance_id TEXT NOT NULL,
    last_login REAL,
    playtime INTEGER,
    created_at REAL,
    FOREIGN KEY (instance_id) REFERENCES servers(instance_id),
    FOREIGN KEY (ign_id) REFERENCES ign(id)
    UNIQUE(ign_id, instance_id)
)STRICT"""

# This will be used to determine what instances a user can
# interact with via `/commands` based upon their discord user id.
USER_INSTANCES_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS user_instances (
    user_id INTEGER NOT NULL,
    instance_id TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (instance_id) REFERENCES servers(instance_id),
    UNIQUE(user_id, instance_id)
)STRICT"""

# This will be used to determine what instances a discord user can
# interact with via `/commands` based upon their discord role id.
ROLE_INSTANCES_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS role_instances (
    role_id INTEGER NOT NULL,
    instance_id TEXT NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES servers(instance_id),
    UNIQUE(role_id, instance_id)
)STRICT"""

# This will be used to determine what instances a discord user can
# interact with via `/commands` based upon the discord guild id.
GUILD_INSTANCES_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS guild_instances (
    guild_id INTEGER NOT NULL,
    instance_id TEXT NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES servers(instance_id),
    UNIQUE(guild_id, instance_id)
)STRICT"""


@dataclass()
class Metrics(Base):
    """
    The Metrics class that represents an IGN's metrics.
    """
    ign_id: int
    instance_id: str
    playtime: int
    _pool: InitVar[asqlite.Pool | None] = None

    @property
    def last_login(self) -> datetime:
        """
         Converts our `last_login` attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        if isinstance((self._last_login), datetime):
            return self._last_login

        return datetime.fromtimestamp(timestamp=self._last_login)

    @last_login.setter
    def last_login(self, value: float) -> None:
        self._last_login: float = value

    @property
    def created_at(self) -> datetime:
        """
        Converts our `created_at` attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        if isinstance((self._created_at), datetime):
            return self._created_at

        return datetime.fromtimestamp(timestamp=self._created_at)

    @created_at.setter
    def created_at(self, value: float) -> None:
        self._created_at: float = value


@dataclass()
class IGN(Base):
    id: int  # primary key from `ign` table. **UNIQUE**
    name: str  # `name`` from `ign` table.
    user_id: int  # `user_id` from `users` table.
    type_id: ServerTypes  # `type_id` from `ign` table.
    metrics: list[Metrics] = field(default_factory=list)  # `ign_metrics` table.
    _pool: InitVar[asqlite.Pool | None] = None

    @property
    def type(self) -> str:
        """
        Returns the instance type the IGN belongs to. \n
        eg `Minecraft, Ark, Source/Valve`
        """
        return ServerTypes(value=self.type_id).name

    # TODO - Test once Instance table is created.
    async def _validate_metrics(self, metric: Metrics) -> None:
        """
        Checks if a `Metrics` object already exists in our `IGN.metrics` attribute.

        Args:
            metric (Metrics): The `Metrics` dataclass object

        Returns:
            None : Returns `None`
        """
        _temp: list[Metrics] = self.metrics

        if len(self.metrics) == 0:
            self.metrics.append(metric)
            return None

        for entry in self.metrics:
            # These are my 2 UNIQUE constraints.

            if (entry.ign_id == metric.ign_id) and (entry.instance_id == metric.instance_id):
                return None
            else:
                _temp.append(metric)
        self.metrics: list[Metrics] = _temp

    # TODO - Test once Instance table is created.
    async def _replace_metrics(self, metric: Metrics) -> None:
        """
        Replace an existing `Metrics` dataclass in our `IGN.metrics` attribute.
        * Typically called when a `Metrics` dataclass object is updated.

        Args:
            metric (Metrics): The `Metrics` dataclass object.

        Returns:
            None: Returns `None`
        """
        _temp: List[Metrics] = self.metrics

        if len(self.metrics) == 0:
            self.metrics.append(metric)
            return None

        for entry in self.metrics:
            if (entry.ign_id == metric.ign_id) and (entry.instance_id == metric.instance_id):
                _temp.remove(entry)
                _temp.append(metric)
                break
        self.metrics = _temp

    # TODO - Test once Instance table is created.
    async def get_metrics(self) -> IGN:
        """
        Updates the IGN object with the latest Metrics from the `ign_metrics` table.
        """
        _metrics: None | list[Row] = await self._fetchall(f"""SELECT * FROM ign_metrics WHERE ign_id = ?""", (self.id,))
        if _metrics is not None:
            [await self._validate_metrics(metric=Metrics(**entry)) for entry in _metrics]
        return self

    # TODO - Test once Instance table is created.
    async def update_metrics(self, instance_id: str, last_login: float = datetime.now().timestamp(), playtime: int = 0) -> Metrics | None:
        """
        Update the IGN's metrics for the provided `instance_id`.
        * Also updates the self `IGN` dataclass object.

        Args:
            instance_id (str): The AMP Instance ID.
            last_login (float, optional): The posix timestamp for IGNs last login. Defaults to datetime.now().timestamp().
            playtime (int, optional): The playtime in minutes. Defaults to 0.

        Returns:
            Metrics | None: Returns a `Metrics` dataclass object, while also updating the `IGN` dataclass object.
        """
        _exists: Row | None = await self._fetchone(f"""SELECT * FROM ign_metrics WHERE ign_id = ? and instance_id = ?""", (self.id, instance_id))
        if _exists is None:
            res: Row | None = await self._execute(f"""INSERT INTO ign_metrics(ign_id, instance_id, last_login, playtime, created_at)
                                      VALUES(?, ?, ?, ?, ?) RETURNING *""", (self.id, instance_id, last_login, playtime, datetime.now().timestamp()))
            return Metrics(**res) if res is not None else None
        else:
            metrics = Metrics(**_exists)
            metrics.last_login = last_login
            metrics.playtime = metrics.playtime + playtime
            await self._replace_metrics(metric=metrics)
            await self._execute(f"""UPDATE ign_metrics SET last_login = ?, playtime = ? WHERE ign_id = ? and instance_id = ?""",
                                (last_login, metrics.playtime, self.id, instance_id))
        return metrics

    # TODO - Test once Instance table is created.
    async def get_instance_metrics(self, instance_id: str) -> Metrics | None:
        """
        Get the Metrics data for a specific `instance_id`.

        Args:
            instance_id(str): The AMP Instance ID.

        Returns:
            Metrics | None: Returns a `Metrics` dataclass object.
        """
        _metrics: None | Row = await self._fetchone(f"""SELECT * FROM ign_metrics WHERE ign_id=? and instance_id=?""", (self.id, instance_id))
        if _metrics is not None:
            return Metrics(**_metrics)
        return None

    async def get_global_playtime(self) -> int:
        """
        Returns the total playtime across all servers.

        Returns:
            int: The total playtime across all servers in minutes.
        """
        res: list[Row] | None = await self._fetchall(f"""SELECT playtime FROM ign_metrics WHERE ign_id=?""", (self.id,))
        if res is not None:
            return sum([entry["playtime"] for entry in res])
        return 0

    async def get_instance_last_login(self, instance_id: str) -> datetime | None:
        """
       Returns the last time this IGN logged into the provided `instance_id`.

        Args:
            instance_id(str): The AMP Instance ID.

        Returns:
            datetime | None: Returns a `Non - Timezone` aware object. Will use OS / machines timezone information.
        """
        res: Row | None = await self._fetchone(f"""SELECT last_login FROM ign_metrics WHERE ign_id=? and instance_id=?""", (self.id, instance_id))
        if res is not None:
            return datetime.fromtimestamp(timestamp=res["last_login"])
        return None

    async def update_name(self, name: str) -> Self | None:
        """
        Updates the IGN name in the `ign` table and returns an updated class object.

        Args:
            name (str): The IGN.

        Returns:
            Self | None: Returns an updated `IGN` dataclass object.
        """
        try:
            await self._execute(f"""UPDATE ign SET name = ? WHERE id = ?""", (name, self.id))
        except IntegrityError as e:
            raise ValueError(f"The `name` provided conflicts with an existing `name`, `user_id` and `type_id` in the Database. name:{name} user_id:{self.user_id} type_id:{self.type_id}")
        self.name = name
        return self

    async def update_user_id(self, user_id: int) -> Self | None:
        """
        Updates the IGN `user_id` in the `ign` table and returns an updated class object.

        Args:
            user_id (int): The Discord User ID.

        Returns:
            Self | None: Returns an updated `IGN` dataclass object.
        """
        try:
            await self._execute(f"""UPDATE ign SET user_id = ? WHERE id = ?""", (user_id, self.id))
        except IntegrityError as e:
            raise ValueError(f"The `user_id` provided conflicts with an existing `name`, `user_id` and `type_id` in the Database. name:{self.name} user_id:{user_id} type_id:{self.type_id}")
        self.user_id = user_id
        return self

    async def update_type_id(self, type_id: ServerTypes) -> Self | None:
        """
        Updates the IGN `type_id` in the `ign` table and returns an updated class object.

        Args:
            type_id (ServerTypes): The ServerTypes enum value.

        Returns:
            Self | None: Returns an updated `IGN` dataclass object.
        """
        try:
            await self._execute(f"""UPDATE ign SET type_id = ? WHERE id = ?""", (type_id.value, self.id))
        except IntegrityError as e:
            raise ValueError(f"The `type_id` provided conflicts with an existing `name`, `user_id` and `type_id` in the Database. name:{self.name} user_id:{self.user_id} type_id:{type_id}")
        self.type_id = type_id
        return self

    async def delete_ign(self) -> int:
        """
        Removes all entries of an IGN from the `ign` table and the `user_metrics` table. Regardless of Server.

        Args:
            ign (str): The IGN to delete from the `ign` table.

        Returns:
            int | None: Row count of removed entries.
        """
        # res: Cursor = await self._execute_with_cursor(f"""DELETE FROM ign_metrics WHERE ign_id = ?""", (self.id,))
        res2: Cursor = await self._execute_with_cursor(f"""DELETE FROM ign WHERE id = ?""", (self.id,))
        # return res.rowcount + res2.rowcount
        return res2.rowcount


@ dataclass()
class User(Base):
    user_id: int
    igns: list[IGN] = field(default_factory=list)
    instance_ids: set[str] = field(default_factory=set)
    _pool: InitVar[asqlite.Pool | None] = None

    async def _validate_igns(self, ign: IGN) -> None:
        _temp: list[IGN] = self.igns

        if len(self.igns) == 0:
            self.igns.append(ign)
            return None

        for entry in self.igns:
            # These are my 3 UNIQUE constraints.

            if (entry.name == ign.name) and (entry.type_id == ign.type_id) and (entry.user_id == ign.user_id):
                return None
            else:
                _temp.append(ign)
        self.igns = _temp

    async def add_ign(self, name: str, type_id: ServerTypes = ServerTypes.GENERAL) -> User | None:
        """
        Adds an IGN to the DATABASE, has a unique constraint of `ign` and `type_id` to prevent duplicates.\n

        Args:
            name (str): The IGN to be added to the DATABASE.
            type_id (int): The IGN type ID. See `db_types` -> ServerTypes.

        Raises:
            ValueError: If the `name` `type_id` already exists in the Database.
            ValueError: If the `type_id` and `user_id` already exists in the Database.

        Returns:
            IGN | None: Returns an IGN class object or None if `fetch()` fails.
        """
        name = name.strip()
        try:
            res: None | Row = await self._execute(f"""INSERT INTO ign(name, user_id, type_id) VALUES(?, ?, ?) ON CONFLICT(user_id, type_id) DO NOTHING RETURNING *""",
                                                  (name, self.user_id, type_id.value))
        # This triggers with (name, type_id) UNIQUE
        except IntegrityError as e:
            raise ValueError(f"The `user_id` provided already has an `name` of this `type_id` in the Database. name:{name} user_id:{self.user_id} type_id:{type_id.value}")
        # This triggers with (type_id, user_id) UNIQUE
        if res is None:
            raise ValueError(f"The `user_id` provided already has an `name` of this `type_id` in the Database. name:{name} user_id:{self.user_id} type_id:{type_id.value}")

        if res is not None:
            await self._validate_igns(ign=IGN(**res))
            return self

    async def _get_igns(self) -> None:
        """
        Get all the IGN's that belong to this DBUser.
        """

        res: list[Row] | None = await self._fetchall(f"""SELECT * FROM ign WHERE user_id = ?""", (self.user_id,))
        if res is not None:
            [await self._validate_igns(ign=await IGN(**entry).get_metrics()) for entry in res]
        return None

    async def _get_instance_list(self) -> None:
        """
        Get all `instance_ids` that this DBUser is allowed to interact with based upon their `user_id`.
        """
        res: list[Row] | None = await self._fetchall(f"""SELECT instance_id FROM user_instances WHERE user_id = ?""", (self.user_id,))
        if res is not None:
            self.instance_ids.update([entry["instance_id"] for entry in res])
        return None

    # TODO - Test once Instance table is done.
    async def add_user_instance(self, instance_id: str) -> User | None:
        """
        Add an `instance_id` to the `user_instances` table.
        * This controls which AMP Instances this DBUser is allowed to interact with.*

        Args:
            instance_id (str): The AMP Instance ID.

        Raises:
            ValueError: If the `instance_id` value is to short.

        Returns:
            User | None: Returns an updated `User` object if the `instance_id` was added to the Database.
        """

        res: Row | None = await self._execute(f"""INSERT INTO user_instances(user_id, instance_id) VALUES(?, ?)
                           ON CONFLICT(user_id, instance_id) DO NOTHING RETURNING *""", (self.user_id, instance_id))
        if res is None:
            raise ValueError(f"The `user_id` provided already has this `instance_id` in the Database. user_id:{self.user_id} instance_id:{instance_id}")

        self.instance_ids.add(res["instance_id"])
        return self

    # TODO - Test once Instance table is done.
    async def remove_user_instance(self, instance_id: str) -> User | None:
        """
        Remove an `instance_id` from the `user_instances` table.
        * This controls which AMP Instances this DBUser is allowed to interact with.

        Args:
            instance_id (str): The AMP Instance ID.

        Returns:
            User | None: Returns an updated `User` object if the `instance_id` was removed from the Database.

        """
        await self._execute(f"""DELETE FROM user_instances WHERE user_id = ? AND instance_id = ?""", (self.user_id, instance_id))
        self.instance_ids.discard(instance_id)
        return self

    # TODO - Test once Instance table is done.
    async def _get_role_based_instance_list(self, roles: int | list[int]) -> None:
        """
        Get all `instance_ids` that this DBUser is allowed to interact with based on their role.
        """

        if isinstance(roles, int):
            roles = [roles]

        for role_id in roles:
            res: list[Row] | None = await self._fetchall(f"""SELECT instance_id FROM role_instances WHERE role_id = ?""", (role_id,))
            if res is not None:
                self.instance_ids.update([entry["instance_id"] for entry in res])
        return None

    # TODO - Test once Instance table is done.
    async def _get_guild_based_instance_list(self, guild_id: int) -> None:
        """
        Get all `instance_ids` that this DBUser is allowed to interact with based on their guild.
        """
        res: list[Row] | None = await self._fetchall(f"""SELECT instance_id FROM guild_instances WHERE guild_id = ?""", (guild_id,))
        if res is not None:
            self.instance_ids.update([entry["instance_id"] for entry in res])
        return None


class DBUser(Base):
    """
    Represents a Discord User in our DATABASE.

    """
    # TODO - Possibly a get_all_igns() method.
    # - Maybe filter by `instance_id` for leader boards or similar?

    async def _initialize_tables(self) -> None:
        """
        Creates the `DBUser` tables.
        """
        tables: list[str] = [USERS_SETUP_SQL, IGN_SETUP_SQL, METRICS_SETUP_SQL,
                             USER_INSTANCES_SETUP_SQL, ROLE_INSTANCES_SETUP_SQL,
                             GUILD_INSTANCES_SETUP_SQL]
        await self._create_tables(schema=tables)

    async def add_user(self, user_id: int) -> User | None:
        """
        Add a Discord User ID to the `users` table.

        Args:
            user_id(int): The Discord User ID.

        Raises:
            ValueError: If the `user_id` already exists in the Database.

        Returns:
            User | None: Returns a User object if the Discord ID exists in the Database.
        """

        _exists: List[Row] | None = await self._select_row_where(table="users", column="user_id", where="user_id", value=user_id)
        if _exists is not None:
            raise ValueError(f"The `user_id` provided already exists in the `users` table. user_id:{user_id}")

        res: None | Row = await self._insert_row(table="users", column="user_id", value=user_id)
        return User(**res) if res is not None else None

    async def get_user(self, user_id: int, roles: list[int] | int | None = None, guild_id: int | None = None) -> User | None:
        """
        Get a User object based on the Discord User ID.

        Args:
            user_id(int): The Discord User ID.
            roles(list[int] | int | None, optional): The Discord Role ID's. Defaults to None.
            guild_id(int | None, optional): The Discord Guild ID. Defaults to None.

        Returns:
            User | None: Returns a User object if the Discord ID exists in the Database.
        """

        _exists: Row | None = await self._fetchone("""SELECT * FROM users WHERE user_id = ?""", (user_id,))
        if _exists is None:
            raise ValueError(f"The `user_id` provided doesn't exists in the `users` table. user_id:{user_id}")

        res = User(**_exists)
        await res._get_igns()
        await res._get_instance_list()
        if roles is not None:
            await res._get_role_based_instance_list(roles=roles)
        if guild_id is not None:
            await res._get_guild_based_instance_list(guild_id=guild_id)
        return res

    async def get_ign(self, name: str, type_id: ServerTypes) -> IGN | None:
        """
        Get a `IGN` object based on the `name` and `type_id`.

        Args:
            name (str): The IGN name.
            type_id (_type_): The AMP Instance Type ID.

        Raises:
            ValueError: If the `name` and `type_id` provided doesn't exists in the `ign` table.

        Returns:
            User | None: Returns a `User` object if the `name` and `type_id` exists in the Database.
        """

        _exists: Row | None = await self._fetchone(f"""SELECT * FROM ign WHERE name = ? and type_id = ?""", (name, type_id.value))
        if _exists is None:
            raise ValueError(f"The `name` and `type_id` provided doesn't exists in the `ign` table. name:{name} type_id:{type_id.value}")
        return IGN(**_exists)

    async def get_all_igns(self) -> list[IGN] | None:
        res: List[Row] | None = await self._fetchall(f"""SELECT * FROM ign""")
        return [IGN(**entry) for entry in res] if res is not None else None

    # TODO - Test once server table is done.
    async def add_role_instance(self, role_id: int, instance_id: str) -> None | Literal[True]:
        """
        Add a `instance_id` to the `role_instances` table.
        * This allows Users with this Discord Role ID to interact with this AMP Instance ID.

        Args:
            role_id(int): The Discord Role ID.
            instance_id(str): The AMP Instance ID.

        Raises:
            ValueError: If the `role_id` provided already has this `instance_id` in the Database.

        Returns:
            None | Literal[True]: Returns `True` if the `role_id` and `instance_id` was added to the Database.
        """

        res: Row | None = await self._execute(f"""INSERT INTO role_instances(role_id, instance_id) VALUES(?, ?)
                                 ON CONFLICT(role_id, instance_id) DO NOTHING""", (role_id, instance_id))
        if res is None:
            raise ValueError(f"The `role_id` provided already has this `instance_id` in the Database. role_id:{role_id} instance_id:{instance_id}")
        return True

    # TODO - Test once server table is done.
    async def remove_role_instance(self, role_id: int, instance_id: str) -> int:
        """
        Remove a `instance_id` from the `role_instances` table.
        * This allows Users with this Discord Role ID to no longer be able to interact with this AMP Instance ID.

        Args:
            role_id(int): The Discord Role ID.
            instance_id(str): The AMP Instance ID.

        Raises:
            ValueError: If the `role_id` provided doesn't have this `instance_id` in the Database.

        Returns:
            int : Returns the number of rows deleted.
        """
        _exists: Row | None = await self._fetchone(f"""SELECT * FROM role_instances WHERE role_id = ? AND instance_id = ?""", (role_id, instance_id))
        if _exists is None:
            raise ValueError(f"The `role_id` provided doesn't have this `instance_id` in the Database. role_id:{role_id} instance_id:{instance_id}")

        res: Cursor = await self._execute_with_cursor(f"""DELETE FROM role_instances WHERE role_id = ? AND instance_id = ?""", (role_id, instance_id))
        return res.rowcount

    # TODO - Test once server table is done.
    async def add_guild_instances(self, guild_id: int, instance_id: str) -> None | Literal[True]:
        """
        Add a `instance_id` to the `guild_instances` table.
        * This allows Users within this Discord Guild ID to interact with this AMP Instance ID.

        Args:
            guild_id (int): The Discord Guild ID.
            instance_id (str): The AMP Instance ID.

        Raises:
            ValueError: If the `guild_id` provided already has this `instance_id` in the Database.

        Returns:
            None | Literal[True]: Returns `True` if the `guild_id` and `instance_id` was added to the Database.
        """

        res: Row | None = await self._execute(f"""INSERT INTO guild_instances(guild_id, instance_id) VALUES(?, ?)
                                 ON CONFLICT(guild_id, instance_id) DO NOTHING""", (guild_id, instance_id))
        if res is None:
            raise ValueError(f"The `guild_id` provided already has this `instance_id` in the Database. guild_id:{guild_id} instance_id:{instance_id}")
        return True

    # TODO - Test once server table is done.
    async def remove_guild_instances(self, guild_id: int, instance_id: str) -> int:
        """
        Remove a `instance_id` from the `guild_instances` table.
        * This allows Users within this Discord Guild ID to no longer be able to interact with this AMP Instance ID.

        Args:
            guild_id (int): The Discord Guild ID.
            instance_id (str): The AMP Instance ID.

        Raises:
            ValueError: If the `guild_id` provided doesn't have this `instance_id` in the Database.

        Returns:
            int : Returns the number of rows deleted.
        """
        _exists: Row | None = await self._fetchone(f"""SELECT * FROM guild_instances WHERE guild_id = ? AND instance_id = ?""", (guild_id, instance_id))
        if _exists is None:
            raise ValueError(f"The `guild_id` provided doesn't have this `instance_id` in the Database. guild_id:{guild_id} instance_id:{instance_id}")

        res: Cursor = await self._execute_with_cursor(f"""DELETE FROM guild_instances WHERE guild_id = ? AND instance_id = ?""", (guild_id, instance_id))
        return res.rowcount
