#Module
import sys
import os
import asyncio
import time
import logging

#prebuilt packages
import discord
from discord.ext import commands 

#custom scripts
import modules.AMP as AMP

CWD = os.getcwd()
loop = asyncio.new_event_loop()
loaded = []

def init(client):
    while client.is_ready() == False:
        time.sleep(1)
    test = ModuleHandler(client)

def testing(client):
    print('Module Testing',client)
    #import modules.modulecommands as modulecommands
    #test2 = modulecommands.init(client)
    #test.__init__(client)

#class ModuleHandler(commands.Cog):
class ModuleHandler():
    """This is the Basic Module Loader for AMP to Discord Integration/Interactions"""
    def __init__(self,client):
        self.logger = logging.getLogger()
        self.logger.info('Modules Initializing...')
        self._client = client
        self.AMP = AMP.getAMP()
        self.AMPInstances = AMP.AMP_Instances
        self.cog_auto_loader()

    def cog_auto_loader(self):
        """This loads all the required Cogs/Scripts for each unique AMPInstance.Module type"""
        global CWD
        #print(f'My Current Working Directory: {CWD}')
        for instance in self.AMPInstances:
            module = self.AMPInstances[instance].Module
            if module == 'GenericModule':
                module = self.AMPInstances[instance].ModuleDisplayName
            if module not in loaded:
                #print(module)
                path = f'modules.{module}' #This gets us to the folder for the module specific scripts to load via the cog.
                try:
                    module_file_list = os.listdir(CWD + '\\' + path.replace('.','\\')) #This gets me the list of files in the directory
                    #print('File List', module_file_list)

                    for script in module_file_list:
                        if script.endswith('.py') and not script.startswith('AMP'):
                            cog = f'{path}.{script[:-3]}'
                            #print('This is my cog var:',cog)
                            #TODO -- This needs testing.
                            try:
                                self._client.load_extension(cog) #We will load the scripts like a cog to access the commands and functions.
                                loaded.append(module)

                            except Exception as e:
                                self.logger.error(f'**ERROR** Loading Module **{cog}** - {e}')
                            else:
                                self.logger.info(f'**SUCCESS** Loading Module **{cog}**')
                
                except FileNotFoundError:
                    try:
                        self._client.load_extension('modules.GenericModule.Generic')
                        loaded.append(module)
                    except Exception as e:
                        self.logger.error(f'**ERROR** Loading Module **modules.GenericModule.Generic** - {e}')
                    else:
                        self.logger.info(f'**SUCCESS** Loading Module **modules.GenericModule.Generic**')
                        
                



