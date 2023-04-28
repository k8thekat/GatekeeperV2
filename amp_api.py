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
from __future__ import annotations
from typing import Union, Any
import json
import pathlib
import traceback

import aiohttp
from aiohttp import ClientResponse

import sys
import logging
from dotenv import load_dotenv
import os
from argparse import Namespace
from pyotp import TOTP  # 2Factor Authentication Python Module
import requests
from requests import Response


class AMP_API():
    _logger = logging.getLogger()
    _use_AMP2FA: bool = False
    _first_run: bool = True
    _cwd = pathlib.Path.cwd()

    load_dotenv()
    AMPUSER: str = os.environ["AMPUSER"].strip()
    AMPPASSWORD: str = os.environ["AMPPASSWORD"].strip()
    AMPURL: str = os.environ["AMPURL"].strip()
    AMPAUTH: str = os.environ["AMPAUTH"].strip()

    FAILED_LOGIN: str = ""
    NO_DATA: str = "Failed to recieve any data from post request."
    UNAUTHORIZED_ACCESS: str = f"{AMPUSER} does not have the required permissions to interact with this instance."

    def __init__(self, session_id: str = '0', args: Union[Namespace, None] = None) -> None:
        self._session_id = session_id
        self._args = args

        if self._first_run:
            self._val_settings()
            self._first_run = False

    async def _call_api(self, api: str, parameters: dict[str, str]) -> ConnectionError | ValueError | PermissionError | Any | bool:
        """Uses `aiohttp.ClientSession` and `.post()` to retrieve information.

        All information is `.json()` serialized."""
        self._AMPheader: dict = {'Accept': 'text/javascript'}
        _post_req: ClientResponse | None
        self._URL = self.AMPURL + "/API/"  # This will be the default URL; this will change on new instances.

        self._logger.info(f'Function {api} was called with {parameters}')

        if self._session_id != "0":
            parameters["SESSIONID"] = self._session_id
        jsonhandler = json.dumps(parameters)

        async with aiohttp.ClientSession() as session:
            try:
                _post_req = await session.post(self._URL + api, headers=self._AMPheader, data=jsonhandler)
                self._logger.debug(f'Post Request Prints: {await _post_req.json()}')

            # FIXME - Need to not catch all Excepts..
            # So I can handle each exception properly.
            except Exception as e:
                print(type(e))
                raise ValueError(e)

            if len(_post_req.content_length) == 0:
                raise ConnectionError(self.NO_DATA)

            if _post_req.status != 200:
                return ConnectionError(self.NO_DATA)

            _post_req_json = await _post_req.json()

        # FIXME -- This will need to be tracked and see what triggers what.
        if "result" in _post_req_json:
            if type(_post_req_json["result"]) == bool:
                if _post_req_json["result"] == True:
                    return _post_req_json

                if _post_req_json["result"] != True:
                    self._logger.error(f'The API Call {api} failed because of {_post_req_json}')
                    return _post_req_json

                if ("Status" in _post_req_json["result"]) and (_post_req_json["result"]["Status"] == False):
                    self._logger.error(f'The API Call {api} failed because of Status: {_post_req_json}')
                    return False

        elif "Title" in _post_req_json:
            if (type(_post_req_json["Title"]) == str) and (_post_req_json["Title"] == 'Unauthorized Access'):
                self._logger.error(f'["Title"]: The API Call {api} failed because of {_post_req_json}')
                self._session_id = "0"
                raise PermissionError(self.UNAUTHORIZED_ACCESS)

        if "result" not in _post_req_json:
            raise ValueError(self.NO_DATA)

        else:
            return _post_req_json

    def _val_settings(self) -> None:
        """Validates the .env settings and if we should use 2FA or not."""
        self._logger.info("Validating your .env file...")
        reset = False
        result: Response

        # if not self.args.token:
        if not self._cwd.joinpath(".env").exists():
            self._logger.critical("**ERROR** Missing our .env, please rename .envtemplate to .env")
            reset = True

        # if -dev is enabled; lets use our DEV information inside our .env file.
        if self._args != None and self._args.dev:  # type:ignore
            self.AMPUSER: str = os.environ["DEV_AMPUSER"].strip()
            self.AMPPASSWORD: str = os.environ["DEV_AMPPASSWORD"].strip()
            self.AMPURL: str = os.environ["DEV_AMPURL"].strip()
            self.AMPAUTH: str = os.environ["DEV_AMPAUTH"].strip()

        # handles validating the url briefly..
        if not self.AMPURL.startswith("http://") and not self.AMPURL.startswith("https://"):
            self._logger.critical("** Please verify your AMPurl. It either needs 'http://'' or 'https://'' depending on your AMP/Network setup. **")
            reset = True

        # if for some reason they left a trailing `/` lets just remove it for them and continue.
        if self.AMPURL.endswith("/"):
            self.AMPURL = self.AMPURL[:-1]

        # lets attempt to connect to the url with request
        # TODO -- Ideally I want to use async here; but unsure how..
        result = requests.get(url=self.AMPURL)
        if not result.status_code == 200:
            self._logger.critical(f"** Please verify your AMPurl, it responded with the response code: {result.status_code}")

        # if our AMPAUTH has a len of 0; 2FA disabled.
        if len(self.AMPAUTH) == 0:
            self._use_AMP2FA = False
        # if our AMPAUTH url is too short; possibly the 6 digit code.
        elif len(self.AMPAUTH) < 7:
            self._logger.critical('**ERROR** Please use your 2 Factor Generator Code (Should be over 25 characters long), not the 6 digit numeric generated code that expires with time.')
            reset = True
        else:
            self._use_AMP2FA = True

        if reset:
            input("Press any key to exit")
            sys.exit(0)

    async def login(self):
        self._AMP2FACTOR: Union[str, TOTP] = ""

        if self._session_id == '0':
            # FIXME -- May need to change how we handle a 2FA code.
            if self._use_AMP2FA:
                try:
                    self._AMP2FACTOR = TOTP(self.AMPAUTH)  # Handles time based 2Factory Auth Key/Code
                    self._AMP2FACTOR.now()

                except AttributeError:
                    self._logger.critical("**ERROR** Please check your 2 Factor Set-up Code in .env, should not contain spaces, escape characters and enclosed in quotes!")
                    sys.exit(1)

            parameters = {
                'username': self.AMPUSER,
                'password': self.AMPPASSWORD,
                'token': self._AMP2FACTOR,
                'rememberMe': True}

            try:
                result = await self._call_api('Core/Login', parameters)
                if isinstance(result, BaseException):
                    return result

                elif "sessionID" in result:
                    self._session_id = result['sessionID']
                    self.Running = True

                else:
                    self._logger.warning(f'{self._InstanceName} - Instance is Offline')
                    self.Running = False
                    return False

            except Exception as e:
                self._logger.warning(f'Core/Login Exception: {traceback.format_exc()}')
                self._logger.warning()(result)

                self._logger.warning(f'{self._InstanceName} - Instance is Offline')
                self.Running = False
                return False

        else:
            return True

    async def _api_test(self):
        """Test AMP API calls with this function"""
        await self.login()
        parameters = {}
        result = await self._call_api('Core/GetModuleInfo', parameters)

        return result

    async def getInstances(self):
        """This gets all Instances on AMP."""
        await self.login()
        parameters = {}
        result = await self._call_api('ADSModule/GetInstances', parameters)
        return result

    async def consoleUpdate(self) -> dict:
        """Requests the recent entries of the console; will acquire all updates from previous API call of consoleUpdate"""
        await self.login()
        parameters = {}
        result = await self._call_api('Core/GetUpdates', parameters)
        return result

    async def consoleMessage(self, msg: str) -> None:
        """Sends a Console Message"""
        await self.login()
        parameters = {'message': msg}
        await self._call_api('Core/SendConsoleMessage', parameters)
        return

    async def startInstance(self) -> None:
        """Starts AMP Instance"""
        await self.login()
        parameters = {}
        await self._call_api('Core/Start', parameters)
        return

    async def stopInstance(self) -> None:
        """Stops AMP Instance"""
        await self.login()
        parameters = {}
        await self._call_api('Core/Stop', parameters)
        return

    async def restartInstance(self) -> None:
        """Restarts AMP Instance"""
        await self.login()
        parameters = {}
        await self._call_api('Core/Restart', parameters)
        return

    async def killInstance(self) -> None:
        """Kills AMP Instance"""
        await self.login()
        parameters = {}
        await self._call_api('Core/Kill', parameters)
        return

    async def getStatus(self):
        """AMP Instance Status Information"""
        await self.login()
        parameters = {}
        result = await self._call_api('Core/GetStatus', parameters)
        return result

    async def getUserList(self):
        """Returns a List of connected users."""
        await self.login()
        parameters = {}
        result = await self._call_api('Core/GetUserList', parameters)
        return result

    async def getSchedule(self):
        await self.login()
        parameters = {}
        result = await self._call_api('Core/GetScheduleData', parameters)
        return result

    async def copyFile(self, source: str, destination: str) -> None:
        await self.login()
        parameters = {
            'Origin': source,
            'TargetDirectory': destination
        }
        await self._call_api('FileManagerPlugin/CopyFile', parameters)
        return

    async def renameFile(self, original: str, new: str) -> None:
        await self.login()
        parameters = {
            'Filename': original,
            'NewFilename': new
        }
        await self._call_api('FileManagerPlugin/RenameFile', parameters)
        return

    async def getDirectoryListing(self, directory: str):
        await self.login()
        parameters = {
            'Dir': directory
        }
        result = await self._call_api('FileManagerPlugin/GetDirectoryListing', parameters)
        return result

    async def getFileChunk(self, name: str, position: int, length: int):
        await self.login()
        parameters = {
            'Filename': name,
            'Position': position,
            'Length': length
        }
        result = await self._call_api('FileManagerPlugin/GetFileChunk', parameters)
        return result

    async def writeFileChunk(self, filename: str, position: int, data: str) -> None:
        await self.login()
        parameters = {
            'Filename': filename,
            'Position': position,
            'Data': data
        }
        await self._call_api('FileManagerPlugin/WriteFileChunk', parameters)
        return

    async def endUserSession(self, session_id: str) -> None:
        """Ends specified User Session"""
        await self.login()
        parameters = {
            'Id': session_id
        }
        await self._call_api('Core/EndUserSession', parameters)
        return

    async def getActiveAMPSessions(self):
        """Returns currently active AMP Sessions"""
        await self.login()
        parameters = {}
        result = await self._call_api('Core/GetActiveAMPSessions', parameters)
        return result

    async def getInstanceStatus(self):
        """Returns AMP Instance Status"""
        await self.login()
        parameters = {}
        result = await self._call_api('ADSModule/GetInstanceStatuses', parameters)
        return result

    async def trashDirectory(self, dir_name: str) -> None:
        """Moves a directory to trash, files must be trashed before they can be deleted."""
        await self.login()
        parameters = {
            'DirectoryName': dir_name
        }
        await self._call_api('FileManagerPlugin/TrashDirectory', parameters)
        return

    async def trashFile(self, filename: str) -> None:
        """Moves a file to trash, files must be trashed before they can be deleted."""
        await self.login()
        parameters = {
            'Filename': filename
        }
        await self._call_api('FileManagerPlugin/TrashFile', parameters)
        return

    async def emptyTrash(self, trash_dir: str) -> None:
        """Empties a trash bin for the AMP Instance"""
        await self.login()
        parameters = {
            'TrashDirectoryName': trash_dir
        }
        await self._call_api('FileManagerPlugin/EmptyTrash', parameters)
        return

    async def takeBackup(self, title: str, description: str, sticky: bool = False) -> None:
        """Takes a backup of the AMP Instance; default `sticky` is False!"""
        await self.login()
        parameters = {
            "Title": title,
            "Description": description,
            "Sticky": sticky
        }
        await self._call_api('LocalFileBackupPlugin/TakeBackup', parameters)
        return

    async def getAMPUserInfo(self, name: str):
        """Gets the AMP User info"""
        await self.login()
        parameters = {
            'Username': name
        }
        result = await self._call_api('Core/GetAMPUserInfo', parameters)
        return result

    async def currentSessionHasPermission(self, permission_node: str) -> dict:
        """Gets current Sessions permission spec"""
        await self.login()
        parameters = {
            'PermissionNode': permission_node
        }
        result = await self._call_api('Core/CurrentSessionHasPermission', parameters)
        return result

    async def getAMPRolePermissions(self, role_id: str) -> dict:
        """Gets full permission spec for Role (returns permission nodes)"""
        await self.login()
        parameters = {
            'RoleId': role_id
        }
        result = await self._call_api('Core/GetAMPRolePermissions', parameters)
        return result

    async def getPermissions(self) -> dict:
        """Gets full Permission spec for self"""
        await self.login()
        parameters = {}
        result = await self._call_api('Core/GetPermissionsSpec', parameters)
        return result

    async def getRoleIds(self) -> dict:
        """Gets a List of all Roles"""
        await self.login()
        parameters = {}
        result = await self._call_api('Core/GetRoleIds', parameters)
        return result

    async def createRole(self, name: str, as_common_role=False):
        """Creates a AMP User role"""
        await self.login()
        parameters = {
            'Name': name,
            'AsCommonRole': as_common_role
        }
        result = await self._call_api('Core/CreateRole', parameters)
        return result

    async def getRole(self, role_id: str):
        """Gets the AMP Role"""
        await self.login()
        parameters = {
            'RoleId': role_id
        }
        result = await self._call_api('Core/GetRole', parameters)
        return result

    async def setAMPUserRoleMembership(self, user_id: str, role_id: str, is_member: bool):
        """ Sets the AMP Users Role Membership"""
        await self.login()
        parameters = {
            'UserId': user_id,
            'RoleId': role_id,
            'IsMember': is_member
        }
        result = await self._call_api('Core/SetAMPUserRoleMembership', parameters)
        return result

    async def setAMPRolePermissions(self, role_id: str, permission_node: str, enabled: bool):
        """Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`"""
        await self.login()
        parameters = {
            'RoleId': role_id,
            'PermissionNode': permission_node,
            'Enabled': enabled
        }
        result = await self._call_api('Core/SetAMPRolePermission', parameters)
        return result

    async def getConfig(self, node: str):
        """Access the provided config node."""
        await self.login()
        parameters = {
            "node": node
        }
        result = await self._call_api("Core/GetConfig", parameters)
        return result

    async def getConfigs(self, node: list[str]):
        """Access the provided config node list."""
        await self.login()
        parameters = {
            "node": node
        }
        result = await self._call_api("Core/GetConfigs", parameters)
        return result
