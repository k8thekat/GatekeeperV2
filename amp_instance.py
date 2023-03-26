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

import time
import traceback

import sys

import threading

from typing import Union
from amp_handler import AMPHandler

from db import DBServer, Database, DBHandler, DBConfig
from amp_api import AMP_API
from amp_console import AMPConsole

from pprint import pprint


class AMPInstance(AMP_API):
    # all these vars come from AMP when getting an Instance's information. Their values can change.
    #AMP2Factor: Union[str, None, TOTP]
    AppState: str
    ApplicationEndpoints: str
    Console: AMPConsole
    ContainerCPUs: str
    ContainerMemoryMB: str
    ContainerMemoryPolicy: str
    Daemon: str
    DaemonAutostart: str
    DisplayImageSource: str
    ExcludeFromFirewall: str
    IP: str
    InstalledVersion: str
    InstanceID: str
    FriendlyName: str
    InstanceName: str
    IsContainerInstance: str
    IsHTTPS: str
    IsTemplateInstance: str
    ManagementMode: str
    Metrics: Union[dict, None]
    Module: str
    Port: str
    ReleaseStream: str
    Running: str
    _SessionID: Union[str, None] = None
    Suspended: str
    TargetID: str
    url: str

    def __init__(self, instance_name: str = 'AMP', instanceID: str = '0', serverdata: dict[str, str] = {}, target_name: Union[str, None] = None):
        super().__init__(instance_name=instance_name, instance_id=instanceID)
        self._AMPHandler: AMPHandler = AMPHandler()

        self._DBHandler: DBHandler = DBHandler()
        self._DB: Database = self._DBHandler.DB
        self._DBConfig: DBConfig = self._DBHandler.DBConfig

        self._initialized = False
        self._App_Running: bool = False  # This is for the Application
        self.InstanceID: str = instanceID  # this should default to 0 on Core AMP
        self._TargetName = target_name  # typically used in Target/Controller systems.
        self.Console: AMPConsole = AMPConsole(self)
        self.APIModule: str
        self.AMP_BotRoleID: Union[str, None] = None
        self.super_AdminID: str
        self._sender_filter_list: list[str] = list()  # Do not send messages from people in this list (case insensitive)
        self._perms = []

        self._last_update_time_lock: threading.Lock
        # if this is the default instance lets set some default vars.
        if self.InstanceID == '0':
            self._perms = ['Core.*',
                           'Core.RoleManagement.*',
                           'Core.UserManagement.*',
                           'Instances.*',
                           'ADS.*',
                           'Settings.*',
                           'ADS.InstanceManagement.*',
                           'FileManager.*',
                           'LocalFileBackup.*',
                           'Core.AppManagement.*']
            self.APIModule = 'AMP'
            self._last_update_time_lock = threading.Lock()

        if self.InstanceID != '0':
            self._url += f"ADSModule/Servers/{self.InstanceID}/API/"
            # This gets all the dictionary values tied to AMP and makes them attributes of self.
            for entry in serverdata:
                setattr(self, entry, serverdata[entry])

            if not hasattr(self, 'Description'):
                self.Description: str = ''

            # This gets me the DB_Server object if it's not there; it adds the server.
            self.DB_Server = self._DB.GetServer(InstanceID=self.InstanceID)
            if self.DB_Server == None:
                self._logger.dev(f'Adding Name: {self.InstanceName} to the Database, Instance ID: {self.InstanceID}')

                try:
                    self.DB_Server: DBServer = self._DB.AddServer(InstanceID=self.InstanceID, InstanceName=self.InstanceName, FriendlyName=self.FriendlyName)
                except Exception as e:
                    self._logger.error(f'We failed to add the {self.InstanceName} {self.InstanceID} to the DB. Error: {traceback.format_exc()}')
                    raise Exception('Failed to Add to Instance to Database')

                self._logger.info(f'*SUCCESS** Added {self.InstanceName} to the Database.')
            else:
                self._logger.info(f'**SUCCESS** Found {self.InstanceName} in the Database.')

            self._logger.dev(f"Instance Name: {self.InstanceName} // InstanceID: {self.InstanceID} // Module: {self.Module} // Port: {self.Port} // DisplayImageSource: {self.DisplayImageSource}")

            # This sets all my DB_Server attributes.
            self._setDBattr()
            if self.Running:
                self._ADScheck()

        # Lets see if we are the main AMP or if the Instance is Running
        # this is going to validate permissions per instance
        if instanceID == '0' or self.Running:
            self._AMP_botRole_exists = False
            self._have_superAdmin = False
            self._have_AMP_botRole = False

            # Lets see what Roles/Permissions we have if it all possible first.
            try:
                permission = self.check_SessionPermissions()  # We either have to have bot Role or Super Admin to get passed this point. So validate.

            except Exception as e:
                self._logger.critical(f'***ATTENTION*** {e} for {self.APIModule} on {self.FriendlyName}! Please consider giving us `Super Admins` and the bot will set its own permissions and role!')
                # If the main AMP is missing permissions; lets quit!
                if instanceID == '0':
                    sys.exit(1)

            if permission:
                # If we have the -super arg no need to check for Gatekeeper Role/etc. Just return.
                if self._AMPHandler._args.super:
                    self._initialized = True
                    return

                role_perms = self.check_GatekeeperRole_Permissions()  # This will fail if we DO NOT have
                # Main Instance
                if instanceID == '0':
                    # Gatekeeper Role doesn't exist we setup our Bot Role Woohoo!
                    if not self._AMP_botRole_exists:
                        self._initialized = True
                        self.setup_AMPbotrole()
                        return

                    # This is an edge case.
                    # Gatekeeper doesn't have its Gatekeeper Role, give it to myself.
                    if not self._have_AMP_botRole:
                        self.setAMPUserRoleMembership(self.AMP_UserID, self.AMP_BotRoleID, True)

                if not role_perms:
                    if not self._have_superAdmin:
                        self.logger.critical(f'We do not have the Role `Super Admins` and are unable to set our Permissions for {"AMP" if self.InstanceID == 0 else self.FriendlyName}')
                        sys.exit(1)

                    # If for some reason we do have Gatekeeper Role and the permissions are NOT setup.
                    if self._AMP_botRole_exists and self._have_AMP_botRole:
                        self.setup_Gatekeeper_Permissions()

                    # If for some reason Gatekeeper Role doesn't exist and we don't have it.
                    else:
                        self.setup_AMPbotrole()

                else:
                    self._logger.info(f'We have proper permissions on {"AMP" if self.InstanceID == 0 else self.FriendlyName}')

        self._initialized = True

    def setup_AMPbotrole(self):
        """Creates the `Gatekeeper` role, Adds us to the Membership of that Role and sets its AMP permissions."""
        self._logger.warning('Creating the AMP role `Gatekeeper`...')
        self.createRole('Gatekeeper')
        self.setRoleIDs()
        self._logger.dev(f'Created `Gatekeeper` role. ID: {self.AMP_BotRoleID}')
        self.AMP_UserID = self.getAMPUserID(self.AMPHandler.tokens.AMPUser)
        self.setAMPUserRoleMembership(self.AMP_UserID, self.AMP_BotRoleID, True)
        self._logger.warning(f'***ATTENTION*** Adding {self.AMPHandler.tokens.AMPUser} to `Gatekeeper` Role.')
        self.setup_Gatekeeper_Permissions()

    def setup_Gatekeeper_Permissions(self):
        """Sets the Permissions Nodes for AMP Gatekeeper Role"""
        self._logger.info('Setting AMP Role Permissions for `Gatekeeper`...')
        import amp_permissions as AMPPerms
        core = AMPPerms.perms_super()
        for perm in core:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]
            if self.setAMPRolePermissions(self.AMP_BotRoleID, perm, enabled):
                self.logger.dev(f'Set __{perm}__ for _Gatekeeper_ to `{enabled}` on {self.FriendlyName if self.InstanceID != 0 else "AMP"}')

    def check_GatekeeperRole_Permissions(self) -> bool:
        """- Will check `Gatekeeper Role` for `Permission Nodes` when we have `Super Admin` and `not InstanceID = 0`.\n
        - Checks for `Gatekeeper Role`, if we `have the Gatekeeper Role` and `Super Admin Role`
        Returns `True` if we have permissions. Otherwise `False`"""
        # If we have Super Admin; lets check for the Bot Role and if we are not on the Main Instance.
        failed = False

        self.AMP_userinfo = self.getAMPUserInfo(self.AMPHandler.tokens.AMPUser)  # This gets my AMP User Information
        self.AMP_UserID = self.getAMPUserID(self.AMPHandler.tokens.AMPUser)  # This gets my AMP User ID
        self.setRoleIDs()

        # `Gatekeeper Role inside of AMP`
        if self.AMP_BotRoleID != None:
            #self.logger.dev('Gatekeeper Role Exists..')
            self._AMP_botRole_exists = True

        # Gatekeeper has `Gatekeeper` Role inside of AMP
        if self._AMP_botRole_exists and self.AMP_BotRoleID in self.AMP_userinfo['result']['Roles']:
            #self.logger.dev('Gatekeeper User has Gatekepeer Role.')
            self._have_AMP_botRole = True

        # `Super_Admin Role inside of AMP`
        if self.super_AdminID in self.AMP_userinfo['result']['Roles']:
            #self.logger.dev('Gatekeeper User has Super Admins')
            self._have_superAdmin = True

        if self._AMP_botRole_exists:
            self.logger.dev(f'Checking `Gatekeeper Role` permissions on {"AMP" if self.InstanceID == 0 else self.FriendlyName}')
            for perm in self.perms:
                # Skip the perm check on ones we "shouldn't have!"
                if perm.startswith('-'):
                    continue

                role_perms = self.getAMPRolePermissions(self.AMP_BotRoleID)

                if perm not in role_perms['result']:
                    if self._have_superAdmin:
                        self.logger.dev(f'We have `Super Admins` Role and we are missing Permissions, returning to setup Permissions.')
                        return False

                    else:
                        end_point = self.AMPHandler.tokens.AMPurl.find(":", 5)
                        self.logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please visit {self.AMPHandler.tokens.AMPurl[:end_point]}:{self.Port} under Configuration -> Role Management -> Gatekeeper')
                    failed = True

            if not failed:
                return True
        else:
            return False

    def check_SessionPermissions(self) -> bool:
        """These check AMP for the proper Permission Nodes.\n
        Returns `True` only if I have ALL the Required Permissions; Otherwise `False`."""
        self._logger.warning(f'Checking Session: {self._SessionID} for proper permissions...')
        failed = False
        for perm in self.perms:
            # Skip the perm check on ones we "shouldn't have!"
            if perm.startswith('-'):
                continue

            check = self.CurrentSessionHasPermission(perm)

            self.logger.dev(f'Session {"has" if check else "is missing" } permisson node: {perm}')
            if check:
                continue

            if self.APIModule == 'AMP':  # AKA the main (InstanceID == 0)
                self.logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please check under Configuration -> User Management for {self.AMPHandler.tokens.AMPUser}.')

            else:
                end_point = self.AMPHandler.tokens.AMPurl.find(":", 5)
                self.logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please visit {self.AMPHandler.tokens.AMPurl[:end_point]}:{self.Port} under Configuration -> Role Management -> Gatekeeper')
            failed = True

        if failed:
            self.logger.critical(f'***ATTENTION*** The Bot is missing permissions, some or all functionality may not work properly!')
            # Please see this image for the required bot user Permissions **(Github link to AMP Basic Perms image here)**
            return check

        return True

    def __getattribute__(self, __name: str):
        if __name in ['_initialized', 'InstanceID', 'serverdata']:
            return super().__getattribute__(__name)

        if self._initialized and (self.InstanceID != 0) and __name in self.serverdata:
            self.AMPHandler.AMP._updateInstanceAttributes()

        return super().__getattribute__(__name)

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

    def _updateInstanceAttributes(self):
        """This updates an AMP Server Objects attributes from `getInstances()` API call."""
        if (not self._initialized) or (time.time() - self.Last_Update_Time < 5):
            return

        if self._last_update_time_lock.acquire(blocking=False) == False:
            return

        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstances', parameters)

        if type(result) == bool:
            self.logger.error(f'Failed to update {self.FriendlyName} attributes, API Call returned {result}')
            return

        if len(result["result"][0]['AvailableInstances']) != 0:
            for Target in result["result"]:
                for instance in Target['AvailableInstances']:  # entry = name['result']['AvailableInstances'][0]['InstanceIDs']
                    # This should be a list of my AMP Servers [{'InstanceID': '<AMP Instance Object>'}]
                    for amp_instance in self.AMPHandler.AMP_Instances:
                        # This should be the <AMP Instance Object> comparing to the Instance Objects we got from `getInstances()`
                        if self.AMPHandler.AMP_Instances[amp_instance].InstanceID == instance['InstanceID']:
                            # This gets all the dictionary values tied to AMP and makes them attributes of self.
                            for entry in instance:
                                setattr(self.AMPHandler.AMP_Instances[amp_instance], entry, instance[entry])
                            break

        self.Last_Update_Time = time.time()
        self._last_update_time_lock.release()

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

    def setRoleIDs(self):
        """Sets `self.AMP_BotRoleID` and `self.super_AdminID` (if they exist)"""
        roles = self.getRoleIds()
        for role in roles:
            if roles[role].lower() == 'gatekeeper':
                self.AMP_BotRoleID = role
                if self.InstanceID == 0:
                    self.logger.dev(f'Found Gatekeeper Role - ID: {self.AMP_BotRoleID}')

            if roles[role].lower() == 'super admins':
                self.super_AdminID = role
                if self.InstanceID == 0:
                    self.logger.dev(f'Found Super Admin Role - ID: {self.super_AdminID}')

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

    def getMetrics(self) -> tuple[str, tuple[str, str], str, tuple[str, str], str]:
        """Returns AMP Instance Metrics \n
        `Uptime str` \n
        `TPS str`  \n
        `Users tuple(str,str)` \n
        `Memory tuple(str, str)` \n
        `CPU str` \n
        """
        Uptime: str = ''
        TPS: str = ''
        Users: tuple[str, str] = ('None', 'None')
        Memory: tuple[str, str] = ('None', 'None')
        CPU: str = ''
        self.Metrics = None

        result = self.getStatus()
        if result == False:
            return TPS, Users, CPU, Memory, Uptime

        if isinstance(result, dict):
            Uptime = str(result['Uptime'])
            TPS = str(result['State'])
            Users = (str(result['Metrics']['Active Users']['RawValue']), str(result['Metrics']['Active Users']['MaxValue']))
            Memory = (str(result['Metrics']['Memory Usage']['RawValue']), str(result['Metrics']['Memory Usage']['MaxValue']))
            CPU = str(result['Metrics']['CPU Usage']['RawValue'])  # This is a percentage
            self.Metrics = result['Metrics']
            return TPS, Users, CPU, Memory, Uptime
        return TPS, Users, CPU, Memory, Uptime

    def getUsersOnline(self) -> tuple[str, str]:
        """Returns Number of Online Players over Player Limit. \n
        `eg 2/10`"""
        result = self.getStatus()
        if result != False:
            Users = (str(result['Metrics']['Active Users']['RawValue']), str(result['Metrics']['Active Users']['MaxValue']))
            return Users

    def getAMPUserID(self, name: str):
        """Returns AMP Users ID Only."""
        result = self.getAMPUserInfo(name=name)
        return result['result']['ID']

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
