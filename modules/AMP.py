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
import os
from datetime import datetime
import logging
import threading

import modules.database as database
import tokens
import utils


SessionIDlist = {}
SuccessfulConnection = False
InstancesFound = False


__client = None
main_DB = database.getDatabase()

curtime = datetime.now()
logger = logging.getLogger()

AMP_Instances = None #server = AMPInstance(entry['InstanceID'],entry,Index = i)
main_AMP = None
AMP_Modules = {}

AMP_Console_Threads = {}

def init(discordBot_client):
    logger.info('AMP Initializion...')
    global AMP_Instances,main_AMP,__client

    __client = discordBot_client

    main_AMP = AMPInstance() #This is my main Object connection for AMP interaction (eg like logging in)
    AMP_Instances = main_AMP.getInstances() #This returns a list of individual AMPInstance Objects

    val_settings()
    instanceCheck()
    #moduleHandler()
    return True

def getAMP():
    """Use this to get the main `<AMPInstance()>` object"""
    global main_AMP
    if main_AMP == None:
        init()
    return main_AMP

def moduleHandler():
    """Do NOT USE; purely for testing Purpose"""
    for instance in AMP_Instances:
        print(dir(AMP_Instances[instance]))
        #print('header',AMP_Instances[instance].AMPheader)
        #print('installed version',AMP_Instances[instance].InstalledVersion)
        #pprint(AMP_Instances[instance].serverdata)

def instanceCheck():
    """Checks for any new Instances since after startup. `(Advise using this in some sort of loop every so often)`\n
    This keeps the AMP_Instance Dictionary Current
    This also adds any new Instances to the Database"""
    logger.info('AMP Instance Update in progress...')
    AMP_instance_check = main_AMP.getInstances()
    for instance in AMP_instance_check:
        if instance not in AMP_Instances:
            AMP_Instances[AMP_instance_check[instance]]
            #!TODO! DB_Update(instance) #This adds the new Instance to the database.

def DB_Update(instance):
    #main_DB = database.getDatabase()
    curdir = os.getcwd()
    if os.path.isfile(curdir + 'Gatekeeper.db'):
        instance_check = main_DB.GetServer(instance)
        if instance_check == None:
            main_DB.AddServer(InstanceID=AMP_Instances[instance].InstanceID,FriendlyName=AMP_Instances[instance].FriendlyName)

#Checks for Errors in Config
def val_settings():
    """Validates the tokens.py settings and 2FA."""
    logger.info('AMP Settings Check in progress...')
    reset = False
    if tokens.AMPurl[-1] == '/' or "\\":
        tokens.AMPurl = tokens.AMPurl[0:-1]
    if os.path.isfile('tokenstemplate.py') or not os.path.isfile('tokens.py'):
        logger.critical('**ERROR** Please rename your tokenstemplate.py file to tokens.py before trying again.')
        reset = True
    if len(tokens.AMPAuth) < 7 or tokens.AMPAuth == '':
        logger.critical("**ERROR** Please check your 2 Factor Set-up Code in tokens.py, should not contain spaces and enclosed in ' '")
        reset = True
    if reset:
        input("Press any Key to Exit")
        sys.exit(0)
    

def Login(func):
    def wrapper(*args, **kargs):
        global SessionIDlist
        self = args[0]

        if self.Running == False:
            #print(f'Instance offline: {self.FriendlyName}')
            return False

        if self.SessionID == 0:
            if self.InstanceID in SessionIDlist:
                self.SessionID = SessionIDlist[self.InstanceID]
                return func(*args, **kargs)

            logger.info(f'AMP Logging in {self.InstanceID}')
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
            #print(result)
            self.SessionID = result['sessionID']
            if ("checkup" not in kargs) or (kargs["checkup"] == False):
                SessionIDlist[self.InstanceID] = self.SessionID

        return func(*args, **kargs)
    return wrapper


