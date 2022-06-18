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

import modules.database as database
import tokens
import utils

Handler = None


class AMPHandler():
    def __init__(self):
        self.logger = logging.getLogger()
        self.__client = None
        self._cwd = pathlib.Path.cwd()

        self.SessionIDlist = {}
        self.AMP_Modules = {}
        self.AMP_Console_Threads = {}
        self.SuccessfulConnection = False
        self.InstancesFound = False

        self.DB = database.getDatabase()

        self.val_settings()
        self.moduleHandler()

        self.AMP = AMPInstance(Handler = self)
        self.AMP_Instances = self.AMP.getInstances()

        #self.instanceCheck()

    def set_discord_client(self,client):
        self.__client = client

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
        if self._cwd.joinpath('Gatekeeper.db').exists():
            instance_check = self.DB.GetServer(instance)
            if instance_check == None:
                self.DB.AddServer(InstanceID=self.AMP_Instances[instance].InstanceID,FriendlyName=self.AMP_Instances[instance].FriendlyName)
    
    #Checks for Errors in Config
    def val_settings(self):
        """Validates the tokens.py settings and 2FA."""
        self.logger.info('AMPHandler validate settings in progress...')
        reset = False
        if tokens.AMPurl.endswith('/') or tokens.AMPurl.endswith('\\'):
            tokens.AMPurl = tokens.AMPurl.replace('/','').replace('\\','')

        if self._cwd.joinpath('tokenstemplate.py').exists() or not self._cwd.joinpath('tokens.py').exists():
            self.logger.critical('**ERROR** Please rename your tokenstemplate.py file to tokens.py before trying again.')
            reset = True

        if len(tokens.AMPAuth) < 7 or tokens.AMPAuth == '':
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
                        self.AMP_Modules[module_name] = getattr(class_module,f'AMP{module_name}')
                        self.logger.info(f'**SUCCESS** Loading AMP Module **{module_name}**')
                        #print(dir(class_module))
                    # module_name = script.name[4:-3].capitalize()
                    # script = str(script).replace("\\",".").replace("/",'.')
                    # #print(script[:-3])
                
                    # try:
                    #     class_module = importlib.import_module(name = f'{script[3:-3]}')

                    except Exception as e:
                        self.logger.error(f'**ERROR** Loading AMP Module **{module_name}** - {e}')
                        continue

        except Exception as e:
            self.logger.error(f'**ERROR** Loading Module ** - File Not Found {e}')
                    
def getAMPHandler()-> AMPHandler:
    global Handler
    if Handler == None:
        Handler = AMPHandler()
    return Handler

