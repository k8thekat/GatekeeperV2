
import functools
import re
from dataclasses import InitVar, dataclass, fields
from datetime import datetime
from sqlite3 import Row
from typing import Any, Literal, Self

from utils import asqlite

from .base import Base
from .types import (DonatorType, Instance_Banner_Settings, Instance_Button,
                    Instance_Settings, WhitelistType)


@dataclass
class Instance_Metrics(Base):
    """
    Represents the data from the `instance_metrics` table.

    """
    instance_id: str
    _pool: InitVar[asqlite.Pool | None] = None


@dataclass
class Instance_Banner(Instance_Banner_Settings, Base):
    _pool: InitVar[asqlite.Pool | None] = None

    @staticmethod
    def _pack(x: int, y: int) -> int:
        """
        Pack the provided `x` and `y` values into a 32-bit integer using bit shift operators.

        Args:
            x (int): int to pack
            y (int): int to pack

        Returns:
            int: A 32-bit integer with the `x` and `y` values packed together.
        """
        return (x << 16) | y

    def color_validation(self, value: str) -> None | str:
        """
        Uses regex the value provided is a valid hex color.

        Args:
            value (str): Hex color code.

        Returns:
            None | str: Returns the value if it is a valid hex color, else returns None.
        """
        if len(value) in [3, 4, 6, 8] and re.search(f'([0-9a-f]{{{len(value)}}})$', value):
            return value
        return None

    def pos_validation(self, value: tuple[int, int]) -> None | int:
        """
        Validates the X,Y by attempting to bit offset them into a 32-bit integer.

        Args:
            value (tuple[int, int]): The X, Y values to check.

        Returns:
            None | int: Returns the value as a 32-bit integer if it is valid, else returns None.
        """
        if len(value) == 2 and self._pack(x=value[0], y=value[1]) <= 52429070:
            return self._pack(x=value[0], y=value[1])
        return None

    def property_validation(self, value: str) -> str:
        """
        Verifies the `property` provided is an attribute of `Instance_Banner_Settings`.

        Args:
            value (str): The Property to validate.

        Raises:
            ValueError: If the `property` provided is not an attribute of `Instance_Banner_Settings`.

        Returns:
            str: The property.
        """
        _properties: list[str] = [field.name for field in fields(class_or_instance=Instance_Banner_Settings)]
        if value in _properties:
            return value
        else:
            raise ValueError(f"The `property` provided is invalid. Property: {value}")

    async def set_color(self, property: str, color: str = "#FFFFFF") -> None:
        """
        Update the `banner_element_color` column(property) with the provided hex color code.

        Args:
            property (str): The `Instance_Banner_Settings` property to set.
            color (str , optional): The hex color code to set. Defaults to `#FFFFFF`.

        Raises:
            ValueError: If the color provided is not a hex color code.
        """
        property = self.property_validation(value=property)
        res: None | str = self.color_validation(value=color)
        if res is None:
            raise ValueError(f"The `color` provided is invalid. Color: {color}")
        else:
            await self._execute(SQL=f"""UPDATE banner_element_color SET {property} = ? WHERE instance_id = ?""", parameters=(color, self.instance_id))

    async def set_position(self, property: str, position: tuple[int, int] = (0, 0)) -> None:
        """
        Update the `banner_element_position` column(property) with the provided X,Y position.

        Args:
            property (str): The `Instance_Banner_Settings` property to set.
            position (tuple[int, int] | None, optional): The X,Y position to set. Defaults to (0, 0).

        Raises:
            ValueError: If the position provided is larger than our Banner Resolution (800x600).
        """
        property = self.property_validation(value=property)

        res: None | int = self.pos_validation(value=position)
        if res is None:
            raise ValueError(f"The `position` provided is invalid. Position: {position}")
        else:
            await self._execute(SQL=f"""UPDATE banner_element_position SET {property} = ? WHERE instance_id = ?""", parameters=(res, self.instance_id))


