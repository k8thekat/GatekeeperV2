# API class types
from typing import Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class State_enum(Enum):
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
    IsTwoFactorEnabled: bool
    Disabled: bool
    GravatarHash: str
    IsLDAPUser: bool
    EmailAddress: str = ""
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
    success: bool
    result: int
    permissions: list[str] = field(default_factory=list)
    resultReason: str = ""
    sessionID: str = ""
    rememberMeToken: str = ""
    userInfo: UserInfo | None = None  # second data class


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
        """
        Convert's the AMP version from a string into a dataclass to access each value independantly. 

        Args:
            data (str): AMP version as a string
        """
        data = data.strip(".")
        self.Major = int(data[0])
        self.Minor = int(data[1])
        self.Revision = int(data[2])
        self.MinorRevision = int(data[3])


@dataclass()
class AMPVersion():
    """
    Represents the AMP Version from `getInstance["AMPVersion"]`
    """
    Build: int
    Major: int
    MajorRevision: int
    Minor: int
    MinorRevision: int
    Revision: int


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


@dataclass()
class Metrics_Data():
    RawValue: int
    MaxValue: int
    Percent: int
    Units: str
    Color: None | str = None
    Color2: None | str = None
    Color3: None | str = None


@dataclass()
class Metrics():
    """
    The Metrics dataclass for Updates_Status().Metrics, houses all the Metrics information.
    """
    Active_Users: Metrics_Data
    CPU_Usage: Metrics_Data
    Memory_Usage: Metrics_Data


@dataclass()
class Status():
    State: State_enum
    Uptime: str
    Metrics: Metrics


@dataclass()
class Console_Entries():
    """
    Represents an individual entry in the related AMP Instances Console. Tied to `Updates().Console_Entries`

    """
    Contents: str
    Source: str
    Type: str
    Timestamp: str

    @property
    def Timestamp(self) -> datetime:
        """
        Converts our Timestamp attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        return datetime.fromtimestamp(int(self._Timestamp[6:-2]) / 1000)

    @Timestamp.setter
    def Timestamp(self, value: str) -> None:
        self._Timestamp = value


@dataclass()
class Ports():
    """
    Current Ports of the related AMP Instance. Tied to `Updates().Ports`
    """
    Listening: bool
    Name: str
    Port: int
    Protocol: int


@dataclass()
class Messages():
    """
    Represents a Message from the dataclass `Updates().Messages`\n
    *Not sure what generates these inside AMP or where to find them.*
    """
    AgeMinutes: int
    Expired: bool
    Id: str
    Message: str
    Source: str


@dataclass()
class Tasks():
    """
    Represents a Task that is being run on an Instance. Tied to dataclass `Updates().Tasks`
    """
    IsPrimaryTask: bool
    StartTime: str
    Id: str
    Name: str
    Description: str
    HideFromUI: bool
    FastDismiss: bool
    LastUpdatePushed: str
    ProgressPercent: float
    IsCancellable: bool
    Origin: str
    IsIndeterminate: bool
    State: int
    Status: str


@dataclass()
class Updates():
    """
    Represents AMP API call `getUpdates` \n
    """
    ConsoleEntries: list[Console_Entries]
    Status: Status
    Messages: list[Messages]  # No ideal usage at this time.
    Ports: list[Ports]  # No ideal usage at this time.
    Tasks: list[Tasks]  # No ideal usage at this time.


@dataclass()
class AMP_Instance():
    """
    Represents the data from AMP API call `getInstance` or `getInstances`
    """
    AppState: State_enum
    ApplicationEndpoints: list[dict[str, str]]  # [{'DisplayName': 'Application ' \n 'Address', 'Endpoint': '0.0.0.0:7785', 'Uri': 'steam://connect/0.0.0.0:7785'}, {'DisplayName': 'SFTP '\n'Server','Endpoint': '0.0.0.0:2240','Uri': 'steam://connect/0.0.0.0:2240'}
    ContainerCPUs: float  # 0.0
    ContainerMemoryMB: int  # 0
    ContainerMemoryPolicy: int  # 0
    Daemon: bool  # False
    DaemonAutostart: bool  # True
    DeploymentArgs: dict[str, str]  # {'FileManagerPlugin.SFTP.SFTPIPBinding': '0.0.0.0','FileManagerPlugin.SFTP.SFTPPortNumber': '2240','GenericModule.App.ApplicationIPBinding': '0.0.0.0','GenericModule.App.ApplicationPort1': '7785','GenericModule.App.ApplicationPort2': '0','GenericModule.App.ApplicationPort3': '0','GenericModule.App.RemoteAdminPort': '0','GenericModule.Meta.Author': 'JasperFirecai2, EnderWolf, '                             'IceOfWraith','GenericModule.Meta.ConfigManifest': 'terrariaconfig.json','GenericModule.Meta.ConfigRoot': 'terraria.kvp','GenericModule.Meta.Description': 'Terraria generic module '\n'with support for '\n'various options.','GenericModule.Meta.DisplayImageSource': 'steam:105600','GenericModule.Meta.DisplayName': 'Terraria','GenericModule.Meta.EndpointURIFormat': 'steam://connect/{0}','GenericModule.Meta.MetaConfigManifest': 'terrariametaconfig.json','GenericModule.Meta.MinAMPVersion': '','GenericModule.Meta.OS': '3','GenericModule.Meta.OriginalSource': 'CubeCoders-AMPTemplates','GenericModule.Meta.URL': 'https://store.steampowered.com/app/105600/Terraria/'},
    DiskUsageMB: int  # 0
    ExcludeFromFirewall: bool  # False,
    FriendlyName: str  # 'VM Terraria',
    IP: str  # '127.0.0.1',
    # InstalledVersion: dict[str, int]  # {'Build': 2,'Major': 2,'MajorRevision': 0,'Minor': 4,'MinorRevision': 0,'Revision': 0}
    InstanceID: str  # '89518e00-3c00-4d6d-93d3-f1faa1541788'
    InstanceName: str  # 'VMTerraria01'
    IsContainerInstance: bool  # False
    IsHTTPS: bool  # False,
    ManagementMode: int  # 10
    Module: str  # 'GenericModule'
    Port: str  # 8097
    ReleaseStream: int  # 10
    Running: bool  # True
    Suspended: bool  # False
    TargetID: str  # '47d31130-25ed-47d3-af50-c0ebd947830d'
    Tags: None | list = None
    AMPVersion: AMPVersion = None
    SpecificDockerImage: str = ""
    ModuleDisplayName: str = ""  # 'Terraria'
    Metrics: Metrics = None
    DisplayImageSource: str = ""  # steam:105600
    Description: str = ""


@dataclass()
class AMP_Controller():
    AvailableInstances: list[AMP_Instance]
    State: State_enum
    AvailableIPs: list[str]
    CanCreate: bool
    CreatesInContainers: bool
    Datastores: list[dict[str, str | int]]
    Description: str
    Disabled: bool
    FriendlyName: str
    Id: int
    InstanceId: str
    IsRemote: bool
    Tags: list[str]
    Platform: dict[str, int | str | bool | AMPVersion | dict[str, int | str]]
    Fitness: dict[str, bool | float | int] = None
    LastUpdated: str

    @property
    def LastUpdated(self) -> datetime:
        """
        Converts our LastUpdated attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        return datetime.fromtimestamp(int(self._LastUpdated[6:-2]) / 1000)

    @LastUpdated.setter
    def LastUpdated(self, value: str) -> None:
        self._LastUpdated = value
