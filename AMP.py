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
import requests
import requests.sessions
import pyotp # 2Factor Authentication Python Module
import json
import time
from pprint import pprint
import sys
import pathlib
from datetime import datetime
import logging
import threading
import importlib.util
import traceback
import os
import discord
import asyncio

import DB

#import utils
dev = True
Handler = None


class AMPHandler():
    def __init__(self,client:discord.Client):
        self.logger = logging.getLogger()
        #self._client = client
        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.SessionIDlist = {}

        self.AMP_Instances = {}
        self.AMP_Modules = {}

        self.AMP_Console_Modules = {}
        self.AMP_Console_Threads = {}

        self.SuccessfulConnection = False
        self.InstancesFound = False

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.tokens = ''

        self.val_settings()
        self.moduleHandler()

        #self.instanceCheck()

    # def set_discord_client(self,client):
    #     """Passes the Discord Bot Client object to AMP_Handler for functionality inside of AMP_Console"""
    #     self.__client = client

    def setup_AMPInstances(self):
        """Intializes the connection to AMP and creates AMP_Instance objects."""
        self.AMP = AMPInstance(Handler = self)
        self.AMP_Instances = self.AMP.getInstances()

    def instanceCheck(self):
        """Checks for any new Instances since after startup. `(Advise using this in some sort of loop every so often)`\n
        This keeps the AMP_Instance Dictionary Current
        This also adds any new Instances to the Database"""
        self.logger.info('AMP Instance Update in progress...')
        AMP_instance_check = self.AMP.getInstances()
        for instance in AMP_instance_check:
            if instance not in self.AMP_Instances:
                self.AMP_Instances[AMP_instance_check[instance]]
                #!TODO! DB_Update(instance) #This adds the new Instance to the database.

    #!TODO! Need to check on startup and every so often for new instances and add them to the DB
    def add_Server_toDB(self,instance):
        """Adds the server to the DB if its not already there."""
        if self._cwd.joinpath('discordBot.db').exists():
            instance_check = self.DB.GetServer(instance)
            if instance_check == None:
                self.DB.AddServer(InstanceID=self.AMP_Instances[instance].InstanceID,InstanceName =self.AMP_Instances[instance].FriendlyName)
    
    #Checks for Errors in Config
    def val_settings(self):
        """Validates the tokens.py settings and 2FA."""
        self.logger.info('AMPHandler is validating your token file...')
        reset = False
        if not dev:
            if self._cwd.joinpath('tokenstemplate.py').exists() or not self._cwd.joinpath('tokens.py').exists():
                self.logger.critical('**ERROR** Please rename your tokenstemplate.py file to tokens.py before trying again.')
                reset = True

        import tokens
        self.tokens = tokens
        if tokens.AMPurl.endswith('/') or tokens.AMPurl.endswith('\\'):
            tokens.AMPurl = tokens.AMPurl.replace('/','').replace('\\','')

        if tokens.AMPAuth != '':
            if len(tokens.AMPAuth) < 7:
                self.logger.critical("**ERROR** Please check your 2 Factor Set-up Code in tokens.py, should not contain spaces,escape characters and enclosed in quotes!")
                reset = True

        if reset:
            input("Press any Key to Exit")
            sys.exit(0)
    
    def moduleHandler(self):
        """AMPs class Loader for specific server types."""
        #traceback.print_stack()
        self.logger.info('AMPHandler moduleHandler loading modules...')
        try:
            dir_list = pathlib.Path.cwd().joinpath('modules').iterdir()
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
                        
                        for DIS in getattr(class_module,f'DisplayImageSources'):
                            self.AMP_Modules[DIS] = getattr(class_module,f'AMP{module_name}')
                            self.AMP_Console_Modules[DIS] = getattr(class_module,f'AMP{module_name}Console')

                        self.logger.info(f'**SUCCESS** {self.name} Loading AMP Module **{module_name}**')

                    except Exception as e:
                        self.logger.error(f'**ERROR** {self.name} Loading AMP Module **{module_name}** - {e}')
                        continue
   
        except Exception as e:
            self.logger.error(f'**ERROR** {self.name} Loading AMP Module ** - File Not Found {e}')
                    
def getAMPHandler(client:discord.Client = None)-> AMPHandler:
    global Handler
    if Handler == None:
        Handler = AMPHandler(client)
    return Handler

