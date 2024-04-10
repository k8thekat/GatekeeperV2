from dataclasses import dataclass
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


@dataclass
class BannerSettings():
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


@dataclass()
class ServerSettings():
    """
    Represents the data from the Database table servers.

    **THIS MUST BE UPDATED TO REPRESENT THE servers DATABASE SCHEMA AT ALL TIMES** \n
    - The dataclass is used to validate column names and column type constraints.

    """
    id: int
    instance_id: str
    instance_name: str
    ip: str = ""
    whitelist: bool = False
    whitelist_disabled: bool = False
    donator: bool = False
    chat_channel: int = 0
    chat_prefix: str = ""
    event_channel: int = 0
    role: int = 0
    avatar_url: str = ""
    hidden: bool = False

    def __setattr__(self, name: str, value: Union[str, int, bool]) -> Any:
        """
        We are overwriting setattr because SQLite returns 0 or 1 for True/False. \n
        Convert it to a `bool` for human readable.

        """
        if hasattr(ServerSettings, name) and (type(getattr(ServerSettings, name)) == bool):
            return super().__setattr__(name, bool(value))
        return super().__setattr__(name, value)
