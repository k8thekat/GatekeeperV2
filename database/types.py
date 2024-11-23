from dataclasses import InitVar, dataclass, field
from enum import Enum
from sqlite3 import Row
from typing import Any, Self, Union


class ServerTypes(Enum):
    """
    Server Types
    """
    GENERAL = 0
    MINECRAFT = 1
    ARK = 2
    SOURCE_VALVE = 3


class WhitelistType(Enum):
    """
    Whitelist Types; related to `instance_settings` table.

    """
    OPEN = 0
    CLOSED = 1
    DISABLED = 2


class DonatorType(Enum):
    """
    Donator Types; related to `instance_settings` table.
    """
    PUBLIC = 0
    PRIVATE = 1


class BannerType(Enum):
    """
    Banner Image Types; related to `instance_banner_settings` table.
    """
    EMBED = 0
    IMAGES = 1


class ButtonStyle(Enum):
    """
    Represents `discord.ButtonStyle` 2.0 values.
    """
    primary = 0
    secondary = 1
    success = 2
    danger = 3
    link = 4


class ButtonStyle_Old():
    """
    Represents `discord.ButtonStyle` old values.
    """
    blurple: ButtonStyle = ButtonStyle.primary
    grey: ButtonStyle = ButtonStyle.secondary
    green: ButtonStyle = ButtonStyle.success
    red: ButtonStyle = ButtonStyle.danger
    link: ButtonStyle = ButtonStyle.link


class Banner_Element():
    """
    Holds the data from the `banner_element_color` and `banner_element_position` table.\n

    * Holds the x, y values and color for an element in the Instance_Banner_Settings.
    """
    x: int
    y: int
    color: str
    _limit = 52429070  # X= 800, Y = 600

    def __init__(self, value: int = 0, color: str = "#FFFFFF") -> None:
        self.x = value >> 16
        self.y = value & 0xFFFF
        self.color = color

    def pack(self) -> int:
        """
        Pack our X and Y values into a 32-bit integer.

        Returns:
            int: A 32-bit integer with the x and y values packed together.
        """
        res: int = (self.x << 16) | self.y
        if self._limit < res:
            raise Exception(f"Banner cords out of bounds: 32-bit int: {res} | Limit: {self._limit}")
        return res

    def _set_cords(self, value: int) -> None:
        self.x = value >> 16
        self.y = value & 0xFFFF

    def _set_color(self, value: str) -> None:
        self.color = value

    @ staticmethod
    def _pack(x: int, y: int) -> int:
        """
        Pack the provided X and Y values into a 32-bit integer.

        Args:
            x (int): int to pack
            y (int): int to pack

        Returns:
            int: A 32-bit integer with the x and y values packed together.
        """
        return (x << 16) | y


@ dataclass
class Instance_Banner_Settings():
    """
    Represent's the data associated with the `instance_banner_settings`, 
    `banner_element_color` and `banner_element_position` table.
    """
    instance_id: str
    image_path: str = "./resources/banners/AMP_Banner.jpg"
    blur_background_amount: int = 0
    name: Banner_Element = field(default_factory=Banner_Element)
    description: Banner_Element = field(default_factory=Banner_Element)
    host: Banner_Element = field(default_factory=Banner_Element)
    password: Banner_Element = field(default_factory=Banner_Element)
    whitelist_open: Banner_Element = field(default_factory=Banner_Element)
    whitelist_closed: Banner_Element = field(default_factory=Banner_Element)
    donator: Banner_Element = field(default_factory=Banner_Element)
    status_online: Banner_Element = field(default_factory=Banner_Element)
    status_offline: Banner_Element = field(default_factory=Banner_Element)
    status_other: Banner_Element = field(default_factory=Banner_Element)
    metrics: Banner_Element = field(default_factory=Banner_Element)
    unique_visitors: Banner_Element = field(default_factory=Banner_Element)
    player_limit_min: Banner_Element = field(default_factory=Banner_Element)
    player_limit_max: Banner_Element = field(default_factory=Banner_Element)
    players_online: Banner_Element = field(default_factory=Banner_Element)

    @property
    def exclude_properties(self) -> list[str]:
        return ["pool", "_pool", "_limit", "instance_id", "image_path", "blur_background_amount"]

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.exclude_properties:
            return super().__setattr__(name, value)
        try:
            cur: Any = getattr(self, name)
        except AttributeError:
            cur = None

        # Make sure we don't already have a Banner_Element dataclass as our attribute
        # if we do; update the attribute with the cords as an int value is going to be our X,Y
        if isinstance(cur, Banner_Element):
            # If we have an int value we need to convert it into cords and set it.
            if isinstance(value, int):
                return cur._set_cords(value=value)
            elif isinstance(value, str):
                return cur._set_color(value=value)
            else:
                raise ValueError(f"Invalid value expected `int` or `str`. Value: {type(value)}{value}")
        else:
            if isinstance(value, str):
                return super().__setattr__(name, Banner_Element(color=value))
            elif isinstance(value, int):
                return super().__setattr__(name, Banner_Element(value=value))
        pass

    def parse(self, data: Row) -> Self:
        _temp: list[str] = data.keys()
        for key in _temp:
            setattr(self, key, data[key])
        return self


@ dataclass
class Instance_Button():
    """
Represent's the data `instance_buttons` table.
"""
    instance_id: str = ""
    button_name: str = ""
    button_url: str = ""
    button_style: ButtonStyle = ButtonStyle.primary


@ dataclass
class Instance_Settings():
    """
    Represents the data from the `instances` table.

    **THIS MUST BE UPDATED TO REPRESENT THE Instance DATABASE SCHEMA AT ALL TIMES** \n
    - The dataclass is used to validate column names and column type constraints.

    """
    instance_id: str
    description: bool
    host: str   # could get the local IP from the API
    password: str
    whitelist: WhitelistType
    whitelist_button: bool
    emoji: str
    donator: DonatorType
    donator_bypass: bool
    metrics: bool
    status: bool
    unique_visitors: bool
    discord_console_channel_id: int
    discord_role_id: int
    avatar_url: str
    hidden: bool

    def __setattr__(self, name: str, value: Union[str, int, bool]) -> Any:
        """
        We are overwriting setattr because SQLite returns 0 or 1 for True/False. \n
        Convert it to a `bool` for human readable.

        """
        if hasattr(Instance_Settings, name) and (type(getattr(Instance_Settings, name)) == bool):
            return super().__setattr__(name, bool(value))
        return super().__setattr__(name, value)
