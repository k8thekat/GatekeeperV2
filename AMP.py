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
from __future__ import annotations
import requests
import requests.sessions
import pyotp  # 2Factor Authentication Python Module
import json
import time
import traceback

import sys
import logging
import threading

from typing import Union

import DB
import AMP_Console


class AMPInstance():
    """AMP Base Class: \n
        Attributes: \n
        `AMP2Factor `\n
        `AMPheader `\n
        `AppState `\n
        `ApplicationEndpoints `\n
        `CallAPI `\n
        `Console - AMPConsole Object `\n
        `ConsoleMessage `\n
        `ConsoleUpdate #returns a list `\n
        `ContainerCPUs `\n
        `ContainerMemoryMB `\n
        `ContainerMemoryPolicy `\n
        `Daemon `\n
        `DaemonAutostart `\n
        `DisplayImageSource `\n
        `ExcludeFromFirewall `\n
        `FriendlyName : What is displayed in AMP Panel `\n
        `IP `\n
        `InstalledVersion `\n
        `InstanceID `\n
        `InstanceName : What the instance was named when it was created! `\n
        `IsContainerInstance `\n
        `IsHTTPS `\n
        `IsTemplateInstance `\n
        `KillInstance `\n
        `Login `\n
        `ManagementMode `\n
        `Metrics `\n
        `Module `\n
        `Port `\n
        `ReleaseStream `\n
        `RestartInstance `\n
        `Running : This is the Instance Status `\n
        `ADS_Running : This is the Dedicated Server `\n
        `SessionID `\n
        `StartInstance `\n
        `StopInstance `\n
        `Suspended `\n
        `TargetID `\n
        `addTask `\n
        `getInstances : # returns list `\n
        `getSchedule : #returns a dict `\n
        `getStatus : #returns TPS,PlayerCount,Uptime `\n
        `serverdata `\n
        `url `\n
        """

    AMP2Factor: str
    AMPheader: dict
    AppState: dict
    ApplicationEndpoints: dict
    Console: AMP_Console.AMPConsole
    ContainerCPUs: int
    ContainerMemoryMB: int
    ContainerMemoryPolicy: str
    Daemon: bool
    DaemonAutostart: bool
    DisplayImageSource: str
    ExcludeFromFirewall: bool
    FriendlyName: str
    IP: str
    InstalledVersion: str
    InstanceID: int
    InstanceName: str
    Module: str

    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str = None):
        self.Initialized = False
        # Do not send messages from people in this list (case insensitive)
        self.SenderFilterList = list()

        self.logger = logging.getLogger()

        self.AMPHandler = Handler
        # if self.AMPHandler == None:
        #     self.AMPHandler = AMP_Handler.getAMPHandler()

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DBConfig = self.DB.DBConfig

        self.SessionID = 0
        # self.Index = Index
        self.serverdata = serverdata
        self.serverlist = {}

        self.InstanceID = instanceID
        self.__setattr__('TargetName', TargetName)
        self.FriendlyName = None

        self.ADS_Running = False  # This is for the ADS (Dedicated Server) not the Instance!

        self.Last_Update_Time = 0

        if instanceID == 0:
            self.Last_Update_Time_Mutex = threading.Lock()

        self.AMP_BotRoleID = None
        self.super_AdminID = None

        self.url = self.AMPHandler.tokens.AMPurl + '/API/'  # base url for AMP console /API/

        if hasattr(self, "perms") == False:
            self.perms = ['Core.*', 'Core.RoleManagement.*', 'Core.UserManagement.*', 'Instances.*', 'ADS.*', 'Settings.*', 'ADS.InstanceManagement.*', 'FileManager.*', 'LocalFileBackup.*', 'Core.AppManagement.*']

        if hasattr(self, 'APIModule') == False:
            self.APIModule = 'AMP'

        self.AMP2Factor = None
        if self.AMPHandler.AMP2FA:
            try:
                self.AMP2Factor = pyotp.TOTP(self.AMPHandler.tokens.AMPAuth)  # Handles time based 2Factory Auth Key/Code
                self.AMP2Factor.now()

            except AttributeError:
                self.logger.critical("**ERROR** Please check your 2 Factor Set-up Code in tokens.py, should not contain spaces,escape characters and enclosed in quotes!")
                self.AMP2Factor = None
                return

        self.AMPheader = {'Accept': 'text/javascript'}  # custom header for AMP API POST requests. AMP is pure POST requests. ***EVERY REQUEST MUST HAVE THIS***
        if instanceID != 0:
            self.url += f"ADSModule/Servers/{instanceID}/API/"

        if default_console:
            self.Console = AMP_Console.AMPConsole(self)

        if instanceID != 0:
            # This gets all the dictionary values tied to AMP and makes them attributes of self.
            for entry in serverdata:
                setattr(self, entry, serverdata[entry])

            if not hasattr(self, 'Description'):
                self.Description = ''

            # This gets me the DB_Server object if it's not there; it adds the server.
            self.DB_Server = self.DB.GetServer(InstanceID=self.InstanceID)
            if self.DB_Server == None:
                self.logger.dev(f'Adding Name: {self.InstanceName} to the Database, Instance ID: {self.InstanceID}')
                try:
                    self.DB_Server = self.DB.AddServer(InstanceID=self.InstanceID, InstanceName=self.InstanceName, FriendlyName=self.FriendlyName)
                except Exception as e:
                    self.logger.error(f'We failed to add the {self.InstanceName} {self.InstanceID} to the DB. Error: {traceback.format_exc()}')
                    raise Exception('Failed to Add to Database')

                self.logger.info(f'*SUCCESS** Added {self.InstanceName} to the Database.')
            else:
                self.logger.info(f'**SUCCESS** Found {self.InstanceName} in the Database.')

            self.logger.dev(f"Instance Name: {self.InstanceName} // InstanceID: {self.InstanceID} // Module: {self.Module} // Port: {self.Port} // DisplayImageSource: {self.DisplayImageSource}")

            # This sets all my DB_Server attributes.
            self._setDBattr()
            if self.Running:
                self._ADScheck()

        # Lets see if we are the main AMP or if the Instance is Running
        if instanceID == 0 or self.Running:
            self._AMP_botRole_exists = False
            self._have_superAdmin = False
            self._have_AMP_botRole = False

            # Lets see what Roles/Permissions we have if it all possible first.
            try:
                permission = self.check_SessionPermissions()  # We either have to have bot Role or Super Admin to get passed this point. So validate.

            except Exception as e:
                self.logger.critical(f'***ATTENTION*** {e} for {self.APIModule} on {self.FriendlyName}! Please consider giving us `Super Admins` and the bot will set its own permissions and role!')
                # If the main AMP is missing permissions; lets quit!
                if instanceID == 0:
                    sys.exit(1)

            if permission:
                # If we have the -super arg no need to check for Gatekeeper Role/etc. Just return.
                if self.AMPHandler.args.super:
                    self.Initialized = True
                    return

                role_perms = self.check_GatekeeperRole_Permissions()  # This will fail if we DO NOT have
                # Main Instance
                if instanceID == 0:
                    # Gatekeeper Role doesn't exist we setup our Bot Role Woohoo!
                    if not self._AMP_botRole_exists:
                        self.Initialized = True
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
                    self.logger.info(f'We have proper permissions on {"AMP" if self.InstanceID == 0 else self.FriendlyName}')

        self.Initialized = True

    def setup_AMPbotrole(self):
        """Creates the `Gatekeeper` role, Adds us to the Membership of that Role and sets its AMP permissions."""
        self.logger.warning('Creating the AMP role `Gatekeeper`...')
        self.createRole('Gatekeeper')
        self.setRoleIDs()
        self.logger.dev(f'Created `Gatekeeper` role. ID: {self.AMP_BotRoleID}')
        self.AMP_UserID = self.getAMPUserID(self.AMPHandler.tokens.AMPUser)
        self.setAMPUserRoleMembership(self.AMP_UserID, self.AMP_BotRoleID, True)
        self.logger.warning(f'***ATTENTION*** Adding {self.AMPHandler.tokens.AMPUser} to `Gatekeeper` Role.')
        self.setup_Gatekeeper_Permissions()

    def setup_Gatekeeper_Permissions(self):
        """Sets the Permissions Nodes for AMP Gatekeeper Role"""
        self.logger.info('Setting AMP Role Permissions for `Gatekeeper`...')
        # import AMP_Permissions as AMPPerms
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
            # self.logger.dev('Gatekeeper Role Exists..')
            self._AMP_botRole_exists = True

        # Gatekeeper has `Gatekeeper` Role inside of AMP
        if self._AMP_botRole_exists and self.AMP_BotRoleID in self.AMP_userinfo['Roles']:
            # if self._AMP_botRole_exists and self.AMP_BotRoleID in self.AMP_userinfo['result']['Roles']:
            # self.logger.dev('Gatekeeper User has Gatekepeer Role.')
            self._have_AMP_botRole = True

        # `Super_Admin Role inside of AMP`
        # if self.super_AdminID in self.AMP_userinfo['result']['Roles']:
        if self.super_AdminID in self.AMP_userinfo['Roles']:
            # self.logger.dev('Gatekeeper User has Super Admins')
            self._have_superAdmin = True

        if self._AMP_botRole_exists:
            self.logger.dev(f'Checking `Gatekeeper Role` permissions on {"AMP" if self.InstanceID == 0 else self.FriendlyName}')
            for perm in self.perms:
                # Skip the perm check on ones we "shouldn't have!"
                if perm.startswith('-'):
                    continue

                role_perms = self.getAMPRolePermissions(self.AMP_BotRoleID)

                if perm not in role_perms:
                    # if perm not in role_perms['result']:
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
        self.logger.warning(f'Checking Session: {self.SessionID} for proper permissions...')
        failed = False
        for perm in self.perms:
            # Skip the perm check on ones we "shouldn't have!"
            if perm.startswith('-'):
                continue
            check = self.CurrentSessionHasPermission(perm)
            self.logger.dev(f'Session {"has" if check else "is missing"} permisson node: {perm}')
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
        if __name in ['Initialized', 'InstanceID', 'serverdata']:
            return super().__getattribute__(__name)

        if self.Initialized and (self.InstanceID != 0) and __name in self.serverdata:
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

    def Login(self) -> bool:
        if self.SessionID == 0:
            if self.InstanceID in self.AMPHandler.SessionIDlist:
                self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
                return

            self.logger.dev(f'AMPInstance Logging in {self.InstanceID}')

            if self.AMP2Factor != None:
                token = self.AMP2Factor.now()

            else:
                token = ''

            parameters = {
                'username': self.AMPHandler.tokens.AMPUser,
                'password': self.AMPHandler.tokens.AMPPassword,
                'token': token,  # get current 2Factor Code
                'rememberMe': True}

            try:
                result = self.CallAPI('Core/Login', parameters)
                if result.get("sessionID"):
                    self.SessionID = result['sessionID']
                    self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
                    self.Running = True

                else:
                    self.logger.warning(f'{self.FriendlyName} - Instance is Offline')
                    self.Running = False
                    return False

            except Exception as e:
                self.logger.dev(f'Core/Login Exception: {traceback.format_exc()}')
                self.logger.dev(result)

                self.logger.warning(f'{self.FriendlyName} - Instance is Offline')
                self.Running = False
                return False

        return True

    def CallAPI(self, APICall, parameters) -> Union[bool, dict]:
        """This is the main API Call function"""
        self.logger.debug(f'Function {APICall} was called with {parameters} by {self.InstanceID}')

        if self.SessionID != 0:
            parameters['SESSIONID'] = self.SessionID
        jsonhandler = json.dumps(parameters)

        while (True):
            try:
                post_req = requests.post(self.url + APICall, headers=self.AMPheader, data=jsonhandler)

                if len(post_req.content) > 0:
                    break

                # Since we are using GetUpdates every second for Console Updates; lets ignore them here so we don't sleep our thread.
                if APICall == 'Core/GetUpdates':
                    break

                self.logger.error(f'{self.FriendlyName}: AMP API recieved no Data; sleeping for 5 seconds...')
                time.sleep(5)

            except:
                if self.AMPHandler.SuccessfulConnection == False:
                    self.logger.critical('Unable to connect to URL; please check Tokens.py -> AMPURL')
                    sys.exit(-1)

                self.logger.warning('AMP API was unable to connect; sleeping for 30 seconds...')
                time.sleep(30)

        self.AMPHandler.SuccessfulConnection = True

        res = post_req.json()

        # Error catcher for API calls
        if (post_req.status_code < 200 or post_req.status_code >= 300):
            self.logger.error(f"AMP_API `{APICall}` status_code:  {post_req.status_code}")
            self.logger.error(post_req.raw)
            return

        if res == None:
            self.logger.debug(f"AMP_API {APICall} json() is `None`")
            self.logger.debug(post_req.raw)
            return

        # {"result": Int or Bool} or dict[str, int] -> Int or Bool

        self.logger.debug(f'Post Request Prints: {res}')
        # Permission errors will trigger this, unsure what else.
        # print("API CALL---->", APICall, type(res), res)
        if isinstance(res, dict) and "result" in res:
            # if "result" in res:
            # This was one of the API calls that failed.
            # if APICall == "Core/GetAMPUserInfo":
            #     print(res["result"])

            # This one was to deal with "Core/Login" as it has a dict key value called "result" that has a int value. (near the end of the res)
            if type(res["result"]) == int:
                # print("Found an int in keyed ['result']")
                return res

            elif type(res['result']) == bool:
                # print("Found a bool in keyed ['result']")
                if res['result'] == True:
                    return res

                elif res['result'] != True:
                    self.logger.error(f'The API Call {APICall} failed because of {res}')
                    return res

                elif ("Status" in res['result']) and (res['result']['Status'] == False):
                    self.logger.error(f'The API Call {APICall} failed because of Status: {res}')
                    return False

            # This should handle the new API by auto defaulting to returning entries without the result key.
            else:
                # print(f"Found result in post_req, returning keyed ['result'] {APICall}")
                return res["result"]

        elif isinstance(res, dict) and "Title" in res:
            if (type(res['Title']) == str) and (res['Title'] == 'Unauthorized Access'):
                self.logger.error(f'["Title"]: The API Call {APICall} failed because of {res}')
                # Resetting the Session ID for the Instance; forcing a new login/SessionID
                self.AMPHandler.SessionIDlist.pop(self.InstanceID)
                self.SessionID = 0
                return False

        else:
            # print("Trigger Else in API call", res)
            return res

    def _ADScheck(self) -> bool:
        """Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP INSTANCE!
        This updates `self.ADS_Running` attribute, also returns `True` on Success or `False` on failure"""
        Success = self.Login()
        self.logger.debug('Server Check, Login Sucess: ' + str(Success))
        if Success:
            status = self.getLiveStatus()
            self.logger.debug(f'{self.FriendlyName} ADS Running: {status}')
            self.ADS_Running = status
            return status

    def _updateInstanceAttributes(self):
        """This updates an AMP Server Objects attributes from `getInstances()` API call."""
        if (not self.Initialized) or (time.time() - self.Last_Update_Time < 5):
            return

        if self.Last_Update_Time_Mutex.acquire(blocking=False) == False:
            return

        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstances', parameters)

        if type(result) == bool:
            self.logger.error(f'Failed to update {self.FriendlyName} attributes, API Call returned {result}')
            return

        if len(result[0]['AvailableInstances']) != 0:
            # if len(result["result"][0]['AvailableInstances']) != 0:
            # for Target in result["result"]:
            for Target in result:
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
        self.Last_Update_Time_Mutex.release()

    def _instance_ThreadManager(self):
        """AMP Instance(s) Thread Manager"""
        self.Login()
        for instance in self.AMPHandler.AMP_Instances:
            server = self.AMPHandler.AMP_Instances[instance]

            # Lets validate our ADS Running before we check for console threads.
            if server.Running and server._ADScheck() and server.ADS_Running:
                # Lets check if the Console Thread is running now.
                if server.Console.console_thread_running == False:
                    self.logger.info(f'{server.FriendlyName}: Starting Console Thread, Instance Online: {server.Running} and ADS Online: {server.ADS_Running}')
                    server.Console.console_thread_running = True

                    if not server.Console.console_thread.is_alive():
                        server.Console.console_thread.start()

            if not server.Running or server.Running and not server.ADS_Running:
                if server.Console.console_thread_running == True:
                    self.logger.error(f'{server.FriendlyName}: Shutting down Console Thread, Instance Online: {server.Running}, ADS Online: {server.ADS_Running}.')
                    server.Console.console_thread_running = False

    def getInstances(self) -> dict:
        """This gets all Instances on AMP."""
        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstances', parameters)
        return result

    def ConsoleUpdate(self) -> dict:
        """Returns `{'ConsoleEntries':[{'Contents': 'String','Source': 'Server thread/INFO','Timestamp': '/Date(1651703130702)/','Type': 'Console'}]`\n
        Will post all updates from previous API call of console update"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetUpdates', parameters)
        return result

    def ConsoleMessage_withUpdate(self, msg: str) -> dict:
        """This will call Console Update after sending the Console Message (Use this for Commands that require feedback)"""
        self.Login()
        parameters = {'message': msg}
        self.CallAPI('Core/SendConsoleMessage', parameters)
        time.sleep(.2)
        update = self.ConsoleUpdate()
        return update

    def ConsoleMessage(self, msg: str):
        """Basic Console Message"""
        self.Login()
        parameters = {'message': msg}
        self.CallAPI('Core/SendConsoleMessage', parameters)
        return

    def StartInstance(self):
        """Starts AMP Instance"""
        self.Login()
        parameters = {}
        self.CallAPI('Core/Start', parameters)
        return

    def StopInstance(self):
        """Stops AMP Instance"""
        self.Login()
        parameters = {}
        self.CallAPI('Core/Stop', parameters)
        return

    def RestartInstance(self):
        """Restarts AMP Instance"""
        self.Login()
        parameters = {}
        self.CallAPI('Core/Restart', parameters)
        return

    def KillInstance(self):
        """Kills AMP Instance"""
        self.Login()
        parameters = {}
        self.CallAPI('Core/Kill', parameters)
        return

    def getStatus(self) -> dict:
        """AMP Instance Status Information"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetStatus', parameters)

        # This happens because CallAPI returns False when it fails permissions.
        if result == False or None:
            return False
        return result

    def getMetrics(self) -> tuple:
        """Returns AMP Instance Metrics \n
        `Uptime str` \n
        `TPS str`  \n
        `Users tuple(str,str)` \n
        `Memory tuple(str, str)` \n
        `CPU str` \n
        """
        Uptime = ''
        TPS = ''
        Users = ('None', 'None')
        Memory = ('None', 'None')
        CPU = ''
        self.Metrics = None

        result = self.getStatus()
        if result == False:
            return TPS, Users, CPU, Memory, Uptime

        Uptime = str(result['Uptime'])
        TPS = str(result['State'])
        Users = (str(result['Metrics']['Active Users']['RawValue']), str(result['Metrics']['Active Users']['MaxValue']))
        Memory = (str(result['Metrics']['Memory Usage']['RawValue']), str(result['Metrics']['Memory Usage']['MaxValue']))
        CPU = str(result['Metrics']['CPU Usage']['RawValue'])  # This is a percentage
        self.Metrics = result['Metrics']
        return TPS, Users, CPU, Memory, Uptime

    def getLiveStatus(self) -> bool:
        """Server is Online and Proper AMP Permissions. \n
        So we check TPS/State to make sure the Dedicated Server is actually 'live'. \n
        `Returns False` when 0 TPS """
        result = self.getStatus()
        if result == False:
            return result

        # This usually happens if the service is offline.
        if isinstance(result, dict) and 'State' in result:
            status = str(result['State'])
            if status == '0':
                return False
            return True
        else:
            return False

    def getUsersOnline(self) -> tuple[str, str]:
        """Returns Number of Online Players over Player Limit. \n
        `eg 2/10`"""
        result = self.getStatus()
        if result != False:
            Users = (str(result['Metrics']['Active Users']['RawValue']), str(result['Metrics']['Active Users']['MaxValue']))
            return Users

    def getUserList(self) -> list[str]:
        """Returns a List of connected users."""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetUserList', parameters)
        user_list = []
        for user in result:
            # for user in result['result']:
            # user_list.append(result['result'][user])
            user_list.append(result[user])
        return user_list

    def getSchedule(self) -> dict:
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetScheduleData', parameters)
        # return result['result']['PopulatedTriggers']
        return result['PopulatedTriggers']

    def setFriendlyName(self, name: str, description: str) -> str:
        """This is used to change an Instance's Friendly Name and or Description. Retains all previous settings. \n
        `This requires the instance to be Offline!`"""
        self.Login()
        parameters = {
            'InstanceId': self.InstanceID,
            'FriendlyName': name,
            'Description': description,
            'StartOnBoot': self.DaemonAutostart,
            'Suspended': self.Suspended,
            'ExcludeFromFirewall': self.ExcludeFromFirewall,
            'RunInContainer': self.IsContainerInstance,
            'ContainerMemory': self.ContainerMemoryMB,
            'MemoryPolicy': self.ContainerMemoryPolicy,
            'ContainerMaxCPU': self.ContainerCPUs}
        response = f'{self.FriendlyName} is about to be changed to {name}; this will restart the instance.'
        self.CallAPI('ADSModule/UpdateInstanceInfo', parameters)
        return response

    def getAPItest(self):
        """Test AMP API calls with this function"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetModuleInfo', parameters)

        return result

    def copyFile(self, source: str, destination: str):
        self.Login()
        parameters = {
            'Origin': source,
            'TargetDirectory': destination
        }
        self.CallAPI('FileManagerPlugin/CopyFile', parameters)
        return

    def renameFile(self, original: str, new: str):
        self.Login()
        parameters = {
            'Filename': original,
            'NewFilename': new
        }
        self.CallAPI('FileManagerPlugin/RenameFile', parameters)
        return

    def getDirectoryListing(self, directory: str) -> list:
        self.Login()
        parameters = {
            'Dir': directory
        }
        result = self.CallAPI('FileManagerPlugin/GetDirectoryListing', parameters)
        return result

    def getFileChunk(self, name: str, position: int, length: int):
        self.Login()
        parameters = {
            'Filename': name,
            'Position': position,
            'Length': length
        }
        result = self.CallAPI('FileManagerPlugin/GetFileChunk', parameters)
        return result

    def writeFileChunk(self, filename: str, position: int, data: str):
        self.Login()
        parameters = {
            'Filename': filename,
            'Position': position,
            'Data': data
        }
        self.CallAPI('FileManagerPlugin/WriteFileChunk', parameters)
        return

    def endUserSession(self, sessionID: str):
        """Ends specified User Session"""
        self.Login()
        parameters = {
            'Id': sessionID
        }
        self.CallAPI('Core/EndUserSession', parameters)
        return

    def getActiveAMPSessions(self) -> dict:
        """Returns currently active AMP Sessions"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetActiveAMPSessions', parameters)
        return result

    def getInstanceStatus(self) -> dict:
        """Returns AMP Instance Status"""
        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstanceStatuses', parameters)
        return result

    def trashDirectory(self, dirname: str):
        """Moves a directory to trash, files must be trashed before they can be deleted."""
        self.Login()
        parameters = {
            'DirectoryName': dirname
        }
        self.CallAPI('FileManagerPlugin/TrashDirectory', parameters)
        return

    def trashFile(self, filename: str):
        """Moves a file to trash, files must be trashed before they can be deleted."""
        self.Login()
        parameters = {
            'Filename': filename
        }
        self.CallAPI('FileManagerPlugin/TrashFile', parameters)
        return

    def emptyTrash(self, trashdir: str):
        """Empties a trash bin for the AMP Instance"""
        self.Login()
        parameters = {
            'TrashDirectoryName': trashdir
        }
        self.CallAPI('FileManagerPlugin/EmptyTrash', parameters)
        return

    def takeBackup(self, title: str, description: str, sticky: bool = False):
        """Takes a backup of the AMP Instance; default `sticky` is False!"""
        self.Login()
        parameters = {
            "Title": title,
            "Description": description,
            "Sticky": sticky
        }
        self.CallAPI('LocalFileBackupPlugin/TakeBackup', parameters)
        return

    def getAMPUserInfo(self, name: str) -> Union[str, dict]:
        """Gets AMP user info. if IdOnly is True; returns AMP User ID only!"""
        self.Login()
        parameters = {
            'Username': name
        }
        result = self.CallAPI('Core/GetAMPUserInfo', parameters)
        return result

    def getAMPUserID(self, name: str):
        """Returns AMP Users ID Only."""
        result = self.getAMPUserInfo(name=name)
        # return result['result']['ID']
        return result['ID']

    def CurrentSessionHasPermission(self, PermissionNode: str) -> dict:
        """Gets current Sessions permission spec"""
        self.Login()
        parameters = {
            'PermissionNode': PermissionNode
        }
        result = self.CallAPI('Core/CurrentSessionHasPermission', parameters)
        if result != False:
            # return result['result']
            return result

        return result

    def getAMPRolePermissions(self, RoleID: str) -> dict:
        """Gets full permission spec for Role (returns permission nodes)"""
        self.Login()
        parameters = {
            'RoleId': RoleID
        }
        result = self.CallAPI('Core/GetAMPRolePermissions', parameters)
        return result

    def getPermissions(self) -> dict:
        """Gets full Permission spec for self"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetPermissionsSpec', parameters)
        return result

    def getRoleIds(self) -> dict:
        """Gets a List of all Roles, if set_roleID is true; it checks for `Gatekeeper` and `Super Admins`. Sets them to self.AMP_BotRoleID and self.super_AdminID"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetRoleIds', parameters)
        # return result['result']
        return result

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

    def createRole(self, name: str, AsCommonRole=False):
        """Creates a AMP User role"""
        self.Login()
        parameters = {
            'Name': name,
            'AsCommonRole': AsCommonRole
        }
        result = self.CallAPI('Core/CreateRole', parameters)
        return result

    def getRole(self, Roleid: str):
        """Gets the AMP Role"""
        self.Login()
        parameters = {
            'RoleId': Roleid
        }
        result = self.CallAPI('Core/GetRole', parameters)
        return result

    def setAMPUserRoleMembership(self, UserID: str, RoleID: str, isMember: bool):
        """ Sets the AMP Users Role Membership"""
        self.Login()
        parameters = {
            'UserId': UserID,
            'RoleId': RoleID,
            'IsMember': isMember
        }
        result = self.CallAPI('Core/SetAMPUserRoleMembership', parameters)
        return result

    def setAMPRolePermissions(self, RoleID: str, PermissionNode: str, Enabled: bool):
        """Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`"""
        self.Login()
        parameters = {
            'RoleId': RoleID,
            'PermissionNode': PermissionNode,
            'Enabled': Enabled
        }
        result = self.CallAPI('Core/SetAMPRolePermission', parameters)

        # if result['result']['Status'] == False:
        if result['Status'] == False:
            self.logger.critical(f'Unable to Set Permission Node __{PermissionNode}__ to `{Enabled}` for {RoleID}')
            return False

        return True

    def getUpdateInfo(self):
        self.Login()
        parameters = {}
        result = self.CallAPI("Core/GetUpdateInfo", parameters)
        return result

    # These are GENERIC Methods below this point purely for typehiting and Linter purpose. ---------------------------------------------------------------------------

    def addWhitelist(self, db_user, in_gamename: str = None):
        """Base Function for AMP.addWhitelist"""
        # Use the DB_User object and get the required IGN depending on the server type.
        return False

    def getWhitelist(self) -> dict[str, str]:
        """Base Function for AMP.getWhitelist"""
        return

    def removeWhitelist(self, db_user: Union[None, DB.DBUser] = None, in_gamename: str = None):
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