class AMPInstance:
    """**Note** Use a seperate thread/async func when intializing AMPInstances"""
    def __init__(self, instanceID = 0, serverdata = {},Index = 0,default_console = False):
        self.url = tokens.AMPurl + '/API/' #base url for AMP console /API/
        if instanceID != 0:
            self.url += f"ADSModule/Servers/{instanceID}/API/"

        self.InstanceID = instanceID
        self.AMPheader = {'Accept': 'text/javascript'} #custom header for AMP API POST requests. AMP is pure POST requests. ***EVERY REQUEST MUST HAVE THIS***

        try:
            self.AMP2Factor = pyotp.TOTP(tokens.AMPAuth) #Handles time based 2Factory Auth Key/Code
            self.AMP2Factor.now()
            #print('Found 2 Factor')
        except AttributeError:
            self.AMP2Factor = None
            #print('No 2 Factor found').
            return

        self.SessionID = 0
        self.Index = Index
        self.serverdata = serverdata

        #!TODO! AMP Console Implimentation
        if default_console:
            self.Console = AMPConsole(self)

        if instanceID != 0:
            for entry in serverdata:
                setattr(self, entry, serverdata[entry])
            self.FriendlyName = self.FriendlyName.replace(' ', '_')
        else:
           self.Running = True


    def CallAPI(self,APICall,parameters):
        global SuccessfulConnection
        if self.SessionID != 0:
            parameters['SESSIONID'] = self.SessionID
        jsonhandler = json.dumps(parameters)
        while(True):

            try:
                post_req = requests.post(self.url+APICall, headers=self.AMPheader, data=jsonhandler)
                if len(post_req.content) > 0:
                    break
                logger.error('AMP API recieved no Data; sleeping for 5 seconds...')
                time.sleep(5)

            except:
                if SuccessfulConnection == False:
                    logger.critical('Unable to connect to URL; please check Tokens.py -> AMPURL')
                    sys.exit(-1)
                logger.error('AMP API was unable to connect; sleeping for 30 seconds...')
                time.sleep(30)

        SuccessfulConnection = True

        #Error catcher for API calls
        if type(post_req.json()) == None:
            logger.error(f"AMP_API CallAPI ret is 0: status_code {post_req.status_code}")
            logger.error(post_req.raw)

        logger.debug(post_req.json())
        return post_req.json()

    @Login
    def getInstances(self):
        """This gets all Instances on AMP and puts them into a dictionary.\n {'InstanceID': AMPAPI class}"""
        global InstancesFound
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstances',parameters) 
        #pprint(result)
        serverlist = {}
        if len(result["result"][0]['AvailableInstances']) != 0:
            InstancesFound = True
            for i in range(0,len(result["result"][0]['AvailableInstances'])): #entry = name['result']['AvailableInstances'][0]['InstanceIDs']
                entry = result["result"][0]['AvailableInstances'][i]  

                if entry['Module'] == 'Minecraft':
                    from modules.Minecraft.amp_minecraft import AMPMinecraft as AMPMC
                    server = AMPMC(entry['InstanceID'],entry,Index = i)
                else:
                    server = AMPInstance(entry['InstanceID'],entry,Index = i)
                serverlist[server.InstanceID] = server

            return serverlist
        else:
            InstancesFound = False
            logger.critical(f'Please ensure the permissions are set correctly, the Bot cannot find any AMP Instances at this time...')
            time.sleep(30)
            

    @Login  
    def ConsoleUpdate(self):
        """Returns `{'ConsoleEntries':[{'Contents': 'String','Source': 'Server thread/INFO','Timestamp': '/Date(1651703130702)/','Type': 'Console'}]`\n
        Will post all updates from previous API call of console update"""
        #print('Console update')
        parameters = {}
        # Will post all updates from previous API call of console update.
        result = self.CallAPI('Core/GetUpdates', parameters)
        return result

    @Login
    def ConsoleMessage_withUpdate(self,msg):
        """This will call Console Update after sending the Console Message (Use this for Commands that require feedback)"""
        msg = ' '.join(msg)
        parameters = {'message': msg}
        #print(parameters)
        self.CallAPI('Core/SendConsoleMessage', parameters)
        time.sleep(0.5)
        update = self.ConsoleUpdate()
        return update

    @Login
    def COnsoleMessage(self,msg):
        """Basic Console Message"""
        msg = ' '.join(msg)
        parameters = {'message': msg}
        #print(parameters)
        self.CallAPI('Core/SendConsoleMessage', parameters)
        return

    @Login
    def StartInstance(self):
        parameters = {}
        self.CallAPI('Core/Start', parameters)
        return

    @Login
    def StopInstance(self):
        parameters = {}
        self.CallAPI('Core/Stop', parameters)
        return

    @Login
    def RestartInstance(self):
        parameters = {}
        self.CallAPI('Core/Restart', parameters)
        return

    @Login
    def KillInstance(self):
        parameters = {}
        self.CallAPI('Core/Kill', parameters)
        return

    @Login
    def getStatus(self):
        """CPU is percentage based <tuple>
        """
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
    
    @Login
    def getUserList(self):
        """Returns a List of connected users."""
        parameters = {}
        result = self.CallAPI('Core/GetUserList', parameters)
        user_list = []
        for user in result['result']:
            user_list.append(result['result'][user])
        return user_list

    @Login
    def getSchedule(self):
        parameters = {}
        result = self.CallAPI('Core/GetScheduleData', parameters)
        return result['result']['PopulatedTriggers']
  
    def setFriendlyName(self,instance,name,description):
        """This is used to change an Instance's Friendly Name and or Description. Retains all previous settings. \n
        `This requires the instance to be Offline!`"""
        parameters = {
                'InstanceId' : instance.InstanceID,
                'FriendlyName': name,
                'Description' : description,
                'StartOnBoot': instance.DaemonAutostart,
                'Suspended' : instance.Suspended,
                'ExcludeFromFirewall': instance.ExcludeFromFirewall,
                'RunInContainer': instance.IsContainerInstance,
                'ContainerMemory' : instance.ContainerMemoryMB,
                'MemoryPolicy' : instance.ContainerMemoryPolicy,
                'ContainerMaxCPU': instance.ContainerCPUs}
        response = f'{instance.FriendlyName} is about to be changed to {name}; this will restart the instance.'
        self.CallAPI('ADSModule/UpdateInstanceInfo', parameters)
        #print(result)
        return response

    @Login
    # Test AMP API calls with this function
    def getAPItest(self):
        parameters = {}
        result = self.CallAPI('Core/GetModuleInfo', parameters)
        #pprint(result)
        return result

    @Login
    def addTask(self,triggerID,methodID,parammap):
        parameters = {
                'TriggerID' : triggerID,
                'MethodID' : methodID,
                'ParameterMapping' : parammap
                }
        self.CallAPI('Core/AddTask', parameters)
        return

    @Login
    def copyFile(self,source,destination):
        parameters = {
            'Origin' : source,
            'TargetDirectory' : destination
        }
        self.CallAPI('FileManagerPlugin/CopyFile', parameters)
        return

    @Login
    def renameFile(self,original,new):
        parameters = {
            'Filename' : original,
            'NewFilename' : new
        }
        self.CallAPI('FileManagerPlugin/RenameFile', parameters)
        return

    @Login
    def getDirectoryListing(self,directory):
        parameters = {
            'Dir' : directory
            }
        result = self.CallAPI('FileManagerPlugin/GetDirectoryListing',parameters)
        return result

    @Login    
    def getFileChunk(self,name,position,length):
        parameters = {
            'Filename' : name,
            'Position' : position,
            'Length' : length
        }
        result = self.CallAPI('FileManagerPlugin/GetFileChunk',parameters)
        return result

    @Login
    def writeFileChunk(self,filename,position,data):
        parameters = {
            'Filename' : filename,
            'Position' : position,
            'Data' : data
        }
        self.CallAPI('FileManagerPlugin/WriteFileChunk', parameters)
        return

    @Login
    def endUserSession(self,sessionIDold):
        parameters = {
            'Id' : sessionIDold
        }
        result = self.CallAPI('Core/EndUserSession', parameters)
        #print(f'Ended user Session {sessionIDold}')
        return

    @Login
    def getActiveAMPSessions(self):
        parameters = {}
        result = self.CallAPI('Core/GetActiveAMPSessions', parameters)
        return result

    @Login
    def getInstanceStatus(self):
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstanceStatuses', parameters)

        return result

    @Login
    def trashDirectory(self,dirname):
        parameters = {
            'DirectoryName' : dirname
        }
        result = self.CallAPI('FileManagerPlugin/TrashDirectory',parameters)
        return result

    @Login
    def trashFile(self,filename):
        parameters = {
            'Filename' : filename
        }
        result = self.CallAPI('FileManagerPlugin/TrashFile',parameters)
        return result
    
    @Login
    def emptyTrash(self,trashdir):
        parameters = {
            'TrashDirectoryName' : trashdir
        }
        result = self.CallAPI('FileManagerPlugin/EmptyTrash',parameters)
        return result

    @Login
    def takeBackup(self,title, description, sticky = False):
        parameters = {
            'Title' : title,
            'Description' : description,
            'Sticky' : sticky
        }
        result = self.CallAPI('LocalFileBackupPlugin/TakeBackup',parameters)
        return result

    #TODO - Need to fix list
    # def sessionCleanup(self):
    #     global SessionIDlist
    #     sessions = self.getActiveAMPSessions()
    #     for entry in sessions['result']:
    #         if entry['Username'] == tokens.AMPUser:
    #             if entry['SessionID'] not in SessionIDlist:
    #                 self.endUserSession(entry['SessionID'])
    #     return

    @Login
    def addWhitelist(self,user):
        """Base Function for AMP.addWhitelist"""
        return user

    @Login
    def getWhitelist(self):
        """Base Function for AMP.getWhitelist"""
        return

    @Login
    def removeWhitelist(self,user):
        """Base Function for AMP.removeWhitelist"""
        return user

    @Login
    def name_Conversion(self,user):
        """Base Function for AMP.name_Conversion"""
        return user

    @Login
    def name_History(self,user):
        """Base Function for AMP.name_History"""
        return user

    