class AMPInstance:
    """Base class for AMP"""
    def __init__(self, instanceID = 0, serverdata = {}, Index = 0, default_console = False, Handler = None):
        self.logger = logging.getLogger()

        self.AMPHandler = Handler
        if self.AMPHandler == None:
            self.AMPHandler = getAMPHandler()

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB

        self.SessionID = 0
        self.Index = Index
        self.serverdata = serverdata
        self.serverlist = {}
        self.InstanceID = instanceID
        self.Server_Running = False #This is for the ADS (Dedicated Server) not the Instance!

        self.url = self.AMPHandler.tokens.AMPurl + '/API/' #base url for AMP console /API/

        self.AMP2Factor = None
        if self.AMPHandler.tokens.AMPAuth != '':
            try:
                self.AMP2Factor = pyotp.TOTP(self.AMPHandler.tokens.AMPAuth) #Handles time based 2Factory Auth Key/Code
                self.AMP2Factor.now()
                #self.logger.info('Found Two Factor Auth Code')
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
            #This gets all the dictionary values tied to AMP and makes them attributes
            for entry in serverdata:
                setattr(self, entry, serverdata[entry])
            #pprint(serverdata)

            self.FriendlyName = self.FriendlyName.replace(' ', '_')
            #print('Instance Attr',dir(self))
            #print('Instance Running',self.Running)
            
            #This gets me the DB_Server object if it's not there; it adds the server.
            #self.DB_Server = None
            self.DB_Server = self.DB.GetServer(InstanceID = self.InstanceID)
            #Possible DB_Server Attributes = InstanceID, InstanceName, DisplayName, Description, IP, Whitelist, Donator, Console_Flag, Console_Filtered, Discord_Console_Channel, Discord_Chat_Channel, Discord_Role
            if self.DB_Server == None:
                self.DB_Server = self.DB.AddServer(InstanceID = self.InstanceID, InstanceName = self.FriendlyName)
                self.logger.info(f'*SUCCESS** Added {self.FriendlyName} to the Database.')
            else:
                self.logger.info(f'**SUCCESS** Found {self.FriendlyName} in the Database.')

            if dev:
                self.logger.info(f"'Name:'{self.FriendlyName} 'Module:' {self.Module} 'Port:'{self.Port} 'DisplayImageSource:'{self.DisplayImageSource}")
            #This sets all my DB_Server attributes.
            self.attr_update()

    def attr_update(self):
        """This will update AMP Instance attributes."""
        #Need to call this every so often. Possibly anytime I get instance information/update instance information
        self.logger.info(f'Updating Server Attributes - Instance Running: {self.Running}')
        self.DB_Server = self.DB.GetServer(InstanceID = self.InstanceID)

        if self.Running:
            server_status = self.server_check() #Using this to see if the API fails to set the server status (offline/online) NOT THE INSTANCE STATUS! Thats self.Running!!
            self.logger.info(f'{self.FriendlyName} ADS Running: {server_status}')
            self.Server_Running = server_status 

        self.DisplayName = self.DB_Server.DisplayName
        self.Description = self.DB_Server.Description
        self.IP = self.DB_Server.IP
        self.Whitelist = self.DB_Server.Whitelist
        self.Donator = self.DB_Server.Donator
        self.Console_Flag = self.DB_Server.Console_Flag
        self.Console_Filtered = self.DB_Server.Console_Filtered
        self.Discord_Console_Channel = self.DB_Server.Discord_Console_Channel
        self.Discord_Chat_Channel = self.DB_Server.Discord_Chat_Channel
        self.Discord_Role = self.DB_Server.Discord_Role
        self.Discord_Reaction = self.DB_Server.Discord_Reaction

    def server_check(self):
        """Use this to check if the AMP Dedicated Server(ADS) is running, NOT THE AMP INSTANCE!"""
        Success = self.Login()
        self.logger.debug('Server Check' + str(Success))
        if Success:
            parameters = {}
            self.CallAPI('Core/GetStatus', parameters)
            return True
        else:
            return False

    def Login(self):
        if self.SessionID == 0:
            if self.InstanceID in self.AMPHandler.SessionIDlist:
                self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
                #return func(*args, **kargs)
                return

            self.logger.info(f'AMPInstance Logging in {self.InstanceID}')

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
                #pprint(result)
                self.SessionID = result['sessionID']
                self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
                self.Running = True

            except:
                #!TODO! Track if Instance is Offline (Login Fails if Instance is Offline)
                self.logger.error(f'{self.FriendlyName} - Instance is Offline')
                self.Running = False
                return False
        return True
        

    def CallAPI(self,APICall,parameters):
        #global SuccessfulConnection
        self.logger.debug(f'Function {APICall} was called with {parameters}.')
        if dev:
            self.logger.info(f'Function {APICall}')

        if self.SessionID != 0:
            parameters['SESSIONID'] = self.SessionID
        jsonhandler = json.dumps(parameters)

        while(True):
            try:
                post_req = requests.post(self.url+APICall, headers=self.AMPheader, data=jsonhandler)
                if len(post_req.content) > 0:
                    break
                self.logger.error('AMP API recieved no Data; sleeping for 5 seconds...')
                time.sleep(5)

            except:
                if self.AMPHandler.SuccessfulConnection == False:
                    self.logger.critical('Unable to connect to URL; please check Tokens.py -> AMPURL')
                    sys.exit(-1)
                self.logger.error('AMP API was unable to connect; sleeping for 30 seconds...')
                time.sleep(30)

        self.AMPHandler.SuccessfulConnection = True

        #Error catcher for API calls
        if type(post_req.json()) == None:
            self.logger.error(f"AMP_API CallAPI ret is 0: status_code {post_req.status_code}")
            self.logger.error(post_req.raw)

        self.logger.debug(post_req.json())
        return post_req.json()

    def getInstances(self):
        """This gets all Instances on AMP and puts them into a dictionary.\n {'InstanceID': AMPAPI class}"""
        global InstancesFound
        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstances',parameters) 
        #pprint(result)
        serverlist = {}
        if len(result["result"][0]['AvailableInstances']) != 0:

            InstancesFound = True
            for i in range(0,len(result["result"][0]['AvailableInstances'])): #entry = name['result']['AvailableInstances'][0]['InstanceIDs']
                instance = result["result"][0]['AvailableInstances'][i] 

                #This exempts the AMPTemplate Gatekeeper
                if instance["FriendlyName"].lower() == 'Gatekeeper':
                    continue 

                if instance['Module'] in self.AMPHandler.AMP_Modules:
                    self.logger.info(f'Loaded __AMP_{instance["Module"]}__ for {instance["FriendlyName"]}')
                    #def __init__(self, instanceID = 0, serverdata = {}, Index = 0, default_console = False, Handler = None):
                    server = self.AMPHandler.AMP_Modules[instance['Module']](instance['InstanceID'],instance,i,self.AMPHandler)
                    serverlist[server.InstanceID] = server

                else:
                    self.logger.info(f'Loaded __AMP_Generic__ for {instance["FriendlyName"]}')
                    server = self.AMPHandler.AMP_Modules['Generic'](instance['InstanceID'],instance,i,self.AMPHandler)
                    serverlist[server.InstanceID] = server

            return serverlist

        else:
            InstancesFound = False
            self.logger.critical(f'Please ensure the permissions are set correctly, the Bot cannot find any AMP Instances at this time...')
            time.sleep(30)
            

    def ConsoleUpdate(self)-> dict:
        """Returns `{'ConsoleEntries':[{'Contents': 'String','Source': 'Server thread/INFO','Timestamp': '/Date(1651703130702)/','Type': 'Console'}]`\n
        Will post all updates from previous API call of console update"""
        parameters = {}
        result = self.CallAPI('Core/GetUpdates', parameters)
        return result

    def ConsoleMessage_withUpdate(self,msg:str)-> dict:
        """This will call Console Update after sending the Console Message (Use this for Commands that require feedback)"""
        parameters = {'message': ' '.join(msg)}
        self.CallAPI('Core/SendConsoleMessage', parameters)
        time.sleep(0.5)
        update = self.ConsoleUpdate()
        return update

    def ConsoleMessage(self,msg:str):
        """Basic Console Message"""
        self.Login()
        #msg = ' '.join(msg)
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

    def getStatus(self)-> tuple:
        """AMP Instance Metrics \n
        CPU is percentage based <tuple>
        """
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetStatus', parameters)
        Uptime = str(result['Uptime'])
        tps = str(result['State'])
        Users = (str(result['Metrics']['Active Users']['RawValue']),str(result['Metrics']['Active Users']['MaxValue']))
        Memory = (str(result['Metrics']['Memory Usage']['RawValue']),str(result['Metrics']['Memory Usage']['MaxValue']))
        cpu = str(result['Metrics']['CPU Usage']['RawValue']) #This is a percentage
        self.Metrics = result['Metrics']
        return tps,Users,cpu,Memory,Uptime
    
    def getUserList(self)-> list:
        """Returns a List of connected users."""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetUserList', parameters)
        user_list = []
        for user in result['result']:
            user_list.append(result['result'][user])
        return user_list

    def getSchedule(self)-> dict:
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetScheduleData', parameters)
        return result['result']['PopulatedTriggers']
  
    def setFriendlyName(self,name:str,description:str) -> str:
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

    def copyFile(self,source,destination):
        self.Login()
        parameters = {
            'Origin' : source,
            'TargetDirectory' : destination
        }
        self.CallAPI('FileManagerPlugin/CopyFile', parameters)
        return

    def renameFile(self,original,new):
        self.Login()
        parameters = {
            'Filename' : original,
            'NewFilename' : new
        }
        self.CallAPI('FileManagerPlugin/RenameFile', parameters)
        return

    def getDirectoryListing(self,directory):
        self.Login()
        parameters = {
            'Dir' : directory
            }
        result = self.CallAPI('FileManagerPlugin/GetDirectoryListing',parameters)
        return result
  
    def getFileChunk(self,name,position,length):
        self.Login()
        parameters = {
            'Filename' : name,
            'Position' : position,
            'Length' : length
        }
        result = self.CallAPI('FileManagerPlugin/GetFileChunk',parameters)
        return result

    def writeFileChunk(self,filename:str,position:int,data:str):
        self.Login()
        parameters = {
            'Filename' : filename,
            'Position' : position,
            'Data' : data
        }
        self.CallAPI('FileManagerPlugin/WriteFileChunk', parameters)
        return

    def endUserSession(self,sessionID:str):
        """Ends specified User Session"""
        self.Login()
        parameters = {
            'Id' : sessionID
        }
        self.CallAPI('Core/EndUserSession', parameters)
        return

    def getActiveAMPSessions(self)-> dict:
        """Returns currently active AMP Sessions"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetActiveAMPSessions', parameters)
        return result

    def getInstanceStatus(self)-> dict:
        """Returns AMP Instance Status"""
        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstanceStatuses', parameters)
        return result

    def trashDirectory(self,dirname:str):
        """Moves a directory to trash, files must be trashed before they can be deleted."""
        self.Login()
        parameters = {
            'DirectoryName' : dirname
        }
        self.CallAPI('FileManagerPlugin/TrashDirectory',parameters)
        return 

    def trashFile(self,filename:str):
        """Moves a file to trash, files must be trashed before they can be deleted."""
        self.Login()
        parameters = {
            'Filename' : filename
        }
        self.CallAPI('FileManagerPlugin/TrashFile',parameters)
        return
    
    def emptyTrash(self,trashdir:str):
        """Empties a trash bin for the AMP Instance"""
        self.Login()
        parameters = {
            'TrashDirectoryName' : trashdir
        }
        self.CallAPI('FileManagerPlugin/EmptyTrash',parameters)
        return

    def takeBackup(self,title:str, description:str, sticky:bool = False):
        """Takes a backup of the AMP Instance; default `sticky` is False!"""
        self.Login()
        parameters = {
            'Title' : title,
            'Description' : description,
            'Sticky' : sticky
        }
        self.CallAPI('LocalFileBackupPlugin/TakeBackup',parameters)
        return

    def addWhitelist(self,user):
        """Base Function for AMP.addWhitelist"""
        return user

    def getWhitelist(self):
        """Base Function for AMP.getWhitelist"""
        return

    def removeWhitelist(self,user):
        """Base Function for AMP.removeWhitelist"""
        return user

    def name_Conversion(self,user):
        """Base Function for AMP.name_Conversion"""
        return user

    def name_History(self,user):
        """Base Function for AMP.name_History"""
        return user

    def check_Whitelist(self,user_id:str):
        """Base Funcion for AMP.check_Whitelist `default return is FALSE`"""
        return False

    def send_message(self,message):
        """Base Function for Discord Chat Messages to AMP ADS"""
        return

class AMPConsole:
    def __init__(self, AMPInstance = AMPInstance):
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
        self.console_chat_messages_list = []
        self.console_chat_message_lock = threading.Lock()


        self.logger.info(f'**SUCCESS** Setting up {self.AMPInstance.FriendlyName} Console')
        self.console_init()


    def console_init(self):
        """This starts our console threads..."""
        #print(self.)
        if self.AMPInstance.Console_Flag:
            #print('Console testing','Module:',self.AMPInstance.Module,'Name:',self.AMPInstance.FriendlyName,'ADS Running:',self.AMPInstance.Server_Running)
            try:
                #!TODO! Finish setting up Consoles
                # self.AMP_Modules[DIS] = getattr(class_module,f'AMP{module_name}')
                # self.AMP_Console_Modules[DIS] = getattr(class_module,f'AMP{module_name}Console')
                if self.AMPInstance.DisplayImageSource in self.AMPHandler.AMP_Console_Modules: #Should be AMP_Console_Modules: {Module_Name: 'Module_class_object'}
                    if self.AMPInstance.Server_Running: #This is the Instance's ADS 
                        self.logger.info(f'Loaded {self.AMPHandler.AMP_Console_Modules[self.AMPInstance.DisplayImageSource]} for {self.AMPInstance.FriendlyName}')
        
                        self.console_thread_running = True

                        #This starts the console parse on our self in a seperate thread.
                        self.console_thread = threading.Thread(target=self.console_parse, name=self.AMPInstance.FriendlyName)

                        #This adds the AMPConsole Thread Object into a dictionary with the key value of AMPInstance.InstanceID
                        self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.console_thread
                        #print(self.console_thread)
                        self.console_thread.start()
                        self.logger.info(f'**SUCCESS** Starting Console Thread for {self.AMPInstance.FriendlyName}...')
                        
                    else:
                        self.logger.info(f'**ERROR** Server: {self.AMPInstance.FriendlyName} Instance is not currently Running')

                else: #If we can't find the proper module; lets load the Generic.
                    if self.AMPInstance.Server_Running: #This is the Instance's ADS 
                        self.logger.info(f'Loaded for {self.AMPHandler.AMP_Console_Modules["Generic"]} for {self.AMPInstance.FriendlyName}')
                        #server_console = self.AMP_Console_Modules['Generic']
                        self.console_thread_running = True
                        self.console_thread = threading.Thread(target=self.console_parse, name= self.AMPInstance.FriendlyName)
                        self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.console_thread
                        self.console_thread.start()
                        self.logger.info(f'**SUCCESS** Starting Console Thread for {self.AMPInstance.FriendlyName}...')

                    else:
                        self.logger.info(f'**ERROR** Server: {self.AMPInstance.FriendlyName} Instance is not currently Running')

            except Exception as e:
                self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.AMPHandler.AMP_Console_Modules['Generic']
                self.logger.error(f'**ERROR** Failed to Start the Console for {self.AMPInstance.FriendlyName}...with {e}')


    def console_parse(self):
        """This handles AMP Console Updates; turns them into bite size messages and sends them to Discord"""
        time.sleep(5)
        while(self.console_thread_running):
            time.sleep(1)
            console = self.AMPInstance.ConsoleUpdate()
            
            for entry in console['ConsoleEntries']:
                if dev:
                    print('Name:',self.AMPInstance.FriendlyName,'DisplayImageSource:',self.AMPInstance.DisplayImageSource,'Console Entry:', entry)
                    continue

                if self.console_filter(entry):
                    continue
                
                #This will vary depending on the server type.
                if self.console_chat(entry):
                    continue

                if self.AMPInstance.Discord_Console_Channel == None:
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
    

    def console_filter(self,message):
        """This will filter depending on the console_filter setting and handle what to send to Discord."""
        #print(message)
        return False

    def console_chat(self,message):
        """This will handle all player chat messages from AMP to Discord"""
        #print(message)
        return False




    

    

    