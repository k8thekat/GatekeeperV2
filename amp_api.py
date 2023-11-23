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
from typing import Union
import json
import traceback
import logging

import aiohttp
from aiohttp import ClientResponse

from pyotp import TOTP  # 2Factor Authentication Python Module


class AMP_API():
    _logger = logging.getLogger()
    _logger.setLevel(logging.INFO)

    def __init__(self, url: str, amp_user: str, amp_password: str, amp_2fa: bool = False, amp_2fa_token: str = "", session_id: str = "0") -> None:
        self._url: str = url + "/API/"
        self._amp_user: str = amp_user
        self._amp_password: str = amp_password
        self._amp_2fa: bool = amp_2fa
        self._amp_2fa_token: str = amp_2fa_token
        self._session_id = session_id

        if self._amp_2fa == True:
            if self._amp_2fa_token == "":
                raise ValueError("You must provide a 2FA Token if you are using 2FA.")
            if self._amp_2fa_token.startswith(("'", '"')) == False or self._amp_2fa_token.endswith(("'", '"')) == False:
                raise ValueError("2FA Token must be enclosed in quotes.")

        # self.FAILED_LOGIN: str = ""
        self.NO_DATA: str = "Failed to recieve any data from post request."
        self.UNAUTHORIZED_ACCESS: str = f"{self._amp_user} user does not have the required permissions to interact with this instance."

    async def _call_api(self, api: str, parameters: dict[str, str]) -> str | bool | dict:
        """
        Uses aiohttp.ClientSession() post request to access the AMP API endpoints. \n
        Will automatically populate the `SESSIONID` parameter if it is not provided.

        Args:
            api (str): The API endpoint to call. eg `Core/GetModuleInfo`
            parameters (dict[str, str]): The parameters to pass to the API endpoint.

        Raises:
            ValueError: When the API call returns no data or raises any exception.
            ConnectionError: When the API call returns a status code other than 200.
            PermissionError: When the API call returns a `Unauthorized Access` error or permission related error.

        Returns:
            Any: Returns unmodified JSON response from the API call. Typically a string or dict.
        """
        header: dict = {'Accept': 'text/javascript'}
        post_req: ClientResponse | None
        self._logger.debug(f'_call_api -> {api} was called with {parameters}')

        if self._session_id != "0":
            parameters["SESSIONID"] = self._session_id

        json_data = json.dumps(parameters)
        async with aiohttp.ClientSession() as session:
            try:
                post_req = await session.post(self._url + api, headers=header, data=json_data)
                self._logger.debug(f'post req-> {await post_req.json()}')
            # TODO - Need to not catch all Excepts..
            except Exception as e:
                # So I can handle each exception properly.
                print("_call_api exception type:", type(e))
                raise ValueError(e)

            if post_req.content_length == 0:
                raise ValueError(self.NO_DATA)

            if post_req.status != 200:
                raise ConnectionError(self.NO_DATA)

            post_req_json = await post_req.json()

        # TODO -- This will need to be tracked and see what triggers what.
        if "result" in post_req_json:
            if type(post_req_json["result"]) == bool:

                if post_req_json["result"] == True:
                    return post_req_json

                if post_req_json["result"] != True:
                    self._logger.error(f'{api} failed because of {post_req_json}')
                    return post_req_json

                if ("Status" in post_req_json["result"]) and (post_req_json["result"]["Status"] == False):
                    self._logger.error(f'{api} failed because of Status: {post_req_json}')
                    return False

        elif "Title" in post_req_json:
            if (type(post_req_json["Title"]) == str) and (post_req_json["Title"] == 'Unauthorized Access'):
                self._logger.error(f'{api} failed because of {post_req_json}')
                self._session_id = "0"
                raise PermissionError(self.UNAUTHORIZED_ACCESS)

        return post_req_json

    async def _connect(self) -> bool | None:
        # TODO - Possibly move this to our Instance class?
        """
        Handles your 2FA code and logging into AMP while also handling the session ID. \n

        Raises:
            ValueError: If session ID is not a string or 2FA code is not a formatted properly.

        Returns:
            bool | None: Returns False if an exception is thrown or the login attempt fails to provide a sessionID value. \n
            Otherwise returns true and sets the class's sessionID value.
        """
        amp_2fa_code: Union[str, TOTP] = ""
        if isinstance(self._session_id, str) == False:
            raise ValueError("You must provide a session id as a string.")
        if self._session_id == '0':
            # FIXME -- May need to change how we handle a 2FA code.
            if self._amp_2fa:
                try:
                    amp_2fa_code = TOTP(self._amp_2fa_token)  # Handles time based 2Factory Auth Key/Code
                    amp_2fa_code.now()

                except AttributeError:
                    raise ValueError("Please check your 2 Factor Code, should not contain spaces, escape characters and it must be enclosed in quotes!")
            else:
                try:

                    result = await self.login(amp_user=self._amp_user, amp_password=self._amp_password, token=amp_2fa_code, rememberME=True)
                    # if isinstance(result, BaseException):
                    #     return result

                    if "sessionID" in result:
                        self._session_id = result['sessionID']

                    else:
                        self._logger.warning("Failed response from Instance")
                        return False

                except Exception as e:
                    self._logger.warning(f'Core/Login Exception: {traceback.format_exc()}')
                    # self._logger.warning(result)
                    return False

        else:
            return True

    async def login(self, amp_user: str, amp_password: str, token: str = "", rememberME: bool = False) -> str | bool | dict:
        """
        AMP API login function. \n

        Args:
            amp_user (str): The username for logging into the AMP Panel
            amp_password (str): The password for logging into the AMP Panel
            token (str, optional): AMP 2 Factor auth code; typically using `TOTP.now()`. Defaults to "".
            rememberME (bool, optional): Remember me token.. Defaults to False.

        Returns:
            str | bool | dict: Returns the JSON response from the API call.
        """
        parameters = {
            'username': amp_user,
            'password': amp_password,
            'token': token,
            'rememberMe': rememberME}
        result = await self._call_api('Core/Login', parameters)
        return result

    async def _api_test(self, api: str, parameters: dict[str, str]) -> str | bool | dict:
        """Test AMP API calls with this function"""
        await self._connect()
        result = await self._call_api(api, parameters)
        return result

    async def getInstances(self):
        """This gets all Instances on AMP."""
        await self._connect()
        parameters = {}
        result = await self._call_api("ADSModule/GetInstances", parameters)
        return result

    async def getInstance(self, instanceID: str) -> str | bool | dict:
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
