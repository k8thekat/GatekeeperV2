#Module
import sys
import os
import asyncio
import time
import logging
import importlib
import pathlib

#prebuilt packages
import discord
from discord.ext import commands 

#custom scripts
import modules.AMP as AMP

#CWD = os.getcwd()
loop = asyncio.new_event_loop()
loaded = []


# def init(client):
#     while client.is_ready() == False:
#         time.sleep(1)
#     test = ModuleHandler(client)

def testing(client):
    print('Module Testing',client)
    #import modules.modulecommands as modulecommands
    #test2 = modulecommands.init(client)
    #test.__init__(client)




#class ModuleHandler(commands.Cog):
class ModuleHandler():
    """This is the Basic Module Loader for AMP to Discord Integration/Interactions"""
    def __init__(self,client):
        self._client = client

        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger()
        self.logger.info(f'{self.name.capitalize()} Initializing...')

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMP_Modules = self.AMPHandler.AMP_Modules

        #await self.cog_auto_loader()
        
    async def cog_auto_loader(self):
        """This loads all the required Cogs/Scripts for each unique AMPInstance.Module type"""

        #Just to make it easier; always load the Generic Module as a base.
        await self._client.load_extension('modules.GenericModule.Generic')
        self.logger.info(f'**SUCCESS** Loading Module **modules.GenericModule.Generic**')
        loaded.append('Generic')

        for instance in self.AMPInstances:
            module = self.AMPInstances[instance].Module

            #This is used to differentiate AMP Servers that use the Generic Template so we can properly handle other server types such as Starbound and Valheim; even though they rely on AMP's Generic Module.
            if module == 'GenericModule':
                module = self.AMPInstances[instance].ModuleDisplayName

            if module not in loaded:
                #print(module)
                path = f'modules.{module}' #This gets us to the folder for the module specific scripts to load via the cog.
                try:
                    module_file_list = pathlib.Path.joinpath(self._cwd,'modules',module).iterdir()
                    #module_file_list = os.listdir(self._cwd + '\\' + path.replace('.','\\')) #This gets me the list of files in the directory
                    #print('File List', module_file_list)

                    for script in module_file_list:
                        if script.name.endswith('.py') and not script.name.lower().startswith('amp'):
                            cog = f'{path}.{script.name[:-3]}'
                            #print('This is my cog var:',cog)

                            #TODO -- This needs testing.
                            try:
                                await self._client.load_extension(cog) #We will load the scripts like a cog to access the commands and functions.
                                loaded.append(module)
                                self.logger.info(f'**SUCCESS** Loading Cog Module **{cog}**')
                                continue

                            except Exception as e:
                                self.logger.error(f'**ERROR** Loading Cog Module **{cog}** - {e}')
                                continue
                        
                except FileNotFoundError as e:
                    self.logger.error(f'**ERROR** Loading Module ** - File Not Found {e}')

                #     # try:
                #     #     await self._client.load_extension('modules.GenericModule.Generic')
                #     #     loaded.append(module)
                #     except Exception as e:
                #         self.logger.error(f'**ERROR** Loading Module **modules.GenericModule.Generic** - {e}')
                #     else:
                #         self.logger.info(f'**SUCCESS** Loading Module **modules.GenericModule.Generic**')
                        
        self.logger.info(f'**All Modules Loaded**')
                



