from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Union


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


class ButtonStyle(Enum):
    """
    Represents `discord.ButtonStyle` 2.0 values.
    """
    primary = 0
    secondary = 1
    success = 2
    danger = 3
    link = 4


class ButtonStyle_Old(Enum):
    """
    Represents `discord.ButtonStyle` old values.
    """
    blurple: ButtonStyle = ButtonStyle.primary
    grey: ButtonStyle = ButtonStyle.secondary
    green: ButtonStyle = ButtonStyle.success
    red: ButtonStyle = ButtonStyle.danger
    link: ButtonStyle = ButtonStyle.link


@dataclass
class Instance_Banner_Settings():
    """
    Represents the data from the Database table banners.
    """
    instance_id: str
    image_path: str = "./resources/banners/AMP_Banner.jpg"
    blur_background_amount: int = 0
    color_header: str = "#85c1e9"
    color_body: str = "#f2f3f4"
    color_host: str = "#5dade2"
    color_whitelist_open: str = "#f7dc6f"
    color_whitelist_closed: str = "#cb4335"
    color_donator: str = "#212f3c"
    color_status_online: str = "#28b463"
    color_status_offline: str = "#e74c3c"
    color_player_limit_min: str = "#ba4a00"
    color_player_limit_max: str = "#5dade2"
    color_player_online: str = "#f7dc6f"


@dataclass
class Instance_Button():
    """
    Represent's the data `instance_buttons` table.
    """
    instance_id: str = ""
    button_name: str = ""
    button_url: str = ""
    button_style: ButtonStyle = ButtonStyle.primary


@dataclass
class Instance_Settings():
    """
    Represents the data from the `Instances` table.

    **THIS MUST BE UPDATED TO REPRESENT THE Instance DATABASE SCHEMA AT ALL TIMES** \n
    - The dataclass is used to validate column names and column type constraints.

    """
    instance_id: str = ""
    host: str = ""  # could get the local IP from the API
    password: str = ""
    whitelist: WhitelistType = WhitelistType.OPEN
    whitelist_button: bool = False
    donator: DonatorType = DonatorType.PUBLIC
    discord_console_channel_id: int = field(default=0)
    discord_role_id: int = field(default=0)
    avatar_url: str = ""
    hidden: bool = False

    def __setattr__(self, name: str, value: Union[str, int, bool]) -> Any:
        """
        We are overwriting setattr because SQLite returns 0 or 1 for True/False. \n
        Convert it to a `bool` for human readable.

        """
        if hasattr(Instance_Settings, name) and (type(getattr(Instance_Settings, name)) == bool):
            return super().__setattr__(name, bool(value))
        return super().__setattr__(name, value)


@dataclass
class Settings():
    """
    Represents the data from the `settings` table.
    """
    guild_id: int = 0  # references `guilds` table `id` value.
    mod_role_id: int | None = None
    donator_role_id: int | None = None
    msg_timeout: int | None = None


@dataclass
class Owner():
    """
    Represents the data from the Database table `owners`.
    """
    guild_id: int
    user_id: int
