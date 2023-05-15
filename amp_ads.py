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
import traceback
from importlib.util import spec_from_file_location, module_from_spec
from argparse import Namespace
from typing import Union
import time

from amp_api import AMP_API
from amp_instance import AMP_Instance


class AMP_ADS(AMP_API):
    """Main AMP window aka Web GUI"""
    _ampModules: list = []
    _ampConsoleModules: list = []
    _ampInstances: dict[str, str] = {}

    Port: str = ""
    Module: str = "ADS"

    # permission attrs
    AMPUSER_id: str
    AMPUSER_info: dict
    SUPERADMIN_roleID: str
    _roleID: str
    _role_exists: bool = False
    _have_role: bool = False
    _have_superAdmin: bool = False

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(AMP_ADS, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self, session_id: str = '0', args: Namespace | None = None) -> None:
        super().__init__(session_id, args)
        self._moduleHandler()

        self._perms = ['Core.*',
                       'Core.RoleManagement.*',
                       'Core.UserManagement.*',
                       'Instances.*',
                       'ADS.*',
                       'Settings.*',
                       'ADS.InstanceManagement.*',
                       'FileManager.*',
                       'LocalFileBackup.*',
                       'Core.AppManagement.*']

    async def getInstances(self):
        results = await super().getInstances()
        for target in results["result"]:
            for amp_instance in target['AvailableInstances']:  # entry = name['result']['AvailableInstances'][0]['InstanceIDs']

                if "ModuleDisplayName" in amp_instance:
                    # TODO -- Design method to prevent Gatekeeper from being noticed.
                    if amp_instance["ModuleDisplayName"] == "GatekeeperV2 Bot":
                        continue

                elif "Module" in amp_instance:
                    # the main Web UI is called `ADS`
                    if amp_instance['Module'] == 'ADS':
                        continue

                    elif amp_instance["Module"] == "GenericModule":
                        server_type = amp_instance["DeploymentArgs"]["GenericModule.Meta.DisplayName"]

                    else:
                        server_type = amp_instance["Module"]

                if server_type not in self._ampModules:
                    server_type = "Generic"

                server: AMP_Instance = self._ampModules[server_type](serverdata=amp_instance)
                self._ampInstances[server.InstanceID] = server

        # # AMPHandler AMP Instances will be empty on first startup; we need to NOT compare for any missing instances.
        # if startup:
        #     return

        # for instanceID in amp_instance_keys:
        #     if instanceID not in available_instances:
        #         amp_server = self._AMP_Instances[instanceID]
        #         self._logger.warning(f'Found the AMP Instance {amp_server.InstanceName} that no longer exists.')
        #         self._logger.warning(f'Removing {amp_server.InstanceName} from `Gatekeepers` available Instance list.')
        #         self._AMP_Instances.pop(instanceID)

        return results

    def _moduleHandler(self):
        """Creates a dictionary of AMP Instance class modules and AMP Console class modules."""
        try:
            dir_list = self._cwd.joinpath('modules').iterdir()
            for folder in dir_list:
                file_list = folder.glob('amp_*.py')
                for script in file_list:
                    module_name = script.name[4:-3].capitalize()
                    try:
                        spec = spec_from_file_location(module_name, script)
                        class_module = module_from_spec(spec)
                        spec.loader.exec_module(class_module)

                        for server_type in getattr(class_module, f'DisplayImageSources'):
                            self._ampModules[server_type] = getattr(class_module, f'AMP{module_name}')
                            self._ampConsoleModules[server_type] = getattr(class_module, f'AMP{module_name}Console')

                    except Exception as e:
                        print(e)
                        self._logger.error(f'**ERROR** Adding AMP Module **{module_name}** | Exception: {traceback.format_exc()}')
                        continue

        except Exception as e:
            print(e)
            self._logger.error(f'**ERROR** Loading AMP Module ** - File Not Found | Exception: {traceback.format_exc()}')

    # All Permission related methods ---------------------------------------------------

    def _updateInstanceAttributes(self):
        """This updates an AMP Server Objects attributes from `getInstances()` API call."""
        if (not self._initialized) or (time.time() - self.Last_Update_Time < 5):
            return

        if self._last_update_time_lock.acquire(blocking=False) == False:
            return

        self.Login()
        parameters = {}
        result = self.CallAPI('ADSModule/GetInstances', parameters)

        if type(result) == bool:
            self.logger.error(f'Failed to update {self.FriendlyName} attributes, API Call returned {result}')
            return

        if len(result["result"][0]['AvailableInstances']) != 0:
            for Target in result["result"]:
                for instance in Target['AvailableInstances']:  # entry = name['result']['AvailableInstances'][0]['InstanceIDs']
                    # This should be a list of my AMP Servers [{'InstanceID': '<AMP Instance Object>'}]
                    for amp_instance in self.AMPHandler.AMP_Instances:
                        # This should be the <AMP Instance Object> comparing to the Instance Objects we got from `getInstances()`
                        if self.AMPHandler.AMP_Instances[amp_instance].InstanceID == instance['InstanceID']:
                            # This gets all the dictionary values tied to AMP and makes them attributes of self.
                            for entry in instance:
                                setattr(self.AMPHandler.AMP_Instances[amp_instance], entry, instance[entry])
                            break

        self.Last_Update_Time = time.time()
        self._last_update_time_lock.release()