class AMPInstance:
    """**Note** Use a seperate thread/async func when intializing AMPInstances"""
    def __init__(self, instanceID = 0, serverdata = {}, Index = 0, default_console = False, Handler = None):
        self.logger = logging.getLogger()

        if Handler:
            self.AMPHandler = Handler
        else:
            self.AMPHandler = getAMPHandler()

        self.SessionID = 0
        self.Index = Index
        self.serverdata = serverdata
        self.serverlist = {}
        self.InstanceID = instanceID
        self.url = tokens.AMPurl + '/API/' #base url for AMP console /API/

        try:
            self.AMP2Factor = pyotp.TOTP(tokens.AMPAuth) #Handles time based 2Factory Auth Key/Code
            self.AMP2Factor.now()
            #self.logger.info('Found Two Factor Auth Code')
        except AttributeError:
            self.AMP2Factor = None
            return

        self.AMPheader = {'Accept': 'text/javascript'} #custom header for AMP API POST requests. AMP is pure POST requests. ***EVERY REQUEST MUST HAVE THIS***
        if instanceID != 0:
            self.url += f"ADSModule/Servers/{instanceID}/API/"
        
        #!TODO! AMP Console Implimentation
        if default_console:
            self.Console = AMPConsole(self)

        if instanceID != 0:
            for entry in serverdata:
                setattr(self, entry, serverdata[entry])
            self.FriendlyName = self.FriendlyName.replace(' ', '_')
        else:
           self.Running = True

    def Login(self):
        #def wrapper(*args, **kargs):
        #global SessionIDlist
        #logger = logging.getLogger()
        #self = args[0]

        #if self.Running == False:
            #print(f'Instance offline: {self.FriendlyName}')
            #return False

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
                    'username': tokens.AMPUser,
                    'password': tokens.AMPPassword,
                    'token': token, #get current 2Factor Code
                    'rememberMe': True}

            result = self.CallAPI('Core/Login',parameters)
            self.SessionID = result['sessionID']
            #if ("checkup" not in kargs) or (kargs["checkup"] == False):
            self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
            return
        
        #return func(*args, **kargs)
    #return wrapper

    def CallAPI(self,APICall,parameters):
        #global SuccessfulConnection
        self.logger.debug(f'Function {APICall} was called with {parameters}.')
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

    # def class_handler(self,instance:dict,Index:int):
    #     #pprint(instance)
    #     """This houses all my AMP Classes to override AMP Instance for a specific server type."""
    #     if instance['Module'] == 'Minecraft':
    #         self.logger.info(f'Loaded AMP{instance["Module"]} for {instance["FriendlyName"]}')
    #         from modules.Minecraft.amp_minecraft import AMPMinecraft as AMPMC
    #         server = AMPMC(instance['InstanceID'],instance,Index = Index)

    #     else:
    #         from modules.GenericModule.amp_Generic import AMPGeneric
    #         #server = AMPGeneric(instance['InstanceID'],instance,Index = Index)
    #         server = AMPInstance(instance['InstanceID'],instance,Index = Index)

    #     return server

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
                if instance['Module'] in self.AMPHandler.AMP_Modules:
                    self.logger.info(f'Loaded __AMP_{instance["Module"]}__ for {instance["FriendlyName"]}')
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
        #print('Console update')
        self.Login()
        parameters = {}
        # Will post all updates from previous API call of console update.
        result = self.CallAPI('Core/GetUpdates', parameters)
        return result

    def ConsoleMessage_withUpdate(self,msg:str)-> dict:
        """This will call Console Update after sending the Console Message (Use this for Commands that require feedback)"""
        self.Login()
        parameters = {'message': ' '.join(msg)}
        #print(parameters)
        self.CallAPI('Core/SendConsoleMessage', parameters)
        time.sleep(0.5)
        update = self.ConsoleUpdate()
        return update

    def ConsoleMessage(self,msg:str):
        """Basic Console Message"""
        self.Login()
        msg = ' '.join(msg)
        parameters = {'message': msg}
        #print(parameters)
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
        #pprint(result)
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
        #print(result)
        return response

    def getAPItest(self):
        """Test AMP API calls with this function"""
        self.Login()
        parameters = {}
        result = self.CallAPI('Core/GetModuleInfo', parameters)
        #pprint(result)
        return result

    # @Login
    # def addTask(self,triggerID,methodID,parammap):
    #     """Adds an AMP Task to the Schedule"""
    #     parameters = {
    #             'TriggerID' : triggerID,
    #             'MethodID' : methodID,
    #             'ParameterMapping' : parammap
    #             }
    #     self.CallAPI('Core/AddTask', parameters)
    #     return

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

    #TODO - Need to fix list
    # def sessionCleanup(self):
    #     global SessionIDlist
    #     sessions = self.getActiveAMPSessions()
    #     for entry in sessions['result']:
    #         if entry['Username'] == tokens.AMPUser:
    #             if entry['SessionID'] not in SessionIDlist:
    #                 self.endUserSession(entry['SessionID'])
    #     return

    def addWhitelist(self,user):
        """Base Function for AMP.addWhitelist"""
        self.Login()
        return user

    def getWhitelist(self):
        """Base Function for AMP.getWhitelist"""
        self.Login()
        return

    def removeWhitelist(self,user):
        """Base Function for AMP.removeWhitelist"""
        self.Login()
        return user

    def name_Conversion(self,user):
        """Base Function for AMP.name_Conversion"""
        self.Login()
        return user

    def name_History(self,user):
        """Base Function for AMP.name_History"""
        self.Login()
        return user

    def check_Whitelist(self,user_id:str):
        """Base Funcion for AMP.check_Whitelist `default return is FALSE`"""
        self.Login()
        return False

