
import functools
from dataclasses import InitVar, dataclass
from datetime import datetime
from sqlite3 import Row
from typing import Any, Literal, Self

from utils import asqlite

from .base import Base
from .types import (DonatorType, Instance_Banner_Settings, Instance_Button,
                    Instance_Settings, WhitelistType)

INSTANCES_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS instances (
    instance_id TEXT NOT NULL UNIQUE,
    instance_name TEXT NOT NULL,
    created_at REAL
)STRICT"""

# TODO - Add support for emoji reactions
INSTANCE_SETTINGS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS instance_settings (
    instance_id TEXT NOT NULL,
    host TEXT DEFAULT 'localhost',
    password TEXT DEFAULT '',
    whitelist INTEGER DEFAULT 0,
    whitelist_button INTEGER DEFAULT 0,
    donator INTEGER DEFAULT 0,
    discord_console_channel_id INTEGER DEFAULT 0,
    discord_role_id INTEGER DEFAULT 0,
    avatar_url TEXT DEFAULT '',
    hidden INTEGER DEFAULT 0,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id)
    UNIQUE(instance_id)
)STRICT"""

INSTANCE_BUTTONS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS instance_buttons (
    instance_id TEXT NOT NULL,
    button_name TEXT NOT NULL,
    button_url TEXT NOT NULL,
    button_style INTEGER NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id)
    UNIQUE(instance_id)
)STRICT"""

INSTANCES_METRICS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS instance_metrics (
    instance_id TEXT NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id)
    UNIQUE(instance_id)
)STRICT"""

INSTANCE_BANNER_SETTINGS_SETUP_SQL = """
CREATE TABLE IF NOT EXISTS instance_banner_settings (
    instance_id INTEGER NOT NULL,
    image_path TEXT,
    blur_background_amount INTEGER DEFAULT 0,
    color_instance_name TEXT DEFAULT #85c1e9,
    color_instance_description TEXT DEFAULT #f2f3f4,
    color_instance_host TEXT DEFAULT #5dade2,
    color_instance_password TEXT DEFAULT #5dade2,
    color_whitelist_open TEXT DEFAULT #f7dc6f,
    color_whitelist_closed TEXT DEFAULT #cb4335,
    color_donator TEXT DEFAULT #212f3c,
    color_status_online TEXT DEFAULT #28b463,
    color_status_offline TEXT DEFAULT #e74c3c,
    color_instance_metrics TEXT DEFAULT #f2f3f4,
    color_unique_visitors TEXT DEFAULT #f2f3f4,
    color_player_limit_min TEXT DEFAULT #ba4a00,
    color_player_limit_max TEXT DEFAULT #5dade2,
    color_players_online TEXT DEFAULT #f7dc6f,
    FOREIGN KEY(instance_id) REFERENCES instances(instance_id)
)STRICT"""


