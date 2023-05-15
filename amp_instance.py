'''
   Copyright (C) 2021-2022 Katelynn Cadwallader.

   This file is part of Gatekeeper, the AMP Minecraft Discord Bot.

   Gatekeeper is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3, or (at your option)
   any later version.

   Gatekeeper is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
   or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
   License for more details.

   You should have received a copy of the GNU General Public License
   along with Gatekeeper; see the file COPYING.  If not, write to the Free
   Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
   02110-1301, USA. 
'''
# AMP API
# by k8thekat // Lightning
# 11/10/2021

import attr
import time
import traceback
from typing import NamedTuple, Union, Any
import sys
import threading

from DB import DBHandler, Database, DBConfig, DBServer
from amp_api import AMP_API
from amp_permissions import check_SessionPermissions, check_GatekeeperRole_Permissions


class Metrics(NamedTuple):
    raw_value: int = 0
    percent: int = 0
    max_value: int = 1
    units: str = ""


class AMP_Instance(AMP_API):
    # base Instance vars
    AppState: int  # 0
    ApplicationEndpoints: list[dict[str, str]]  # [{'DisplayName': 'Application ' \n 'Address', 'Endpoint': '0.0.0.0:7785', 'Uri': 'steam://connect/0.0.0.0:7785'}, {'DisplayName': 'SFTP '\n'Server','Endpoint': '0.0.0.0:2240','Uri': 'steam://connect/0.0.0.0:2240'}
    ContainerCPUs: float  # 0.0
    ContainerMemoryMB: str  # 0
    ContainerMemoryPolicy: Any  # 0
    Daemon: bool  # False
    DaemonAutostart: bool  # True
    DeploymentArgs: dict[str, str]  # {'FileManagerPlugin.SFTP.SFTPIPBinding': '0.0.0.0','FileManagerPlugin.SFTP.SFTPPortNumber': '2240','GenericModule.App.ApplicationIPBinding': '0.0.0.0','GenericModule.App.ApplicationPort1': '7785','GenericModule.App.ApplicationPort2': '0','GenericModule.App.ApplicationPort3': '0','GenericModule.App.RemoteAdminPort': '0','GenericModule.Meta.Author': 'JasperFirecai2, EnderWolf, '                             'IceOfWraith','GenericModule.Meta.ConfigManifest': 'terrariaconfig.json','GenericModule.Meta.ConfigRoot': 'terraria.kvp','GenericModule.Meta.Description': 'Terraria generic module '\n'with support for '\n'various options.','GenericModule.Meta.DisplayImageSource': 'steam:105600','GenericModule.Meta.DisplayName': 'Terraria','GenericModule.Meta.EndpointURIFormat': 'steam://connect/{0}','GenericModule.Meta.MetaConfigManifest': 'terrariametaconfig.json','GenericModule.Meta.MinAMPVersion': '','GenericModule.Meta.OS': '3','GenericModule.Meta.OriginalSource': 'CubeCoders-AMPTemplates','GenericModule.Meta.URL': 'https://store.steampowered.com/app/105600/Terraria/'},
    Description: str
    DiskUsageMB: str  # 0
    DisplayImageSource: str  # steam:105600
    ExcludeFromFirewall: bool  # False,
    FriendlyName: str  # 'VM Terraria',
    IP: str  # '127.0.0.1',
    InstalledVersion: dict[str, int]  # {'Build': 2,'Major': 2,'MajorRevision': 0,'Minor': 4,'MinorRevision': 0,'Revision': 0}
    InstanceID: str  # '89518e00-3c00-4d6d-93d3-f1faa1541788'
    InstanceName: str  # 'VMTerraria01'
    IsContainerInstance: bool  # False
    IsHTTPS: bool  # False,
    ManagementMode: int  # 10
    Metrics: dict[dict[str, str]]  # {'Active Users': {'Color': '#7B249E','Color3': '#FFF','MaxValue': 8,'Percent': 0,'RawValue': 0,'Units': ''},'CPU Usage': {'Color': '#A8221A','Color2': '#A8221A','Color3': '#FFF','MaxValue': 100,'Percent': 0,'RawValue': 0,'Units': '%'},'Memory Usage': {'Color': '#246BA0','Color3': '#FFF','MaxValue': 7917,'Percent': 0,'RawValue': 0,'Units': 'MB'}}
    # Module: str  # 'GenericModule'
    ModuleDisplayName: str  # 'Terraria'
    # Port: str  # 8097
    ReleaseStream: int  # 10
    Running: bool  # True
    Suspended: bool  # False
    Tags: list[Any]
    TargetID: str  # '47d31130-25ed-47d3-af50-c0ebd947830d'

    # custom attrs
    _app_running: bool = False
    _perms: list[str] = []
    _ignore_list: list[str] = []
    _super_adminID: str
    _apiModule: str
    _roleID: Union[str, None]
    _targetName: str
    _initialized: bool = False
    _last_update_time_lock: threading.Lock

    # permission attrs
    AMPUSER_id: str
    AMPUSER_info: dict
    SUPERADMIN_roleID: str
    _roleID: str
    _role_exists: bool = False
    _have_role: bool = False
    _have_superAdmin: bool = False

    def __init__(self, serverData: dict[str, str]) -> None:
        super().__init__()
        self._URL = self.AMPURL + f"ADSModule/Servers/{self.InstanceID}/API/"
        # most if not all of these are type hinted above as base instance vars
        for entry in serverData:
            setattr(self, entry, serverData[entry])

        # DB setup
        self._DBHandler: DBHandler = DBHandler()
        self._DB: Database = self._DBHandler._DB
        self._DBConfig: DBConfig = self._DBHandler._DBConfig

        self.DB_Server = self._DB.GetServer(InstanceID=self.InstanceID)
        if self.DB_Server is None:
            try:
                self.DB_Server: DBServer = self._DB.AddServer(InstanceID=self.InstanceID, InstanceName=self.InstanceName, FriendlyName=self.FriendlyName)
            except Exception as e:
                self._logger.error(f'We failed to add the {self.InstanceName} {self.InstanceID} to the DB. | Error: {traceback.format_exc()}')
                raise Exception('Failed to Add to Instance to Database')

        #     # Lets see what Roles/Permissions we have if it all possible first.
        #     try:
        #         permission = self.check_SessionPermissions()  # We either have to have bot Role or Super Admin to get passed this point. So validate.

        #     except Exception as e:
        #         self._logger.critical(f'***ATTENTION*** {e} for {self.APIModule} on {self.FriendlyName}! Please consider giving us `Super Admins` and the bot will set its own permissions and role!')
        #         # If the main AMP is missing permissions; lets quit!
        #         if instanceID == '0':
        #             sys.exit(1)

        #     if permission:
        #         # If we have the -super arg no need to check for Gatekeeper Role/etc. Just return.
        #         if self._AMPHandler._args.super:
        #             self._initialized = True
        #             return

        #         role_perms = self.check_GatekeeperRole_Permissions()  # This will fail if we DO NOT have
        #         # Main Instance
        #         if instanceID == '0':
        #             # Gatekeeper Role doesn't exist we setup our Bot Role Woohoo!
        #             if not self._AMP_botRole_exists:
        #                 self._initialized = True
        #                 self.setup_AMPbotrole()
        #                 return

        #             # This is an edge case.
        #             # Gatekeeper doesn't have its Gatekeeper Role, give it to myself.
        #             if not self._have_AMP_botRole:
        #                 self.setAMPUserRoleMembership(self.AMP_UserID, self.AMP_BotRoleID, True)

        #         if not role_perms:
        #             if not self._have_superAdmin:
        #                 self.logger.critical(f'We do not have the Role `Super Admins` and are unable to set our Permissions for {"AMP" if self.InstanceID == 0 else self.FriendlyName}')
        #                 sys.exit(1)

        #             # If for some reason we do have Gatekeeper Role and the permissions are NOT setup.
        #             if self._AMP_botRole_exists and self._have_AMP_botRole:
        #                 self.setup_Gatekeeper_Permissions()

        #             # If for some reason Gatekeeper Role doesn't exist and we don't have it.
        #             else:
        #                 self.setup_AMPbotrole()

        #         else:
        #             self._logger.info(f'We have proper permissions on {"AMP" if self.InstanceID == 0 else self.FriendlyName}')

        self._initialized = True

    def __setattr__(self, attr: str, value: Any):
        if hasattr(self, "_initilized") and self._initialized:
            return

        super().__setattr__(attr, value)

    @property
    def memoryUsage(self) -> Metrics:
        if "Memory Usage" in self.Metrics:
            _raw_value: str = self.Metrics["Memory Usage"]["RawValue"]
            _max_value: str = self.Metrics["Memory Usage"]["MaxValue"]
            _percent: str = self.Metrics["Memory Usage"]["Percent"]
            _units: str = self.Metrics["Memory Usage"]["Units"]
            return Metrics(_raw_value, _max_value, _percent, _units)
        else:
            return Metrics()

    @property
    def cpuUsage(self) -> Metrics:
        if "CPU Usage" in self.Metrics:
            _raw_value: str = self.Metrics["CPU Usage"]["RawValue"]
            _max_value: str = self.Metrics["CPU Usage"]["MaxValue"]
            _percent: str = self.Metrics["CPU Usage"]["Percent"]
            _units: str = self.Metrics["CPU Usage"]["Units"]
            return Metrics(_raw_value, _max_value, _percent, _units)
        else:
            return Metrics()

    @property
    def activeUsers(self) -> Metrics:
        if "Active Users" in self.Metrics:
            _raw_value: str = self.Metrics["Active Users"]["RawValue"]
            _max_value: str = self.Metrics["Active Users"]["MaxValue"]
            _percent: str = self.Metrics["Active Users"]["Percent"]
            _units: str = self.Metrics["Active Users"]["Units"]
            return Metrics(_raw_value, _max_value, _percent, _units)
        else:
            return Metrics()

    @property
    def manageURL(self) -> str | None:
        ret: Union[str, None] = None
        results = self.getConfig(node="ADSModule.Networking.BaseURL")
        if "CurrentValue" in results:
            value = results["CurrentValue"]
            ret = value + f"/?instance={self.InstanceID}"
            return ret

    # def __getattribute__(self, __name: str):
    #     if __name in ['_initialized', 'InstanceID', 'serverdata']:
    #         return super().__getattribute__(__name)

    #     if self._initialized and (self.InstanceID != 0) and __name in self.serverdata:
    #         self.AMPHandler.AMP._updateInstanceAttributes()

    #     return super().__getattribute__(__name)

    def _setDBattr(self):
        """This is used to set/update the DB attributes for the AMP server"""
        self.DB_Server = self.DB.GetServer(InstanceID=self.InstanceID)
        self.DisplayName = self.DB_Server.DisplayName
        self.Host = self.DB_Server.Host
        self.Whitelist = self.DB_Server.Whitelist
        self.Whitelist_disabled = self.DB_Server.Whitelist_disabled
        self.Donator = self.DB_Server.Donator
        self.Console_Flag = self.DB_Server.Console_Flag
        self.Console_Filtered = self.DB_Server.Console_Filtered
        self.Console_Filtered_Type = self.DB_Server.Console_Filtered_Type
        self.Discord_Console_Channel = self.DB_Server.Discord_Console_Channel
        self.Discord_Chat_Channel = self.DB_Server.Discord_Chat_Channel
        self.Discord_Chat_Prefix = self.DB_Server.Discord_Chat_Prefix
        self.Discord_Event_Channel = self.DB_Server.Discord_Event_Channel
        self.Discord_Role = self.DB_Server.Discord_Role
        self.Avatar_url = self.DB_Server.Avatar_url
        self.Hidden = self.DB_Server.Hidden
        self.background_banner_path = self.DB_Server.getBanner().background_path

    def _ADScheck(self) -> bool:
        """Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP INSTANCE!
        This updates `self._App_Running` attribute, also returns `True` on Success or `False` on failure(not running)"""
        Success = self.Login()
        self.logger.debug('Server Check, Login Sucess: ' + str(Success))
        if Success:
            status: bool = self.getLiveStatus()
            self.logger.debug(f'{self.FriendlyName} ADS Running: {status}')
            self._App_Running = status
            return status
        else:
            return False

    def _instance_ThreadManager(self):
        """AMP Instance(s) Thread Manager"""
        self.Login()
        for instance in self.AMPHandler.AMP_Instances:
            server = self.AMPHandler.AMP_Instances[instance]

            # Lets validate our ADS Running before we check for console threads.
            if server.Running and server._ADScheck() and server._App_Running:
                # Lets check if the Console Thread is running now.
                if server.Console.console_thread_running == False:
                    self.logger.info(f'{server.FriendlyName}: Starting Console Thread, Instance Online: {server.Running} and ADS Online: {server._App_Running}')
                    server.Console.console_thread_running = True

                    if not server.Console.console_thread.is_alive():
                        server.Console.console_thread.start()

            if not server.Running or server.Running and not server._App_Running:
                if server.Console.console_thread_running == True:
                    self.logger.error(f'{server.FriendlyName}: Shutting down Console Thread, Instance Online: {server.Running}, ADS Online: {server._App_Running}.')
                    server.Console.console_thread_running = False

    def getLiveStatus(self) -> bool:
        """Server is Online and Proper AMP Permissions. \n
        So we check TPS/State to make sure the Dedicated Server is actually 'live'. \n
        `Returns False` when 0 TPS """
        result = self.getStatus()
        if result == False:
            return result

        # This usually happens if the service is offline.
        if 'State' in result:
            status = str(result['State'])
            if status == '0':
                return False
            return True
        else:
            return False

    # These are GENERIC Methods below this point purely for typehiting and Linter purpose. ---------------------------------------------------------------------------

    def addWhitelist(self, db_user, in_gamename: str = None):
        """Base Function for AMP.addWhitelist"""
        # Use the DB_User object and get the required IGN depending on the server type.
        return False

    def getWhitelist(self) -> dict[str, str]:
        """Base Function for AMP.getWhitelist"""
        return

    def removeWhitelist(self, db_user, in_gamename: str = None):
        """Base Function for AMP.removeWhitelist"""
        return False

    def name_Conversion(self):
        """Base Function for AMP.name_Conversion"""
        return None

    def name_History(self, user):
        """Base Function for AMP.name_History"""
        return user

    def check_Whitelist(self, db_user=None, in_gamename: str = None):
        self.logger.dev(f'Checking if {in_gamename if db_user == None else db_user.DiscordName} is whitelisted on {self.FriendlyName}...')
        """Returns `None` if the ign is whitelisted \n
        Returns `False` if no UUID exists \n
        Returns `True` if not in Whitelisted"""
        return None

    def Chat_Message(self, message: str, author: str = None, author_prefix: str = None):
        """Base Function for Discord Chat Messages to AMP ADS"""
        return

    def Chat_Message_Formatter(self, message: str):
        """Base Function for Server Chat Message Formatter"""
        return message

    def get_IGN_Avatar(self, db_user=None, user: str = None):
        """Base Function for customized discord messages (Primarily Minecraft)"""
        return False

    def Broadcast_Message(self, message, prefix: str = None):
        """Base Function for Broadcast Messages to AMP ADS"""
        return