class AMPConsole:
    def __init__(self, AMPInstance = AMPInstance):
        self.logger = logging.getLogger()

        self.AMPHandler = getAMPHandler()
        self.AMPInstance = AMPInstance
        self.AMP_Console_Threads = self.AMPHandler.AMP_Console_Threads

        self.DB = database.getDatabase()
        self.DB_Server = self.DB.GetServer(self.AMPInstance.InstanceID)

        self.__client = self.AMPHandler.__client
        self.uBot = utils.botUtils(self.__client)
        self.dBot = utils.discordBot(self.__client)

        self.console_thread = None
        self.console_thread_running = False

        try:
            self.console = self.DB_Server.Console
            self.console_filter_level = self.DB_Server.Console_Filtered
            self.console_channel = self.uBot.channelparse(self.DB_Server.DiscordConsoleChannel)
        except:
            self.console = False
            self.console_filter_level = False
            self.console_channel = None

        self.console_message_list = []

        self.console_start()
     
    async def console_start(self):
        """This starts our console threads..."""
        if self.console:
            try:
                self.console_thread = threading.Thread(self.console_parse())
                self.console_thread_running = True
                self.AMP_Console_Threads[self.AMPInstance.InstanceID] = AMPConsole
                logging.info(f'Initiating Server Console for {self.AMPInstance.FriendlyName}...')
            except Exception as e:
                self.AMP_Console_Threads[self.AMPInstance.InstanceID] = AMPConsole
                logging.error(f'Failed to Start the Console for {self.AMPInstance.FriendlyName}...')


    async def console_parse(self):
        """This handles AMP Console Updates; turns them into bite size messages and sends them to Discord"""
        if self.console_channel == None:
            return

        console = self.AMPInstance.ConsoleUpdate()
            
        for entry in console['ConsoleEntries']:
            if self.console_filter(entry):
                continue

            if self.console_chat(entry):
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
                        self.console_message_list.append(f"{entry['Source']}: {newmsg.lstrip()}")
                        entry['Contents'] = entry['Contents'][msg_len_index+1:len(entry['Contents'])]
                        msg_len_index = len(entry['Contents'])
                        continue
            else:
                self.console_message_list.append(f"{entry['Source']}: {entry['Contents']}") 

        if len(self.console_message_list) > 0:
            bulkentry = ''
            for entry in self.console_message_list:
                if len(bulkentry + entry) < 1500:
                    bulkentry = bulkentry + entry + '\n' 

                else:
                    try: #!TODO Needs to be Tested!
                        await self.dBot.sendMessage(self.console_channel,bulkentry[:-1])
                        #await self.send_message(bulkentry[:-1])
                    except Exception as e:
                        self.logger.error(f'Unable to Send Console Message...{e}')

                    bulkentry = entry + '\n'

            if len(bulkentry):
                try: #!TODO Needs to be Tested!
                    await self.dBot.sendMessage(self.console_channel,bulkentry[:-1])
                    #await self.send_message(bulkentry[:-1])
                except Exception as e:
                    self.logger.error(f'Unable to Send Console Message...{e}')
        return
    
    async def console_filter(self,message):
        """This will filter depending on the console_filter setting and handle what to send to Discord."""
        print(message)
        return True

    async def console_chat(self,message):
        """This will handle all player chat messages from AMP to Discord"""
        print(message)
        return True



    

    

    