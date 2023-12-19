# API class types
from typing import Self, Any, overload
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class State(Enum):
    """
    Represents the state of an instance

    Author: p0t4t0sandwich -> https://github.com/p0t4t0sandwich/ampapi-py/blob/main/ampapi/types.py
    """
    Undefined = -1
    Stopped = 0
    PreStart = 5
    Configuring = 7  # The server is performing some first-time-start configuration.
    Starting = 10
    Ready = 20
    Restarting = 30  # Server is in the middle of stopping, but once shutdown has finished it will automatically restart.
    Stopping = 40
    PreparingForSleep = 45
    Sleeping = 50  # The application should be able to be resumed quickly if using this state. Otherwise use Stopped.
    Waiting = 60  # The application is waiting for some external service/application to respond/become available.
    Installing = 70
    Updating = 75
    AwaitingUserInput = 80  # Used during installation, means that some user input is required to complete setup (authentication etc).
    Failed = 100
    Suspended = 200
    Maintainence = 250
    Indeterminate = 999  # The state is unknown, or doesn't apply (for modules that don't start an external process)


@dataclass()
class UserInfo():
    """
    Represents an AMP users information.

    """
    ID: str
    Username: str
    EmailAddress: str
    IsTwoFactorEnabled: bool
    Disabled: bool
    GravatarHash: str
    IsLDAPUser: bool
    LastLogin: str

    @property
    def LastLogin(self) -> datetime:
        """
        Converts our LastLogin attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        return datetime.fromtimestamp(int(self._LastLogin[6:-2]) / 1000)

    @LastLogin.setter
    def LastLogin(self, value: str) -> None:
        self._LastLogin = value


@dataclass()
class LoginResults():
    """
    Represents an AMP Login response.

    """
    resultReason: str
    success: bool
    permissions: list[str]
    sessionID: str
    rememberMeToken: str
    result: int
    userInfo: UserInfo  # second data class


@dataclass(init=True)
class AMP_Version():
    """
    Conversion class for `UpdateInfo.Build`

    """
    Major: int
    Minor: int
    Revision: int
    MinorRevision: int

    def __init__(self, data: str) -> None:
        data = data.strip(".")
        self.Major = int(data[0])
        self.Minor = int(data[1])
        self.Revision = int(data[2])
        self.MinorRevision = int(data[3])


@dataclass()
class UpdateInfo():
    """
    Represents AMP API call `Core/GetUpdateInfo`

    """
    UpdateAvailable: bool
    Version: str
    ReleaseNotesURL: str
    ToolsVersion: str
    PatchOnly: bool
    Build: AMP_Version

    @property
    def Build(self) -> AMP_Version:
        """
        Converters our Build str into a data class we can use better.

        Returns:
            AMP_Version: Returns an `AMP_Version` data class
        """
        return AMP_Version(data=self._Build)

    @Build.setter
    def Build(self, value: str) -> None:
        self._Build = value
