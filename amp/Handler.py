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
import os
import sys
import importlib.util
from argparse import Namespace
import time
import re
import traceback
from threading import Thread
import requests


from DB import DBConfig, DBHandler, Database
from amp.Instance import AMPInstance

from dotenv.main import load_dotenv
import os


class AMPHandler():
    load_dotenv()
    AMP_SETUP: bool = False
    FAILED_CONNECTION: int = 0

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(AMPHandler, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self, args: Namespace | None = None) -> None:
        self._args: Namespace | None = args
        self._logger = logging.getLogger()
        self._name = os.path.basename(__file__)

        # AMP specific settings.
        self._AMP2FA: bool = False
        self._superUser: bool = False
        # self._session_IDs: dict[str, str] = {}
        self._AMP_Modules: dict[str, AMPInstance] = {}
        self._AMP_Instances: dict[str, AMPInstance] = {}
        self._AMP_Console_Modules: dict[str, AMPInstance] = {}
        self._AMP_Console_Threads: dict[str, Thread] = {}

        self._SuccessfulConnection: bool = False

        self._DBHandler: DBHandler = DBHandler()
        self._DB: Database = self._DBHandler.DB  # Main Database object
        self._DBConfig: DBConfig = self._DBHandler.DBConfig
        self._moduleHandler()

        self._Core_AMP: AMPInstance = self._setup_AMPInstances()
        self._logger.dev("Checking for AMP Instances(s)...")  # type:ignore
        self._instanceValidation(AMP=self._Core_AMP, startup=True)
        # called last; this puts AMP Handler into a state of constantly checking for instances.
        self._instance_check_loop()

    def _instance_check_loop(self):
        """Checks for new AMP Instances every 30 seconds.."""
        while True:
            self._instanceValidation(AMP=self._Core_AMP)
            self._Core_AMP._instance_ThreadManager()
            time.sleep(30)

    def _setup_AMPInstances(self) -> AMPInstance:
        """Creates Core AMP Instance, Target Instances Objects.
        Removes Super Admin Role from AMP Gatekeeper Role unless -super"""
        self._Core_AMP = AMPInstance()  # This is what starts it all.
        self._instanceValidation(AMP=self._Core_AMP, startup=True)

        # By the time the core AMP Instance returns super_AdminID should be set..
        # This removes Super Admins from the bot user! Controlled through parser args!
        if self._args != None and not self._args.super and not self._args.dev:  # type:ignore

            self._Core_AMP.setAMPUserRoleMembership(self._Core_AMP.AMP_UserID, self._Core_AMP.super_AdminID, False)
            self._logger.warning(f"***ATTENTION*** Removing {self._Core_AMP.AMPUSER} from `Super Admins` Role!")
        return self._Core_AMP

    def _get_AMP_instance_names(self, public: bool = False) -> dict[str, str]:
        """Creates a list of Instance Names/DisplayName or Friendly Name."""
        AMP_Instances_Names_dict: dict[str, str] = {}

        for instanceID, server in self._AMP_Instances.items():
            # If this is a "Public" Server Autocomplete or List/etc lets not SHOW our Hidden servers.
            if public and server.Hidden:
                continue

            # Using _TargetName as a unique identifier for the server if they match names.
            if server.DisplayName != None:
                server_name: str = server.DisplayName

            else:
                if server.FriendlyName not in AMP_Instances_Names_dict:
                    server_name = server.FriendlyName

                else:
                    server_name = server.InstanceName

            if hasattr(server, "_TargetName") and server._TargetName != None:
                server_name = f'({server._TargetName}) | ' + server_name
                # _TargetName = f'({server._TargetName}) | '

            else:
                AMP_Instances_Names_dict[instanceID] = server_name

        return AMP_Instances_Names_dict

    def _moduleHandler(self):
        """Creates a Dictionary of AMP_Modules and AMP_Console_Modules to be loaded later."""
        self._logger.dev('AMPHandler moduleHandler checking modules...')  # type:ignore
        try:
            dir_list = self._cwd.joinpath('modules').iterdir()
            for folder in dir_list:
                file_list = folder.glob('amp_*.py')
                for script in file_list:
                    module_name = script.name[4:-3].capitalize()
                    try:
                        spec = importlib.util.spec_from_file_location(module_name, script)
                        class_module = importlib.util.module_from_spec(spec)  # type:ignore
                        spec.loader.exec_module(class_module)  # type:ignore

                        for DIS in getattr(class_module, f'DisplayImageSources'):
                            self._AMP_Modules[DIS] = getattr(class_module, f'AMP{module_name}')
                            self._AMP_Console_Modules[DIS] = getattr(class_module, f'AMP{module_name}Console')

                        self._logger.dev(f'**SUCCESS** {self._name} Adding AMP Module **{module_name}**')  # type:ignore

                    except Exception as e:
                        self._logger.error(f'**ERROR** {self._name} Adding AMP Module **{module_name}** - {traceback.format_exc()}')
                        continue

        except Exception as e:
            self._logger.error(f'**ERROR** {self._name} Loading AMP Module ** - File Not Found {traceback.format_exc()}')

    def _instanceValidation(self, AMP: AMPInstance, startup: bool = False):
        """Creates AMP Instance Objects when `startup = True` 
        Checks if any new instances have been created since last check. If so, updates self._AMP_Instances with new objects."""
        result = AMP.getInstances()
        amp_instance_keys = list(self._AMP_Instances.keys())  # This could be empty on startup;
        available_instances = []
        # if len(result["result"][0]['AvailableInstances']) == 0:
        if len(result[0]['AvailableInstances']) == 0:
            self._logger.critical(f'***ATTENTION*** Please ensure the permissions are set correctly, the Bot cannot find any AMP Instances at this time...')

            self.FAILED_CONNECTION += 1
            if self.FAILED_CONNECTION == 5:
                self._logger.critical(f"Failed Multiple Instance lookups; exiting...")
                sys.exit(1)

            else:
                time.sleep(30)

        # for Target in result["result"]:
        for Target in result:
            for amp_instance in Target['AvailableInstances']:  # entry = name['result']['AvailableInstances'][0]['InstanceIDs']

                if amp_instance['Module'] == 'ADS':
                    continue

                # This exempts the AMPTemplate Gatekeeper *hopefully* by looking at the url for the banner image; which should contain the word Gatekeeper in it.
                # This could fail if I ever design another service/template and store the display image in the same repo; unlikely though.
                flag_reg = re.search("(gatekeeper)", amp_instance['DisplayImageSource'].lower())
                # If the flag exists and finds a match, lets continue
                if flag_reg != None and flag_reg.group():
                    continue

                # Creating a new list of Instances with just their IDs.
                available_instances.append(amp_instance['InstanceID'])

                if amp_instance['InstanceID'] in amp_instance_keys:
                    continue

                if not startup:
                    self._logger.info(f'Found a New AMP Instance since Startup; Creating AMP Object for {amp_instance["FriendlyName"]}')

                if amp_instance['DisplayImageSource'] in self._AMP_Modules:
                    name = str(self._AMP_Modules[amp_instance["DisplayImageSource"]]).split("'")[1]
                    image_source = amp_instance['DisplayImageSource']
                else:
                    name = "Generic"
                    image_source = "Generic"

                self._logger.dev(f'Loaded __{name}__ for {amp_instance["FriendlyName"]}')  # type:ignore
                server: AMPInstance = self._AMP_Modules[image_source](instanceID=amp_instance['InstanceID'], serverdata=amp_instance, Handler=self)
                self._AMP_Instances[server.InstanceID] = server

        # AMPHandler AMP Instances will be empty on first startup; we need to NOT compare for any missing instances.
        if startup:
            return

        for instanceID in amp_instance_keys:
            if instanceID not in available_instances:
                amp_server = self._AMP_Instances[instanceID]
                self._logger.warning(f'Found the AMP Instance {amp_server.InstanceName} that no longer exists.')
                self._logger.warning(f'Removing {amp_server.InstanceName} from `Gatekeepers` available Instance list.')
                self._AMP_Instances.pop(instanceID)
