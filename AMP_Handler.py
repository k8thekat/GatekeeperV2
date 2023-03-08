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
import logging
import pathlib
import os, sys
import importlib
from argparse import Namespace
import time
import re
import traceback

import AMP
import DB

#import utils
Handler = None
AMP_setup = False

def AMP_init(args: Namespace):
    global AMP_setup
    handler = getAMPHandler(args= args)
    handler.setup_AMPInstances() 
    AMP_setup = True
    amp_server_instance_check()

def amp_server_instance_check():
    """Checks for new AMP Instances every 30 seconds.."""
    while True:
        handler = getAMPHandler()
        handler.logger.dev('Checking AMP Instance(s) Status...')
        handler._instanceValidation(AMP= handler.AMP)
        handler.AMP._instance_ThreadManager()
        time.sleep(30)

class AMPHandler():
    def __init__(self, args: Namespace):
        self.args = args
        self.logger = logging.getLogger()
        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.AMP2FA = False
        self.tokens = ''

        self.superUser = False
    
        self.SessionIDlist = {}

        self.AMP_Modules = {}
        self.AMP_Instances = {}

        self.AMP_Console_Modules = {}
        self.AMP_Console_Threads = {}

        self.SuccessfulConnection = False
        #self.InstancesFound = False

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.val_settings()
        self.moduleHandler()
       

    def setup_AMPInstances(self):
        """Intializes the connection to AMP and creates AMP_Instance objects."""
        self.AMP = AMP.AMPInstance(Handler = self)
        self._instanceValidation(AMP= self.AMP, startup= True)

        #This removes Super Admins from the bot user! Controlled through parser args!
        if not self.args.super and not self.args.dev:
            self.AMP.setAMPUserRoleMembership(self.AMP.AMP_UserID, self.AMP.super_AdminID, False) 
            self.logger.warning(f'***ATTENTION*** Removing {self.tokens.AMPUser} from `Super Admins` Role!')
    
    def get_AMP_instance_names(self, public: bool= False) -> dict[str, str]:
        """Creates a list of Instance Names/DisplayName or Friendly Name."""
        AMP_Instances_Names = {}
        for instanceID, server in self.AMP_Instances.items():
            #If this is a "Public" Server Autocomplete or List/etc lets not SHOW our Hidden servers.
            if public and server.Hidden:
                continue
            
            #Using TargetName as a unique identifier for the server if they match names.
            if server.DisplayName != None:
                server_name = server.DisplayName
             
            else:
                if server.FriendlyName not in AMP_Instances_Names:
                    server_name = server.FriendlyName
                else:
                    server_name = server.InstanceName

            if hasattr(server, 'TargetName') and server.TargetName != None:
                server_name = f'({server.TargetName}) | ' + server_name
                #TargetName = f'({server.TargetName}) | ' 

            AMP_Instances_Names[instanceID] = server_name

        return AMP_Instances_Names
    
    #Checks for Errors in Config
    def val_settings(self):
        """Validates the tokens.py settings and 2FA."""
        self.logger.info('AMPHandler is validating your token file...')
        reset = False

        if not self.args.token:
            if not self._cwd.joinpath('tokens.py').exists():
                self.logger.critical('**ERROR** Missing file tokens.py, please rename tokenstemplate.py or make a copy before trying again.')
                reset = True

        if self.args.dev and pathlib.Path('tokens_dev.py').exists():
            self.logger.dev('Using Dev Tokens File --')
            import tokens_dev as tokens

        else:
            import tokens

        self.tokens = tokens
        if not tokens.AMPurl.startswith('http://') and not tokens.AMPurl.startswith('https://'):
            self.logger.critical('** Please verify your AMPurl. It either needs "http://" or "https://" depending on your AMP/Network setup. **')
            reset = True
            
        if tokens.AMPurl.endswith('/'):
            #self.logger.warning(f'** Please remove the forward slash at the end of {tokens.AMPurl} **, we temporarily did it for you. This may break things...')
            tokens.AMPurl = tokens.AMPurl[:-1]
        
        tokens.AMPAuth = tokens.AMPAuth.strip()
        if len(tokens.AMPAuth) == 0:
            self.AMP2FA = False
        elif len(tokens.AMPAuth) < 7:
            self.logger.critical('**ERROR** Please use your 2 Factor Generator Code (Should be over 25 characters long), not the 6 digit numeric generated code that expires with time.')
            reset = True
        else:
            self.AMP2FA = True

        if reset:
            input("Press any Key to Exit")
            sys.exit(0)
    
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
                        self.logger.error(f'**ERROR** {self.name} Loading AMP Module **{module_name}** - {traceback.format_exc()}')
                        continue
   
        except Exception as e:
            self.logger.error(f'**ERROR** {self.name} Loading AMP Module ** - File Not Found {traceback.format_exc()}')
                    
    def _instanceValidation(self, AMP: AMP.AMPInstance, startup:bool = False):
        """This checks if any new instances have been created since last check. If so, updates AMP_Instances and creates the object."""
        result = AMP.getInstances()
        amp_instance_keys = list(self.AMP_Instances.keys()) #This could be empty on startup;
        available_instances = []
        if len(result["result"][0]['AvailableInstances']) == 0:
            self.logger.critical(f'***ATTENTION*** Please ensure the permissions are set correctly, the Bot cannot find any AMP Instances at this time...')
            time.sleep(30)
            return
        
        for Target in result["result"]:
            for amp_instance in Target['AvailableInstances']: #entry = name['result']['AvailableInstances'][0]['InstanceIDs']
                
                #This exempts the AMPTemplate Gatekeeper *hopefully* by looking at the url for the banner image; which should contain the word Gatekeeper in it.
                #This could fail if I ever design another service/template and store the display image in the same repo; unlikely though.
                if amp_instance['Module'] == 'ADS':
                    continue

                flag_reg = re.search("(gatekeeper)", amp_instance['DisplayImageSource'].lower())
                #If the flag exists and finds a match, lets continue
                if flag_reg != None and flag_reg.group(): 
                    continue 
                
                #Creating a new list of Instances with just their IDs.
                available_instances.append(amp_instance['InstanceID'])

                if amp_instance['InstanceID'] in amp_instance_keys:
                    continue

                if not startup:
                    self.logger.info(f'Found a New AMP Instance since Startup; Creating AMP Object for {amp_instance["FriendlyName"]}')
                    
                if amp_instance['DisplayImageSource'] in self.AMP_Modules:
                    name = str(self.AMP_Modules[amp_instance["DisplayImageSource"]]).split("'")[1]
                    image_source = amp_instance['DisplayImageSource']
                else:
                    name = "Generic"
                    image_source = "Generic"
                
                self.logger.dev(f'Loaded __{name}__ for {amp_instance["FriendlyName"]}')
                server = self.AMP_Modules[image_source](instanceID= amp_instance['InstanceID'], serverdata= amp_instance, Handler= self)
                self.AMP_Instances[server.InstanceID] = server

      
        #AMPHandler AMP Instances will be empty on first startup; we need to NOT compare for any missing instances.
        if startup:
            return
        
        for instanceID in amp_instance_keys:
            if instanceID not in available_instances:
                amp_server = self.AMP_Instances[instanceID]
                self.logger.warning(f'Found the AMP Instance {amp_server.InstanceName} that no longer exists.')
                self.logger.warning(f'Removing {amp_server.InstanceName} from `Gatekeepers` available Instance list.')
                self.AMP_Instances.pop(instanceID)

def getAMPHandler(args: Namespace= False) -> AMPHandler:
    global Handler
    if Handler == None:
        Handler = AMPHandler(args= args)
    return Handler