@dataclass()
class Instance(Base):
    """
    Represents the data from the `instances` table.
    """
    instance_id: str | None
    instance_name: str | None
    created_at: datetime  # type:ignore
    _pool: InitVar[asqlite.Pool | None] = None

    def __hash__(self) -> int:
        return hash(self.instance_id)

    def __eq__(self, other) -> Any | Literal[False]:
        try:
            return self.instance_id == other.instance_id
        except AttributeError:
            return False

    @staticmethod
    def exists(func):
        @functools.wraps(wrapped=func)
        async def wrapper_exists(self: Self, *args, **kwargs) -> bool:
            res: Row | None = await self._fetchone(SQL=f"""SELECT instance_id FROM instances WHERE instance_id = ?""", parameters=(self.instance_id,))
            if res is None:
                raise ValueError(f"The `instance_id` of this class doesn't exist in the `instances` table. ID: {self.instance_id}")
            return await func(self, *args, *kwargs)
        return wrapper_exists

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

    @property
    def settings(self) -> Instance_Settings:
        """
        Represents the data from the `instance_settings` table.
        """
        return self._settings

    @property
    def metrics(self) -> Instance_Metrics:
        """
        Represents the data from the `instance_metrics` table.
        """
        return self._metrics

    @property
    def banner(self) -> Instance_Banner:
        """
        Holds the dataclass `Instance_Banner_Settings`.
        """
        return self._banner

    @exists
    async def _remove_instance(self) -> bool | None:
        """
        Remove a `instance_id` from the `instances` table and any tables referencing the `instances_id`.

        Raises:
            ValueError: If the `instance_id` doesn't exist.

        Returns:
            bool | None: Returns `True` if the `instance_id` was removed.
        """
        assert self.instance_id  # this is validated in the `exists` decorator
        try:
            # await self._delete_row_where(table="instances", where="instance_id", value=self.instance_id)
            await self._execute(SQL=f"""DELETE FROM instances WHERE instance_id = ?""", parameters=(self.instance_id,))
        except Exception as e:
            raise ValueError(f"The `instance_id` provided doesn't exists in the Database. instance_id:{self.instance_id}")
        # await self._delete_row_where(table="instance_settings", where="instance_id", value=self.instance_id)
        # await self._delete_row_where(table="instance_buttons", where="instance_id", value=self.instance_id)
        # await self._delete_row_where(table="instance_metrics", where="instance_id", value=self.instance_id)
        self.instance_id = None
        self.instance_name = None
        self.created_at = 0
        return True

    @exists
    async def _get_settings(self) -> Self:
        """
        Get the data from the `instance_settings` table.

        Returns:
            Instance_Settings: Returns an `Instance_Settings` dataclass object.
        """

        res: Row | None = await self._fetchone(SQL=f"""SELECT * FROM instance_settings WHERE instance_id = ?""", parameters=(self.instance_id,))
        if res is None:
            raise ValueError(f"The `instance_id` provided doesn't have an entry in the `instance_settings` table. Instance ID:{self.instance_id}")
        self._settings = Instance_Settings(**res)
        return self

    @exists
    async def _get_metrics(self) -> Self:
        """
        Get the data from the `instance_metrics` table.

        Returns:
            Instance_Metrics: Returns an `Instance_Metrics` dataclass object.
        """

        res: Row | None = await self._fetchone(SQL=f"""SELECT * FROM instance_metrics WHERE instance_id = ?""", parameters=(self.instance_id,))
        if res is None:
            raise ValueError(f"The `instance_id` provided doesn't have an entry in the `instance_metrics` table. Instance ID:{self.instance_id}")
        self._metrics = Instance_Metrics(**res)
        return self

    @exists
    async def _get_banner(self) -> Self:
        banner_settings: Row | None = await self._fetchone(SQL=f"""SELECT image_path, blur_background_amount FROM instance_banner_settings
                                               WHERE instance_id = ?""", parameters=(self.instance_id,))
        if banner_settings is None:
            raise ValueError(f"The `instance_id` provided doesn't have an entry in the `instance_banner_settings` table. Instance ID:{self.instance_id}")

        banner_element_colors: Row | None = await self._fetchone(SQL=f""" SELECT * FROM banner_element_color WHERE instance_id = ?""", parameters=(self.instance_id,))

        if banner_element_colors is None:
            raise ValueError(f"The `instance_id` provided doesn't have an entry in the `banner_element_color` table. Instance ID:{self.instance_id}")

        banner_element_pos: Row | None = await self._fetchone(SQL=f"""SELECT * FROM banner_element_position WHERE instance_id = ?""", parameters=(self.instance_id,))

        if banner_element_pos is None:
            raise ValueError(f"The `instance_id` provided doesn't have an entry in the `banner_element_position` table. Instance ID:{self.instance_id}")

        _temp = Instance_Banner(**{**banner_settings, **banner_element_colors})
        _temp.parse(**banner_element_pos)
        self._banner: Instance_Banner = _temp
        return self

    @exists
    async def set_host(self, host: str) -> str:
        """
        Set the `host` attribute in the `instance_settings` table.

        Args:
            host (str): The host/IP for users to access the instance.

        Returns:
            str: Returns `Instance_Settings.host`.
        """
        await self._execute(SQL=f"""UPDATE instance_settings SET host=? WHERE instance_id=?""", parameters=(host.strip(), self.instance_id))
        self.settings.host = host.strip()
        return self.settings.host

    @exists
    async def set_password(self, password: str) -> str:
        """
        Set the `password` attribute in the `instance_settings` table.

        Args:
            password (str): The password to use to connect to the instance.

        Returns:
            str: Returns `Instance_Settings.password`.
        """
        await self._execute(SQL=f"""UPDATE instance_settings SET password=? WHERE instance_id=?""", parameters=(password.strip(), self.instance_id))
        self.settings.password = password.strip()
        return self.settings.password

    @exists
    async def set_whitelist(self, whitelist: WhitelistType) -> WhitelistType:
        """
        Set the `whitelist` attribute in the `instance_settings` table.

        Args:
            whitelist (WhitelistType): The Whitelist Type.

        Returns:
            WhitelistType: Returns `Instance_Settings.whitelist`.
        """
        await self._execute(SQL=f"""UPDATE instance_settings SET whitelist=? WHERE instance_id=?""", parameters=(whitelist.value, self.instance_id))
        self.settings.whitelist = whitelist
        return self.settings.whitelist

    @exists
    async def set_whitelist_button(self, whitelist_button: bool) -> bool:
        """
        Set the `whitelist_button` attribute in the `instance_settings` table.

        Args:
            whitelist_button (bool): `True or False` if the whitelist button should be seen.

        Returns:
            bool: Returns `Instance_Settings.whitelist_button`.
        """
        await self._execute(SQL=f"""UPDATE instance_settings SET whitelist_button=? WHERE instance_id=?""", parameters=(whitelist_button, self.instance_id))
        self.settings.whitelist_button = whitelist_button
        return self.settings.whitelist_button

    @exists
    async def set_emoji(self, emoji: str) -> str:
        """
        Set the `emoji` attribute in the `instance_settings` table.

        Args:
            emoji (str): The Discord Emoji to use.

        Returns:
            str: Returns `Instance_Settings.emoji`.
        """
        await self._execute(SQL=f"""UPDATE instance_settings SET emoji=? WHERE instance_id=?""", parameters=(emoji, self.instance_id))
        self.settings.emoji = emoji
        return self.settings.emoji

    @exists
    async def set_donator(self, donator: DonatorType) -> DonatorType:
        """
        Set the `donator` attribute in the `instance_settings` table.

        Args:
            donator (DonatorType): The Donator Type.
            pos (tuple[int, int], optional): The position of the banner element. (X, Y)

        Returns:
            DonatorType: Returns `Instance_Settings.donator`.
        """

        await self._execute(SQL=f"""UPDATE instance_settings SET donator=? WHERE instance_id=?""", parameters=(donator.value, self.instance_id))
        self.settings.donator = donator
        return self.settings.donator

    @exists
    async def set_discord_console_channel_id(self, channel_id: int) -> int:
        """
        Sets the `discord_console_channel` attribute in the `instance_settings` table.

        Args:
            channel_id (int): The Discord Channel ID.

        Raises:
            ValueError: If the `channel_id` is to short. (<15)

        Returns:
            int: Returns `Instance_Settings.discord_console_channel`.
        """

        if len(str(object=channel_id)) < 15:
            raise ValueError("The `channel_id` is to short. (<15)")

        await self._execute(SQL=f"""UPDATE instance_settings SET discord_console_channel_id=? WHERE instance_id=?""", parameters=(channel_id, self.instance_id))
        self.settings.discord_console_channel_id = channel_id
        return self.settings.discord_console_channel_id

    @exists
    async def set_discord_role_id(self, role_id: int) -> int:
        """
        Sets the `discord_role_id` attribute in the `instance_settings` table.

        Args:
            role_id (int): The Discord Role ID.

        Raises:
            ValueError: If the `discord_role_id` is to short. (<15)

        Returns:
            int: Returns `Instance_Settings.discord_role_id`.
        """
        if len(str(object=role_id)) < 15:
            raise ValueError("The `discord_role_id` is to short. (<15)")

        await self._execute(SQL=f"""UPDATE instance_settings SET discord_role_id=? WHERE instance_id=?""", parameters=(role_id, self.instance_id))
        self.settings.discord_role_id = role_id
        return self.settings.discord_role_id

    @exists
    async def set_avatar_url(self, avatar_url: str) -> str:
        """
        Sets the `avatar_url` attribute in the `instance_settings` table.

        Args:
            avatar_url (str): The URL of the avatar icon.

        Returns:
            str: Returns `Instance_Settings.avatar_url`.
        """
        await self._execute(SQL=f"""UPDATE instance_settings SET avatar_url=? WHERE instance_id=?""", parameters=(avatar_url.strip(), self.instance_id))
        self.settings.avatar_url = avatar_url.strip()
        return self.settings.avatar_url

    @exists
    async def set_hidden(self, hidden: bool) -> bool:
        """
        Sets the `hidden` attribute in the `instance_settings` table. \n
        This controls if the instance can be seen via slash commands for general users.

        Args:
            hidden (bool): The `hidden` attribute.

        Returns:
            bool: Returns `Instance_Settings.hidden`.
        """
        await self._execute(SQL=f"""UPDATE instance_settings SET hidden=? WHERE instance_id=?""", parameters=(hidden, self.instance_id))
        self.settings.hidden = hidden
        return self.settings.hidden


