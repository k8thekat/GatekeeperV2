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

from amp_api import AMP_API
from amp_instance import AMP_Instance


class AMP_ADS(AMP_API):
    """Main AMP window aka Web GUI"""
    _ampModules: list = []
    _ampConsoleModules: list = []
    _ampInstances: dict[str, str] = {}
    Port: str = ""
    Module: str = "ADS"

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
    def _setup_AMPbotrole(self):
        """Creates the `Gatekeeper` role, Adds us to the Membership of that Role and sets its AMP permissions."""
        self._logger.warning('Creating the AMP role `Gatekeeper`...')
        self.createRole('Gatekeeper')
        self.setRoleIDs()
        self.AMP_UserID = self.getAMPUserID(self.AMPUSER)
        self.setAMPUserRoleMembership(self.AMP_UserID, self.AMP_BotRoleID, True)
        self._logger.warning(f'***ATTENTION*** Adding {self.AMPUSER} to `Gatekeeper` Role.')
        self.setup_Gatekeeper_Permissions()

    def check_GatekeeperRole_Permissions(self) -> bool:
        """- Will check `Gatekeeper Role` for `Permission Nodes` when we have `Super Admin` and `not InstanceID = 0`.\n
        - Checks for `Gatekeeper Role`, if we `have the Gatekeeper Role` and `Super Admin Role`
        Returns `True` if we have permissions. Otherwise `False`"""
        # If we have Super Admin; lets check for the Bot Role and if we are not on the Main Instance.
        failed = False

        self.AMP_userInfo = self.getAMPUserInfo(self.AMPUSER)  # This gets my AMP User Information
        self.AMP_userID = self.getAMPUserID(self.AMPUSER)  # This gets my AMP User ID
        self.setRoleIDs()

        # `Gatekeeper Role inside of AMP`
        if self.AMP_BotRoleID != None:
            # self.logger.dev('Gatekeeper Role Exists..')
            self._AMP_botRole_exists = True

        # Gatekeeper has `Gatekeeper` Role inside of AMP
        if self._AMP_botRole_exists and self.AMP_BotRoleID in self.AMP_userinfo['result']['Roles']:
            # self.logger.dev('Gatekeeper User has Gatekepeer Role.')
            self._have_AMP_botRole = True

        # `Super_Admin Role inside of AMP`
        if self.super_AdminID in self.AMP_userinfo['result']['Roles']:
            # self.logger.dev('Gatekeeper User has Super Admins')
            self._have_superAdmin = True

        if self._AMP_botRole_exists:
            self.logger.dev(f'Checking `Gatekeeper Role` permissions on {"AMP" if self.InstanceID == 0 else self.FriendlyName}')
            for perm in self.perms:
                # Skip the perm check on ones we "shouldn't have!"
                if perm.startswith('-'):
                    continue

                role_perms = self.getAMPRolePermissions(self.AMP_BotRoleID)

                if perm not in role_perms['result']:
                    if self._have_superAdmin:
                        self.logger.dev(f'We have `Super Admins` Role and we are missing Permissions, returning to setup Permissions.')
                        return False

                    else:
                        end_point = self.AMPHandler.tokens.AMPurl.find(":", 5)
                        self.logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please visit {self.AMPHandler.tokens.AMPurl[:end_point]}:{self.Port} under Configuration -> Role Management -> Gatekeeper')
                    failed = True

            if not failed:
                return True
        else:
            return False

    def getAMPUserID(self, name: str):
        """Returns AMP Users ID Only."""
        result = self.getAMPUserInfo(name=name)
        return result['result']['ID']

    def setRoleIDs(self):
        """Sets `self.AMP_BotRoleID` and `self.super_AdminID` (if they exist)"""
        roles = self.getRoleIds()
        for role in roles:
            if roles[role].lower() == 'gatekeeper':
                self.AMP_BotRoleID = role
                if self.InstanceID == 0:
                    self.logger.dev(f'Found Gatekeeper Role - ID: {self.AMP_BotRoleID}')

            if roles[role].lower() == 'super admins':
                self.super_AdminID = role
                if self.InstanceID == 0:
                    self.logger.dev(f'Found Super Admin Role - ID: {self.super_AdminID}')

    async def check_SessionPermissions(self) -> bool:
        """These check AMP for the proper Permission Nodes.\n
        Returns `True` only if I have ALL the Required Permissions; Otherwise `False`."""
        self._logger.warning(f'Checking Session: {self._session_id} for proper permissions...')
        failed = False
        for perm in self._perms:
            # Skip the perm check on ones we "shouldn't have!"
            if perm.startswith('-'):
                continue

            check = await self.currentSessionHasPermission(perm)

            # self._logger.dev(f'Session {"has" if check else "is missing" } permisson node: {perm}')
            if check:
                continue

            if self.Module == 'AMP':  # AKA the main (InstanceID == 0)
                self._logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please check under Configuration -> User Management for {self.AMPUSER}.')

            else:
                end_point = self.AMPURL.find(":", 5)
                self._logger.warning(f'Gatekeeper is missing the permission __{perm}__ Please visit {self.AMPURL[:end_point]}:{self.Port} under Configuration -> Role Management -> Gatekeeper')
            failed = True

        if failed:
            self._logger.critical(f'***ATTENTION*** The Bot is missing permissions, some or all functionality may not work properly!')
            # Please see this image for the required bot user Permissions **(Github link to AMP Basic Perms image here)**
            return check

        return True

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
