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
#AMP API 
# by k8thekat // Lightning
# 11/10/2021
from argparse import Namespace
import requests
import requests.sessions
import pyotp # 2Factor Authentication Python Module
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
from typing import Union

import DB

#import utils
Handler = None


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
    def __init__(self, instanceID=0, serverdata={}, default_console=False, Handler=None):
        self.Initialized = False

        self.logger = logging.getLogger()

        self.AMPHandler = Handler
        if self.AMPHandler == None:
            self.AMPHandler = getAMPHandler()

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DBConfig = self.DB.GetConfig()

        self.SessionID = 0
        #self.Index = Index
        self.serverdata = serverdata
        self.serverlist = {}

        self.InstanceID = instanceID
        self.FriendlyName = None

        self.ADS_Running = False #This is for the ADS (Dedicated Server) not the Instance!

        self.Last_Update_Time = 0

        if instanceID == 0:
            self.Last_Update_Time_Mutex = threading.Lock()
        
        self.AMP_BotRoleID = None
        self.super_AdminID = None

        self.url = self.AMPHandler.tokens.AMPurl + '/API/' #base url for AMP console /API/

        if hasattr(self, "perms") == False:
            self.perms = ['Core.*','Core.RoleManagement.*','Core.UserManagement.*','Instances.*','ADS.*','Settings.*','ADS.InstanceManagement.*','FileManager.*','LocalFileBackup.*','Core.AppManagement.*']

        if hasattr(self,'APIModule') == False:
            self.APIModule = 'AMP'

        self.AMP2Factor = None
        if self.AMPHandler.AMP2FA:
            try:
                self.AMP2Factor = pyotp.TOTP(self.AMPHandler.tokens.AMPAuth) #Handles time based 2Factory Auth Key/Code
                self.AMP2Factor.now()

            except AttributeError:
                self.logger.critical("**ERROR** Please check your 2 Factor Set-up Code in tokens.py, should not contain spaces,escape characters and enclosed in quotes!")
                self.AMP2Factor = None
                return

        self.AMPheader = {'Accept': 'text/javascript'} #custom header for AMP API POST requests. AMP is pure POST requests. ***EVERY REQUEST MUST HAVE THIS***
        if instanceID != 0:
            self.url += f"ADSModule/Servers/{instanceID}/API/"
        
        if default_console:
            self.Console = AMPConsole(self)

        if instanceID != 0:
            #This gets all the dictionary values tied to AMP and makes them attributes of self.
            for entry in serverdata:
                setattr(self, entry, serverdata[entry])


            #This gets me the DB_Server object if it's not there; it adds the server.
            self.DB_Server = self.DB.GetServer(InstanceID = self.InstanceID)
            if self.DB_Server == None:
                self.logger.dev(f'Adding Name: {self.InstanceName} to the Database, Instance ID: {self.InstanceID}')
                try:
                    self.DB_Server = self.DB.AddServer(InstanceID= self.InstanceID, InstanceName= self.InstanceName)
                except Exception as e:
                    self.logger.warning(f'We failed to add the {self.InstanceName} {self.InstanceID} to the DB. Attempting to use {self.FriendlyName} for Instance Name')
                    
                if self.FriendlyName == None:
                    self.FriendlyName = self.InstanceName

                try:
                    self.DB_Server = self.DB.AddServer(InstanceID= self.InstanceID, InstanceName= self.FriendlyName)
                except Exception as e:
                    self.logger.critical(f'We failed to add the {self.InstanceName} {self.InstanceID} to the DB, exiting setup. Please consider changing the Friendly Name to something Unique.')
                    sys.exit(1)
                
                

                self.logger.info(f'*SUCCESS** Added {self.InstanceName} to the Database.')
            else:
                self.logger.info(f'**SUCCESS** Found {self.InstanceName} in the Database.')

            self.logger.dev(f"Instance Name: {self.InstanceName} // InstanceID: {self.InstanceID} // Module: {self.Module} // Port: {self.Port} // DisplayImageSource: {self.DisplayImageSource}")

            #This sets all my DB_Server attributes.
            self._setDBattr()
            if self.Running:
                self._ADScheck()

        #Lets see if we are the main AMP or if the Instance is Running
        if instanceID == 0 or self.Running:
            self._AMP_botRole_exists = False
            self._have_superAdmin = False
            self._have_AMP_botRole = False

            #Lets see what Roles/Permissions we have if it all possible first.
            try:
                permission = self.check_SessionPermissions() #We either have to have bot Role or Super Admin to get passed this point. So validate.

            except Exception as e:
                self.logger.critical(f'***ATTENTION*** {e} for {self.APIModule} on {self.FriendlyName}! Please consider giving us `Super Admins` and the bot will set its own permissions and role!')
                #If the main AMP is missing permissions; lets quit!
                if instanceID == 0:
                    sys.exit(1)

            if permission:
                #If we have the -super arg no need to check for Gatekeeper Role/etc. Just return.
                if self.AMPHandler.args.super:
                    self.Initialized = True
                    return
                
                role_perms = self.check_GatekeeperRole_Permissions() #This will fail if we DO NOT have
                #Main Instance
                if instanceID == 0:
                    #Gatekeeper Role doesn't exist we setup our Bot Role Woohoo!
                    if not self._AMP_botRole_exists:
                        self.Initialized = True
                        self.setup_AMPbotrole()
                        return
                    
                    #This is an edge case.
                    #Gatekeeper doesn't have its Gatekeeper Role, give it to myself.
                    if not self._have_AMP_botRole:
                        self.setAMPUserRoleMembership(self.AMP_UserID, self.AMP_BotRoleID, True)

                if not role_perms:
                    if not self._have_superAdmin:
                        self.logger.critical(f'We do not have the Role `Super Admins` and are unable to set our Permissions for {"AMP" if self.InstanceID == 0 else self.FriendlyName}')
                        sys.exit(1)

                    #If for some reason we do have Gatekeeper Role and the permissions are NOT setup.
                    if self._AMP_botRole_exists and self._have_AMP_botRole:
                        self.setup_Gatekeeper_Permissions()

                    #If for some reason Gatekeeper Role doesn't exist and we don't have it.
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
        import amp_permissions as AMPPerms
        core = AMPPerms.perms_super()
        for perm in core:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]
            if self.setAMPRolePermissions(self.AMP_BotRoleID, perm, enabled):
                self.logger.dev(f'Set __{perm}__ for _Gatekeeper_ to `{enabled}` on {self.FriendlyName if self.InstanceID != 0 else "AMP"}')

    def check_GatekeeperRole_Permissions(self)-> bool:
        """- Will check `Gatekeeper Role` for `Permission Nodes` when we have `Super Admin` and `not InstanceID = 0`.\n
        - Checks for `Gatekeeper Role`, if we `have the Gatekeeper Role` and `Super Admin Role`
        Returns `True` if we have permissions. Otherwise `False`"""
        #If we have Super Admin; lets check for the Bot Role and if we are not on the Main Instance.
        failed = False 

        self.AMP_userinfo = self.getAMPUserInfo(self.AMPHandler.tokens.AMPUser) #This gets my AMP User Information
        self.AMP_UserID = self.getAMPUserID(self.AMPHandler.tokens.AMPUser) #This gets my AMP User ID
        self.setRoleIDs()

        #`Gatekeeper Role inside of AMP`
        if self.AMP_BotRoleID != None:
            #self.logger.dev('Gatekeeper Role Exists..')
            self._AMP_botRole_exists = True

        #Gatekeeper has `Gatekeeper` Role inside of AMP
        if self._AMP_botRole_exists and self.AMP_BotRoleID in self.AMP_userinfo['result']['Roles']:
            #self.logger.dev('Gatekeeper User has Gatekepeer Role.')
            self._have_AMP_botRole = True

        #`Super_Admin Role inside of AMP`
        if self.super_AdminID in self.AMP_userinfo['result']['Roles']:
            #self.logger.dev('Gatekeeper User has Super Admins')
            self._have_superAdmin = True

        if self._AMP_botRole_exists:
            self.logger.dev(f'Checking `Gatekeeper Role` permissions on {"AMP" if self.InstanceID == 0 else self.FriendlyName}')
            for perm in self.perms:
                #Skip the perm check on ones we "shouldn't have!"
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
        self.logger.warning(f'Checking Session: {self.SessionID} for proper permissions...')
        failed = False
        for perm in self.perms:
            #Skip the perm check on ones we "shouldn't have!"
            if perm.startswith('-'):
                continue

            check = self.CurrentSessionHasPermission(perm)

            self.logger.dev(f'Session {"has" if check else "is missing" } permisson node: {perm}')
            
            if check != True:
                if self.APIModule == 'AMP': #AKA the main (InstanceID == 0)
                    self.logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please check under Configuration -> User Management for {self.AMPHandler.tokens.AMPUser}.')

                else:
                    end_point = self.AMPHandler.tokens.AMPurl.find(":", 5)
                    self.logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please visit {self.AMPHandler.tokens.AMPurl[:end_point]}:{self.Port} under Configuration -> Role Management -> Gatekeeper')
                failed = True

        if failed:
            self.logger.critical(f'***ATTENTION*** The Bot is missing permissions, some or all functionality may not work properly!')
            #Please see this image for the required bot user Permissions **(Github link to AMP Basic Perms image here)**
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
        self.DB_Server = self.DB.GetServer(InstanceID = self.InstanceID)
        self.DisplayName = self.DB_Server.DisplayName
        self.Nicknames = self.DB_Server.Nicknames
        self.Display_Description = self.DB_Server.Description
        self.Display_IP = self.DB_Server.Display_IP
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
                    'token': token, #get current 2Factor Code
                    'rememberMe': True}

            try:
                result = self.CallAPI('Core/Login',parameters)
                
                self.SessionID = result['sessionID']
                self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
                self.Running = True

            except:
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

        while(True):
            try:
                post_req = requests.post(self.url+APICall, headers=self.AMPheader, data=jsonhandler)

                if len(post_req.content) > 0:
                    break

                #Since we are using GetUpdates every second for Console Updates; lets ignore them here so we don't sleep our thread.
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

        #Error catcher for API calls
        if type(post_req.json()) == None:
            self.logger.error(f"AMP_API CallAPI ret is 0: status_code {post_req.status_code}")
            self.logger.error(post_req.raw)

        self.logger.debug(f'Post Request Prints: {post_req.json()}')

        if post_req.json() == None:
            return 

        #Permission errors will trigger this, unsure what else.
        if "result" in post_req.json():

            if type(post_req.json()['result']) == bool:
                if post_req.json()['result'] == True:
                    return post_req.json()

                if post_req.json()['result'] != True:
                    self.logger.error(f'The API Call {APICall} failed because of {post_req.json()}')
                    return post_req.json()

                if "Status" in post_req.json()['result'] and (post_req.json()['result']['Status'] == False):
                    self.logger.error(f'The API Call {APICall} failed because of Status: {post_req.json()}')
                    return False

        if "Title" in post_req.json():
            if type(post_req.json()['Title']) == str and post_req.json()['Title'] == 'Unauthorized Access':
                self.logger.error(f'["Title"]: The API Call {APICall} failed because of {post_req.json()}')
                raise Exception('Unauthorized Access -')
                #return False
                
        return post_req.json()

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
        result = self.CallAPI('ADSModule/GetInstances',parameters) 
        if len(result["result"][0]['AvailableInstances']) != 0:
            for Target in result["result"]:
                for instance in Target['AvailableInstances']: #entry = name['result']['AvailableInstances'][0]['InstanceIDs']
                    #This should be a list of my AMP Servers [{'InstanceID': '<AMP Instance Object>'}]
                    for amp_instance in self.AMPHandler.AMP_Instances:
                        #This should be the <AMP Instance Object> comparing to the Instance Objects we got from `getInstances()`
                        if self.AMPHandler.AMP_Instances[amp_instance].InstanceID == instance['InstanceID']:
                            #print('Found Instance', amp_instance.InstanceID, amp_instance.FriendlyName)
                            ##This gets all the dictionary values tied to AMP and makes them attributes of self.
                            for entry in instance:
                                #print(amp_instance, entry, instance[entry])
                                setattr(self.AMPHandler.AMP_Instances[amp_instance], entry, instance[entry])
                            break

        self.Last_Update_Time = time.time()
        self.Last_Update_Time_Mutex.release()

    def _instanceValidation(self) -> str:
        """This checks if any new instances have been created since last check. If so, updates AMP_Instances and creates the object."""
        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstances',parameters) 
        #serverlist = {}
        amp_instance_keys = self.AMPHandler.AMP_Instances.keys()
        if len(result["result"][0]['AvailableInstances']) != 0:
            for Target in result["result"]:
                for amp_instance in Target['AvailableInstances']: #entry = name['result']['AvailableInstances'][0]['InstanceIDs']
                    
                    #This exempts the AMPTemplate Gatekeeper *hopefully*
                    flag_reg = re.search("(gatekeeper)", amp_instance['FriendlyName'].lower())
                    if flag_reg != None:
                        if flag_reg.group():
                            continue 
                    
                    if amp_instance['Module'] == 'ADS':
                        continue

                    if amp_instance['InstanceID'] not in amp_instance_keys:
                        self.logger.info(f'Found a New AMP Instance since Startup; Creating AMP Object for {amp_instance["FriendlyName"]}')
                        if amp_instance['DisplayImageSource'] in self.AMPHandler.AMP_Modules:
                            name = str(self.AMPHandler.AMP_Modules[amp_instance["DisplayImageSource"]]).split("'")[1]
                            self.logger.dev(f'Loaded __{name}__ for {amp_instance["FriendlyName"]}')
                            #def __init__(self, instanceID = 0, serverdata = {}, Index = 0, default_console = False, Handler = None):
                            server = self.AMPHandler.AMP_Modules[amp_instance['DisplayImageSource']](instanceID= amp_instance['InstanceID'], serverdata= amp_instance, Handler= self.AMPHandler)
                            self.AMPHandler.AMP_Instances[server.InstanceID] = server
                            return amp_instance['FriendlyName'] 

                        else:
                            self.logger.dev(f'Loaded __AMP_Generic__ for {amp_instance["FriendlyName"]}')
                            server = self.AMPHandler.AMP_Modules['Generic'](instanceID= amp_instance['InstanceID'], serverdata= amp_instance, Handler= self.AMPHandler)
                            self.AMPHandler.AMP_Instances[server.InstanceID] = server
                            return amp_instance['FriendlyName']
    
    def _instance_ThreadManager(self):
        """AMP Instance(s) Thread Manager"""
        self.Login()
        for instance in self.AMPHandler.AMP_Instances:
            server = self.AMPHandler.AMP_Instances[instance]
            
            #Lets validate our ADS Running before we check for console threads.
            if server.Running and server._ADScheck() and server.ADS_Running:
                #Lets check if the Console Thread is running now.
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
        result = self.CallAPI('ADSModule/GetInstances',parameters)
        #pprint(result)
        return result     

    def ConsoleUpdate(self) -> dict:
        """Returns `{'ConsoleEntries':[{'Contents': 'String','Source': 'Server thread/INFO','Timestamp': '/Date(1651703130702)/','Type': 'Console'}]`\n
        Will post all updates from previous API call of console update"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetUpdates', parameters)
        return result

    def ConsoleMessage_withUpdate(self, msg:str) -> dict:
        """This will call Console Update after sending the Console Message (Use this for Commands that require feedback)"""
        self.Login()
        parameters = {'message': msg}
        self.CallAPI('Core/SendConsoleMessage', parameters)
        time.sleep(.2)
        update = self.ConsoleUpdate()
        return update

    def ConsoleMessage(self, msg:str):
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

        #This happens because CallAPI returns False when it fails permissions.
        if result == False:
            return False
        return result

    def getMetrics(self) -> tuple:
        """Returns AMP Instance Metrics \n
        `Uptime str` \n
        `TPS str`  \n
        `Users tuple(str,str)` \n
        `Memory tuple(str, str)` \n
        `CPU tuple(str, str)` \n
        """
        result = self.getStatus()
        if result != False:
            Uptime = str(result['Uptime'])
            TPS = str(result['State'])
            Users = (str(result['Metrics']['Active Users']['RawValue']),str(result['Metrics']['Active Users']['MaxValue']))
            Memory = (str(result['Metrics']['Memory Usage']['RawValue']),str(result['Metrics']['Memory Usage']['MaxValue']))
            CPU = str(result['Metrics']['CPU Usage']['RawValue']) #This is a percentage
            self.Metrics = result['Metrics']
            return TPS, Users, CPU, Memory, Uptime
    
    def getLiveStatus(self) -> bool:
        """Server is Online and Proper AMP Permissions. \n
        So we check TPS/State to make sure the Dedicated Server is actually 'live'. \n
        `Returns False` when 0 TPS """
        result = self.getStatus()
        if result != False:
            status = str(result['State'])
            if status == '0':
                return False
            return True

    def getUsersOnline(self) -> tuple[str, str]:
        """Returns Number of Online Players over Player Limit. \n
        `eg 2/10`"""
        result = self.getStatus()
        if result != False:
            Users = (str(result['Metrics']['Active Users']['RawValue']),str(result['Metrics']['Active Users']['MaxValue']))
            return Users
        
    def getUserList(self) -> list[str]:
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
  
    def setFriendlyName(self, name:str, description:str) -> str:
        """This is used to change an Instance's Friendly Name and or Description. Retains all previous settings. \n
        `This requires the instance to be Offline!`"""
        self.Login()
        parameters = {
                'InstanceId' :  self.InstanceID,
                'FriendlyName': name,
                'Description' : description,
                'StartOnBoot': self.DaemonAutostart,
                'Suspended' : self.Suspended,
                'ExcludeFromFirewall': self.ExcludeFromFirewall,
                'RunInContainer': self.IsContainerInstance,
                'ContainerMemory' : self.ContainerMemoryMB,
                'MemoryPolicy' : self.ContainerMemoryPolicy,
                'ContainerMaxCPU': self.ContainerCPUs}
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

    def copyFile(self, source:str, destination:str):
        self.Login()
        parameters = {
            'Origin' : source,
            'TargetDirectory' : destination
        }
        self.CallAPI('FileManagerPlugin/CopyFile', parameters)
        return

    def renameFile(self, original:str, new:str):
        self.Login()
        parameters = {
            'Filename' : original,
            'NewFilename' : new
        }
        self.CallAPI('FileManagerPlugin/RenameFile', parameters)
        return

    def getDirectoryListing(self, directory:str) -> list:
        self.Login()
        parameters = {
            'Dir' : directory
            }
        result = self.CallAPI('FileManagerPlugin/GetDirectoryListing',parameters)
        return result
  
    def getFileChunk(self, name:str, position:int, length:int):
        self.Login()
        parameters = {
            'Filename' : name,
            'Position' : position,
            'Length' : length
        }
        result = self.CallAPI('FileManagerPlugin/GetFileChunk',parameters)
        return result

    def writeFileChunk(self,filename:str, position:int, data:str):
        self.Login()
        parameters = {
            'Filename' : filename,
            'Position' : position,
            'Data' : data
        }
        self.CallAPI('FileManagerPlugin/WriteFileChunk', parameters)
        return

    def endUserSession(self, sessionID:str):
        """Ends specified User Session"""
        self.Login()
        parameters = {
            'Id' : sessionID
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

    def trashDirectory(self, dirname:str):
        """Moves a directory to trash, files must be trashed before they can be deleted."""
        self.Login()
        parameters = {
            'DirectoryName' : dirname
        }
        self.CallAPI('FileManagerPlugin/TrashDirectory',parameters)
        return 

    def trashFile(self, filename:str):
        """Moves a file to trash, files must be trashed before they can be deleted."""
        self.Login()
        parameters = {
            'Filename' : filename
        }
        self.CallAPI('FileManagerPlugin/TrashFile',parameters)
        return
    
    def emptyTrash(self, trashdir:str):
        """Empties a trash bin for the AMP Instance"""
        self.Login()
        parameters = {
            'TrashDirectoryName' : trashdir
        }
        self.CallAPI('FileManagerPlugin/EmptyTrash',parameters)
        return

    def takeBackup(self, title:str, description:str, sticky:bool=False):
        """Takes a backup of the AMP Instance; default `sticky` is False!"""
        self.Login()
        parameters = {
            "Title" : title,
            "Description" : description,
            "Sticky" : sticky
        }
        self.CallAPI('LocalFileBackupPlugin/TakeBackup',parameters)
        return

    def getAMPUserInfo(self, name:str) -> Union[str, dict]:
        """Gets AMP user info. if IdOnly is True; returns AMP User ID only!"""
        self.Login()
        parameters = {
            'Username' : name
        }
        result = self.CallAPI('Core/GetAMPUserInfo', parameters)
        return result

    def getAMPUserID(self, name:str):
        """Returns AMP Users ID Only."""
        result = self.getAMPUserInfo(name= name)
        return result['result']['ID']

    def CurrentSessionHasPermission(self, PermissionNode:str) -> dict:
        """Gets current Sessions permission spec"""
        self.Login()
        parameters = {
            'PermissionNode' : PermissionNode
        }
        result = self.CallAPI('Core/CurrentSessionHasPermission', parameters)
        
        if result != False:
            return result['result']

        return result

    def getAMPRolePermissions(self, RoleID:str) -> dict:
        """Gets full permission spec for Role (returns permission nodes)"""
        self.Login()
        parameters = {
            'RoleId' : RoleID
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
        return result['result']
    
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

    def createRole(self, name:str, AsCommonRole=False):
        """Creates a AMP User role"""
        self.Login()
        parameters = {
            'Name' : name,
            'AsCommonRole' : AsCommonRole
        }
        result = self.CallAPI('Core/CreateRole', parameters)
        return result

    def getRole(self, Roleid:str):
        """Gets the AMP Role"""
        self.Login()
        parameters = {
            'RoleId' : Roleid
        }
        result = self.CallAPI('Core/GetRole', parameters)
        return result
    
    def setAMPUserRoleMembership(self, UserID:str, RoleID:str, isMember:bool):
        """ Sets the AMP Users Role Membership"""
        self.Login()
        parameters = {
            'UserId' : UserID,
            'RoleId' : RoleID,
            'IsMember' : isMember
        }
        result = self.CallAPI('Core/SetAMPUserRoleMembership',parameters)
        return result

    def setAMPRolePermissions(self, RoleID:str, PermissionNode:str, Enabled:bool):
        """Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`"""
        self.Login()
        parameters = {
            'RoleId' : RoleID,
            'PermissionNode' : PermissionNode,
            'Enabled' : Enabled
        }
        result = self.CallAPI('Core/SetAMPRolePermission', parameters)

        if result['result']['Status'] == False:
            self.logger.critical(f'Unable to Set Permission Node __{PermissionNode}__ to `{Enabled}` for {RoleID}')
            return False
      
        return True

    #These are GENERIC Methods below this point ---------------------------------------------------------------------------
    def addWhitelist(self, name:str):
        """Base Function for AMP.addWhitelist"""
        return False

    def getWhitelist(self):
        """Base Function for AMP.getWhitelist"""
        return False

    def removeWhitelist(self, name:str):
        """Base Function for AMP.removeWhitelist"""
        return False

    def whitelist_intake(self, discord_user: discord.Member, user_name:str):
        """Base Function for AMP.whitelist_intake"""
        return True
  
    def name_Conversion(self):
        """Base Function for AMP.name_Conversion"""
        return None

    def name_History(self, user):
        """Base Function for AMP.name_History"""
        return user

    def check_Whitelist(self, discord_user: discord.Member= None, in_gamename:str= None):
        """Base Funcion for AMP.check_Whitelist `default return is None`"""
        return None

    def Chat_Message(self, message:str, author:str=None, author_prefix:str=None):
        """Base Function for Discord Chat Messages to AMP ADS"""
        return

    def Chat_Message_Formatter(self, message:str):
        """Base Function for Server Chat Message Formatter"""
        return message

    def get_IGN_Avatar(self, db_user=None, user:str=None):
        """Base Function for customized discord messages"""
        return False

    def Broadcast_Message(self, message, prefix:str=None):
        """Base Function for Broadcast Messages to AMP ADS"""
        return

class AMPHandler():
    def __init__(self, args:Namespace):
        self.args = args
        self.logger = logging.getLogger()
        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.AMP2FA = False
        self.tokens = ''

        self.superUser = False
    
        self.SessionIDlist = {}

        self.AMP_Modules = {}

        self.AMP_Console_Modules = {}
        self.AMP_Console_Threads = {}

        self.SuccessfulConnection = False
        self.InstancesFound = False

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.val_settings()
        self.moduleHandler()

    def setup_AMPInstances(self):
        """Intializes the connection to AMP and creates AMP_Instance objects."""
        self.AMP = AMPInstance(Handler = self)
        self.getAMPInstances(amp= self.AMP)

        #This removes Super Admins from the bot user! Controlled through parser args!
        if self.args.super or not self.args.dev:
            self.AMP.setAMPUserRoleMembership(self.AMP.AMP_UserID, self.AMP.super_AdminID, False) 
            self.logger.warning(f'***ATTENTION*** Removing {self.tokens.AMPUser} from `Super Admins` Role!')
    
    def get_AMP_instance_names(self) -> list[str]:
        """This only works for ONLINE/EXISTING Instances. Anything offline wont show up."""
        AMP_Instances_Names = []
        for server in self.AMP_Instances:
            if self.AMP_Instances[server].DisplayName != None:
                AMP_Instances_Names.append(self.AMP_Instances[server].DisplayName)
            else:
                if self.AMP_Instances[server].FriendlyName not in AMP_Instances_Names:
                    AMP_Instances_Names.append(self.AMP_Instances[server].FriendlyName)
                else:
                    AMP_Instances_Names.append(self.AMP_Instances[server].InstanceName)
        return AMP_Instances_Names
    
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
        if not tokens.AMPurl.startswith('http://') and not tokens.AMPurl.startswith('https://'):
            self.logger.critical('** Please verifiy your AMPurl. **')
            reset = True
            
        if tokens.AMPurl.endswith('/'):
            self.logger.warning(f'** Please remove the forward slash at the end of {tokens.AMPurl} **, we temporarily did it for you. This may break things...')
            tokens.AMPurl = tokens.AMPurl[:-1]
        
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
        self.logger.dev('AMPHandler moduleHandler loading modules...')
        try:
            dir_list = self._cwd.joinpath('modules').iterdir()
            for folder in dir_list:
                file_list = folder.glob('amp_*.py')
                for script in file_list:
                    module_name = script.name[4:-3].capitalize()
                    try:
                        #print(script)
                        spec = importlib.util.spec_from_file_location(module_name, script)
                        class_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(class_module)

                        # self.AMP_Modules[module_name] = getattr(class_module,f'AMP{module_name}')
                        # self.AMP_Console_Modules[module_name] = getattr(class_module,f'AMP{module_name}Console')
                        #!ATTENTION! This may change in the future. Depends on the table update.
                        for DIS in getattr(class_module,f'DisplayImageSources'):
                            self.AMP_Modules[DIS] = getattr(class_module, f'AMP{module_name}')
                            self.AMP_Console_Modules[DIS] = getattr(class_module, f'AMP{module_name}Console')

                        self.logger.dev(f'**SUCCESS** {self.name} Loading AMP Module **{module_name}**')

                    except Exception as e:
                        self.logger.error(f'**ERROR** {self.name} Loading AMP Module **{module_name}** - {e}')
                        continue
   
        except Exception as e:
            self.logger.error(f'**ERROR** {self.name} Loading AMP Module ** - File Not Found {e}')
                    
    def getAMPInstances(self, amp: AMPInstance) -> dict[AMPInstance]:
        """Creates all the AMP Instance Objects and puts them into a dictionary.\n `{'InstanceID': AMPInstance}`"""
        data = amp.getInstances()
        self.AMP_Instances = {}
        if len(data["result"][0]['AvailableInstances']) != 0:
            self.InstancesFound = True
            # for Target in data["result"]:
            #     for amp_instance in data["result"][Target]['AvailableInstances']: #entry = name['result']['AvailableInstances'][0]['InstanceIDs']
            #         instance = data["result"][0]['AvailableInstances']

            #         #This exempts the AMPTemplate Gatekeeper *hopefully*
            #         flag_reg = re.search("(gatekeeper)",instance['FriendlyName'].lower())
            #         if flag_reg != None:
            #             if flag_reg.group():
            #                 continue 
                        
            #         #This should omit the main AMP instance.
            #         if instance['Module'] == 'ADS':
            #             continue

            #         if instance['DisplayImageSource'] in self.AMP_Modules:
            #             name = str(self.AMP_Modules[instance["DisplayImageSource"]]).split("'")[1]
            #             self.logger.dev(f'Loaded __{name}__ for {instance["FriendlyName"]}')
            #             #def __init__(self, instanceID = 0, serverdata = {}, Index = 0, default_console = False, Handler = None):
            #             server = self.AMP_Modules[instance['DisplayImageSource']](instanceID= instance['InstanceID'], serverdata= instance, Handler= self)
            #             self.AMP_Instances[server.InstanceID] = server

            #         else:
            #             self.logger.dev(f'Loaded __AMP_Generic__ for {instance["FriendlyName"]}')
            #             server = self.AMP_Modules['Generic'](instanceID= instance['InstanceID'], serverdata= instance, Handler= self)
            #             self.AMP_Instances[server.InstanceID] = server
            for Target in data["result"]:
                for amp_instance in Target['AvailableInstances']: #entry = name['result']['AvailableInstances'][0]['InstanceIDs']

                    #This exempts the AMPTemplate Gatekeeper *hopefully*
                    flag_reg = re.search("(gatekeeper)", amp_instance['FriendlyName'].lower())
                    if flag_reg != None:
                        if flag_reg.group():
                            continue 
                        
                    #This should omit the main AMP instance.
                    if amp_instance['Module'] == 'ADS':
                        continue

                    if amp_instance['DisplayImageSource'] in self.AMP_Modules:
                        name = str(self.AMP_Modules[amp_instance["DisplayImageSource"]]).split("'")[1]
                        self.logger.dev(f'Loaded __{name}__ for {amp_instance["FriendlyName"]}')
                        #def __init__(self, instanceID = 0, serverdata = {}, Index = 0, default_console = False, Handler = None):
                        server = self.AMP_Modules[amp_instance['DisplayImageSource']](instanceID= amp_instance['InstanceID'], serverdata= amp_instance, Handler= self)
                        self.AMP_Instances[server.InstanceID] = server

                    else:
                        self.logger.dev(f'Loaded __AMP_Generic__ for {amp_instance["FriendlyName"]}')
                        server = self.AMP_Modules['Generic'](instanceID= amp_instance['InstanceID'], serverdata= amp_instance, Handler= self)
                        self.AMP_Instances[server.InstanceID] = server
                 

        else:
            self.InstancesFound = False
            self.logger.critical(f'***ATTENTION*** Please ensure the permissions are set correctly, the Bot cannot find any AMP Instances at this time...')
            time.sleep(30)

def getAMPHandler(args:bool=False) -> AMPHandler:
    global Handler
    if Handler == None:
        Handler = AMPHandler(args= args)
    return Handler

class AMPConsole:
    FILTER_TYPE_CONSOLE = 0
    FILTER_TYPE_EVENT = 1
    FILTER_TYPE_BLACKLIST = 0
    FILTER_TYPE_WHITELIST = 1

    def __init__(self, AMPInstance= AMPInstance):
        self.logger = logging.getLogger()

        self.AMPInstance = AMPInstance
        self.AMPHandler = getAMPHandler()
        self.AMP_Console_Threads = self.AMPHandler.AMP_Console_Threads

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig
        self.DB_Server = self.DB.GetServer(InstanceID = self.AMPInstance.InstanceID)

        self.console_thread = None
        self.console_thread_running = False

        self.console_messages = []
        self.console_message_list = []
        self.console_message_lock = threading.Lock()

        self.console_chat_messages = []
        self.console_chat_message_lock = threading.Lock()

        self.console_event_messages = []
        self.console_event_message_lock = threading.Lock()

        self.logger.dev(f'**SUCCESS** Setting up {self.AMPInstance.FriendlyName} Console')
        self.console_init()

    def console_init(self):
        """This starts our console threads..."""
        if self.AMPInstance.Console_Flag:
            try:
                # self.AMP_Modules[DIS] = getattr(class_module,f'AMP{module_name}')
                # self.AMP_Console_Modules[DIS] = getattr(class_module,f'AMP{module_name}Console')
                if self.AMPInstance.DisplayImageSource in self.AMPHandler.AMP_Console_Modules: #Should be AMP_Console_Modules: {Module_Name: 'Module_class_object'}
                    self.logger.dev(f'Loaded {self.AMPHandler.AMP_Console_Modules[self.AMPInstance.DisplayImageSource]} for {self.AMPInstance.FriendlyName}')
    
                    #This starts the console parse on our self in a seperate thread.
                    self.console_thread = threading.Thread(target=self.console_parse, name=self.AMPInstance.FriendlyName)

                    #This adds the AMPConsole Thread Object into a dictionary with the key value of AMPInstance.InstanceID
                    self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.console_thread

                    if self.AMPInstance.Running and self.AMPInstance._ADScheck() and self.AMPInstance.ADS_Running:
                        self.console_thread.start()
                        self.console_thread_running = True
                        self.logger.dev(f'**SUCCESS** Starting Console Thread for {self.AMPInstance.FriendlyName}...')
                        
                else: #If we can't find the proper module; lets load the Generic.
                    self.logger.dev(f'Loaded for {self.AMPHandler.AMP_Console_Modules["Generic"]} for {self.AMPInstance.FriendlyName}')
            
                    self.console_thread = threading.Thread(target=self.console_parse, name= self.AMPInstance.FriendlyName)
                    self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.console_thread

                    if self.AMPInstance.Running and self.AMPInstance._ADScheck() and self.AMPInstance.ADS_Running:
                        self.console_thread.start()
                        self.console_thread_running = True
                        self.logger.dev(f'**SUCCESS** Starting Console Thread for {self.AMPInstance.FriendlyName}...')

            except Exception as e:
                self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.AMPHandler.AMP_Console_Modules['Generic']
                self.logger.critical(f'**ERROR** Failed to Start the Console for {self.AMPInstance.FriendlyName}...with {e}')

    def console_parse(self):
        """This handles AMP Console Updates; turns them into bite size messages and sends them to Discord"""
        time.sleep(5)
        last_entry_time = 0
        while(1):
            time.sleep(1)
            
            if not self.console_thread_running:
                time.sleep(10)
                continue
            
            if not self.AMPInstance.Running:
                time.sleep(10)
                continue

            console = self.AMPInstance.ConsoleUpdate()

            for entry in console['ConsoleEntries']:
                #This prevents old messages from getting handled again and spamming on restart.
                entry_time = datetime.fromtimestamp(float(entry['Timestamp'][6:-2])/1000,tz= timezone.utc)
                if last_entry_time == 0:
                    last_entry_time = entry_time
                    break

                if entry_time < last_entry_time:
                    last_entry_time = entry_time
                    continue
                
                self.logger.dev(f'Name: {self.AMPInstance.FriendlyName} DisplayImageSource: {self.AMPInstance.DisplayImageSource} Console Entry: {entry}')
                self.logger.dev(f'Console Filtered: {bool(self.AMPInstance.Console_Filtered)} ConsoleFiltered Type: {self.AMPInstance.Console_Filtered_Type} Console Channel: {self.AMPInstance.Discord_Console_Channel}')
                self.logger.dev(f"Chat Channel: {self.AMPInstance.Discord_Chat_Channel} Chat Prefix: {self.DB_Server.Discord_Chat_Prefix} Event Channel: {self.AMPInstance.Discord_Event_Channel}")
                #This will add the Servers Discord_Chat_Prefix to the beginning of any of the messages.
                #Its done down here to prevent breaking of any exisiting filtering.
                if self.DB_Server.Discord_Chat_Prefix != None:
                    entry['Prefix'] = self.DB_Server.Discord_Chat_Prefix

                #This should handle server events(such as join/leave/disconnects)
                #if self.console_events(entry):
                    #continue

                #This will vary depending on the server type. 
                # I don't want to filter out the chat message here though. Just send it to two different places!
                if self.console_chat(entry):
                    continue
                
                #This will filter any messages such as errors or mods loading, etc..
                if self.console_filter(entry):
                    continue

                if len(entry['Contents']) > 1500:
                    index_hunt = entry['Contents'].find(';')
                    if index_hunt == -1:
                        continue

                    msg_len_index = entry['Contents'].rindex(';')

                    while msg_len_index > 1500:
                        msg_len_indexend = msg_len_index
                        msg_len_index = entry['Contents'].rindex(';',0,msg_len_indexend)

                        if msg_len_index < 1500:
                            newmsg = entry['Contents'][0:msg_len_index]
                            self.console_message_list.append(newmsg.lstrip())
                            entry['Contents'] = entry['Contents'][msg_len_index+1:len(entry['Contents'])]
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

        self.logger.warning(f'{self.AMPInstance.FriendlyName} Thread Loop is Ending')
    
    def console_filter(self, message):
        """Controls what will be sent to the Discord Console Channel via AMP Console. \n
        Return `True` to Continue, `False` to Return Message"""
        if self.AMPInstance.Console_Filtered:
            
            #This is to prevent Regex filtering on Chat Messages.
            if message['Type'] == 'Chat':
                return False

            #0 = Blacklist | 1 = Whitelist (0 = False/ 1 = True)
            return_bool = bool(self.AMPInstance.Console_Filtered_Type)

            regex = self.DB_Server.GetServerRegexPatterns()
            for pattern in regex:
                flag = re.search(regex[pattern]['Pattern'], message['Contents'])
                if flag != None:
                    #0 = Console | 1 = Event
                    #This is Console Regex Filtering
                    if regex[pattern]['Type'] == self.FILTER_TYPE_CONSOLE:
                        return not return_bool

                    #This is Event Regex Filtering
                    if regex[pattern]['Type'] == self.FILTER_TYPE_EVENT:
                        self.console_event_message_lock.acquire()
                        self.console_event_messages.append(message['Contents'])
                        self.console_event_message_lock.release()
                        return not return_bool
            else:
                self.logger.dev(f'Filtered Message: {message}')
                return return_bool
            
    def console_chat(self, message):
        """This will handle all player chat messages from AMP to Discord.\n
        Format's Server Chat Messages for better readability to the Console"""
        #{'Timestamp': '/Date(1657587898574)/', 'Source': 'IceOfWraith', 'Type': 'Chat', 'Contents': 'This is a local message','Prefix': 'Discord_Chat_Prefix}
        #Currently all servers set "Type" to Chat! So lets use those.
        if message["Type"] == 'Chat':
      
            #Removed the odd character for color idicators on text
            message['Contents'] = message['Contents'].replace('�','')

            self.console_chat_message_lock.acquire()
            self.console_chat_messages.append(message)
            self.console_chat_message_lock.release()

            self.console_message_lock.acquire()
            self.console_messages.append(f"{message['Source']}: {message['Contents']}")
            self.console_message_lock.release()
            return True
        return False

    # def console_events(self, message):
    #     """This will handle all player join/leave/disconnects and other achievements. THIS SHOULD ALWAYS RETURN FALSE!
    #     ALL events go to `self.console_event_messages` """
    #     return False