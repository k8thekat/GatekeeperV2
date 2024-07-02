import functools
from dataclasses import InitVar, dataclass, field, fields
from sqlite3 import Row
from typing import Literal, Self

from utils import asqlite

from .base import Base
from .instance import Instance
from .types import Instance_Banner_Settings


@dataclass
class Banner_Group_Message():
    """
    Represents the data from the `banner_group_messages` table.
    """
    group_channel_id: int
    discord_message_id: int

    def __hash__(self) -> int:
        return hash((self.group_channel_id, self.discord_message_id))

    def __eq__(self, other) -> None | Literal[False]:
        try:
            return self.group_channel_id == other.group_channel_id and self.discord_message_id == other.discord_message_id
        except AttributeError:
            return False


@dataclass
class Banner_Group_Channel(Base):
    """
    Represents the data from the `banner_group_channels` table.
    """
    id: int | None
    discord_guild_id: int | None
    discord_channel_id: int | None
    group_id: int | None
    discord_messages: set[Banner_Group_Message] | None
    _pool: InitVar[asqlite.Pool | None] = None

    @staticmethod
    def exists(func):
        @functools.wraps(wrapped=func)
        async def wrapper_exists(self: Self, *args, **kwargs) -> bool:
            res: Row | None = await self._fetchone(SQL=f"""SELECT id FROM banner_group_channels WHERE id = ?""", parameters=(self.id,))
            if res is None:
                raise ValueError(f"The `id` of this class doesn't exist in the `banner_group_channels` table. ID: {self.id}")
            return await func(self, *args, **kwargs)
        return wrapper_exists

    @exists
    async def _remove_channel(self) -> None:
        """
        Remove this Banner Group Channel from the `banner_group_channels` table.
        """
        self.discord_guild_id = None
        self.discord_channel_id = None
        self.discord_messages = None
        # await self._execute(f"""DELETE FROM banner_group_messages WHERE group_channel_id = ?""", (self.id,))
        await self._execute(SQL=f"""DELETE FROM banner_group_channels WHERE id = ?""", parameters=(self.id,))
        self.id = None

    @exists
    async def update_discord_channel_id(self, discord_channel_id: int) -> Self:
        """
        Update the `discord_channel_id` of this Banner Group Channel.

        Args:
            discord_channel_id (int): The Discord Channel ID.

        Returns:
            Self: An updated Banner Group Channel object.
        """
        await self._execute(SQL=f"""UPDATE banner_group_channels SET discord_channel_id = ? WHERE id = ?""", parameters=(discord_channel_id, self.id))
        self.discord_channel_id = discord_channel_id
        return self

    @exists
    async def add_message(self, discord_message_id: int) -> Self:
        """
        Add a Discord Message ID to the `banner_group_messages` table related to this Banner Group Channel.

        Args:
            discord_message_id (int): The Discord Message ID.

        Raises:
            ValueError: The `discord_message_id` provided already exists in the `banner_group_messages` table.

        Returns:
            Self: An updated Banner Group Channel object.
        """
        res: Row | None = await self._execute(SQL=f"""INSERT INTO banner_group_messages(group_channel_id, discord_message_id) VALUES(?, ?)
                                              ON CONFLICT(group_channel_id, discord_message_id) DO NOTHING RETURNING *""",
                                              parameters=(self.id, discord_message_id))
        if res is None:
            raise ValueError(f"The `discord_message_id` provided already exists in the `banner_group_messages` table. Message ID: {discord_message_id}")

        if self.discord_messages is None:
            self.discord_messages = set()

        self.discord_messages.add(Banner_Group_Message(**res))
        return self

    @exists
    async def remove_message(self, discord_message_id: int) -> Self:
        """
        Remove a message from this Banner Group Channel.

        Args:
            discord_message_id (int): The Discord Message ID.

        Returns:
            Self: An updated Banner Group Channel object.
        """
        assert self.id
        await self._execute(SQL=f"""DELETE FROM banner_group_messages WHERE group_channel_id = ? and discord_message_id = ?""", parameters=(self.id, discord_message_id))
        if self.discord_messages is None:
            return self
        for message in self.discord_messages:
            if message.discord_message_id == discord_message_id:
                self.discord_messages.remove(message)
                break
        return self

    @exists
    async def get_messages(self) -> set[Banner_Group_Message] | None:
        """
        Get all the Banner Group Messages related to this Banner Group Channel and update the object.

        Returns:
            set[Banner_Group_Message]: Returns `self.discord_messages` attribute.
        """
        res: list[Row] | None = await self._fetchall(SQL=f"""SELECT * FROM banner_group_messages WHERE group_channel_id = ?""", parameters=(self.id,))
        if res is None:
            return self.discord_messages
        self.discord_messages = set([Banner_Group_Message(**message) for message in res])
        return self.discord_messages


