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
import traceback
import logging
from pprint import pprint

import aiohttp
from aiohttp import ClientResponse

from .types import *
from dataclass_wizard import fromdict

from pyotp import TOTP  # 2Factor Authentication Python Module


class AMP_API():
    _logger = logging.getLogger()
    _logger.setLevel(logging.INFO)

    def __init__(self, url: str, amp_user: str, amp_password: str, amp_2fa: bool = False, amp_2fa_token: str = "", instance_url: None | str = None) -> None:
        self._url: str = url + "/API/"
        self._amp_user: str = amp_user
        self._amp_password: str = amp_password
        self._amp_2fa: bool = amp_2fa
        self._amp_2fa_token: str = amp_2fa_token
        self._session_id: str = "0"

        if self._amp_2fa == True:
            if self._amp_2fa_token == "":
                raise ValueError("You must provide a 2FA Token if you are using 2FA.")
            if self._amp_2fa_token.startswith(("'", '"')) == False or self._amp_2fa_token.endswith(("'", '"')) == False:
                raise ValueError("2FA Token must be enclosed in quotes.")

        # self.FAILED_LOGIN: str = ""
        self.NO_DATA: str = "Failed to recieve any data from post request."
        self.ADS_ONLY: str = "This API call is only available on ADS instances."
        self.UNAUTHORIZED_ACCESS: str = f"{self._amp_user} user does not have the required permissions to interact with this instance."

    async def _call_api(self, api: str, parameters: None | dict[str, Any] = None) -> None | str | bool | dict | list[Any]:
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
            None | str | bool | dict | list[Any]: Returns unmodified JSON response from the API call. Typically a string or dict.
        """
        header: dict = {"Accept": "text/javascript"}
        post_req: ClientResponse | None
        self._logger.debug(f"_call_api -> {api} was called with {parameters}")

        # This should save us some boiler plate code throughout our API calls.
        if parameters == None:
            parameters = {}

        if self._session_id != "0":
            parameters["SESSIONID"] = self._session_id

        json_data = json.dumps(parameters)

        # _url = self._url + "/API/" + api
        print(api, self._url + api)
        async with aiohttp.ClientSession() as session:
            try:
                post_req = await session.post(self._url + api, headers=header, data=json_data)
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

        if post_req_json == None:
            raise ConnectionError(self.NO_DATA)
        # I should force return Data classes with this to help better handle the API change. See types.py
        # They removed "result" from all replies thus breaking most if not all future code.
        # Core/Login can trigger this because it has a key "result" near the end.
        # TODO -- This will need to be tracked and see what triggers what.
        # Possibly catch failed login's sooner; check `Core/Login` after the dict check.
        # `{'resultReason': 'Internal Auth - No reason given', 'success': False, 'result': 0}`
        # See about returning None or similar and use `if not None` checks on each API return.
        print("API CALL---->", api, type(post_req_json))

        if isinstance(post_req_json, dict):
            if "result" in post_req_json:
                data = post_req_json["result"]

                if isinstance(data, bool) and data == False:
                    self._logger.error(f"{api} failed because of {post_req_json}")
                    return data

                elif isinstance(data, dict) and "Status" in data and data["Status"] == False:
                    self._logger.error(f"{api} failed because of Status: {post_req_json}")
                    return data["Status"]

                # This is to handle the new API Core/Login
                elif api == "Core/Login":
                    return post_req_json

                else:
                    # Return our dict keyed data.
                    return data

            elif "Title" in post_req_json:
                data = post_req_json["Title"]
                if isinstance(data, str) and data == "Unauthorized Access":
                    self._logger.error(f'{api} failed because of {post_req_json}')
                    self._session_id = "0"
                    raise PermissionError(self.UNAUTHORIZED_ACCESS)
            else:
                return post_req_json
        else:
            print("_call_api -> else `return post_req_json`")
            return post_req_json

    async def _connect(self) -> bool | None:
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
        if self._session_id == "0":
            if self._amp_2fa == True:
                try:
                    # Handles time based 2Factory Auth Key/Code
                    amp_2fa_code = TOTP(self._amp_2fa_token)
                    amp_2fa_code.now()

                except AttributeError:
                    raise ValueError("Please check your 2 Factor Code, should not contain spaces, escape characters and it must be enclosed in quotes!")
            else:
                try:

                    result = await self.login(amp_user=self._amp_user, amp_password=self._amp_password, token=amp_2fa_code, rememberME=True)

                    if isinstance(result, LoginResults):
                        self._session_id = result.sessionID
                    # if type(result) == dict and "sessionID" in result:
                    #     self._session_id = result['sessionID']

                    else:
                        self._logger.warning("Failed response from Instance")

                except Exception as e:
                    self._logger.warning(f'Core/Login Exception: {traceback.format_exc()}')

    async def login(self, amp_user: str, amp_password: str, token: str = "", rememberME: bool = False) -> LoginResults | None | bool | int | str:
        """
        AMP API login function. \n

        Args:
            amp_user (str): The username for logging into the AMP Panel
            amp_password (str): The password for logging into the AMP Panel
            token (str, optional): AMP 2 Factor auth code; typically using `TOTP.now()`. Defaults to "".
            rememberME (bool, optional): Remember me token.. Defaults to False.

        Returns:
            LoginResults | None | bool | int | str: On success returns a LoginResult dataclass.
                See `types.py -> LoginResult`
        """
        parameters = {
            'username': amp_user,
            'password': amp_password,
            'token': token,
            'rememberMe': rememberME}
        result = await self._call_api('Core/Login', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(LoginResults, result)  # type:ignore

    async def callEndPoint(self, api: str, parameters: None | dict[str, Any] = None) -> list | dict | str | bool | int | None:
        """
        Universal API method for calling any API endpoint. Some API endpoints require ADS and some may require an Instance ID. \n

        Args:
            api (str): API endpoint to call. `eg "Core/GetModuleInfo"` (Assume this starts with www.yourAMPURL.com/API/)
            parameters (None | dict[str, str]): Parameters to pass to the API endpoint. Session ID is already handled for you. Defaults to None

        Returns:
            list | dict | str | bool | int | None: Returns the JSON response from the API call.
        """
        await self._connect()
        result = await self._call_api(api, parameters)
        return result

    async def getInstances(self) -> list[Controller] | str | bool | int | None:
        """
        Returns a list of all Instances on the AMP Panel.\n
        **Requires ADS**

        Returns:
            list[Controller] | str | bool | int | None: On success returns a list of Controller dataclasses. 
                See `types.py -> Controller`\n
        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        parameters = {}
        # _controllers: list[Controller] = []
        result = await self._call_api("ADSModule/GetInstances", parameters)
        # if isinstance(result, list):
        #     for controller in result:
        #         _controllers.append(fromdict(Controller, controller))
        # return _controllers
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return list(fromdict(Controller, controller) for controller in result)

    async def getInstance(self, instanceID: str) -> Instance | str | bool | int | None:
        """
        Returns the Instance information for the provided Instance ID.\n
        **Requires ADS**

        Args:
            instanceID (str): The Instance ID to get information for.

        Returns:
            Instance | str | bool | int | None: On success returns a Instance dataclass. 
                See `types.py -> Instance`
        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        parameters = {"InstanceId": instanceID}
        result = await self._call_api("ADSModule/GetInstance", parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(Instance, result)  # type:ignore

    async def getUpdates(self) -> Updates | str | bool | int | None:
        """
        Requests the recent entries of the Instance Updates; will acquire all updates from previous API call of `getUpdate()`

        Returns:
            Updates | str | bool | int | None: On success returns a Updates dataclass.
                See `types.py -> Updates`
        """
        await self._connect()
        result = await self._call_api('Core/GetUpdates')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(Updates, result)  # type:ignore

    async def sendConsoleMessage(self, msg: str) -> None:
        """
        Sends a string to the Console. (eg `/list`)

        Returns:
            None: ""
        """
        await self._connect()
        parameters = {'message': msg}
        await self._call_api('Core/SendConsoleMessage', parameters)
        return

    async def startInstance(self) -> str | dict | list | bool | int | None:
        """
        Starts the AMP Server/Instance

        Returns:
            ActionResult | str | bool | int | None: Results from the API call.
                See `types.py -> ActionResult`
        """
        await self._connect()
        result = await self._call_api('Core/Start')
        return ActionResult(**result)  # type:ignore

    async def stopInstance(self) -> None:
        """
        Stops the AMP Server/Instance

        Returns:
            None: ""
        """
        await self._connect()
        await self._call_api('Core/Stop')
        return

    async def restartInstance(self) -> str | dict | list | bool | int | None:
        """
        Restarts the AMP Server/Instance

        Returns:
            ActionResult | str | bool | int | None: Results from the API call.
                See `types.py -> ActionResult`
        """
        await self._connect()
        result = await self._call_api('Core/Restart')
        return ActionResult(**result)  # type:ignore

    async def killInstance(self) -> None:
        """
        Kills the AMP Server/Instance

        Returns:
            None: ""
        """
        await self._connect()
        await self._call_api('Core/Kill')
        return

    async def getStatus(self) -> Status | str | bool | int | None:
        """
        Gets the AMP Server/Instance Status information.

        Returns:
            Status | str | bool | int | None: On success returns a Status dataclass.
                See `types.py -> Status`
        """
        await self._connect()
        result = await self._call_api('Core/GetStatus')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(Status, result)  # type:ignore

    async def getUserList(self) -> Players | str | bool | int | None:
        """
        Returns a dictionary of the connected Users to the Server.

        Returns:
            Players | str | bool | int | None: on success returns a Player dataclass.
                See `types.py -> Players`
        """
        await self._connect()
        result = await self._call_api('Core/GetUserList')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        # TODO- Needs to be validated.
        return Players(data=result)  # type:ignore

    async def getScheduleData(self) -> ScheduleData | str | bool | int | None:
        """
        Returns a dictionary of the Server/Instance Schedule events and triggers.

        Returns:
            ScheduleData | str | bool | int | None: On success returns a ScheduleData dataclass.
                See `types.py -> ScheduleData`
        """
        await self._connect()
        result = await self._call_api('Core/GetScheduleData')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(ScheduleData, result)  # type:ignore

    async def copyFile(self, source: str, destination: str) -> ActionResult | str | bool | int | None:
        """
        Moves a file from the source directory to the destination. The path is relative to the Server/Instance home directory.\n
            Example `await Instance.copyFile("eula.txt", "test")` would move `/eula.txt` to `/test/eula.txt`

        Args:
            source (str): Directory starts from the Instance home path (`/`) along with the file name and the extension. (eg. "eula.txt")
                -> (File Manager `/` directory) eg `.ampdata/instance/VM_Minecraft/Minecraft/` *this is the home directory*
            destination (str): Similar to source; do not include the file name. (eg. "test")

        Returns:
            ActionResult | str | bool | int | None: Results from the API call.
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'Origin': source,
            'TargetDirectory': destination
        }
        result = await self._call_api('FileManagerPlugin/CopyFile', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def renameFile(self, original: str, new: str) -> ActionResult | str | bool | int | None:
        """
        Changes the name of a file. \n
            Path's are absolute and relative to the Instances home directory. Do not include the (`/`)

        Args:
            original (str): The path to the file and the file name included. (eg. "test/myfile.txt")
            new (str): The file name to be changed; no path needed. (eg. "renamed_myfile.txt")

        Returns:
            ActionResult | str | bool | int | None: Results from the API call.
            See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'Filename': original,
            'NewFilename': new
        }
        result = await self._call_api('FileManagerPlugin/RenameFile', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def renameDirectory(self, oldDirectory: str, newDirectoryName: str) -> ActionResult | str | bool | int | None:
        """
        Changes the name of a file.\n
            Path's are absolute and relative to the Instances home directory. Do not include the (`/`)

        Args:
            oldDirectory (str): The full path to the old directory.
            newDirectoryName (str): The name component of the new directory (not the full path).

        Returns:
            ActionResult | str | bool | int | None: Results from the API call.
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'oldDirectory': oldDirectory,
            'newDirectoryName': newDirectoryName
        }
        result = await self._call_api('FileManagerPlugin/RenameDirectory', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def getDirectoryListing(self, directory: str = "") -> list[Directory] | str | bool | int | None:
        """
        Returns a dictionary of the directory's properties and the files contained in the directory and their properties.

        Args:
            directory (str): Relative to the Server root directory . eg `Minecraft/` - If a file has a similar name it may return the file instead of the directory.

        Returns:
            list[Directory] | str | bool | int | None: Returns a list of Directory dataclasses.
                See `types.py -> Directory`
        """

        await self._connect()
        parameters = {
            'Dir': directory
        }
        result = await self._call_api('FileManagerPlugin/GetDirectoryListing', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return list(Directory(**directory) for directory in result)

    async def getFileChunk(self, name: str, position: int, length: int) -> FileChunk | str | bool | int | None:
        """
        Returns a specific section of Base64Data from a file.

        Args:
            name (str): File to open and read from.
            position (int): Start position to read from.
            length (int): How far to read from the start position.

        Returns:
            FileChunk | str | bool | int | None: Returns a FileChunk dataclass.
                See `types.py -> FileChunk`
        """
        await self._connect()
        parameters = {
            'Filename': name,
            'Position': position,
            'Length': length
        }
        result = await self._call_api('FileManagerPlugin/GetFileChunk', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return FileChunk(**result)  # type:ignore

    async def writeFileChunk(self, filename: str, data: str, offset: int, finalChunk: bool) -> ActionResult | str | bool | int | None:
        """
        Write data to a file with an offset.

        Args:
            filename (str): File to write data to.
            data (str): binary data to be written.
            offset (int): data offset from 0.
            finalChunk (bool): UNK

        Returns:
            ActionResult | str | bool | int | None: Results from the API call.
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'Filename': filename,
            'Data': data,
            'Offset': offset,
            "FinalChunk": finalChunk
        }
        result = await self._call_api('FileManagerPlugin/WriteFileChunk', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def endUserSession(self, session_id: str) -> str | None:
        """
        Closes the specified User's session ID to AMP.\n
        **Requires ADS**

        Args:
            session_id (str): session ID to end.

        Returns:
            None: ""
        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        parameters = {
            'Id': session_id
        }
        await self._call_api('Core/EndUserSession', parameters)
        return

    async def getActiveAMPSessions(self) -> Session | str | bool | int | None:
        """
        Returns currently active AMP Sessions.\n
        **Requires ADS**

        Returns:
            Session | str | bool | int | None: Returns a dataclass Session.
                See `types.py -> Session`
        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        result = await self._call_api('Core/GetActiveAMPSessions')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return Session(**result)  # type:ignore

    async def getInstanceStatuses(self) -> list[InstanceStatus] | dict | str | bool | int | None:
        """
        Returns a dictionary of the Server/Instance Status. \n
        **Requires ADS**

        Returns:
            list[InstanceStatus] | dict | str | bool | int | None: Returns a list of InstanceStatus dataclasses.
                See `types.py -> InstanceStatus`

        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        result = await self._call_api('ADSModule/GetInstanceStatuses')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return list(InstanceStatus(**instance)for instance in result)

    async def trashDirectory(self, dir_name: str) -> ActionResult | str | bool | int | None:
        """
        Moves a directory to the trash, files must be trashed before they can be `emptied`.\n
        See emptyTrash().

        Args:
            dir_name (str): Directory name; relative to the Server/Instance root. Supports pathing. eg `/home/config`

        Returns:
            ActionResult | str | bool | int | None: Results from the API call. 
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'DirectoryName': dir_name
        }
        result = await self._call_api('FileManagerPlugin/TrashDirectory', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def trashFile(self, filename: str) -> ActionResult | str | bool | int | None:
        """
        Moves a file to the trash, files must be trashed before they can be `emptied`. \n
        See emptyTrash().

        Args:
            filename (str): File name; relative to the Server/Instance root. Supports pathing. eg `/home/config`

        Returns:
            ActionResult | str | bool | int | None: Results from the API call. 
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'Filename': filename
        }
        result = await self._call_api('FileManagerPlugin/TrashFile', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def emptyTrash(self, trash_dir: str) -> ActionResult | str | bool | int | None:
        """
        Empties a trash bin for the AMP Server/Instance.

        Args:
            trash_dir (str): Directory name; relative to the Server/Instance root. Supports pathing. eg `/home/config` \n
            Typically the directory is called `Trashed Files`, it is case sensitive and located in the Server/Instance root directory.

        Returns:
            ActionResult | str | bool | int | None: Results from the API call. 
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'TrashDirectoryName': trash_dir
        }
        result = await self._call_api('FileManagerPlugin/EmptyTrash', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def takeBackup(self, title: str, description: str, sticky: bool = False) -> ActionResult | str | bool | int | None:
        """
        Takes a backup of the AMP Server/Instance.

        Args:
            title (str): Title of the backup; aka `Name`
            description (str): Brief description of why or what the backup is for.
            sticky (bool, optional): Sticky backups won't be deleted to make room for automatic backups. Defaults to `False`.

        Returns:
            ActionResult | str | bool | int | None: Results from the API call. 
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            "Title": title,
            "Description": description,
            "Sticky": sticky
        }
        result = await self._call_api('LocalFileBackupPlugin/TakeBackup', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def getAMPUserInfo(self, name: str) -> User | str | bool | dict | None:
        """
        Retrieves the AMP User information for the provided username.\n

        Args:
            name (str): AMP User name.

        Returns:
            User | str | bool | dict: On success returns a User dataclass. 
                See `types.py -> User`
        """

        await self._connect()
        parameters = {
            'Username': name
        }
        result = await self._call_api('Core/GetAMPUserInfo', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return User(**result)  # type:ignore

    async def currentSessionHasPermission(self, permission_node: str) -> str | bool | dict | list | None:
        """
        Retrieves the current Session IDs permissions. This will differ between the ADS and a Server/Instance.

        Args:
            permission_node (str): The permission node to check for. eg `Core.RoleManagement.DeleteRoles` \n
            Supports looking for a blocked permisson node simply by appending `-` in front of the permission node. eg `-Core.RoleManagement.DeleteRoles`\n
            Supports wildcards `*`. eg `Core.RoleManagement.*`

        Returns:
            str | bool | dict | list | None: On success returns a bool.
        """
        await self._connect()
        parameters = {
            'PermissionNode': permission_node
        }
        result = await self._call_api('Core/CurrentSessionHasPermission', parameters)
        return result

    async def getAMPRolePermissions(self, role_id: str) -> str | bool | dict | list | None:
        """
        Retrieves the AMP Role permission nodes for the provided role ID.

        Args:
            role_id (str): The role ID. eg `5d6566e0-fae2-41d7-bfb6-d21033247f2e`

        Returns:
            str | bool | dict | list | None: On success returns a list containing all the permission nodes for the provided role ID.
        """
        await self._connect()
        parameters = {
            'RoleId': role_id
        }
        result = await self._call_api("Core/GetAMPRolePermissions", parameters)
        return result

    async def getPermissionsSpec(self) -> str | bool | dict | list | None:
        """
        Retrieves the AMP Permissions node tree.

        Returns:
            str | bool | dict | list | None: On success returns a dictionary containing all the permission nodes, descriptions and other attributes.
        """
        await self._connect()
        result = await self._call_api("Core/GetPermissionsSpec")
        return result

    async def getRoleIds(self) -> str | bool | dict | list | None:
        """
        Retrieves all the Roles AMP currently has and the role IDs.

        Returns:
            Roles | str | bool | dict | list | None: On success returns a Roles dataclass containing all the roles and their IDs. Example below. \n
        """
        await self._connect()
        result = await self._call_api('Core/GetRoleIds')
        return result

    async def createRole(self, name: str, as_common_role: bool = False) -> ActionResult | str | bool | dict | list | None:
        """
        Creates an AMP Role.

        Args:
            name (str): The name of the role.
            as_common_role (bool, optional): A role that everyone has. Defaults to False.

        Returns:
            ActionResult | str | bool | dict | list | None: On success returns a ActionResult dataclass.
                See `types.py -> ActionResult`

        """
        await self._connect()
        parameters = {
            'Name': name,
            'AsCommonRole': as_common_role
        }
        result = await self._call_api('Core/CreateRole', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def getRole(self, role_id: str) -> Role | str | bool | dict | list | None:
        """
        Retrieves the AMP Role information for the provided role ID.

        Args:
            role_id (str): The role ID to get information for.

        Returns:
            str | bool | dict: On success returns a Role dataclass.
                See `types.py -> Role`

        """
        await self._connect()
        parameters = {
            'RoleId': role_id
        }
        result = await self._call_api('Core/GetRole', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return Role(**result)  # type:ignore

    async def setAMPUserRoleMembership(self, user_id: str, role_id: str, is_member: bool) -> ActionResult | str | bool | dict | list | None:
        """
        Adds a user to an AMP role.

        Args:
            user_id (str): User ID to add to the role.
            role_id (str): Role ID to add the user to.
            is_member (bool): `True` to add the user to the role, `False` to remove the user from the role.

        Returns:
            ActionResult | str | bool | dict | list | None: On success returns a ActionResult dataclass.
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'UserId': user_id,
            'RoleId': role_id,
            'IsMember': is_member
        }
        result = await self._call_api('Core/SetAMPUserRoleMembership', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def setAMPRolePermission(self, role_id: str, permission_node: str, enabled: Union[None, bool]) -> ActionResult | str | bool | dict | list | None:
        """
        Set a permission node to `True` or `False` for the provided AMP role.

        Args:
            role_id (str): AMP role id.
            permission_node (str): AMP permission node. eg `Core.RoleManagement.DeleteRoles`
            enabled (Union[None, bool]): Set a permission to `True`, `False` or `None` depending on the results you can disable or enable an entire tree node of permissions.

        Returns:
            ActionResult | str | bool | dict | list | None: On success returns a ActionResult dataclass.
                See `types.py -> ActionResult`
        """
        await self._connect()
        parameters = {
            'RoleId': role_id,
            'PermissionNode': permission_node,
            'Enabled': enabled
        }
        result = await self._call_api('Core/SetAMPRolePermission', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return ActionResult(**result)  # type:ignore

    async def getSettingsSpec(self) -> str | bool | dict | list | None:
        """
        Retrieves a Server/Instance nodes list.
        See `util.getNodespec` for a list of possible nodes.

        Returns:
            str | bool | dict: On success returns a dictionary containing all of the Server/Instance nodes and there information.
        """
        await self._connect()
        result = await self._call_api('Core/GetSettingsSpec')
        return result

    async def getConfig(self, node: str) -> Node | str | bool | dict | list | None:
        # TODO - Need to figure out how this command works entirely. Possible need a new node list
        """
        Returns the config settings for a specific node.

        Args:
            node (str): The AMP node to inspect eg `ADSModule.Networking.BaseURL`

        Returns:
            str | bool | dict: On success returns a dictionary containing the following. \n
        """
        await self._connect()
        parameters = {
            "node": node
        }
        result = await self._call_api("Core/GetConfig", parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return Node(**result)  # type:ignore

    async def getConfigs(self, nodes: list[str]) -> list[Node] | str | bool | dict | list | None:
        # TODO - Need to figure out how this command works entirely. Possible need a new node list
        """
        Returns the config settings for each node in the list.

        Args:
            node (list[str]): List of nodes to look at.

        Returns:
            str | bool | dict: On success returns a list of Node dataclasses.
                See `types.py -> Node`
        """
        await self._connect()
        parameters = {
            "nodes": nodes
        }
        result = await self._call_api("Core/GetConfigs", parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return list(Node(**node) for node in result)

    async def getUpdateInfo(self) -> UpdateInfo | str | int | bool | None:
        """
        Returns a data class `UpdateInfo` and `UpdateInfo.Build = AMP_Version` to access Version information for AMP.

        Returns:
            UpdateInfo | str | int | bool | None: On success returns a UpdateInfo dataclass.
                See `types.py -> UpdateInfo`
        """
        await self._connect()
        result = await self._call_api("Core/GetUpdateInfo")
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return UpdateInfo(**result)  # type:ignore

    async def getAllAMPUserInfo(self) -> list[User] | str | int | bool | None:
        """
        Represents all the AMP User info.

        Returns:
            list[User] | str | int | bool | None: On success returns a list of User dataclasses.
                See `types.py -> User`
        """
        await self._connect()
        result = await self._call_api("Core/GetAllAMPUserInfo")
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return list(User(**user) for user in result)