class AMPConsole:
    def __init__(self, AMPInstance = AMPInstance):
        self.AMPInstance = AMPInstance

        self.DB = main_DB
        self.DB_Server = self.DB.GetServer(self.AMPInstance.InstanceID)

        self.uBot = utils.botUtils(__client)
        self.dBot = utils.discordBot(__client)

        self.console_thread = None
        self.console_thread_running = False

        try:
            self.console = self.DB_Server.Console
            self.console_filter = self.DB_Server.Console_Filtered
            self.console_channel = self.uBot.channelparse(self.DB_Server.DiscordConsoleChannel)
        except:
            self.console = False
            self.console_filter = False
            self.console_channel = None

        self.console_message_list = []

        self.console_start()
     
    async def console_start(self):
        """This starts our console threads..."""
        if self.console:
            global AMP_Console_Threads
            try:
                self.console_thread = threading.Thread(self.console_parse())
                self.console_thread_running = True
                AMP_Console_Threads[self.AMPInstance.InstanceID] = AMPConsole
                logging.info(f'Initiating Server Console for {self.AMPInstance.FriendlyName}...')
            except Exception as e:
                AMP_Console_Threads[self.AMPInstance.InstanceID] = AMPConsole
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
                        logger.error(f'Unable to Send Console Message...{e}')

                    bulkentry = entry + '\n'

            if len(bulkentry):
                try: #!TODO Needs to be Tested!
                    await self.dBot.sendMessage(self.console_channel,bulkentry[:-1])
                    #await self.send_message(bulkentry[:-1])
                except Exception as e:
                    logger.error(f'Unable to Send Console Message...{e}')
        return
    
    async def console_filter(self,message):
        """This will filter depending on the console_filter setting and handle what to send to Discord."""
        print(message)
        return True

    async def console_chat(self,message):
        """This will handle all player chat messages from AMP to Discord"""
        print(message)
        return True



    

    

    