@dataclass
class Instance_Metrics(Base):
    # TODO - Define __hash__ and __eq__ to compare objects via sets.
    """
    Represents the data from the `instance_metrics` table.

    """
    instance_id: str
    _pool: InitVar[asqlite.Pool | None] = None


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
        async def wrapper_exists(self: Instance, *args, **kwargs) -> bool:
            res: Row | None = await self._fetchone(f"""SELECT instance_id FROM instances WHERE instance_id = ?""", (self.instance_id,))
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
        return self._settings

    @property
    def metrics(self) -> Instance_Metrics:
        return self._metrics

    @property
    def banner(self) -> Instance_Banner_Settings:
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
            await self._delete_row_where(table="instances", where="instance_id", value=self.instance_id)
        except Exception as e:
            raise ValueError(f"The `instance_id` provided doesn't exists in the Database. instance_id:{self.instance_id}")
        await self._delete_row_where(table="instance_settings", where="instance_id", value=self.instance_id)
        await self._delete_row_where(table="instance_buttons", where="instance_id", value=self.instance_id)
        await self._delete_row_where(table="instance_metrics", where="instance_id", value=self.instance_id)
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

        res: Row | None = await self._fetchone(f"""SELECT * FROM instance_settings WHERE instance_id = ?""", (self.instance_id,))
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

        res: Row | None = await self._fetchone(f"""SELECT * FROM instance_metrics WHERE instance_id = ?""", (self.instance_id,))
        if res is None:
            raise ValueError(f"The `instance_id` provided doesn't have an entry in the `instance_metrics` table. Instance ID:{self.instance_id}")
        self._metrics = Instance_Metrics(**res)
        return self

    @exists
    async def _get_banner(self) -> Self:
        res: Row | None = await self._fetchone(f"""SELECT * FROM instance_banner_settings WHERE instance_id = ?""", (self.instance_id,))
        if res is None:
            raise ValueError(f"The `instance_id` provided doesn't have an entry in the `instance_banner_settings` table. Instance ID:{self.instance_id}")
        self._banner = Instance_Banner_Settings(**res)
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
        await self._execute(f"""UPDATE instance_settings SET host=? WHERE instance_id=?""", (host.strip(), self.instance_id))
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
        await self._execute(f"""UPDATE instance_settings SET password=? WHERE instance_id=?""", (password.strip(), self.instance_id))
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
        await self._execute(f"""UPDATE instance_settings SET whitelist=? WHERE instance_id=?""", (whitelist.value, self.instance_id))
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
        await self._execute(f"""UPDATE instance_settings SET whitelist_button=? WHERE instance_id=?""", (whitelist_button, self.instance_id))
        self.settings.whitelist_button = whitelist_button
        return self.settings.whitelist_button

    @exists
    async def set_donator(self, donator: DonatorType) -> DonatorType:
        """
        Set the `donator` attribute in the `instance_settings` table.

        Args:
            donator (DonatorType): The Donator Type.

        Returns:
            DonatorType: Returns `Instance_Settings.donator`.
        """
        await self._execute(f"""UPDATE instance_settings SET donator=? WHERE instance_id=?""", (donator.value, self.instance_id))
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

        await self._execute(f"""UPDATE instance_settings SET discord_console_channel_id=? WHERE instance_id=?""", (channel_id, self.instance_id))
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

        await self._execute(f"""UPDATE instance_settings SET discord_role_id=? WHERE instance_id=?""", (role_id, self.instance_id))
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
        await self._execute(f"""UPDATE instance_settings SET avatar_url=? WHERE instance_id=?""", (avatar_url.strip(), self.instance_id))
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
        await self._execute(f"""UPDATE instance_settings SET hidden=? WHERE instance_id=?""", (hidden, self.instance_id))
        self.settings.hidden = hidden
        return self.settings.hidden


class DBInstance(Base):
    async def _initialize_tables(self) -> None:
        """
        Creates the `DBInstance` tables.

        """
        tables: list[str] = [INSTANCES_SETUP_SQL, INSTANCE_SETTINGS_SETUP_SQL, INSTANCE_BUTTONS_SETUP_SQL, INSTANCES_METRICS_SETUP_SQL, INSTANCE_BANNER_SETTINGS_SETUP_SQL]
        await self._create_tables(schema=tables)

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
        res: Row | None = await self._execute(f"""INSERT INTO instances(instance_id, instance_name, created_at) VALUES(?, ?, ?) ON CONFLICT(instance_id) DO NOTHING RETURNING *""", (instance_id, instance_name, datetime.now().timestamp()))
        if res is None:
            raise ValueError(f"The `instance_id` already exists `instances` table. Instance ID:{instance_id}")

        _instance = Instance(**res)
        _settings: Row | None = await self._execute(f"""INSERT INTO instance_settings(instance_id) VALUES(?) ON CONFLICT(instance_id) DO NOTHING RETURNING *""", (instance_id,))
        if _settings is None:
            return _instance

        _metrics: Row | None = await self._execute(f"""INSERT INTO instance_metrics(instance_id) VALUES(?) ON CONFLICT(instance_id) DO NOTHING RETURNING *""", (instance_id,))
        if _metrics is None:
            return _instance

        _banner_settings: Row | None = await self._execute(f"""INSERT INTO instance_banner_settings(instance_id) VALUES(?) ON CONFLICT(instance_id) DO NOTHING RETURNING *""", (instance_id,))
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
        _exists: Row | None = await self._fetchone(f"""SELECT * FROM instances WHERE instance_id = ?""", (instance_id,))
        if _exists is None:
            raise ValueError(f"The `instance_id` provided doesn't exist in the `instances` table. Instance ID:{instance_id}")

        _instance: Instance = await Instance(**_exists)._get_settings()
        await _instance._get_metrics()
        return _instance
