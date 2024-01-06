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

    def __init__(self, url: str, amp_user: str, amp_password: str, amp_2fa: bool = False, amp_2fa_token: str = "", instance_url: str = None) -> None:
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

    async def _call_api(self, api: str, parameters: None | dict[str, Any] = None) -> str | bool | dict | list[Any]:
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
            print("Else return post_req_json")
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

    async def login(self, amp_user: str, amp_password: str, token: str = "", rememberME: bool = False) -> LoginResults:
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
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(LoginResults, result)

    async def callEndPoint(self, api: str, parameters: None | dict[str, Any] = None) -> str | bool | dict:
        """
        Universal API method for calling any API endpoint. Some API endpoints require ADS and some may require an Instance ID. \n

        Args:
            api (str): API endpoint to call. `eg "Core/GetModuleInfo"` (Assume this starts with www.yourAMPURL.com/API/)
            parameters (None | dict[str, str]): Parameters to pass to the API endpoint. Session ID is already handled for you. Defaults to None

        Returns:
            str | bool | dict: Returns the JSON response from the API call.
        """
        await self._connect()
        result = await self._call_api(api, parameters)
        return result

    async def getInstances(self) -> list[Controller]:
        """
        Returns a list of all Instances on the AMP Panel.\n
        **Requires ADS**

        Returns:
            str | bool | dict: On success returns a dictionary containing Server/Instance specific information. \n
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

    async def getInstance(self, instanceID: str) -> Instance:
        """
        Returns the Instance information for the provided Instance ID.\n
        **Requires ADS**

        Args:
            instanceID (str): The Instance ID to get information for.

        Returns:
            str | bool | dict: Returns the JSON response from the API call.
        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        parameters = {"InstanceId": instanceID}
        result = await self._call_api("ADSModule/GetInstance", parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(Instance, result)

    async def getUpdates(self) -> Updates:
        """
        Requests the recent entries of the Instance Updates; will acquire all updates from previous API call of `getUpdate()`

        Returns:
            str | bool | dict: Returns the JSON response from the API call.
        """
        await self._connect()
        result = await self._call_api('Core/GetUpdates')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(Updates, result)

    async def sendConsoleMessage(self, msg: str) -> None:
        """
        Sends a string to the Console. (eg `/list`)
        """
        await self._connect()
        parameters = {'message': msg}
        await self._call_api('Core/SendConsoleMessage', parameters)
        return

    async def startInstance(self) -> None:
        """
        Starts the AMP Server/Instance
        """
        await self._connect()
        await self._call_api('Core/Start')
        return

    async def stopInstance(self) -> None:
        """
        Stops the AMP Server/Instance
        """
        await self._connect()
        await self._call_api('Core/Stop')
        return

    async def restartInstance(self) -> None:
        """
        Restarts the AMP Server/Instance
        """
        await self._connect()
        await self._call_api('Core/Restart')
        return

    async def killInstance(self) -> None:
        """
        Kills the AMP Server/Instance
        """
        await self._connect()
        await self._call_api('Core/Kill')
        return

    async def getStatus(self) -> Status:
        """
        Gets the AMP Server/Instance Status information.

        Returns:
            str | bool | dict: On success returns a dict containing various key/value combos below. \n
            `{'State': int, 'Uptime': 'str', 'Metrics': {'CPU Usage': {'RawValue': int, 'MaxValue': int, 'Percent': int, 'Units': '%', 'Color': 'hex', 'Color2': 'hex', 'Color3': 'hex'}, 'Memory Usage': {'RawValue': int, 'MaxValue': int, 'Percent': int, 'Units': 'MB', 'Color': 'hex', 'Color3': 'hex'}, 'Active Users': {'RawValue': int, 'MaxValue': int, 'Percent': int, 'Units': '', 'Color': 'hex', 'Color3': 'hex'}}}`
        """
        await self._connect()
        result = await self._call_api('Core/GetStatus')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(Status, result)

    async def getUserList(self) -> str | bool | dict:
        """
        Returns a dictionary of the connected Users to the Server.

        Returns:
            str | bool | dict: On success a dictionary with a key value of "Users" followed by a list of each user name.
        """
        await self._connect()
        result = await self._call_api('Core/GetUserList')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        # TODO- Needs to be validated.
        return Players(data=result)

    async def getScheduleData(self) -> str | bool | dict:
        """
        Returns a dictionary of the Server/Instance Schedule events and triggers.

        Returns:
            str | bool | dict: On success a dictionary with the schedules broken up by Events and Triggers.
        """
        await self._connect()
        result = await self._call_api('Core/GetScheduleData')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return fromdict(ScheduleData, result)

    async def copyFile(self, source: str, destination: str) -> None:
        """
        Moves a file from the source directory to the destination. The path is relative to the Server/Instance root.

        Args:
            source (str): Use forward slashes for the path. eg `Minecraft/mods/`
            destination (str): Same as source.
        """
        await self._connect()
        parameters = {
            'Origin': source,
            'TargetDirectory': destination
        }
        await self._call_api('FileManagerPlugin/CopyFile', parameters)
        return

    async def renameFile(self, original: str, new: str) -> None:
        """
        Changes the name of a file.

        Args:
            original (str): Old File name.
            new (str): New name to change the file to.
        """
        await self._connect()
        parameters = {
            'Filename': original,
            'NewFilename': new
        }
        await self._call_api('FileManagerPlugin/RenameFile', parameters)
        return

    async def getDirectoryListing(self, directory: str) -> str | bool | dict:
        """
        Returns a dictionary of the directory's properties and the files contained in the directory and their properties.

        Args:
            directory (str): Relative to the Server root directory . eg `Minecraft/` - If a file has a similar name it may return the file instead of the directory.

        Returns:
            str | bool | dict: On success returns a dictionary containing the following. \n
            `{'IsDirectory': bool, 'IsVirtualDirectory': bool, 'Filename': 'string', 'SizeBytes': int, 'Created': 'unix timestamp', 'Modified': 'unix timestamp', 'IsDownloadable': bool, 'IsEditable': bool, 'IsArchive': bool, 'IsExcludedFromBackups': bool}`
        """
        await self._connect()
        parameters = {
            'Dir': directory
        }
        result = await self._call_api('FileManagerPlugin/GetDirectoryListing', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return list(Directory(**directory) for directory in result)

    async def getFileChunk(self, name: str, position: int, length: int) -> str | bool | dict:
        """
        Returns a specific section of Base64Data from a file.

        Args:
            name (str): File to open and read from.
            position (int): Start position to read from.
            length (int): How far to read from the start position.

        Returns:
            str | bool | dict: On success returns a dictionary containing the following. \n
            `{'Base64Data': 'str', 'BytesLength': int}`
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
        return FileChunk(**result)

    async def writeFileChunk(self, filename: str, position: int, data: str) -> None:
        """
        Writes data to the file specified starting at the position specified.

        Args:
            filename (str): Name of the file to write to.
            position (int): Position to start writing in the file.
            data (str): data to write to the file.
        """
        await self._connect()
        parameters = {
            'Filename': filename,
            'Position': position,
            'Data': data
        }
        await self._call_api('FileManagerPlugin/WriteFileChunk', parameters)
        return

    async def endUserSession(self, session_id: str) -> str | None:
        """
        Closes the specified User's session ID to AMP.\n
        **Requires ADS**

        Args:
            session_id (str): session ID to end.
        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        parameters = {
            'Id': session_id
        }
        await self._call_api('Core/EndUserSession', parameters)
        return

    async def getActiveAMPSessions(self) -> str | bool | dict:
        """
        Returns currently active AMP Sessions.\n
        **Requires ADS**

        Returns:
            str | bool | dict: On success returns a dictionary containing the following. \n
            `{'Source': '127.0.0.1', 'SessionID': '649a601d-694a-48b2-946d-f4fe4c02f920', 'LastActivity': 'unix timestamp', 'StartTime': 'unix timestamp', 'Username': 'bot', 'SessionType': 'FTP'}`
        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        result = await self._call_api('Core/GetActiveAMPSessions')
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return Session(**result)

    async def getInstanceStatuses(self) -> str | bool | dict:
        """
        Returns a dictionary of the Server/Instance Status. \n
        **Requires ADS**

        Returns:
            str | bool | dict: On success returns a dictionary containing the following. \n
            `{'InstanceID': '0009776e-0d48-44ff-93de-b3852ce3fdad', 'Running': bool}`
        """
        if type(self) != AMP_API:
            return self.ADS_ONLY

        await self._connect()
        result = await self._call_api('ADSModule/GetInstanceStatuses')
        return result

    async def trashDirectory(self, dir_name: str) -> None:
        """
        Moves a directory to the trash, files must be trashed before they can be `emptied`.\n
        See emptyTrash().


        Args:
            dir_name (str): Directory name; relative to the Server/Instance root. Supports pathing. eg `/home/config`
        """
        await self._connect()
        parameters = {
            'DirectoryName': dir_name
        }
        await self._call_api('FileManagerPlugin/TrashDirectory', parameters)
        return

    async def trashFile(self, filename: str) -> None:
        """
        Moves a file to the trash, files must be trashed before they can be `emptied`. \n
        See emptyTrash().

        Args:
            filename (str): File name; relative to the Server/Instance root. Supports pathing. eg `/home/config`
        """
        await self._connect()
        parameters = {
            'Filename': filename
        }
        await self._call_api('FileManagerPlugin/TrashFile', parameters)
        return

    async def emptyTrash(self, trash_dir: str) -> None:
        """
        Empties a trash bin for the AMP Server/Instance.

        Args:
            trash_dir (str): Directory name; relative to the Server/Instance root. Supports pathing. eg `/home/config` \n
            Typically the directory is called `Trashed Files`, it is case sensitive and located in the Server/Instance root directory.
        """
        await self._connect()
        parameters = {
            'TrashDirectoryName': trash_dir
        }
        await self._call_api('FileManagerPlugin/EmptyTrash', parameters)
        return

    async def takeBackup(self, title: str, description: str, sticky: bool = False) -> None:
        """
        Takes a backup of the AMP Server/Instance.

        Args:
            title (str): Title of the backup; aka `Name`
            description (str): Brief description of why or what the backup is for.
            sticky (bool, optional): Sticky backups won't be deleted to make room for automatic backups. Defaults to `False`.
        """
        await self._connect()
        parameters = {
            "Title": title,
            "Description": description,
            "Sticky": sticky
        }
        await self._call_api('LocalFileBackupPlugin/TakeBackup', parameters)
        return

    async def getAMPUserInfo(self, name: str) -> str | bool | dict:
        """
        Retrieves the AMP User information for the provided username.\n

        Args:
            name (str): AMP User name.

        Returns:
            str | bool | dict: Typically returns a dictionary containing the following. \n
            `{'ID': str, 'Name': 'Gatekeeper', 'Disabled': bool, 'Permissions': [], 'IsSuperUser': bool, 'LastLogin': 'unix timestamp', 'PasswordExpires': bool, 'CannotChangePassword': bool, 'MustChangePassword': bool, 'IsTwoFactorEnabled': bool, 'Roles': list(str), 'IsLDAPUser': bool, 'GravatarHash': str}}
        """

        await self._connect()
        parameters = {
            'Username': name
        }
        result = await self._call_api('Core/GetAMPUserInfo', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return User(**result)

    async def currentSessionHasPermission(self, permission_node: str) -> str | bool | dict:
        """
        Retrieves the current Session IDs permissions. This will differ between the ADS and a Server/Instance.

        Args:
            permission_node (str): The permission node to check for. eg `Core.RoleManagement.DeleteRoles` \n
            Supports looking for a blocked permisson node simply by appending `-` in front of the permission node. eg `-Core.RoleManagement.DeleteRoles`\n
            Supports wildcards `*`. eg `Core.RoleManagement.*`

        Returns:
            str | bool | dict: On success returns a dictionary containing a bool.
        """
        await self._connect()
        parameters = {
            'PermissionNode': permission_node
        }
        result = await self._call_api('Core/CurrentSessionHasPermission', parameters)
        return result

    async def getAMPRolePermissions(self, role_id: str) -> str | bool | dict:
        """
        Retrieves the AMP Role permission nodes for the provided role ID.

        Args:
            role_id (str): The role ID. eg `5d6566e0-fae2-41d7-bfb6-d21033247f2e`

        Returns:
            str | bool | dict: On success returns a list containing all the permission nodes for the provided role ID.
        """
        await self._connect()
        parameters = {
            'RoleId': role_id
        }
        result = await self._call_api("Core/GetAMPRolePermissions", parameters)
        return result

    async def getPermissionsSpec(self) -> str | bool | dict:
        """
        Retrieves the AMP Permissions node tree.

        Returns:
            str | bool | dict: On success returns a dictionary containing all the permission nodes, descriptions and other attributes.
        """
        await self._connect()
        result = await self._call_api("Core/GetPermissionsSpec")
        return result

    async def getRoleIds(self) -> str | bool | dict:
        """
        Retrieves all the Roles AMP currently has and the role IDs.

        Returns:
            str | bool | dict: On success returns a dictionary containing all the roles and their IDs. Example below. \n
            `{'00000000-0000-0000-0000-000000000000': 'Default',
            '9d390d0e-79a0-48c1-8eeb-c803876cd8e1': 'Super Admins'}`
        """
        await self._connect()
        result = await self._call_api('Core/GetRoleIds')
        return result

    async def createRole(self, name: str, as_common_role: bool = False) -> str | bool | dict:
        """
        Creates an AMP Role.

        Args:
            name (str): The name of the role.
            as_common_role (bool, optional): A role that everyone has. Defaults to False.

        Returns:
            str | bool | dict: On success returns a dictionary containing the role ID and Status. \n 
            `{'Result': '41f46907-43ac-40dc-95dc-4db17cf51a9c', 'Status': True}`\n
            Failure-> `{'result': {'Result': '00000000-0000-0000-0000-000000000000', 'Status': False, 'Reason': 'You do not have permission to create common roles.'}}`
        """
        await self._connect()
        parameters = {
            'Name': name,
            'AsCommonRole': as_common_role
        }
        result = await self._call_api('Core/CreateRole', parameters)
        return result

    async def getRole(self, role_id: str) -> str | bool | dict:
        """
        Retrieves the AMP Role information for the provided role ID.

        Args:
            role_id (str): The role ID to get information for.

        Returns:
            str | bool | dict: On success will return a dictionary containing the following. \n
            `{'ID': '41f46907-43ac-40dc-95dc-4db17cf51a9c', 'IsDefault': bool, 'Name': 'Gatekeeper', 'Description': str, 'Hidden': bool, 'Permissions': list(str), 'Members': list(str), 'IsInstanceSpecific': bool, 'IsCommonRole': bool, 'DisableEdits': bool}`
        """
        await self._connect()
        parameters = {
            'RoleId': role_id
        }
        result = await self._call_api('Core/GetRole', parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return Role(**result)

    async def setAMPUserRoleMembership(self, user_id: str, role_id: str, is_member: bool) -> str | bool | dict:
        """
        Adds a user to an AMP role.

        Args:
            user_id (str): User ID to add to the role.
            role_id (str): Role ID to add the user to.
            is_member (bool): `True` to add the user to the role, `False` to remove the user from the role.

        Returns:
            str | bool | dict: On success returns a `Status` bool.
        """
        await self._connect()
        parameters = {
            'UserId': user_id,
            'RoleId': role_id,
            'IsMember': is_member
        }
        result = await self._call_api('Core/SetAMPUserRoleMembership', parameters)
        return result

    async def SetAMPRolePermission(self, role_id: str, permission_node: str, enabled: Union[None, bool]) -> str | bool | dict:
        """
        Set a permission node to `True` or `False` for the provided AMP role.

        Args:
            role_id (str): AMP role id.
            permission_node (str): AMP permission node. eg `Core.RoleManagement.DeleteRoles`
            enabled (Union[None, bool]): Set a permission to `True`, `False` or `None` depending on the results you can disable or enable an entire tree node of permissions.

        Returns:
            str | bool | dict: On success returns a `Status` bool.
        """
        await self._connect()
        parameters = {
            'RoleId': role_id,
            'PermissionNode': permission_node,
            'Enabled': enabled
        }
        result = await self._call_api('Core/SetAMPRolePermission', parameters)
        return result

    async def getSettingsSpec(self) -> str | bool | dict:
        """
        Retrieves a Server/Instance nodes list.
        See `util.getNodespec` for a list of possible nodes.

        Returns:
            str | bool | dict: On success returns a dictionary containing all of the Server/Instance nodes and there information.
        """
        await self._connect()
        result = await self._call_api('Core/GetSettingsSpec')
        return result

    async def getConfig(self, node: str) -> str | bool | dict:
        # TODO - Need to figure out how this command works entirely. Possible need a new node list
        """
        Returns the config settings for a specific node.

        Args:
            node (str): The AMP node to inspect eg `ADSModule.Networking.BaseURL`

        Returns:
            str | bool | dict: On success returns a dictionary containing the following. \n
            `{'ReadOnly': bool, 'Name': str, 'Description': str , 'Category': str, 'CurrentValue': str, 'ValType': str, 'EnumValuesAreDeferred': bool, 'Node': str, 'InputType': str, 'IsProvisionSpec': bool, 'ReadOnlyProvision': bool, 'Actions': list, 'Keywords': str, 'AlwaysAllowRead': bool, 'Tag': str, 'MaxLength': int, 'Placeholder': str, 'Suffix': str, 'Meta': str, 'RequiresRestart': bool, 'Required': bool}`
        """
        await self._connect()
        parameters = {
            "node": node
        }
        result = await self._call_api("Core/GetConfig", parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return Node(**result)

    async def getConfigs(self, nodes: list[str]) -> list[Node]:
        # TODO - Need to figure out how this command works entirely. Possible need a new node list
        """
        Returns the config settings for each node in the list.

        Args:
            node (list[str]): List of nodes to look at.

        Returns:
            str | bool | dict: On success returns a list of dictionarys containing the same information as `getConfig`
        """
        await self._connect()
        parameters = {
            "nodes": nodes
        }
        result = await self._call_api("Core/GetConfigs", parameters)
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return list(Node(**node) for node in result)

    async def getUpdateInfo(self) -> UpdateInfo:
        """
        Returns a data class `UpdateInfo` and `UpdateInfo.Build = AMP_Version` to access Version information for AMP.

        Returns:
            UpdateInfo: data class `UpdateInfo` see `types.py`
        """
        await self._connect()
        result = await self._call_api("Core/GetUpdateInfo")
        if isinstance(result, Union[None, bool, int, str]):
            return result
        return UpdateInfo(**result)

    async def getAllAMPUserInfo(self) -> list[User]:
        """
        Represents all the AMP User info.

        Returns:
            list[User]: list of `User` data class.
        """
        await self._connect()
        result = await self._call_api("Core/GetAllAMPUserInfo")
        return list(User(**user) for user in result)
