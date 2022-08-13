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
from argparse import Namespace
import requests
import requests.sessions
import pyotp  # 2Factor Authentication Python Module
import json
import time
from pprint import pprint
import sys
import pathlib
from datetime import datetime, timezone
import logging
import threading
import importlib.util
import os
import discord
import re

import DB

#import utils
Handler = None


class AMPHandler():
    def __init__(self, client: discord.Client, args: Namespace):
        self.args = args
        # print(self.args)
        self.logger = logging.getLogger()
        #self._client = client
        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.AMP2FA = False
        self.tokens = ''

        self.superUser = False

        self.SessionIDlist = {}

        self.AMP_Instances = {}
        self.AMP_Instances_Names = []
        self.AMP_Modules = {}

        self.AMP_Console_Modules = {}
        self.AMP_Console_Threads = {}

        self.SuccessfulConnection = False
        self.InstancesFound = False

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.val_settings()
        self.moduleHandler()

    def setup_AMPInstances(self):
        """Intializes the connection to AMP and creates AMP_Instance objects."""
        self.AMP = AMPInstance(Handler=self)
        # pprint(self.AMP.getAMPRolePermissions(self.AMP.AMP_BotRoleID))
        self.AMP_Instances = self.AMP.getInstances()
        self.get_AMP_instance_names()
        #pprint(self.AMP.getAMPRolePermissions(self.AMP.AMP_BotRoleID))

        # This removes Super Admins from the bot user! Controlled through parser args!
        if self.args.super or not self.args.dev:
            self.AMP.setAMPUserRoleMembership(self.AMP.AMP_UserID, self.AMP.super_AdminID, False)
            self.logger.warning(f'***ATTENTION*** Removing {self.tokens.AMPUser} from `Super Admins` Role!')
    
    def get_AMP_instance_names(self):
        for server in self.AMP_Instances:
            if self.AMP_Instances[server].DisplayName != None:
                self.AMP_Instances_Names.append(self.AMP_Instances[server].DisplayName)
            else:
                self.AMP_Instances_Names.append(self.AMP_Instances[server].FriendlyName)

    def AMP_instanceCheck(self):
        """Checks for any new Instances since after startup. \n
        This keeps the AMP_Instance Dictionary Current
        This also adds any new Instances to the Database"""
        self.logger.dev('AMP Instance Update in progress...')
        AMP_instance_check = self.AMP.getInstances()
        for instance in AMP_instance_check:
            if instance not in self.AMP_Instances:
                new_server = AMP_instance_check[instance]
                self.AMP_Instances[AMP_instance_check[instance]] #Add the new instance to the original server list.
                if self.DB.GetServer(new_server.InstanceID) == None:
                    self.logger.warn(f'Found a new Instance during Runtime - Adding {new_server.FriendlyName} to our Instance List and Database.')
                    self.DB.AddServer(InstanceID= new_server.InstanceID,InstanceName= new_server.FriendlyName)
    
    #Checks for Errors in Config
    def val_settings(self):
        """Validates the tokens.py settings and 2FA."""
        self.logger.info('AMPHandler is validating your token file...')
        reset = False

        if not self.args.token:
            if self._cwd.joinpath('tokenstemplate.py').exists() or not self._cwd.joinpath('tokens.py').exists():
                self.logger.critical('**ERROR** Please rename your tokenstemplate.py file to tokens.py before trying again.')
                reset = True

        import tokens
        self.tokens = tokens
        if not tokens.AMPurl.startswith('http://'):
            self.logger.critical('** Please Append "http://" at the start of your AMPurl.')
            reset = True
            
        if tokens.AMPurl.endswith('/') or tokens.AMPurl.endswith('\\'):
            tokens.AMPurl = tokens.AMPurl.replace('/', '').replace('\\', '')

        if len(tokens.AMPAuth) < 7:
            if tokens.AMPAuth == '':
                self.AMP2FA = False
                return
            else:
                self.logger.critical('**ERROR** Please use your 2 Factor Generator Code (Should be over 25 characters long), not the 6 digit numeric generated code that expires with time.')
                reset = True

        if reset:
            input("Press any Key to Exit")
            sys.exit(0)

        self.AMP2FA = True

    def moduleHandler(self):
        """AMPs class Loader for specific server types."""
        # traceback.print_stack()
        self.logger.dev('AMPHandler moduleHandler loading modules...')
        try:
            dir_list = self._cwd.joinpath('modules').iterdir()
            for folder in dir_list:
                file_list = folder.glob('amp_*.py')
                for script in file_list:
                    module_name = script.name[4:-3].capitalize()
                    try:
                        # print(script)
                        spec = importlib.util.spec_from_file_location(module_name, script)
                        class_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(class_module)

                        # self.AMP_Modules[module_name] = getattr(class_module,f'AMP{module_name}')
                        # self.AMP_Console_Modules[module_name] = getattr(class_module,f'AMP{module_name}Console')
                        #!TODO! This may change in the future. Depends on the table update.
                        for DIS in getattr(class_module, 'DisplayImageSources'):
                            self.AMP_Modules[DIS] = getattr(class_module, f'AMP{module_name}')
                            self.AMP_Console_Modules[DIS] = getattr(class_module, f'AMP{module_name}Console')

                        self.logger.dev(f'**SUCCESS** {self.name} Loading AMP Module **{module_name}**')

                    except Exception as e:
                        self.logger.error(f'**ERROR** {self.name} Loading AMP Module **{module_name}** - {e}')
                        continue

        except Exception as e:
            self.logger.error(f'**ERROR** {self.name} Loading AMP Module ** - File Not Found {e}')


