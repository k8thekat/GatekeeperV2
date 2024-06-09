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
    DonatorType _summary_
    """
    PUBLIC = 0
    PRIVATE = 1


@dataclass
class InstanceBannerSettings():
    """
    Represents the data from the Database table banners.
    """
    server_id: int
    background_path: str = "./resources/banners/AMP_Banner.jpg"
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
class InstanceButton():
    instance_id: str
    button_name: str
    button_url: str
    button_style: int


@dataclass
class InstanceSettings():
    """
    Represents the data from the Database table servers.

    **THIS MUST BE UPDATED TO REPRESENT THE servers DATABASE SCHEMA AT ALL TIMES** \n
    - The dataclass is used to validate column names and column type constraints.

    """
    instance_id: str
    instance_name: str
    host: str = ""  # could get the local IP from the API
    password: str | None = None
    whitelist: WhitelistType = WhitelistType.OPEN
    donator: DonatorType = DonatorType.PUBLIC
    discord_console_channel: int = field(default=0)
    discord_role_id: int = field(default=0)
    avatar_url: str = ""
    hidden: bool = False

    def __setattr__(self, name: str, value: Union[str, int, bool]) -> Any:
        """
        We are overwriting setattr because SQLite returns 0 or 1 for True/False. \n
        Convert it to a `bool` for human readable.

        """
        if hasattr(InstanceSettings, name) and (type(getattr(InstanceSettings, name)) == bool):
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
