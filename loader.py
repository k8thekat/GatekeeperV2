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
import logging
import pathlib
import importlib.util
import traceback

#prebuilt packages
import discord

#custom scripts
from AMP_Handler import AMPHandler
from AMP import AMPInstance

#loop = asyncio.new_event_loop()
loaded = []

class Handler():
    """This is the Basic Module Loader for AMP to Discord Integration/Interactions"""
    def __init__(self, client:discord.Client):
        self._client = client

        self._cwd = pathlib.Path.cwd()
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger()

        self.AMPHandler: AMPHandler = AMPHandler()
        self.AMP: AMPInstance = self.AMPHandler.AMP
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMP_Modules = self.AMPHandler.AMP_Modules
        self.Cog_Modules = {}

        self.logger.info(f'**SUCCESS** Initializing {self.name.capitalize()} ')
        
    async def module_auto_loader(self):
        """This loads all the required Cogs/Scripts for each unique AMPInstance.Module type"""
        try:
            dir_list = self._cwd.joinpath('modules').iterdir()

            for folder in dir_list:
                file_list = folder.glob('cog_*.py')

                for script in file_list:
                    module_name = script.name[4:-3].capitalize()
                    spec = importlib.util.spec_from_file_location(module_name, script)
                    class_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(class_module)

                    for DIS in getattr(class_module,f'DisplayImageSources'):
                        self.Cog_Modules[DIS] = script
                    
                    self.logger.dev(f'**SUCCESS** {self.name} Found Server Cog Module **{module_name}**')
                    
        except Exception as e:
            self.logger.error(f'**ERROR** {self.name} Finding Server Cog Module ** - File Not Found {traceback.format_exc()}')

        #Just to make it easier; always load the Generic Module as a base.
        await self._client.load_extension('modules.Generic.generic')
        self.logger.dev(f'**SUCCESS** {self.name} Loading Server Cog Module **Generic**')
        loaded.append('Generic')

        #This loads the Cog Module if it finds a Instance that requires said Module.
        for instance in self.AMPInstances:
            DisplayImageSource = self.AMPInstances[instance].DisplayImageSource
            if DisplayImageSource in self.Cog_Modules:
                path = self.Cog_Modules[DisplayImageSource]
                cog = (".").join(path.as_posix().split("/")[-3:])[:-3]
                try:
                    await self._client.load_extension(cog)
                    self.logger.info(f'**SUCCESS** {self.name} Loading Server Cog Module **{path.stem}**')

                except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                    continue
                
                except Exception as e:
                    self.logger.error(f'**ERROR** {self.name} Loading Server Cog Module **{path.stem}** - {traceback.format_exc()}')
     
        self.logger.info(f'**All Server Modules Loaded**')

    async def cog_auto_loader(self, reload= False):
        """This will load all Cogs inside of the cogs folder."""
        path = f'cogs' #This gets us to the folder for the module specific scripts to load via the cog.

        loaded_cogs = []
        #Grab all the cogs inside my `cogs` folder and duplicate the list.
        cog_file_list = pathlib.Path.joinpath(self._cwd,'cogs').iterdir()
        cur_cog_file_list = list(cog_file_list)

        #This while loop will force it to load EVERY cog it finds until the list is empty.
        while len(cur_cog_file_list) > 0:
            for script in cur_cog_file_list:
                #Ignore Pycache or similar files.
                #Lets Ignore our Custom Permisisons Cog. We will load it on-demand.
                if script.name.startswith('__') or script.name.lower() == 'permissions_cog.py' or not script.name.endswith('.py'):
                    cur_cog_file_list.remove(script)
                    continue

                module_name = script.name[:-3].title() #File name ofc.
                spec = importlib.util.spec_from_file_location(module_name, script)
                class_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(class_module)


                module_dependencies = getattr(class_module, f'Dependencies')
                self.logger.dev(f"Checking Dependencies on {script.name}")
                if module_dependencies != None:
                    
                    missing_dependencies = False
                    for dependency in module_dependencies:
                        #If the cog we need isnt loaded; skip. We will come back around to it.
                        if dependency.lower() not in loaded_cogs:
                            missing_dependencies = True
                            break

                    #If our Cogs dependecies are missing; lets go onto our next cog.
                    if missing_dependencies:
                        self.logger.dev(f"Missing Dependencies: {dependency.lower()} for {script.name}")
                        continue

                    
                cog = f'{path}.{script.name[:-3]}'

                try:
                    if reload:
                        await self._client.reload_extension(cog)
                        loaded_cogs.append(script.name.lower()) #Append to our loaded cogs for dependency check
                        cur_cog_file_list.remove(script) #Remove the entry from our cog list; so we don't attempt to load it again.

                    else:
                        await self._client.load_extension(cog)
                        loaded_cogs.append(script.name.lower()) #Append to our loaded cogs for dependency check
                        cur_cog_file_list.remove(script) #Remove the entry from our cog list; so we don't attempt to load it again.

                    self.logger.dev(f'**FINISHED LOADING** {self.name} -> **{cog}**')

                #If the cog is already loaded; we still need to remove it from the list.
                # except discord.ext.commands.errors.ExtensionAlreadyLoaded:
                #     cur_cog_file_list.remove(script) 
                #     self.logger.error(f"**ERROR** Loading Cog {script.name}** - Extension Already Loaded {traceback.format_exc()}")
                #     continue

                # except FileNotFoundError as e:
                #     cur_cog_file_list.remove(script) 
                #     self.logger.error(f'**ERROR** Loading Cog {script.name}** - File Not Found {traceback.format_exc()}')
                #We just need to catch the error; we won't do anything else with it.
                
                except Exception as e:
                    cur_cog_file_list.remove(script) 
                    self.logger.dev(f'Removed cog from loader list: {script.name}')
                    self.logger.error(f'**ERROR** Loading Cog {script.name}** - {e} {traceback.format_exc()}')
                    continue
                
        self.logger.info(f'**All Cog Modules Loaded**')

                



