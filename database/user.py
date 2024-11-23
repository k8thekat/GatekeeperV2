from __future__ import annotations

import functools
from dataclasses import InitVar, dataclass, field
from datetime import datetime, timedelta
from sqlite3 import Cursor, IntegrityError, OperationalError, Row
from typing import List, Literal, Self

import utils.asqlite as asqlite

from .base import Base
from .types import *


@dataclass()
class Metrics(Base):
    """
    Represents the data from the `ign_metrics` table.
    """
    ign_id: int
    instance_id: str
    playtime: int
    last_login: datetime
    created_at: datetime
    _pool: InitVar[asqlite.Pool | None] = None

    def __hash__(self) -> int:
        return hash((self.ign_id, self.instance_id))

    def __eq__(self, other) -> Any | Literal[False]:
        try:
            return self.ign_id == other.ign_id and self.instance_id == other.instance_id
        except AttributeError:
            return False

    def __post_init__(self, _pool: asqlite.Pool | None = None) -> None:
        self.last_login = datetime.fromtimestamp(timestamp=self.last_login)   # type:ignore
        self.created_at = datetime.fromtimestamp(timestamp=self.created_at)  # type:ignore


@dataclass()
class IGN(Base):
    """
    Represents the data from the `ign` table with methods to update it and access the metrics information related to the `ign`.
    See `metrics` attribute for more information.

    """
    id: int  # primary key from `ign` table. **UNIQUE**
    name: str  # `name`` from `ign` table.
    user_id: int  # `user_id` from `users` table.
    type_id: int  # `type_id` from `ign` table.
    metrics: set[Metrics] = field(default_factory=set)  # `ign_metrics` table.
    _pool: InitVar[asqlite.Pool | None] = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> Any | Literal[False]:
        try:
            return self.id == other.id
        except AttributeError:
            return False

    @staticmethod
    def exists(func):
        @functools.wraps(wrapped=func)
        async def wrapper_exists(self: Self, *args, **kwargs) -> bool:
            res: Row | None = await self._fetchone(SQL=f"""SELECT id FROM ign WHERE id = ?""", parameters=(self.id,))
            if res is None:
                raise ValueError(f"The `id` of this class doesn't exists in the `ign` table. ID:{self.id}")
            return await func(self, *args, **kwargs)
        return wrapper_exists

    @property
    def type(self) -> str:
        """
        Returns the instance type the IGN belongs to. \n
        eg `Minecraft, Ark, Source/Valve`
        """
        return ServerTypes(value=self.type_id).name

    @exists
    async def _replace_metrics(self, metric: Metrics) -> None:
        """
        Replace an existing `Metrics` dataclass in our `IGN.metrics` attribute.
        * Typically called when a `Metrics` dataclass object is updated.

        Args:
            metric (Metrics): The `Metrics` dataclass object.

        Returns:
            None: Returns `None`
        """
        _temp: list[Metrics] = list(self.metrics)

        if len(self.metrics) == 0:
            self.metrics.add(metric)
            return None

        for entry in _temp:
            if (entry.ign_id == metric.ign_id) and (entry.instance_id == metric.instance_id):
                _temp.remove(entry)
                _temp.append(metric)
                break
        self.metrics = set(_temp)

    # TODO - Test once Instance table is done.
    @exists
    async def get_metrics(self) -> set[Metrics]:
        """
        Updates our Self with the latest Metrics from the `ign_metrics` table.

        Returns:
            set[Metrics]: Returns our `Self.metrics` attribute.
        """
        res: None | list[Row] = await self._fetchall(f"""SELECT * FROM ign_metrics WHERE ign_id = ?""", (self.id,))
        if res is not None:
            self.metrics = set([Metrics(**entry) for entry in res])
        return self.metrics

    # TODO - Test once Instance table is created.
    @exists
    async def update_metrics(self, instance_id: str, last_login: float = datetime.now().timestamp(), playtime: int = 0) -> Metrics | None:
        """
        Update our Self's metrics attribute for the provided `instance_id`.

        Args:
            instance_id (str): The AMP Instance ID.
            last_login (float, optional): The posix timestamp for IGNs last login. Defaults to datetime.now().timestamp().
            playtime (int, optional): The playtime in minutes. Defaults to 0.

        Returns:
            Metrics | None: Returns a `Metrics` dataclass object, while also updating our Self object.
        """
        _exists: Row | None = await self._fetchone(f"""SELECT * FROM ign_metrics WHERE ign_id = ? and instance_id = ?""", (self.id, instance_id))
        if _exists is None:
            try:
                res: Row | None = await self._execute(f"""INSERT INTO ign_metrics(ign_id, instance_id, last_login, playtime, created_at)
                                        VALUES(?, ?, ?, ?, ?) RETURNING *""", (self.id, instance_id, last_login, playtime, datetime.now().timestamp()))
            except IntegrityError as e:
                if e.args[0] == "FOREIGN KEY constraint failed":
                    raise NotImplementedError(f"The `instance_id` provided does not exist in the `instances` table. Instance ID: {instance_id}")
                raise e
            return Metrics(**res) if res is not None else None
        else:
            metrics = Metrics(**_exists)
            metrics.last_login = datetime.fromtimestamp(timestamp=last_login)
            metrics.playtime = metrics.playtime + playtime
            await self._replace_metrics(metric=metrics)
            await self._execute(f"""UPDATE ign_metrics SET last_login = ?, playtime = ? WHERE ign_id = ? and instance_id = ?""",
                                (last_login, metrics.playtime, self.id, instance_id))
        return metrics

    # TODO - Test once Instance table is created.
    @exists
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

    # TODO - Test once Instance table is created.
    @exists
    async def get_global_playtime(self) -> int:
        """
        Returns the total playtime across all instances.

        Returns:
            int: The total playtime across all instances in minutes.
        """
        res: list[Row] | None = await self._fetchall(f"""SELECT playtime FROM ign_metrics WHERE ign_id=?""", (self.id,))
        if res is not None:
            return sum([entry["playtime"] for entry in res])
        return 0

    # TODO - Test once Instance table is created.
    @exists
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

    @exists
    async def update_name(self, name: str) -> Self | None:
        """
        Updates the IGN name in the `ign` table.

        Args:
            name (str): The IGN.

        Returns:
            Self | None: Returns an updated Self object.
        """
        try:
            await self._execute(f"""UPDATE ign SET name = ? WHERE id = ?""", (name, self.id))
        except IntegrityError as e:
            raise ValueError(f"The `name` provided conflicts with an existing `name`, `user_id` and `type_id` in the Database. name:{name} user_id:{self.user_id} type_id:{self.type_id}")
        self.name = name
        return self

    @exists
    async def update_user_id(self, user_id: int) -> Self | None:
        """
        Updates the `user_id` in the `ign` table

        Args:
            user_id (int): The Discord User ID.

        Returns:
            Self | None: Returns an updated Self object.
        """

        if len(str(object=user_id)) < 15:
            raise ValueError("Your `user_id` value is to short. (<15)")

        _exists: Row | None = await self._fetchone(SQL=f"""SELECT * FROM users WHERE user_id = ?""", parameters=(user_id,))
        if _exists is None:
            raise ValueError(f"The `user_id` provided doesn't exists in the `users` table. user_id:{user_id}")

        try:
            await self._execute(f"""UPDATE ign SET user_id = ? WHERE id = ?""", (user_id, self.id))
        except IntegrityError as e:
            raise ValueError(f"The `user_id` provided conflicts with an existing `name`, `user_id` and `type_id` in the Database. name:{self.name} user_id:{user_id} type_id:{self.type_id}")
        self.user_id = user_id
        return self

    @exists
    async def update_type_id(self, type_id: ServerTypes) -> Self | None:
        """
        Updates the `type_id` in the `ign` table.

        Args:
            type_id (ServerTypes): The ServerTypes enum value.

        Returns:
            Self | None: Returns an updated Self object.
        """
        try:
            await self._execute(f"""UPDATE ign SET type_id = ? WHERE id = ?""", (type_id.value, self.id))
        except IntegrityError as e:
            raise ValueError(f"The `type_id` provided conflicts with an existing `name`, `user_id` and `type_id` in the Database. name:{self.name} user_id:{self.user_id} type_id:{type_id}")
        self.type_id = type_id.value
        return self

    @exists
    async def delete_ign(self) -> int:
        """
        Removes all entries our Self from the `ign` table and the `user_metrics` table. Regardless of Instance.

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
    """
    This represents the data from the `user` table with methods to update it and the AMP Instances it has access to for commands.
    See `instance_ids`.

    """
    user_id: int
    igns: set[IGN] = field(default_factory=set)
    instance_ids: set[str] = field(default_factory=set)
    _pool: InitVar[asqlite.Pool | None] = None

    async def add_ign(self, name: str, type_id: ServerTypes = ServerTypes.GENERAL) -> IGN | None:
        """
        Adds an IGN to the DATABASE, has a unique constraint of `ign` and `type_id` to prevent duplicates.\n

        Args:
            name (str): The IGN to be added to the DATABASE.
            type_id (int): The ServerTypes enum value. See `db_types` -> ServerTypes.

        Raises:
            ValueError: If the `name` `type_id` already exists in the Database.
            ValueError: If the `type_id` and `user_id` already exists in the Database.

        Returns:
            IGN | None: Returns an IGN class object or None if `fetch()` fails.
        """
        name = name.strip()
        # try:
        res: None | Row = await self._execute(f"""INSERT INTO ign(name, user_id, type_id) VALUES(?, ?, ?) ON CONFLICT(user_id, type_id) DO NOTHING RETURNING *""",
                                              (name, self.user_id, type_id.value))
        # except IntegrityError as e:
        #     raise ValueError(f"The `user_id` provided already has a `name` of this `type_id` in the Database. name:{name} user_id:{self.user_id} type_id:{type_id.value}")

        if res is None:
            raise ValueError(f"The `user_id` provided already has a `name` of this `type_id` in the Database. name:{name} user_id:{self.user_id} type_id:{type_id.value}")

        if res is not None:
            _temp = IGN(**res)
            self.igns.add(_temp)
            return _temp

    async def get_igns(self) -> set[IGN]:
        """
        Get all the IGN's that belong to this User.
        """

        res: list[Row] | None = await self._fetchall(f"""SELECT * FROM ign WHERE user_id = ?""", (self.user_id,))
        if res is not None:
            self.igns = set([IGN(**entry) for entry in res])
        return self.igns

    # TODO - Test once Instance table is done.
    async def get_instance_list(self) -> set[str]:
        """
        Get all `instance_ids` that this DBUser is allowed to interact with based upon their `user_id`.
        """
        res: list[Row] | None = await self._fetchall(f"""SELECT instance_id FROM user_instances WHERE user_id = ?""", (self.user_id,))
        if res is not None:
            self.instance_ids = set([entry["instance_id"] for entry in res])
        return self.instance_ids

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
            User | None: Returns an updated Self object if the `instance_id` was added to the Database.
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
            User | None: Returns an updated Self object if the `instance_id` was removed from the Database.

        """
        await self._execute(f"""DELETE FROM user_instances WHERE user_id = ? AND instance_id = ?""", (self.user_id, instance_id))
        self.instance_ids.remove(instance_id)
        return self

    # TODO - Test once Instance table is done.
    async def get_role_based_instance_list(self, roles: int | list[int]) -> set[str]:
        """
        Get all `instance_ids` that this DBUser is allowed to interact with based on their role.
        """

        if isinstance(roles, int):
            roles = [roles]

        for role_id in roles:
            res: list[Row] | None = await self._fetchall(f"""SELECT instance_id FROM role_instances WHERE role_id = ?""", (role_id,))
            if res is not None:
                self.instance_ids = set([entry["instance_id"] for entry in res])
        return self.instance_ids

    # TODO - Test once Instance table is done.
    async def get_guild_based_instance_list(self, guild_id: int) -> set[str]:
        """
        Get all `instance_ids` that this DBUser is allowed to interact with based on their guild.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: list[Row] | None = await self._fetchall(f"""SELECT instance_id FROM guild_instances WHERE guild_id = ?""", (guild_id,))
        if res is not None:
            self.instance_ids = set([entry["instance_id"] for entry in res])
        return self.instance_ids


class DBUser(Base):
    """
    Controls the interactions with our `user` table and any reference tables in our DATABASE.

    """

    async def add_user(self, user_id: int) -> User | None:
        """
        Add a Discord User ID to the `users` table.

        Args:
            user_id(int): The Discord User ID.

        Raises:
            ValueError: If the `user_id` value is to short we raise an exception.

        Returns:
            User | None: Returns a User object if the Discord ID exists in the Database.
        """
        if len(str(object=user_id)) < 15:
            raise ValueError("Your `user_id` value is to short. (<15)")

        res: None | Row = await self._execute(SQL=f"""INSERT INTO users(user_id) VALUES(?) ON CONFLICT(user_id) DO NOTHING RETURNING *""", parameters=(user_id,))
        return User(**res) if res is not None else None

    async def get_user(self, user_id: int, roles: list[int] | int | None = None, guild_id: int | None = None) -> User | None:
        """
        Get a User object based on the Discord User ID. Use the `roles` and `guild_id` to populate AMP Instances the User is allowed to interact with.

        Args:
            user_id(int): The Discord User ID.
            roles(list[int] | int | None, optional): The Discord Role ID's. Defaults to None.
            guild_id(int | None, optional): The Discord Guild ID. Defaults to None.

        Raises:
            ValueError: If the `user_id` value is to short we raise an exception.
            ValueError: If the `user_id` value doesn't exists we raise an exception.

        Returns:
            User | None: Returns a User object if the Discord ID exists in the Database.
        """

        if len(str(object=user_id)) < 15:
            raise ValueError("Your `user_id` value is to short. (<15)")

        _exists: Row | None = await self._fetchone("""SELECT * FROM users WHERE user_id = ?""", (user_id,))
        if _exists is None:
            raise ValueError(f"The `user_id` provided doesn't exists in the `users` table. user_id:{user_id}")

        res = User(**_exists)
        await res.get_igns()
        await res.get_instance_list()
        if roles is not None:
            await res.get_role_based_instance_list(roles=roles)
        if guild_id is not None:
            await res.get_guild_based_instance_list(guild_id=guild_id)
        return res

    async def get_ign(self, name: str, type_id: ServerTypes) -> IGN | None:
        """
        Get a `IGN` object based on the `name` and `type_id`.

        Args:
            name (str): The IGN name.
            type_id (_type_): The ServerTypes enum value.

        Raises:
            ValueError: If the `name` and `type_id` provided doesn't exists in the `ign` table.

        Returns:
            User | None: Returns a `User` object if the `name` and `type_id` exists in the Database.
        """
        # TODO - Default type_id to None and get all IGN's that match and return a list of IGN's instead.
        res: Row | None = await self._fetchone(f"""SELECT * FROM ign WHERE name = ? and type_id = ?""", (name, type_id.value))
        return IGN(**res) if res is not None else None

    async def get_all_igns_by_type(self, type_id: ServerTypes) -> list[IGN] | None:
        """
        Get all IGN's from the `ign` table that match the `type_id`.

        Args:
            type_id (ServerTypes): The ServerTypes enum value.

        Returns:
            list[IGN] | None: Returns a list of `IGN` objects.
        """
        res: List[Row] | None = await self._fetchall(f"""SELECT * FROM ign WHERE type_id = ?""", (type_id.value,))
        return [IGN(**entry) for entry in res] if res is not None else None

    # TODO - Test once server table is done.
    async def get_unique_visitors(self, instance_id: str, since: timedelta = timedelta(days=7)) -> list[IGN] | None:
        """
        Get the number of unique `IGN` visitors in the last `since` time.

        Args:
            instance_id (str): The AMP Instance ID.
            since (timedelta, optional): How far back to select from `ign_metrics`. Defaults to timedelta(days=7).

        Returns:
            list[IGN] | None: Returns a list of `IGN` objects.
        """
        _time: datetime | float = datetime.now() - since
        _time = _time.timestamp()
        _temp_ign: list[IGN] = []
        _users: list[Row] | None = await self._fetchall(f"""SELECT * FROM ign_metrics WHERE instance_id = ? AND created_at > ?""", (instance_id, _time))
        if _users is None:
            return None

        for user in _users:
            _ign: Row | None = await self._fetchone(f"""SELECT * FROM ign WHERE id = ?""", (user["ign_id"],))
            if _ign is not None:
                _temp_ign.append(IGN(**_ign))
            else:
                continue
        return _temp_ign

    # TODO - Test once server table is done.
    async def add_role_instance(self, role_id: int, instance_id: str) -> Literal[False] | Literal[True]:
        """
        Add a `instance_id` to the `role_instances` table.
        * This allows Users with this Discord Role ID to interact with this AMP Instance ID.

        Args:
            role_id(int): The Discord Role ID.
            instance_id(str): The AMP Instance ID.

        Raises:
            ValueError: If the `role_id` value is to short we raise an exception.
            ValueError: If the `role_id` provided already has this `instance_id` in the Database.

        Returns:
            Literal[False] | Literal[True]: Returns `True` if the `role_id` and `instance_id` was added to the Database.
        """

        if len(str(object=role_id)) < 15:
            raise ValueError("Your `role_id` value is to short. (<15)")

        res: Row | None = await self._execute(f"""INSERT INTO role_instances(role_id, instance_id) VALUES(?, ?)
                                 ON CONFLICT(role_id, instance_id) DO NOTHING RETURNING *""", (role_id, instance_id))
        # if res is None:
        #     raise ValueError(f"The `role_id` provided already has this `instance_id` in the Database. role_id:{role_id} instance_id:{instance_id}")
        return True if res is not None else False

    # TODO - Test once server table is done.
    async def remove_role_instance(self, role_id: int, instance_id: str) -> Literal[False] | Literal[True]:
        """
        Remove a `instance_id` from the `role_instances` table.
        * This allows Users with this Discord Role ID to no longer be able to interact with this AMP Instance ID.

        Args:
            role_id(int): The Discord Role ID.
            instance_id(str): The AMP Instance ID.

        Raises:
            ValueError: If the `role_id` value is to short we raise an exception.
            ValueError: If the `role_id` provided doesn't have this `instance_id` in the Database.

        Returns:
            int : Returns the number of rows deleted.
        """
        if len(str(object=role_id)) < 15:
            raise ValueError("Your `role_id` value is to short. (<15)")

        res: Row | None = await self._fetchone(f"""SELECT * FROM role_instances WHERE role_id = ? AND instance_id = ?""", (role_id, instance_id))
        if res is None:
            # raise ValueError(f"The `role_id` provided doesn't have this `instance_id` in the Database. role_id:{role_id} instance_id:{instance_id}")
            return False

        await self._execute_with_cursor(f"""DELETE FROM role_instances WHERE role_id = ? AND instance_id = ?""", (role_id, instance_id))
        return True

    # TODO - Test once server table is done.
    async def add_guild_instances(self, guild_id: int, instance_id: str) -> Literal[False] | Literal[True]:
        """
        Add a `instance_id` to the `guild_instances` table.
        * This allows Users within this Discord Guild ID to interact with this AMP Instance ID.

        Args:
            guild_id (int): The Discord Guild ID.
            instance_id (str): The AMP Instance ID.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.
            ValueError: If the `guild_id` provided already has this `instance_id` in the Database.

        Returns:
            None | Literal[True]: Returns `True` if the `guild_id` and `instance_id` was added to the Database.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: Row | None = await self._execute(f"""INSERT INTO guild_instances(guild_id, instance_id) VALUES(?, ?)
                                 ON CONFLICT(guild_id, instance_id) DO NOTHING""", (guild_id, instance_id))
        # if res is None:
        #     raise ValueError(f"The `guild_id` provided already has this `instance_id` in the Database. guild_id:{guild_id} instance_id:{instance_id}")
        return True if res is not None else False

    # TODO - Test once server table is done.
    async def remove_guild_instances(self, guild_id: int, instance_id: str) -> Literal[False] | Literal[True]:
        """
        Remove a `instance_id` from the `guild_instances` table.
        * This allows Users within this Discord Guild ID to no longer be able to interact with this AMP Instance ID.

        Args:
            guild_id (int): The Discord Guild ID.
            instance_id (str): The AMP Instance ID.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.
            ValueError: If the `guild_id` provided doesn't have this `instance_id` in the Database.

        Returns:
            int : Returns the number of rows deleted.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: Row | None = await self._fetchone(f"""SELECT * FROM guild_instances WHERE guild_id = ? AND instance_id = ?""", (guild_id, instance_id))
        if res is None:
            return False
            # raise ValueError(f"The `guild_id` provided doesn't have this `instance_id` in the Database. guild_id:{guild_id} instance_id:{instance_id}")

        await self._execute_with_cursor(f"""DELETE FROM guild_instances WHERE guild_id = ? AND instance_id = ?""", (guild_id, instance_id))
        return True
