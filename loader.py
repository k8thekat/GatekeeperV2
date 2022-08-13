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
import os
import asyncio
import logging
import pathlib
import importlib.util

#prebuilt packages
from discord.ext import commands 

#custom scripts
import AMP

loop = asyncio.new_event_loop()
loaded = []



class Handler():
    """This is the Basic Module Loader for AMP to Discord Integration/Interactions"""
    def __init__(self,client:commands.Bot):
        self._client = client

        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger()

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMP_Modules = self.AMPHandler.AMP_Modules
        self.Cog_Modules = {}

        self.logger.info(f'**SUCCESS** Initializing... {self.name.capitalize()} ')
        #await self.cog_auto_loader()
        
    async def module_auto_loader(self):
        """This loads all the required Cogs/Scripts for each unique AMPInstance.Module type"""
        #Just to make it easier; always load the Generic Module as a base.
        await self._client.load_extension('modules.Generic.generic')
        self.logger.dev(f'**SUCCESS** {self.name} Loading Cog Module **modules.Generic.generic**')
        loaded.append('Generic')
        try:
            dir_list = self._cwd.joinpath('modules').iterdir()
            for folder in dir_list:
                file_list = folder.glob('cog_*.py')
                for script in file_list:
                    module_name = script.name[4:-3].capitalize()
                    try:
                        #print(script)
                        spec = importlib.util.spec_from_file_location(module_name, script)
                        class_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(class_module)
                        #if instance['DisplayImageSource'] in self.AMPHandler.AMP_Modules:
                        for DIS in getattr(class_module,f'DisplayImageSources'):
                            print(DIS,script)
                            self.Cog_Modules[DIS] = script
                        
                        self.logger.dev(f'**SUCCESS** {self.name} Loading Cog Module **{module_name}**')
                    except Exception as e:
                        self.logger.error(f'**ERROR** {self.name} Loading Cog Module **{module_name}** - {e}')
                        continue

                    
   
        except Exception as e:
            self.logger.error(f'**ERROR** {self.name} Loading Cog Module ** - File Not Found {e}')
                    
        for instance in self.AMPInstances:
            DisplayImageSource = self.AMPInstances[instance].DisplayImageSource
            print('DIS', self.AMPInstances[instance].DisplayImageSource)
            if DisplayImageSource in self.Cog_Modules:
                path = self.Cog_Modules[DIS]
                path = self._cwd.joinpath('modules')
                print(path.)
                print(path.as_posix())
                print(path.absolute())
                #cog = f'{self.Cog_Modules[DIS].as_posix().replace("/",".")}.{script.name[:-3]}'
                #print('cog',cog)
                #await self._client.load_extension()

        #     #This is used to differentiate AMP Servers that use the Generic Template so we can properly handle other server types such as Starbound and Valheim; even though they rely on AMP's Generic Module.
        #     if module == 'GenericModule':
        #         module = self.AMPInstances[instance].ModuleDisplayName

        #     if module not in loaded:
        #         #print(module)
        #         path = f'modules.{module}' #This gets us to the folder for the module specific scripts to load via the cog.
        #         try:
        #             module_file_list = pathlib.Path.joinpath(self._cwd,'modules',module).iterdir()
        #             #module_file_list = os.listdir(self._cwd + '\\' + path.replace('.','\\')) #This gets me the list of files in the directory
        #             #print('File List', module_file_list)

        #             for script in module_file_list:
        #                 if script.name.endswith('.py') and not script.name.lower().startswith('amp'):
        #                     cog = f'{path}.{script.name[:-3]}'
        #                     #print('This is my cog var:',cog)

        #                     try:
        #                         await self._client.load_extension(cog) #We will load the scripts like a cog to access the commands and functions.
        #                         loaded.append(module)
        #                         self.logger.dev(f'**SUCCESS** {self.name} Loading Cog Module **{cog}**')
        #                         continue

        #                     except Exception as e:
                                
        #                         self.logger.error(f'**ERROR** {self.name} Loading Cog Module **{cog}** - {e}')
        #                         continue
                        
        #         except FileNotFoundError as e:
        #             self.logger.error(f'**ERROR** {self.name} Loading Module ** - File Not Found {e}')
                    

                        
        self.logger.info(f'**All Modules Loaded**')

    async def cog_auto_loader(self):
        """This will load all Cogs inside of the cogs folder needed for interaction with DB and AMP"""
        path = f'cogs' #This gets us to the folder for the module specific scripts to load via the cog.
        try:
            cog_file_list = pathlib.Path.joinpath(self._cwd,'cogs').iterdir()
            for script in cog_file_list:
                if script.name.endswith('.py'):
                    cog = f'{path}.{script.name[:-3]}'

                    try:
                        await self._client.load_extension(cog) 
                        self.logger.dev(f'**SUCCESS** {self.name} Loading Cog **{cog}**')
                        continue

                    except Exception as e:
                        self.logger.error(f'**ERROR** {self.name} Loading Cog **{cog}** - {e}')
                        continue
                
        except FileNotFoundError as e:
            self.logger.error(f'**ERROR** Loading Cog ** - File Not Found {e}')
            

                



