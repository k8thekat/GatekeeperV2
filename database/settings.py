import functools
from dataclasses import dataclass, field
from sqlite3 import Row
from typing import Any, Self

import utils.asqlite as asqlite

from .base import Base
from .types import BannerType

# TODO - Docstring all the class methods.


@dataclass
class Settings(Base):
    """
    Represents the `settings` table in the database.
    """
    guild_id: int  # references `guilds` table `id` value.
    mod_role_id: int | None = None
    donator_role_id: int | None = None
    msg_timeout: int | None = None
    auto_update_banner: bool = True
    banner_type: BannerType = field(default=BannerType.IMAGES)  # type: ignore
    auto_whitelist: bool = True
    whitelist_request_channel_id: int | None = None

    whitelist_replies: set[str] = field(default_factory=set)
    owners: set[int] = field(default_factory=set)
    prefixes: set[str] = field(default_factory=set)

    @property
    def banner_type(self) -> int:
        return self._banner_type.value

    @banner_type.setter
    def banner_type(self, value: BannerType) -> None:
        self._banner_type: BannerType = value

    @staticmethod
    def exists(func):
        @functools.wraps(wrapped=func)
        async def wrapper_exists(self: Self, *args, **kwargs) -> bool:
            res: Row | None = await self._fetchone(SQL=f"""SELECT settings FROM instances WHERE guild_id = ?""", parameters=(self.guild_id,))
            if res is None:
                raise ValueError(f"The `guild_id` of this class doesn't exist in the `settings` table. ID: {self.guild_id}")
            return await func(self, *args, *kwargs)
        return wrapper_exists

    @exists
    async def set_mod_role_id(self, role_id: int) -> Self:
        """
        Set the `mod_role_id` value in the `settings` table.

        Args:
            role_id (int): The Discord Role ID. eg `617967701381611520`

        Raises:
            ValueError: If the `role_id` value is to short we raise an exception.

        Returns:
            Settings | None : Returns a Settings dataclass object.
        """

        if len(str(object=role_id)) < 15:
            raise ValueError("Your `role_id` value is to short. (<15)")

        res: None | Row = await self._update_row_where(table="settings", column="mod_role_id", value=role_id, where="guild_id", where_value=self.guild_id)
        self.mod_role_id = role_id
        return self

    @exists
    async def set_donator_role_id(self, role_id: int) -> Self:
        """
        Update the `donator_role_id`` value in the `settings` table.

        Args:
            role_id (int): The Discord Role ID. eg `617967701381611520`

        Raises:
            ValueError: If the `role_id` value is to short we raise an exception.

        Returns:
            Settings | None: Returns a Settings dataclass object.
        """

        if len(str(object=role_id)) < 15:
            raise ValueError("Your `role_id` value is to short. (<15)")

        res: None | Row = await self._update_row_where(table="settings", column="donator_role_id", value=role_id, where="guild_id", where_value=self.guild_id)
        self.donator_role_id = role_id
        return self

    @exists
    async def set_message_timeout(self, timeout: int = 120) -> Self:
        """
        Updates the `msg_timeout` value in the `settings` table. \n
         *aka time till the message is auto-deleted after a the bot sends a message.*

        Args:
            timeout (int): seconds. Default is `120` seconds.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            Settings | None: Returns a Settings dataclass object.
        """

        res: None | Row = await self._update_row_where(table="settings", column="msg_timeout", value=timeout, where="guild_id", where_value=self.guild_id)
        self.msg_timeout = timeout
        return self

    @exists
    async def set_auto_update_banner(self, value: bool = True) -> Self:
        res: None | Row = await self._update_row_where(table="settings", column="auto_update_banner", value=value, where="guild_id", where_value=self.guild_id)
        self.auto_update_banner = value
        return self

    @exists
    async def set_banner_type(self, banner_type: BannerType = BannerType.IMAGES) -> Self:
        res: None | Row = await self._update_row_where(table="settings", column="banner_type", value=banner_type.value, where="guild_id", where_value=self.guild_id)
        self.banner_type = banner_type
        return self

    @exists
    async def set_auto_whitelist(self, value: bool = True) -> Self:
        res: None | Row = await self._update_row_where(table="settings", column="auto_whitelist", value=value, where="guild_id", where_value=self.guild_id)
        self.auto_whitelist = value
        return self

    @exists
    async def set_whitelist_request_channel(self, channel_id: int) -> Self:
        if len(str(object=channel_id)) < 15:
            raise ValueError("Your `channel_id` value is to short. (<15)")
        res: None | Row = await self._update_row_where(table="settings", column="whitelist_request_channel_id", value=channel_id, where="guild_id", where_value=self.guild_id)
        self.whitelist_request_channel_id = channel_id
        return self

    @exists
    async def add_owner(self, user_id: int) -> Self:
        """
        Add a Discord User ID to the `owners` table. \n

        Args:
            user_id (int): The Discord User ID.

        Raises:
            ValueError: If the `user_id` value is to short we raise an exception.

        Returns:
            Owner | None: Returns a Owner dataclass object.
        """

        if len(str(object=user_id)) < 15:
            raise ValueError("Your `user_id` value is to short. (<15)")

        res: None | Row = await self._execute(SQL=f"""INSERT INTO owners(guild_id, user_id) VALUES(?, ?)
                                              ON CONFLICT(guild_id, user_id) DO NOTHING RETURNING *""", parameters=(self.guild_id, user_id))
        if res is not None:
            self.owners.add(user_id)
        return self

    @exists
    async def remove_owner(self, user_id: int) -> Self:
        """
        Remove a Discord User ID from the `owners` table.

        Args:
            user_id (int): The Discord User ID.

        Raises:
            ValueError: If the `user_id` value is to short we raise an exception.

        Returns:
            Self | None: Returns a Settings dataclass object.
        """

        if len(str(object=user_id)) < 15:
            raise ValueError("Your `user_id` value is to short. (<15)")

        res: None | Row = await self._execute("""SELECT * FROM owners WHERE guild_id = ? AND user_id = ?""", (self.guild_id, user_id))
        if res is None:
            raise ValueError(f"The `user_id` provided does not exist in the `owners` table. user_id:{user_id}")

        await self._execute("""DELETE FROM owners WHERE guild_id = ? AND user_id = ?""", (self.guild_id, user_id))
        self.owners.remove(user_id)
        return self

    @exists
    async def get_owners(self) -> set[int]:
        """
        Get all the owners from the `owners` table.

        Returns:
            set[int]: Returns a set of Discord User IDs.
        """

        res: list[Row] | None = await self._fetchall(SQL=f"""SELECT * FROM owners WHERE guild_id = ?""", parameters=(self.guild_id,))
        if res is not None:
            self.owners = set(row["user_id"] for row in res)
        return self.owners

    @exists
    async def add_prefix(self, prefix: str) -> Self:
        """
        Add a prefix to the `prefixes` table.

        Args:
            prefix(str): A phrase or single character. eg `?` or `gatekeeper`.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            Self: Returns the `Self` object.

        """

        prefix = prefix.strip()
        res: None | Row = await self._execute(SQL="""INSERT INTO prefixes(guild_id, prefix) VALUES(?, ?) ON CONFLICT(guild_id, prefix) DO NOTHING RETURNING *""", parameters=(self.guild_id, prefix))
        if res is not None:
            self.prefixes.add(prefix)
        return self

    @exists
    async def remove_prefix(self, prefix: str) -> Self:
        """
        Remove a prefix from the `prefixes` table.

        Args:
            prefix(str): The prefix to remove from the table.

        Raises:
            ValueError: If the `prefix` does not exist we raise an exception.

        Returns:
            Self: Returns the `Self` object.
        """

        res: None | Row = await self._execute("""SELECT prefix FROM prefixes WHERE guild_id = ? AND prefix = ?""", (self.guild_id, prefix))
        if res is None:
            raise ValueError(f"The `prefix` provided does not exist in the `prefixes` table. prefix:{prefix}")

        await self._execute("""DELETE FROM prefixes WHERE guild_id = ? AND prefix = ?""", (self.guild_id, prefix))
        self.prefixes.remove(prefix)
        return self

    @exists
    async def get_prefixes(self) -> set[str]:
        """"
        Get all the prefixes from the `prefixes` table.

        Args:
            guild_id (int): The Discord Guild ID.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            set[str]: Returns a set of prefixes.
        """

        res: list[Row] | None = await self._fetchall(f"""SELECT prefix FROM prefixes WHERE guild_id = ?""", (self.guild_id,))
        if res is not None:
            self.prefixes = set(row["prefix"] for row in res)
        return self.prefixes

    @exists
    async def add_whitelist_reply(self, reply: str) -> Self:
        reply = reply.strip()
        res: Row | None = await self._execute("""INSERT INTO whitelist_replies(guild_id, reply) VALUES(?, ?) ON CONFLICT(guild_id, reply) DO NOTHING RETURNING *""", (self.guild_id, reply))
        if res is not None:
            self.whitelist_replies.add(reply)
        return self

    @exists
    async def remove_whitelist_reply(self, reply: str) -> Self:
        res: None | Row = await self._execute("""SELECT reply FROM whitelist_replies WHERE guild_id = ? AND reply = ?""", (self.guild_id, reply))
        if res is None:
            raise ValueError(f"The `reply` provided does not exist in the `whitelist_replies` table. reply:{reply}")

        await self._execute("""DELETE FROM whitelist_replies WHERE guild_id = ? AND reply = ?""", (self.guild_id, reply))
        self.whitelist_replies.remove(reply)
        return self

    @exists
    async def get_whitelist_replies(self) -> set[str]:
        res: list[Row] | None = await self._fetchall(f"""SELECT reply FROM whitelist_replies WHERE guild_id = ?""", (self.guild_id,))
        if res is not None:
            self.whitelist_replies = set(row["reply"] for row in res)
        return self.whitelist_replies


class DBSettings(Base):
    """
    Controls the interactions with our `settings` table and any reference tables in our DATABASE.
    """

    async def add_guild_id(self, guild_id: int) -> Settings | None:
        """
        Add a Discord Guild ID to the `guilds` table.

        Args:
            guild_id (int): The Discord Guild ID.

        Raises:
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            Settings | None: Returns a Settings dataclass object if the Guild ID was added to the Database.
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
            ValueError: If the `guild_id` value is to short we raise an exception.

        Returns:
            Settings | None: Returns a Settings dataclass object.
        """
        if len(str(object=guild_id)) < 15:
            raise ValueError("Your `guild_id` value is to short. (<15)")

        res: asqlite.List[Row] | Row | None = await self._select_row_where(table="settings", column="*", where="guild_id", value=guild_id)
        return Settings(**res[0]) if res is not None else None
