# API class types
from typing import Any, Union, NamedTuple
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


class PostCreate(Enum):
    """
    Represents the state of the API call `ADSModule/DeployTemplate`

    """
    Do_Nothing = 0
    Update_Once = 1
    Update_Always = 2
    Update_and_Start_Once = 3
    Update_and_Start_Always = 4
    Start_Always = 5


@dataclass()
class Login_UserInfo():
    """
    Represents an AMP users information, tied to `LoginResults()`

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
    userInfo: Login_UserInfo | None = None  # second data class


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
    """
    Represents the data from `Metrics()`
    """
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
    """
    Tied to `Updates()`, represents the Instance stats
    """
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
    Represents the data from AMP API call `getUpdates` \n
    """
    ConsoleEntries: list[Console_Entries]
    Status: Status
    Messages: list[Messages]  # No ideal usage at this time.
    Ports: list[Ports] | None = None  # No ideal usage at this time.
    Tasks: list[Tasks] | None = None  # No ideal usage at this time.


@dataclass()
class Instance():
    """
    Represents the data from the AMP API call `getInstance()` or a list of these from `getInstances()`

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
class Controller():
    """
    Represents an AMP Controller (aka Target manager) that manages the Instances it has access to.

    """
    AvailableInstances: list[Instance]
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


@dataclass()
class TriggerTasks():
    """
    Tied to `Triggers()`.

    Hold's information regarding AMP Tasks and their status.

    """
    Id: str
    TaskMethodName: str
    ParameterMapping: dict[str, str]
    EnabledState: int
    Locked: bool
    CreatedBy: str
    Order: int


@dataclass()
class Methods():
    """
    Tied to `ScheduleData().AvailableMethods`.

    Hold's information regarding Methods/Events that are available to the Instance. Varies depending on instance type.
    """
    Id: str = ""
    Name: str = ""
    Description: str = ""
    Consumes: list[dict[str, str]] = field(default_factory=list[dict[str, str]])


@dataclass()
class Triggers():
    """
    Tied to `ScheduleData().AvailableTriggers` and `ScheduleData().PopulatedTriggers`
    """
    EnabledState: int
    Tasks: list[TriggerTasks] = field(default_factory=list[dict[str, str]])
    Id: str = ""
    Type: str = ""
    Description: str = ""
    TriggerType: str = ""
    Emits: list[str] = field(default_factory=list[str])


@dataclass()
class ScheduleData():
    """
    Represents the Data returned from the AMP API call `getScheduleData()`
    """
    AvailableMethods: list[Methods] | None = None
    # AvailableTriggers: list[str] | None = None
    AvailableTriggers: list[Triggers] | None = None
    # PopulatedTriggers: list[str] | None = None
    PopulatedTriggers: list[Triggers] | None = None


@dataclass(init=True)
class Players():
    """
    Represents the Data returned from the AMP API call `getUserlist()`
    The attributes are not 100% accurate. Used Minecraft Module as a test.
    `{'6eb7be5e-3d33-4b40-8aab-7889c243cc1a': 'Anth0kage', 'ac2d31c0-1ae6-400e-9748-df40a4d9c7b2': 'Razgro'}`

    """
    id: str = ""
    name: str = ""

    def __init__(self, data: dict[str, str]):
        for key, value in data.items():
            setattr(self, "id", key)
            setattr(self, "name", value)


@dataclass()
class User():
    """
    Represents the Data returned from the AMP API call `getAllAMPUserInfo()`

    """
    CannotChangePassword: bool
    Disabled: bool
    GravatarHash: str
    ID: str
    IsLDAPUser: bool
    IsSuperUser: bool
    IsTwoFactorEnabled: bool
    MustChangePassword: bool
    Name: str
    PasswordExpires: bool
    Permissions: list[str]
    Roles: list[str]
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
class Node():
    """
    Represents the data returns from the AMP API call `getConfig()` or `getConfigs()`

    """
    Actions: list[str]
    AlwaysAllowRead: bool
    Category: str
    CurrentValue: str
    Description: str
    EnumValuesAreDeferred: bool
    InputType: str
    IsProvisionSpec: bool
    Keywords: str
    MaxLength: int
    Name: str
    Node: str
    Placeholder: str
    ReadOnly: bool
    ReadOnlyProvision: bool
    RequiresRestart: bool
    Suffix: str
    Tag: str
    ValType: str


@dataclass()
class Role():
    """
    Represents the data returns from the AMP API call `getRole()`

    """
    ID: str
    IsDefault: bool
    Name: str
    Description: str
    Hidden: bool
    Permissions: list[str]
    Members: list[str]
    IsInstanceSpecific: bool
    IsCommonRole: bool
    DisableEdits: bool


@dataclass()
class FileChunk():
    """
    Repesents the data returns from AMP API call `getFileChunk()`
    """
    Base64Data: str
    BytesLength: int


@dataclass()
class Directory():
    """
    Repesents the data returns from AMP API call `getDirectoryListing()`
    """
    IsDirectory: bool
    IsVirtualDirectory: bool
    Filename: str
    SizeBytes: int
    IsDownloadable: bool
    IsEditable: bool
    IsArchive: bool
    IsExcludedFromBackups: bool
    Created: str
    Modified: str

    @property
    def Created(self) -> datetime:
        """
        Converts our Created attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        return datetime.fromtimestamp(int(self._Created[6:-2]) / 1000)

    @Created.setter
    def Created(self, value: str) -> None:
        self._Created = value

    @property
    def Modified(self) -> datetime:
        """
        Converts our Modified attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        return datetime.fromtimestamp(int(self._Modified[6:-2]) / 1000)

    @Modified.setter
    def Modified(self, value: str) -> None:
        self._Modified = value


@dataclass()
class Session():
    """
    Represents the data returns from the AMP API call `getActiveAMPSessions()`

    """
    Source: str
    SessionID: str
    Username: str
    SessionType: str
    StartTime: str
    LastActivity: str

    @property
    def StartTime(self) -> datetime:
        """
        Converts our StartTime attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        return datetime.fromtimestamp(int(self._StartTime[6:-2]) / 1000)

    @StartTime.setter
    def StartTime(self, value: str) -> None:
        self._StartTime = value

    @property
    def LastActivity(self) -> datetime:
        """
        Converts our LastActivity attribute into a Datetime Object.

        Returns:
            datetime: Returns a `Non-Timezone` aware object. Will use OS/machines timezone information.
        """
        return datetime.fromtimestamp(int(self._LastActivity[6:-2]) / 1000)

    @LastActivity.setter
    def LastActivity(self, value: str) -> None:
        self._LastActivity = value