@dataclass()
class Banner_Group(Base):
    """
    Represents the data from the `banner_group` table.
    """
    group_id: int | None
    name: str | None
    instances: set[Instance] | None = field(default_factory=set)
    channels: set[Banner_Group_Channel] | None = field(default_factory=set)
    _pool: InitVar[asqlite.Pool | None] = None

    @staticmethod
    def exists(func):
        @functools.wraps(wrapped=func)
        async def wrapper_exists(self: Self, *args, **kwargs) -> bool:
            res: Row | None = await self._fetchone(SQL=f"""SELECT group_id FROM banner_group WHERE group_id = ?""", parameters=(self.group_id,))
            if res is None:
                raise ValueError(f"The `group_id` of this class doesn't exist in the `banner_group` table. Group ID: {self.group_id}")
            return await func(self, *args, **kwargs)
        return wrapper_exists

    @exists
    async def remove_banner_group(self, name: str) -> None:
        """
        Remove a Banner Group from the `banner_group` table.

        Args:
            name(str): Name of the Banner Group.

        Raises:
            ValueError: If the name provided already exists in the Database.
            ValueError: If the `group_id` of this class doesn't exists in the `banner_group` table.

        """
        if self.channels is not None:
            for channel in self.channels:
                await channel._remove_channel()
        self.channels = None
        self.name = None
        self.instances = None
        # await self._execute(f"""DELETE FROM banner_group_channels WHERE group_id=?""", (self.group_id,))
        # await self._execute(f"""DELETE FROM banner_group_instances WHERE group_id=?""", (self.group_id,))
        await self._execute(SQL=f"""DELETE FROM banner_group WHERE name=?""", parameters=(name,))
        self.group_id = None

    @exists
    async def add_instance(self, instance_id: str) -> Self:
        """
        Add an AMP Instance to this Banner Group.

        Args:
            instance_id (str): The AMP Instance ID.

        Raises:
            ValueError: If the `instance_id` provided doesn't exists in the `instances` table.
            ValueError: If the `group_id` of this class doesn't exists in the `banner_group` table.

        Returns:
            Self: An Updated Banner Group object.
        """

        await self._execute(SQL=f"""INSERT INTO banner_group_instances(instance_id, group_id) VALUES(?, ?)""", parameters=(instance_id, self.group_id))
        res: Row | None = await self._fetchone(SQL=f"""SELECT * FROM instances WHERE instance_id = ?""", parameters=(instance_id,))
        if res is None:
            raise ValueError(f"The `instance_id` provided doesn't exists in the `instances` table. Instance ID: {instance_id}")

        if self.instances is None:
            self.instances = set()

        self.instances.add(Instance(**res))
        return self

    @exists
    async def remove_instance(self, instance_id: str) -> Self:
        """
        Remove an AMP Instance from this Banner Group.

        Args:
            instance_id (str): The AMP Instance ID.

        Raises:
            ValueError: If the `instance_id` provided doesn't exists in the `instances` table.
            ValueError: If the `group_id` of this class doesn't exists in the `banner_group` table.

        Returns:
            Self: An Update Banner Group object.
        """
        _exists: Row | None = await self._fetchone(SQL=f"""SELECT * FROM instances WHERE instance_id = ?""", parameters=(instance_id,))
        if _exists is None:
            raise ValueError(f"The `instance_id` provided doesn't exists in the `instances` table. Instance ID: {instance_id}")
        await self._execute(SQL=f"""DELETE FROM banner_group_instances WHERE instance_id=? AND group_id=?""", parameters=(instance_id, self.group_id))
        if self.instances is None:
            return self
        for instance in self.instances:
            if instance.instance_id == instance_id:
                self.instances.remove(instance)
                break
        return self

    @exists
    async def get_instances(self) -> set[Instance] | None:
        """
        Get all AMP Instances related to this Banner Group and updated the object.

        Raise:
            ValueError: If the `group_id` of this class doesn't exists in the `banner_group` table.

        Returns:
            set[Instance] | None: Returns `self.instances`.
        """
        res: list[Row] | None = await self._fetchall(SQL=f"""SELECT instance_id FROM banner_group_instances WHERE group_id=?""", parameters=(self.group_id,))
        if res is None:
            return self.instances
        self.instances = set([Instance(**instance) for instance in res])
        return self.instances

    @exists
    async def get_channels(self) -> set[Banner_Group_Channel] | None:
        """
        Get all Banner Group Channels related to this Banner Group and update the object.

        Raise:
            ValueError: If the `group_id` of this class doesn't exists in the `banner_group` table.

        Returns:
            set[Banner_Group_Channel] | None: Returns `self.channels`.
        """
        res: list[Row] | None = await self._fetchall(SQL=f"""SELECT * FROM banner_group_channels WHERE group_id=?""", parameters=(self.group_id,))
        if res is None:
            return self.channels
        self.channels = set([Banner_Group_Channel(**channel) for channel in res])
        return self.channels

    @exists
    async def add_channel(self, discord_guild_id: int, discord_channel_id: int) -> Banner_Group_Channel:
        """
        Add a Discord Channel ID to the `banner_group_channels` table.

        Args:
            discord_guild_id (int): The Discord Guild ID.
            discord_channel_id (int): The Discord Channel ID.

        Raises:
            ValueError: If the `group_id` of this class doesn't exists in the `banner_group` table.
            ValueError: If the `discord_guild_id` and `discord_channel_id` provided already exists in the `banner_group_channels` table.

        Returns:
            Banner_Group_Channel: A Banner Group Channel dataclass object.
        """
        res: Row | None = await self._execute(SQL=f"""INSERT INTO banner_group_channels(discord_guild_id, discord_channel_id, group_id) VALUES(?, ?, ?)
                            ON CONFLICT(discord_guild_id, discord_channel_id) DO NOTHING RETURNING *""",
                                              parameters=(discord_guild_id, discord_channel_id, self.group_id))
        if res is None:
            raise ValueError(f"The `discord_guild_id` and `discord_channel_id` provided already exists in the `banner_group_channels` table. Guild ID: {discord_guild_id}, Channel ID: {discord_channel_id}")
        if self.channels is None:
            self.channels = set()
        _group = Banner_Group_Channel(**res)
        self.channels.add(_group)
        return _group


class DBBanner(Base):
    """
    Controls the interactions with our `banner_group` table and any reference tables in our DATABASE.
    """

    async def add_banner_group(self, name: str) -> Banner_Group | None:
        """
        Add a Banner Group to the `banner_group` table.

        Args:
            name(str): Name of the Banner Group.

        Raises:
            ValueError: If the name provided already exists in the Database.

        Returns:
            Banner_Group | None: Returns a `Banner_Group` object if the name provided already exists in the Database.

        """
        res: Row | None = await self._execute(SQL=f"""INSERT INTO banner_group(name) VALUES(?) ON CONFLICT(name) DO NOTHING RETURNING * """, parameters=(name,))
        if res is None:
            raise ValueError(f"The `name` provided already exists in the `banner_group` table. Name: {name}")
        return Banner_Group(**res)

    async def get_banner_group(self, name: str) -> Banner_Group | None:
        res: Row | None = await self._fetchone(SQL=f"""SELECT * FROM banner_group WHERE name=?""", parameters=(name,))
        if res is None:
            raise ValueError(f"The `name` provided doesn't exists in the `banner_group` table. Name: {name}")
        _group = Banner_Group(**res)
        await _group.get_instances()
        await _group.get_channels()
        return _group