def getAMPHandler(client: discord.Client = None, args: bool = False) -> AMPHandler:
    global Handler
    if Handler is None:
        Handler = AMPHandler(client=client, args=args)
    return Handler


class AMPInstance:
    """Base class for AMP"""

    def __init__(self, instanceID=0, serverdata={}, Index=0, default_console=False, Handler=None):
        self.logger = logging.getLogger()

        self.AMPHandler = Handler
        if self.AMPHandler is None:
            self.AMPHandler = getAMPHandler()

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB

        self.SessionID = 0
        self.Index = Index
        self.serverdata = serverdata
        self.serverlist = {}
        self.InstanceID = instanceID
        self.ADS_Running = False  # This is for the ADS (Dedicated Server) not the Instance!

        self.url = self.AMPHandler.tokens.AMPurl + '/API/'  # base url for AMP console /API/

        if not hasattr(self, "perms"):
            self.perms = ['Core.*', 'Core.RoleManagement.*', 'Core.UserManagement.*', 'Instances.*', 'ADS.*',
                          'Settings.*', 'ADS.InstanceManagement.*', 'FileManager.*', 'LocalFileBackup.*', 'Core.AppManagement.*']
        if not hasattr(self, 'APIModule'):
            self.APIModule = 'AMP'

        self.super_AdminID = None
        self.AMP_BotRoleID = None

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
            self.Console = AMPConsole(self)

        if instanceID != 0:
            # This gets all the dictionary values tied to AMP and makes them attributes
            for entry in serverdata:
                setattr(self, entry, serverdata[entry])

            # This cleans up the friendly name making it easier to use.
            self.FriendlyName = self.FriendlyName.replace(' ', '_')

            # This gets me the DB_Server object if it's not there; it adds the server.
            self.DB_Server = self.DB.GetServer(InstanceID=self.InstanceID)
            # Possible DB_Server Attributes = InstanceID, InstanceName, DisplayName, Description, IP, Whitelist, Donator, Console_Flag, Console_Filtered, Discord_Console_Channel, Discord_Chat_Channel, Discord_Role
            if self.DB_Server is None:
                self.DB_Server = self.DB.AddServer(InstanceID=self.InstanceID, InstanceName=self.FriendlyName)
                self.logger.info(f'*SUCCESS** Added {self.FriendlyName} to the Database.')
            else:
                self.logger.info(f'**SUCCESS** Found {self.FriendlyName} in the Database.')

            self.logger.dev(f"Name: {self.FriendlyName} // InstanceID: {self.InstanceID} // Module: {self.Module} // Port: {self.Port} // DisplayImageSource: {self.DisplayImageSource}")

            # This sets all my DB_Server attributes.
            self.attr_update()

        # Lets see if we are the main AMP or if the Instance is Running
        if instanceID == 0 or self.Running:
            if self.check_AMPpermissions():  # We either have to have super or our bot role perms has been set manually!
                self.AMP_userinfo = self.getAMPUserInfo(self.AMPHandler.tokens.AMPUser)  # This gets my AMP User Information
                self.AMP_UserID = self.getAMPUserInfo(self.AMPHandler.tokens.AMPUser, True)  # This gets my AMP User ID
                self.getRoleIds(True)  # This checks for Super Admins role and discord_bot role
                # print('Bot Role ID:',self.AMP_BotRoleID)
                # print('Super Admin?',self.super_AdminID in self.AMP_userinfo['result']['Roles'])
                # print('Bot Role?', self.AMP_BotRoleID not in self.AMP_userinfo['result']['Roles'])
                # print('InstanceID:', instanceID)

                # Bot role doesn't exists, but we have Super Admin!
                if self.AMP_BotRoleID is None and self.super_AdminID in self.AMP_userinfo['result']['Roles']:
                    self.logger.warning('***ATTENTION*** We have `Super Admins`, setting up AMP Permissions and creating `discord_bot` role!')
                    self.setup_AMPbotrole()
                    self.setup_AMPpermissions()

                # Bot role doesn't exists and we do not have Super Admin!
                if self.AMP_BotRoleID is None and self.super_AdminID not in self.AMP_userinfo['result']['Roles']:
                    self.logger.critical(
                        '***ATTENTION*** AMP is missing the role `discourd_bot`, Please create a role under "Configuration -> Role Management" called `discord_bot` or give the bot user `Super Admins`, then restart the bot.')

                # Bot role exists but we do not have discord_bot role and we do not have Super Admin!
                if self.AMP_BotRoleID is not None and self.AMP_BotRoleID not in self.AMP_userinfo['result']['Roles'] and self.super_AdminID not in self.AMP_userinfo['result']['Roles']:
                    self.logger.critical(
                        f'***ATTENTION*** {self.AMPHandler.tokens.AMPUser}is missing the role `discourd_bot`, Please set the role under "Configuration -> Role Management", then restart the bot.')

                # Bot role exists but we do not have discord_bot role and we have Super Admin!
                # Give myself the role here
                if self.AMP_BotRoleID is not None and self.AMP_BotRoleID not in self.AMP_userinfo['result']['Roles'] and self.super_AdminID in self.AMP_userinfo['result']['Roles']:
                    self.logger.warning('***ATTENTION*** Adding `discord_bot` to our roles!')
                    self.setAMPUserRoleMembership(self.AMP_UserID, self.AMP_BotRoleID, True)

                # Not the main AMP Instance and the Bot Role Exists and we have the discord_bot role and we have super also!
                if instanceID != 0 and self.AMP_BotRoleID is not None and self.AMP_BotRoleID in self.AMP_userinfo['result']['Roles'] and self.super_AdminID in self.AMP_userinfo['result']['Roles']:
                    self.logger.warning(f'***ATTENTION*** `discord_bot` role exists and we have `Super Admins` - Setting up Instance permissions for {self.FriendlyName}')
                    self.setup_AMPpermissions()

            else:
                self.logger.critical(f'***ATTENTION*** We are missing permissions for {self.APIModule}! Please consider giving us `Super Admins` and the bot will set its own permissions and role!')
                # If the main AMP is missing permissions; lets quit!
                if instanceID == 0:
                    sys.exit(1)

    def setup_AMPbotrole(self):
        """Creates the `discord_bot` role."""
        self.logger.warning('Creating the AMP role `discord_bot`.')
        self.createRole('discord_bot')
        self.getRoleIds(True)
        self.logger.dev(f'Created `discord_bot` role. ID: {self.AMP_BotRoleID}')
        self.AMP_UserID = self.getAMPUserInfo(self.AMPHandler.tokens.AMPUser, True)
        self.setAMPUserRoleMembership(self.AMP_UserID, self.AMP_BotRoleID, True)
        self.logger.warning(f'***ATTENTION*** Adding {self.AMPHandler.tokens.AMPUser} to `discord_bot` Role.')

    def setup_AMPpermissions(self):
        """Sets the Permissions for main AMP Module"""
        self.logger.info('Setting AMP permissions...')
        import amp_permissions as AMPPerms
        core = AMPPerms.perms_super()
        for perm in core:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]
            self.setAMPRolePermissions(self.AMP_BotRoleID, perm, enabled)
            self.logger.dev(f'Set {perm} for {self.AMP_BotRoleID} to {enabled}')
        return

    def check_AMPpermissions(self):
        """These check the permissions for AMP Modules"""
        self.logger.warning(f'Checking {self.APIModule} for proper permissions...')
        failed = False
        for perm in self.perms:
            # Skip the perm check on ones we "shouldn't have!"
            if perm.startswith('-'):
                continue
            has_permission = self.CurrentSessionHasPermission(perm)

            self.logger.dev(f'Permission check on __{perm}__ is: {has_permission}')

            if not has_permission:
                if self.APIModule == 'AMP':
                    self.logger.warning(f'The Bot is missing the permission {perm} Please check under Configuration -> User Management for the Bot.')
                else:
                    end_point = self.AMPHandler.tokens.AMPurl.find(":", 5)
                    self.logger.warning(
                        f'The Bot is missing the permission {perm} Please visit {self.AMPHandler.tokens.AMPurl[:end_point]}:{self.Port} under Configuration -> Role Management -> discord_bot')
                failed = True

        if failed:
            self.logger.critical('***ATTENTION*** The Bot is missing permissions, some or all functionality may not work properly!')
            # Please see this image for the required bot user Permissions **(Github link to AMP Basic Perms image here)**
            return False

        return True

    def attr_update(self):
        """This will update AMP Instance attributes."""
        # Need to call this every so often. Possibly anytime I get instance information/update instance information
        self.logger.dev(f'Updating Server Attributes - Instance Running: {self.Running}')
        self.DB_Server = self.DB.GetServer(InstanceID=self.InstanceID)

        if self.Running:
            server_status = self.server_check()  # Using this to see if the API fails to set the server status (offline/online) NOT THE INSTANCE STATUS! Thats self.Running!!
            self.logger.dev(f'{self.FriendlyName} ADS Running: {server_status}')
            self.ADS_Running = server_status

        self.DisplayName = self.DB_Server.DisplayName
        self.Description = self.DB_Server.Description
        self.IP = self.DB_Server.IP
        self.Whitelist = self.DB_Server.Whitelist
        self.Donator = self.DB_Server.Donator
        self.Console_Flag = self.DB_Server.Console_Flag  # This should be default to True
        self.Console_Filtered = self.DB_Server.Console_Filtered
        self.Discord_Console_Channel = self.DB_Server.Discord_Console_Channel
        self.Discord_Chat_Channel = self.DB_Server.Discord_Chat_Channel
        self.Discord_Role = self.DB_Server.Discord_Role
        self.Discord_Reaction = self.DB_Server.Discord_Reaction

    def server_check(self):
        """Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP INSTANCE!"""
        Success = self.Login()
        self.logger.dev('Server Check Login Sucess: ' + str(Success))
        if Success and self.getStatus(True):
            return True

        return False

    def Login(self):
        if self.SessionID == 0:
            if self.InstanceID in self.AMPHandler.SessionIDlist:
                self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
                # return func(*args, **kargs)
                return

            self.logger.dev(f'AMPInstance Logging in {self.InstanceID}')

            if self.AMP2Factor is not None:
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
                self.SessionID = result['sessionID']
                self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
                self.Running = True

            except Exception:
                self.logger.warning(f'{self.FriendlyName} - Instance is Offline')
                self.Running = False
                return False
        return True

    def CallAPI(self, APICall, parameters):
        #global SuccessfulConnection
        self.logger.dev(f'Function {APICall} was called with {parameters} by {self.InstanceID}')

        if self.SessionID != 0:
            parameters['SESSIONID'] = self.SessionID
        jsonhandler = json.dumps(parameters)

        while(True):
            try:
                post_req = requests.post(self.url + APICall, headers=self.AMPheader, data=jsonhandler)

                if len(post_req.content) > 0:
                    break

                # Since we are using GetUpdates every second for Console Updates; lets ignore them here so we don't sleep our thread.
                if APICall == 'Core/GetUpdates':
                    break

                self.logger.error(f'{self.FriendlyName}: AMP API recieved no Data; sleeping for 5 seconds...')
                time.sleep(5)

            except Exception:
                if not self.AMPHandler.SuccessfulConnection:
                    self.logger.critical('Unable to connect to URL; please check Tokens.py -> AMPURL')
                    sys.exit(-1)
                self.logger.warning('AMP API was unable to connect; sleeping for 30 seconds...')
                time.sleep(30)

        self.AMPHandler.SuccessfulConnection = True

        # Error catcher for API calls
        post_req_json = post_req.json()
        if type(post_req_json) is None:
            self.logger.error(f"AMP_API CallAPI ret is 0: status_code {post_req.status_code}")
            self.logger.error(post_req.raw)

        self.logger.debug(f'Post Request Prints: {post_req_json}')

        if post_req_json is None:
            return

        # Permission errors will trigger this, unsure what else.
        if "result" in post_req_json:

            if type(post_req_json['result']) == bool and post_req_json['result']:
                return post_req_json

            if type(post_req_json['result']) == bool and not post_req_json['result']:
                self.logger.error(f'The API Call {APICall} failed because of {post_req_json}')
                return post_req_json

            if type(post_req_json['result']) == bool and "Status" in post_req_json['result'] and not post_req_json['result']['Status']:
                self.logger.error(f'The API Call {APICall} failed because of {post_req_json}')
                return False

        if "Title" in post_req_json:
            if type(post_req_json['Title']) == str and post_req_json['Title'] == 'Unauthorized Access':
                self.logger.error(f'["Title"]: The API Call {APICall} failed because of {post_req_json}')
                return False

        return post_req_json

    def getInstances(self):
        """This gets all Instances on AMP and puts them into a dictionary.\n {'InstanceID': AMPAPI class}"""
        global InstancesFound
        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstances', parameters)
        # pprint(result)
        serverlist = {}
        if len(result["result"][0]['AvailableInstances']) != 0:

            InstancesFound = True
            for i in range(0, len(result["result"][0]['AvailableInstances'])):  # entry = name['result']['AvailableInstances'][0]['InstanceIDs']
                instance = result["result"][0]['AvailableInstances'][i]

                # This exempts the AMPTemplate Gatekeeper *hopefully*
                flag_reg = re.search("(gatekeeper)", instance['FriendlyName'].lower())
                if flag_reg is not None:
                    if flag_reg.group():
                        continue

                #!TODO! This may change when and IF AMP adds a better table value for unique Server types!
                if instance['DisplayImageSource'] in self.AMPHandler.AMP_Modules:
                    name = str(self.AMPHandler.AMP_Modules[instance["DisplayImageSource"]]).split("'")[1]
                    self.logger.dev(f'Loaded __{name}__ for {instance["FriendlyName"]}')
                    # def __init__(self, instanceID = 0, serverdata = {}, Index = 0, default_console = False, Handler = None):
                    server = self.AMPHandler.AMP_Modules[instance['DisplayImageSource']](instance['InstanceID'], instance, i, self.AMPHandler)
                    serverlist[server.InstanceID] = server

                else:
                    self.logger.dev(f'Loaded __AMP_Generic__ for {instance["FriendlyName"]}')
                    server = self.AMPHandler.AMP_Modules['Generic'](instance['InstanceID'], instance, i, self.AMPHandler)
                    serverlist[server.InstanceID] = server

            return serverlist

        else:
            InstancesFound = False
            self.logger.critical('***ATTENTION*** Please ensure the permissions are set correctly, the Bot cannot find any AMP Instances at this time...')
            time.sleep(30)

    def ConsoleUpdate(self) -> dict:
        """Returns `{'ConsoleEntries':[{'Contents': 'String','Source': 'Server thread/INFO','Timestamp': '/Date(1651703130702)/','Type': 'Console'}]`\n
        Will post all updates from previous API call of console update"""
        parameters = {}
        result = self.CallAPI('Core/GetUpdates', parameters)
        return result

    def ConsoleMessage_withUpdate(self, msg: str) -> dict:
        """This will call Console Update after sending the Console Message (Use this for Commands that require feedback)"""
        parameters = {'message': ' '.join(msg)}
        self.CallAPI('Core/SendConsoleMessage', parameters)
        time.sleep(0.5)
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

    def getStatus(self, running_check: bool = False, users_only: bool = False) -> tuple:
        """AMP Instance Metrics \n
        CPU is percentage based <tuple>
        """
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetStatus', parameters)

        # This happens because CallAPI returns False when it fails permissions.
        if not result:
            return False

        # This works if I had permission and the server is online, but not actually running. So we check TPS to make sure the server is actually 'live'
        if running_check and result:
            status = str(result['State'])
            return status != '0'

        # If we want to check ONLY online users!
        if users_only:
            Users = (str(result['Metrics']['Active Users']['RawValue']), str(result['Metrics']['Active Users']['MaxValue']))
            return Users

        Uptime = str(result['Uptime'])
        tps = str(result['State'])
        Users = (str(result['Metrics']['Active Users']['RawValue']), str(result['Metrics']['Active Users']['MaxValue']))
        Memory = (str(result['Metrics']['Memory Usage']['RawValue']), str(result['Metrics']['Memory Usage']['MaxValue']))
        cpu = str(result['Metrics']['CPU Usage']['RawValue'])  # This is a percentage
        self.Metrics = result['Metrics']
        return tps, Users, cpu, Memory, Uptime

    def getUserList(self) -> list:
        """Returns a List of connected users."""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetUserList', parameters)
        user_list = []
        for user in result['result']:
            user_list.append(result['result'][user])
        return user_list

    def getSchedule(self) -> dict:
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetScheduleData', parameters)
        return result['result']['PopulatedTriggers']

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
            'ContainerMaxCPU': self.ContainerCPUs
        }
        response = f'{self.FriendlyName} is about to be changed to {name}; this will restart the instance.'
        self.CallAPI('ADSModule/UpdateInstanceInfo', parameters)
        return response

    def getAPItest(self):
        """Test AMP API calls with this function"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetModuleInfo', parameters)
        pprint(result)
        return result

    def copyFile(self, source, destination):
        self.Login()
        parameters = {
            'Origin': source,
            'TargetDirectory': destination
        }
        self.CallAPI('FileManagerPlugin/CopyFile', parameters)
        return

    def renameFile(self, original, new):
        self.Login()
        parameters = {
            'Filename': original,
            'NewFilename': new
        }
        self.CallAPI('FileManagerPlugin/RenameFile', parameters)
        return

    def getDirectoryListing(self, directory):
        self.Login()
        parameters = {
            'Dir': directory
        }
        result = self.CallAPI('FileManagerPlugin/GetDirectoryListing', parameters)
        return result

    def getFileChunk(self, name, position, length):
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
            'Title': title,
            'Description': description,
            'Sticky': sticky
        }
        self.CallAPI('LocalFileBackupPlugin/TakeBackup', parameters)
        return

    def getAMPUserInfo(self, name: str, IdOnly=False):
        """Gets AMP user info. if IdOnly is True; returns AMP User ID only!"""
        self.Login()
        parameters = {
            'Username': name
        }
        result = self.CallAPI('Core/GetAMPUserInfo', parameters)
        if IdOnly:
            return result['result']['ID']
        return result

    def CurrentSessionHasPermission(self, PermissionNode: str):
        """Gets current Sessions permission spec"""
        self.Login()
        parameters = {
            'PermissionNode': PermissionNode
        }
        result = self.CallAPI('Core/CurrentSessionHasPermission', parameters)

        if result:
            return result['result']

        return result

    def getAMPRolePermissions(self, RoleID: str):
        """Gets full permission spec for Role (returns permission nodes)"""
        self.Login()
        parameters = {
            'RoleId': RoleID
        }
        result = self.CallAPI('Core/GetAMPRolePermissions', parameters)
        return result

    def getPermissions(self):
        """Gets full Permission spec for self"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetPermissionsSpec', parameters)
        return result

    def getRoleIds(self, set_roleID=False):
        """Gets a List of all Roles, if set_roleID is true; it checks for `discord_bot` and `Super Admins`. Sets them to self.AMP_BotRoleID and self.super_AdminID"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetRoleIds', parameters)

        if set_roleID:
            roles = result['result']
            for role in roles:
                if roles[role] == 'discord_bot':
                    self.AMP_BotRoleID = role
                    #print('AMP Bot Role',self.AMP_BotRoleID,role)

                if roles[role] == 'Super Admins':
                    self.super_AdminID = role
                    #print('Super Admin',self.super_AdminID,role)

            if self.AMP_BotRoleID is None:
                return False

            if self.AMP_BotRoleID is not None and self.super_AdminID is not None:
                return True

        return result['result']

    def createRole(self, name: str, AsCommonRole=False):
        """Creates a AMP User role"""
        self.Login()
        parameters = {
            'Name': name,
            'AsCommonRole': AsCommonRole
        }
        result = self.CallAPI('Core/CreateRole', parameters)
        pprint(result)
        return result

    def getRole(self, Roleid: str):
        """Gets the AMP Role"""
        self.Login()
        parameters = {
            'RoleId': Roleid
        }
        result = self.CallAPI('Core/GetRole', parameters)
        return result

    def setAMPUserRoleMembership(self, UserID, RoleID, isMember: bool):
        """ Sets the AMP Users Role Membership"""
        self.Login()
        parameters = {
            'UserId': UserID,
            'RoleId': RoleID,
            'IsMember': isMember
        }
        result = self.CallAPI('Core/SetAMPUserRoleMembership', parameters)
        return result

    def setAMPRolePermissions(self, RoleID, PermissionNode: str, Enabled: bool):
        """Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`"""
        self.Login()
        parameters = {
            'RoleId': RoleID,
            'PermissionNode': PermissionNode,
            'Enabled': Enabled
        }
        result = self.CallAPI('Core/SetAMPRolePermission', parameters)
        if not result['result']:
            self.logger.critical(f'Unable to Set permissions {result}')
        return result

    # These are GENERIC Methods below this point ---------------------------------------------------------------------------
    def addWhitelist(self, user):
        """Base Function for AMP.addWhitelist"""
        return user

    def getWhitelist(self):
        """Base Function for AMP.getWhitelist"""
        return

    def removeWhitelist(self, user):
        """Base Function for AMP.removeWhitelist"""
        return user

    def name_Conversion(self, user):
        """Base Function for AMP.name_Conversion"""
        return user

    def name_History(self, user):
        """Base Function for AMP.name_History"""
        return user

    def check_Whitelist(self, user_id: str):
        """Base Funcion for AMP.check_Whitelist `default return is FALSE`"""
        return False

    def send_message(self, message):
        """Base Function for Discord Chat Messages to AMP ADS"""
        return

    def discord_message(self, user):
        """Base Function for customized discord messages"""
        return False


class AMPConsole:
    def __init__(self, AMPInstance=AMPInstance):
        self.logger = logging.getLogger()

        self.AMPInstance = AMPInstance
        self.AMPHandler = getAMPHandler()
        self.AMP_Console_Threads = self.AMPHandler.AMP_Console_Threads

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig
        self.DB_Server = self.DB.GetServer(InstanceID=self.AMPInstance.InstanceID)

        self.console_thread = None
        self.console_thread_running = False

        self.console_messages = []
        self.console_message_list = []
        self.console_message_lock = threading.Lock()

        self.console_chat_messages = []
        self.console_chat_messages_list = []
        self.console_chat_message_lock = threading.Lock()

        self.logger.dev(f'**SUCCESS** Setting up {self.AMPInstance.FriendlyName} Console')
        self.console_init()

    def console_init(self):
        """This starts our console threads..."""
        if self.AMPInstance.Console_Flag:
            try:
                # self.AMP_Modules[DIS] = getattr(class_module,f'AMP{module_name}')
                # self.AMP_Console_Modules[DIS] = getattr(class_module,f'AMP{module_name}Console')
                if self.AMPInstance.DisplayImageSource in self.AMPHandler.AMP_Console_Modules:  # Should be AMP_Console_Modules: {Module_Name: 'Module_class_object'}
                    if self.AMPInstance.ADS_Running:  # This is the Instance's ADS
                        self.logger.dev(f'Loaded {self.AMPHandler.AMP_Console_Modules[self.AMPInstance.DisplayImageSource]} for {self.AMPInstance.FriendlyName}')

                        self.console_thread_running = True

                        # This starts the console parse on our self in a seperate thread.
                        self.console_thread = threading.Thread(target=self.console_parse, name=self.AMPInstance.FriendlyName)

                        # This adds the AMPConsole Thread Object into a dictionary with the key value of AMPInstance.InstanceID
                        self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.console_thread
                        self.console_thread.start()
                        self.logger.dev(f'**SUCCESS** Starting Console Thread for {self.AMPInstance.FriendlyName}...')

                    else:
                        self.logger.warning(f'**ATTENTION** Server: {self.AMPInstance.FriendlyName} ADS is not currently Running, unable to Start Console Thread.')

                else:  # If we can't find the proper module; lets load the Generic.
                    if self.AMPInstance.ADS_Running:  # This is the Instance's ADS
                        self.logger.dev(f'Loaded for {self.AMPHandler.AMP_Console_Modules["Generic"]} for {self.AMPInstance.FriendlyName}')
                        #server_console = self.AMP_Console_Modules['Generic']
                        self.console_thread_running = True
                        self.console_thread = threading.Thread(target=self.console_parse, name=self.AMPInstance.FriendlyName)
                        self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.console_thread
                        self.console_thread.start()
                        self.logger.dev(f'**SUCCESS** Starting Console Thread for {self.AMPInstance.FriendlyName}...')

                    else:
                        self.logger.warning(f'**ATTENTION** Server: {self.AMPInstance.FriendlyName} ADS is not currently Running, unable to Start Console Thread.')

            except Exception as e:
                self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.AMPHandler.AMP_Console_Modules['Generic']
                self.logger.critical(f'**ERROR** Failed to Start the Console for {self.AMPInstance.FriendlyName}...with {e}')

    def console_parse(self):
        """This handles AMP Console Updates; turns them into bite size messages and sends them to Discord"""
        time.sleep(5)
        last_entry_time = 0
        while(self.console_thread_running):
            time.sleep(1)
            console = self.AMPInstance.ConsoleUpdate()

            for entry in console['ConsoleEntries']:
                # This prevents old messages from getting handled again and spamming on restart.
                entry_time = datetime.fromtimestamp(float(entry['Timestamp'][6:-2]) / 1000, tz=timezone.utc)
                if last_entry_time == 0:
                    last_entry_time = entry_time
                    break

                if entry_time < last_entry_time:
                    last_entry_time = entry_time
                    continue

                self.logger.dev(f'Name: {self.AMPInstance.FriendlyName} DisplayImageSource: {self.AMPInstance.DisplayImageSource} Console Entry: {entry}')
                self.logger.dev(f"Console Channel: {self.AMPInstance.Discord_Console_Channel} Chat Channel: {self.AMPInstance.Discord_Chat_Channel}")

                # This should handle server events(such as join/leave/disconnects)
                #print('Console Events')
                if self.console_events(entry):
                    continue

                # This will vary depending on the server type.
                # I don't want to filter out the chat message here though. Just send it to two different places!
                #print('Console Chat')
                if self.console_chat(entry):
                    continue

                # This will filter any messages such as errors or mods loading, etc..
                #print('Console Filter')
                if self.console_filter(entry):
                    print(f"Filtered message {entry}")
                    continue

                if len(entry['Contents']) > 1500:
                    index_hunt = entry['Contents'].find(';')
                    if index_hunt == -1:
                        continue

                    msg_len_index = entry['Contents'].rindex(';')

                    while msg_len_index > 1500:
                        msg_len_indexend = msg_len_index
                        msg_len_index = entry['Contents'].rindex(';', 0, msg_len_indexend)

                        if msg_len_index < 1500:
                            newmsg = entry['Contents'][0:msg_len_index]
                            self.console_message_list.append(newmsg.lstrip())
                            entry['Contents'] = entry['Contents'][msg_len_index + 1:len(entry['Contents'])]
                            msg_len_index = len(entry['Contents'])
                            continue
                else:
                    self.console_message_list.append(entry['Contents'])

            if len(self.console_message_list) > 0:
                bulkentry = ''
                for entry in self.console_message_list:
                    if len(bulkentry + entry) < 1500:
                        bulkentry = bulkentry + entry + '\n'

                    else:
                        self.console_message_lock.acquire()
                        self.console_messages.append(bulkentry[:-1])
                        self.console_message_lock.release()
                        self.logger.debug(self.AMPInstance.FriendlyName + bulkentry[:-1])
                        bulkentry = entry + '\n'

                if len(bulkentry):
                    self.console_message_lock.acquire()
                    self.console_messages.append(bulkentry[:-1])
                    self.console_message_lock.release()
                    self.logger.debug(self.AMPInstance.FriendlyName + bulkentry[:-1])

            self.console_message_list = []

    def console_filter(self, message):
        """This will filter depending on the console_filter setting and handle what to send to Discord."""
        return False

    def console_chat(self, message):
        """This will handle all player chat messages from AMP to Discord"""
        # **EXAMPLE** Name: ARK_-_Lost_Island DisplayImageSource: steam:346110 Console Entry:
        #{'Timestamp': '/Date(1657587898574)/', 'Source': 'IceOfWraith', 'Type': 'Chat', 'Contents': 'This is a local message'}

        # Currently all servers set "Type" to Chat! So lets use those.
        if message["Type"] == 'Chat':
            print('Found a Chat message')

            #Removed the odd character for color idicators on text
            message = message.replace('�','')

            self.console_chat_message_lock.acquire()
            self.console_chat_messages.append(message)
            self.console_chat_message_lock.release()

            self.console_message_lock.acquire()
            self.console_messages.append(f"{message['Source']}: {message['Contents']}")
            self.console_message_lock.release()
            return True
        return False

    def console_events(self, message):
        """This will handle all player join/leave/disconnects and other achievements. THIS SHOULD ALWAYS RETURN FALSE!"""
        return False
