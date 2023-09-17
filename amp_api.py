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
from typing import TypedDict


class API_Params(TypedDict):
    url: str
    user: str
    password: str
    auth: str
    use_auth: bool
    session_id: str


class AMP_API():
    _logger = logging.getLogger()
    _cwd = pathlib.Path.cwd()

    def __init__(self, args: Union[API_Params, None] = None) -> None:
        self._args = args
        self._URL: str = args['url'] + "/API/"
        self._AMPUSER: str = args['user']
        self._AMPPASSWORD: str = args['password']
        self._AMPAUTH: str = args['auth']
        self._use_2FA: bool = args['use_auth']
        self._session_id = args['session_id']

        self.FAILED_LOGIN: str = ""
        self.NO_DATA: str = "Failed to recieve any data from post request."
        self.UNAUTHORIZED_ACCESS: str = f"{self._AMPUSER} does not have the required permissions to interact with this instance."

    async def _call_api(self, api: str, parameters: dict[str, str]):
        """Uses `aiohttp.ClientSession` and `.post()` to retrieve information.

        All information is `.json()` serialized."""
        self._AMPheader: dict = {'Accept': 'text/javascript'}
        _post_req: ClientResponse | None
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

            if _post_req.content_length == 0:
                raise ValueError(self.NO_DATA)

            if _post_req.status != 200:
                raise ConnectionError(self.NO_DATA)

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

        return _post_req_json

    async def _connect(self) -> BaseException | bool | None:
        self._AMP2FACTOR: Union[str, TOTP] = ""

        if self._session_id == '0':
            # FIXME -- May need to change how we handle a 2FA code.
            if self._use_2FA:
                try:
                    self._AMP2FACTOR = TOTP(self._AMPAUTH)  # Handles time based 2Factory Auth Key/Code
                    self._AMP2FACTOR.now()

                except AttributeError:
                    self._logger.critical("**ERROR** Please check your 2 Factor Set-up Code in .env, should not contain spaces, escape characters and enclosed in quotes!")
                    sys.exit(1)

            try:
                result = await self.login(amp_user=self._AMPUSER, amp_password=self._AMPPASSWORD, token=self._AMP2FACTOR, rememberME=True)
                if isinstance(result, BaseException):
                    return result

                elif "sessionID" in result:
                    self._session_id = result['sessionID']
                    self.Running = True

                else:
                    self._logger.warning("Failed response from Instance")
                    self.Running = False
                    return False

            except Exception as e:
                self._logger.warning(f'Core/Login Exception: {traceback.format_exc()}')
                self._logger.warning(result)
                self.Running = False
                return False

        else:
            return True

    async def login(self, amp_user: str, amp_password: str, token: str = "", rememberME: bool = False):
        """
        login _summary_

        Args:
            amp_user (str): The username for logging into the AMP Panel
            amp_password (str): The password for logging into the AMP Panel
            token (str, optional): Used for 2FA Auth. Leave blank if you do not use 2FA. Defaults to "".
            rememberME (bool, optional): _description_. Defaults to False.

        Returns:
            _type_: _description_
        """
        parameters = {
            'username': amp_user,
            'password': amp_password,
            'token': token,
            'rememberMe': rememberME}
        result = await self._call_api('Core/Login', parameters)
        return result

    async def _api_test(self):
        """Test AMP API calls with this function"""
        await self._connect()
        parameters = {}
        result = await self._call_api('Core/GetModuleInfo', parameters)
        return result

    async def getInstances(self):
        """This gets all Instances on AMP."""
        await self._connect()
        parameters = {}
        result = await self._call_api('ADSModule/GetInstances', parameters)
        return result

    async def getInstance(self, instanceID: str):
        await self._connect()
        parameters = {"InstanceId": instanceID}
        result = await self._call_api("ADSModule/GetInstance", parameters)
        return result

    async def consoleUpdate(self) -> dict:
        """Requests the recent entries of the console; will acquire all updates from previous API call of consoleUpdate"""
        await self._connect()
        parameters = {}
        result = await self._call_api('Core/GetUpdates', parameters)
        return result

    async def consoleMessage(self, msg: str) -> None:
        """Sends a Console Message"""
        await self._connect()
        parameters = {'message': msg}
        await self._call_api('Core/SendConsoleMessage', parameters)
        return

    async def startInstance(self) -> None:
        """Starts AMP Instance"""
        await self._connect()
        parameters = {}
        await self._call_api('Core/Start', parameters)
        return

    async def stopInstance(self) -> None:
        """Stops AMP Instance"""
        await self._connect()
        parameters = {}
        await self._call_api('Core/Stop', parameters)
        return

    async def restartInstance(self) -> None:
        """Restarts AMP Instance"""
        await self._connect()
        parameters = {}
        await self._call_api('Core/Restart', parameters)
        return

    async def killInstance(self) -> None:
        """Kills AMP Instance"""
        await self._connect()
        parameters = {}
        await self._call_api('Core/Kill', parameters)
        return

    async def getStatus(self):
        """AMP Instance Status Information"""
        await self._connect()
        parameters = {}
        result = await self._call_api('Core/GetStatus', parameters)
        return result

    async def getUserList(self):
        """Returns a List of connected users."""
        await self._connect()
        parameters = {}
        result = await self._call_api('Core/GetUserList', parameters)
        return result

    async def getSchedule(self):
        await self._connect()
        parameters = {}
        result = await self._call_api('Core/GetScheduleData', parameters)
        return result

    async def copyFile(self, source: str, destination: str) -> None:
        await self._connect()
        parameters = {
            'Origin': source,
            'TargetDirectory': destination
        }
        await self._call_api('FileManagerPlugin/CopyFile', parameters)
        return

    async def renameFile(self, original: str, new: str) -> None:
        await self._connect()
        parameters = {
            'Filename': original,
            'NewFilename': new
        }
        await self._call_api('FileManagerPlugin/RenameFile', parameters)
        return

    async def getDirectoryListing(self, directory: str):
        await self._connect()
        parameters = {
            'Dir': directory
        }
        result = await self._call_api('FileManagerPlugin/GetDirectoryListing', parameters)
        return result

    async def getFileChunk(self, name: str, position: int, length: int):
        await self._connect()
        parameters = {
            'Filename': name,
            'Position': position,
            'Length': length
        }
        result = await self._call_api('FileManagerPlugin/GetFileChunk', parameters)
        return result

    async def writeFileChunk(self, filename: str, position: int, data: str) -> None:
        await self._connect()
        parameters = {
            'Filename': filename,
            'Position': position,
            'Data': data
        }
        await self._call_api('FileManagerPlugin/WriteFileChunk', parameters)
        return

    async def endUserSession(self, session_id: str) -> None:
        """Ends specified User Session"""
        await self._connect()
        parameters = {
            'Id': session_id
        }
        await self._call_api('Core/EndUserSession', parameters)
        return

    async def getActiveAMPSessions(self):
        """Returns currently active AMP Sessions"""
        await self._connect()
        parameters = {}
        result = await self._call_api('Core/GetActiveAMPSessions', parameters)
        return result

    async def getInstanceStatus(self):
        """Returns AMP Instance Status"""
        await self._connect()
        parameters = {}
        result = await self._call_api('ADSModule/GetInstanceStatuses', parameters)
        return result

    async def trashDirectory(self, dir_name: str) -> None:
        """Moves a directory to trash, files must be trashed before they can be deleted."""
        await self._connect()
        parameters = {
            'DirectoryName': dir_name
        }
        await self._call_api('FileManagerPlugin/TrashDirectory', parameters)
        return

    async def trashFile(self, filename: str) -> None:
        """Moves a file to trash, files must be trashed before they can be deleted."""
        await self._connect()
        parameters = {
            'Filename': filename
        }
        await self._call_api('FileManagerPlugin/TrashFile', parameters)
        return

    async def emptyTrash(self, trash_dir: str) -> None:
        """Empties a trash bin for the AMP Instance"""
        await self._connect()
        parameters = {
            'TrashDirectoryName': trash_dir
        }
        await self._call_api('FileManagerPlugin/EmptyTrash', parameters)
        return

    async def takeBackup(self, title: str, description: str, sticky: bool = False) -> None:
        """Takes a backup of the AMP Instance; default `sticky` is False!"""
        await self._connect()
        parameters = {
            "Title": title,
            "Description": description,
            "Sticky": sticky
        }
        await self._call_api('LocalFileBackupPlugin/TakeBackup', parameters)
        return

    async def getAMPUserInfo(self, name: str):
        """Gets the AMP User info"""
        await self._connect()
        parameters = {
            'Username': name
        }
        result = await self._call_api('Core/GetAMPUserInfo', parameters)
        return result

    async def currentSessionHasPermission(self, permission_node: str) -> dict:
        """Gets current Sessions permission spec"""
        await self._connect()
        parameters = {
            'PermissionNode': permission_node
        }
        result = await self._call_api('Core/CurrentSessionHasPermission', parameters)
        return result

    async def getAMPRolePermissions(self, role_id: str) -> dict:
        """Gets full permission spec for Role (returns permission nodes)"""
        await self._connect()
        parameters = {
            'RoleId': role_id
        }
        result = await self._call_api('Core/GetAMPRolePermissions', parameters)
        return result

    async def getPermissions(self) -> dict:
        """Gets full Permission spec for self"""
        await self._connect()
        parameters = {}
        result = await self._call_api('Core/GetPermissionsSpec', parameters)
        return result

    async def getRoleIds(self) -> dict:
        """Gets a List of all Roles"""
        await self._connect()
        parameters = {}
        result = await self._call_api('Core/GetRoleIds', parameters)
        return result

    async def createRole(self, name: str, as_common_role=False):
        """Creates a AMP User role"""
        await self._connect()
        parameters = {
            'Name': name,
            'AsCommonRole': as_common_role
        }
        result = await self._call_api('Core/CreateRole', parameters)
        return result

    async def getRole(self, role_id: str):
        """Gets the AMP Role"""
        await self._connect()
        parameters = {
            'RoleId': role_id
        }
        result = await self._call_api('Core/GetRole', parameters)
        return result

    async def setAMPUserRoleMembership(self, user_id: str, role_id: str, is_member: bool):
        """ Sets the AMP Users Role Membership"""
        await self._connect()
        parameters = {
            'UserId': user_id,
            'RoleId': role_id,
            'IsMember': is_member
        }
        result = await self._call_api('Core/SetAMPUserRoleMembership', parameters)
        return result

    async def setAMPRolePermissions(self, role_id: str, permission_node: str, enabled: bool):
        """Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`"""
        await self._connect()
        parameters = {
            'RoleId': role_id,
            'PermissionNode': permission_node,
            'Enabled': enabled
        }
        result = await self._call_api('Core/SetAMPRolePermission', parameters)
        return result

    async def getConfig(self, node: str):
        """Access the provided config node."""
        await self._connect()
        parameters = {
            "node": node
        }
        result = await self._call_api("Core/GetConfig", parameters)
        return result

    async def getConfigs(self, node: list[str]):
        """Access the provided config node list."""
        await self._connect()
        parameters = {
            "node": node
        }
        result = await self._call_api("Core/GetConfigs", parameters)
        return result
