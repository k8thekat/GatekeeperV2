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

import logging
import traceback
import dataclasses
from typing import NamedTuple, Union, Any, override
import copy


import threading

from amp.API import AMP_API
from amp.types import *


class Metrics_Tuple(NamedTuple):
    raw_value: int = 0
    percent: int = 0
    max_value: int = 1
    units: str = ""


class AMPInstance(AMP_API):

    # custom attrs
    # TODO - Most of this may go away.
    # _app_running: bool = False
    # _perms: list[str] = []
    # _ignore_list: list[str] = []
    # _super_adminID: str
    # _apiModule: str
    # _roleID: Union[str, None]
    # _targetName: str
    # _initialized: bool = False
    # _last_update_time_lock: threading.Lock

    # permission attrs
    # TODO - Most of this may go away.
    # AMPUSER_id: str
    # AMPUSER_info: dict
    # SUPERADMIN_roleID: str
    # _role_exists: bool = False
    # _have_role: bool = False
    # _have_superAdmin: bool = False

    # def __init__(self, API: AMP_API, data: AMP_Instance) -> None:
    def __init__(self, instance: Instance, api: AMP_API) -> None:
        self.logger = logging.getLogger()
        self.data: Instance = instance  # This is our Instance dataclass. See types `Instance()`
        # self._session_id = api._session_id
        # self.API = copy.deepcopy(api)
        # We update our AMP URL per instance for API calls.
        # I need to get to -> http://192.168.4.50:8080/API/ADSModule/Servers/51a1a1dd-324b-422f-9093-f0d376ca7282/API
        _url = api._url + f"ADSModule/Servers/{self.data.InstanceID}"
        super().__init__(url=_url, amp_user=api._amp_user, amp_password=api._amp_password, amp_2fa=api._amp_2fa, amp_2fa_token=api._amp_2fa_token)
        # print("updating url")

    # @override
    # async def getInstanceStatus(self) -> str | bool | dict:
    #     """
    #     Returns a dictionary of all Server/Instance status information. `*API ONLY*`
    #     """
    #     return await super().getInstanceStatus()

    # TODO - Redo this entire method and approach.
    # Possible have the ADS handle adding the servers and not the Instance?
    # def database_setup(self):
    #     # DB setup
    #     self._DBHandler: DBHandler = DBHandler()
    #     self._DB: Database = self._DBHandler._DB
    #     self._DBConfig: DBConfig = self._DBHandler._DBConfig

    #     self.DB_Server = self._DB.GetServer(InstanceID=self.InstanceID)
    #     if self.DB_Server is None:
    #         try:
    #             self.DB_Server: DBServer = self._DB.AddServer(InstanceID=self.InstanceID, InstanceName=self.InstanceName, FriendlyName=self.FriendlyName)
    #         except Exception as e:
    #             self._logger.error(f'We failed to add the {self.InstanceName} {self.InstanceID} to the DB. | Error: {traceback.format_exc()}')
    #             raise Exception('Failed to Add to Instance to Database')

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

        # self._initialized = True

    # def __setattr__(self, attr: str, value: Any):
    #     if hasattr(self, "_initilized") and self._initialized:
    #         return

    #     super().__setattr__(attr, value)

    @property
    def manageURL(self) -> str | None:
        """
        Network URL to manage the AMP Instance

        Returns:
            str | None: str if the URL exists, None if not.
        """
        ret: Union[str, None] = None
        results = self.getConfig(node="ADSModule.Networking.BaseURL")
        if type(results) == dict and "CurrentValue" in results:
            value = results["CurrentValue"]
            ret = value + f"/?instance={self.data.InstanceID}"
        return ret

    # def __getattribute__(self, __name: str):
    #     if __name in ['_initialized', 'InstanceID', 'serverdata']:
    #         return super().__getattribute__(__name)

    #     if self._initialized and (self.InstanceID != 0) and __name in self.serverdata:
    #         self.AMPHandler.AMP._updateInstanceAttributes()

    #     return super().__getattribute__(__name)

    # def _setDBattr(self):
    #     """This is used to set/update the DB attributes for the AMP server"""
    #     self.DB_Server = self.DB.GetServer(InstanceID=self.InstanceID)
    #     self.DisplayName = self.DB_Server.DisplayName
    #     self.Host = self.DB_Server.Host
    #     self.Whitelist = self.DB_Server.Whitelist
    #     self.Whitelist_disabled = self.DB_Server.Whitelist_disabled
    #     self.Donator = self.DB_Server.Donator
    #     self.Console_Flag = self.DB_Server.Console_Flag
    #     self.Console_Filtered = self.DB_Server.Console_Filtered
    #     self.Console_Filtered_Type = self.DB_Server.Console_Filtered_Type
    #     self.Discord_Console_Channel = self.DB_Server.Discord_Console_Channel
    #     self.Discord_Chat_Channel = self.DB_Server.Discord_Chat_Channel
    #     self.Discord_Chat_Prefix = self.DB_Server.Discord_Chat_Prefix
    #     self.Discord_Event_Channel = self.DB_Server.Discord_Event_Channel
    #     self.Discord_Role = self.DB_Server.Discord_Role
    #     self.Avatar_url = self.DB_Server.Avatar_url
    #     self.Hidden = self.DB_Server.Hidden
    #     self.background_banner_path = self.DB_Server.getBanner().background_path

    # def _ADScheck(self) -> bool:
    #     """Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP INSTANCE!
    #     This updates `self._App_Running` attribute, also returns `True` on Success or `False` on failure(not running)"""
    #     Success = self.Login()
    #     self.logger.debug('Server Check, Login Sucess: ' + str(Success))
    #     if Success:
    #         status: bool = self.getLiveStatus()
    #         self.logger.debug(f'{self.FriendlyName} ADS Running: {status}')
    #         self._App_Running = status
    #         return status
    #     else:
    #         return False

    # def _instance_ThreadManager(self):
    #     """AMP Instance(s) Thread Manager"""
    #     self.Login()
    #     for instance in self.AMPHandler.AMP_Instances:
    #         server = self.AMPHandler.AMP_Instances[instance]

    #         # Lets validate our ADS Running before we check for console threads.
    #         if server.Running and server._ADScheck() and server._App_Running:
    #             # Lets check if the Console Thread is running now.
    #             if server.Console.console_thread_running == False:
    #                 self.logger.info(f'{server.FriendlyName}: Starting Console Thread, Instance Online: {server.Running} and ADS Online: {server._App_Running}')
    #                 server.Console.console_thread_running = True

    #                 if not server.Console.console_thread.is_alive():
    #                     server.Console.console_thread.start()

    #         if not server.Running or server.Running and not server._App_Running:
    #             if server.Console.console_thread_running == True:
    #                 self.logger.error(f'{server.FriendlyName}: Shutting down Console Thread, Instance Online: {server.Running}, ADS Online: {server._App_Running}.')
    #                 server.Console.console_thread_running = False

    # def getLiveStatus(self) -> bool:
    #     """Server is Online and Proper AMP Permissions. \n
    #     So we check TPS/State to make sure the Dedicated Server is actually 'live'. \n
    #     `Returns False` when 0 TPS """
    #     result = self.getStatus()
    #     if result == False:
    #         return result

    #     # This usually happens if the service is offline.
    #     if 'State' in result:
    #         status = str(result['State'])
    #         if status == '0':
    #             return False
    #         return True
    #     else:
    #         return False

    # These are GENERIC Methods below this point purely for typehiting and Linter purpose. ---------------------------------------------------------------------------

    # def addWhitelist(self, db_user, in_gamename: str = None):
    #     """Base Function for AMP.addWhitelist"""
    #     # Use the DB_User object and get the required IGN depending on the server type.
    #     return False

    # def getWhitelist(self) -> dict[str, str]:
    #     """Base Function for AMP.getWhitelist"""
    #     return

    # def removeWhitelist(self, db_user, in_gamename: str = None):
    #     """Base Function for AMP.removeWhitelist"""
    #     return False

    # def name_Conversion(self):
    #     """Base Function for AMP.name_Conversion"""
    #     return None

    # def name_History(self, user):
    #     """Base Function for AMP.name_History"""
    #     return user

    # def check_Whitelist(self, db_user=None, in_gamename: str = None):
    #     self.logger.dev(f'Checking if {in_gamename if db_user == None else db_user.DiscordName} is whitelisted on {self.FriendlyName}...')
    #     """Returns `None` if the ign is whitelisted \n
    #     Returns `False` if no UUID exists \n
    #     Returns `True` if not in Whitelisted"""
    #     return None

    # def Chat_Message(self, message: str, author: str = None, author_prefix: str = None):
    #     """Base Function for Discord Chat Messages to AMP ADS"""
    #     return

    # def Chat_Message_Formatter(self, message: str):
    #     """Base Function for Server Chat Message Formatter"""
    #     return message

    # def get_IGN_Avatar(self, db_user=None, user: str = None):
    #     """Base Function for customized discord messages (Primarily Minecraft)"""
    #     return False

    # def Broadcast_Message(self, message, prefix: str = None):
    #     """Base Function for Broadcast Messages to AMP ADS"""
    #     return