class DBInstance(Base):
    """
    Controls the interactions with our `instances` table and any reference tables in our DATABASE.

    """

    async def add_instance(self, instance_id: str, instance_name: str) -> Instance | None:
        """
        Add an AMP Instance to the `instances` table.

        Args:
            instance_id (str): The AMP Instance ID.
            instance_name (str): The AMP Instance Name.

        Raises:
            ValueError: If the `instance_id` already exists we raise an exception.

        Returns:
            Instance | None: Returns an `Instance` object if the `instance_id` exists in the Database.
        """
        _instance = None
        res: Row | None = await self._execute(SQL=f"""INSERT INTO instances(instance_id, instance_name, created_at) VALUES(?, ?, ?)
                                              ON CONFLICT(instance_id) DO NOTHING RETURNING *""", parameters=(instance_id, instance_name, datetime.now().timestamp()))
        if res is None:
            raise ValueError(f"The `instance_id` already exists `instances` table. Instance ID:{instance_id}")

        _instance = Instance(**res)
        _settings: Row | None = await self._execute(SQL=f"""INSERT INTO instance_settings(instance_id) VALUES(?)
                                                    ON CONFLICT(instance_id) DO NOTHING RETURNING *""",
                                                    parameters=(instance_id,))
        if _settings is None:
            return _instance

        _metrics: Row | None = await self._execute(SQL=f"""INSERT INTO instance_metrics(instance_id) VALUES(?) ON CONFLICT(instance_id) DO NOTHING RETURNING *""",
                                                   parameters=(instance_id,))
        if _metrics is None:
            return _instance

        _banner_settings: Row | None = await self._execute(SQL=f"""INSERT INTO instance_banner_settings(instance_id) VALUES(?)
                                                           ON CONFLICT(instance_id) DO NOTHING RETURNING *""", parameters=(instance_id,))
        if _banner_settings is None:
            return _instance

        await _instance._get_settings()
        await _instance._get_metrics()
        await _instance._get_banner()
        return _instance

    async def get_instance(self, instance_id: str) -> Instance | None:
        """
       Get a Instance object based on the AMP Instance ID.
       * This will populate the `Instance.settings` and `Instance.metrics` attribute.

        Args:
            instance_id (str): The AMP Instance ID.

        Raises:
            ValueError: If the `instance_id` doesn't exist we raise an exception.

        Returns:
            Instance | None: Returns an `Instance` object if the `instance_id` exists in the Database.
        """
        _exists: Row | None = await self._fetchone(SQL=f"""SELECT * FROM instances WHERE instance_id = ?""", parameters=(instance_id,))
        if _exists is None:
            raise ValueError(f"The `instance_id` provided doesn't exist in the `instances` table. Instance ID:{instance_id}")

        _instance: Instance = await Instance(**_exists)._get_settings()
        await _instance._get_metrics()
        await _instance._get_banner()
        return _instance
