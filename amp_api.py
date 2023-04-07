from __future__ import annotations
from typing import Union
import json
import pathlib
import traceback

import aiohttp
from aiohttp import ClientResponse

import time
import sys
import logging
from dotenv import load_dotenv
import os
from argparse import Namespace
from pyotp import TOTP  # 2Factor Authentication Python Module
import requests

from amp_handler import AMPHandler


class AMP_API():
    _logger = logging.getLogger()
    _AMPHandler: AMPHandler = AMPHandler()
    _AMPheader: dict = {'Accept': 'text/javascript'}
    _InstanceName: str = ""
    _URL: str = ""
    #_SESSION_IDS: dict[str, str]
    _use_AMP2FA: bool = False
    _AMP2FACTOR: Union[str, TOTP] = ""

    FAILED_LOGIN: str = ""
    NO_DATA: str = "Failed to recieve any data from post request."
    UNAUTHORIZED_ACCESS: str = "Gatekeeper does not have the required permissions to interact with this instance."

    load_dotenv()
    AMPUSER: str = os.environ["AMPUSER"].strip()
    AMPPASSWORD: str = os.environ["AMPPASSWORD"].strip()
    AMPURL: str = os.environ["AMPURL"].strip()
    AMPAUTH: str = os.environ["AMPAUTH"].strip()

    def __init__(self, instance_name: str, instance_id: str = '0', session_id: Union[str, dict[str, str]] = '0', args: Union[Namespace, None] = None):
        self._session_id = session_id
        self._InstanceName = instance_name
        self._InstanceID = instance_id
        self._cwd = pathlib.Path.cwd()
        self._URL = self._URL + "/API"  # This will be the default URL; this will change on new instances.
        self._args = args

        if self._InstanceID == '0':
            self._val_settings()

    async def _call_api(self, api: str, parameters: dict[str, str]):
        """This is the API Call function"""
        # TODO -- Use ValueError()
        # set vars for typical return errors depending on the issue returned.
        # see below the bool returns and change to some system of str
        # example
        # UNAUTHORIZED_ACCESS:str = "AMP/Gatekeeper does not have the required permissions to interact with this instance."
        # `ValueError(UNAUTHORIZED_ACCESS) or ValueError(FAILED_STATUS)`
        self._logger.info(f'Function {api} was called with {parameters}')
        _post_req: ClientResponse | None
        jsonhandler = json.dumps(parameters)

        # while (True):
        try:
            async with aiohttp.ClientSession() as session:
                _post_req = session.post(self._URL + api, headers=self._AMPheader, data=jsonhandler)
                self._logger.debug(f'Post Request Prints: {_post_req.json()}')
            # self._logger.error(f'{self._InstanceName}: AMP API recieved no Data; sleeping for 5 seconds...')
            # time.sleep(5)
        # FIXME - Need to not catch all Excepts..
        except Exception as e:
            print(type(e))  # So I can handle each exception properly.
            raise ValueError(e)
            # if self._AMPHandler._SuccessfulConnection == False:
            #     self._logger.critical('Unable to connect to URL; please check Tokens.py -> AMPURL')
            #     sys.exit(-1)

            # self._logger.warning('AMP API was unable to connect; sleeping for 30 seconds...')
            # time.sleep(30)

        if _post_req.status != 200:
            return ConnectionError(self.NO_DATA)
        # self._AMPHandler._SuccessfulConnection = True

        # Error catcher for API calls
        # FIXME Possible issue here..
        # if type(_post_req.json()) == None:
        #     self._logger.error(f"AMP_API CallAPI ret is 0: status_code {_post_req.status_code}")
        #     self._logger.error(_post_req.raw)

        # if _post_req.json() == None:
        #     self._logger.error('Failed to recieve data from post request.')
        #     return False
        _post_req_json = _post_req.json()
        # Since we are using GetUpdates every second for Console Updates; lets ignore them here so we don't sleep our thread.
        # FIXME -- This may not need to be here anymore.
        if api == 'Core/GetUpdates':
            return _post_req_json

        if len(_post_req.content) > 0:
            raise ConnectionError(self.NO_DATA)

        # FIXME -- This will need to be tracked and see what triggers what.
        if hasattr(_post_req_json, "result"):
            # if "result" in _post_req.json():
            if type(_post_req_json["result"]) == bool:
                if _post_req_json["result"] == True:
                    return _post_req_json

                if _post_req_json["result"] != True:
                    self._logger.error(f'The API Call {api} failed because of {_post_req_json}')
                    return _post_req_json

                if ("Status" in _post_req_json["result"]) and (_post_req_json["result"]["Status"] == False):
                    self._logger.error(f'The API Call {api} failed because of Status: {_post_req_json}')
                    return False

        elif hasattr(_post_req_json, "Title"):
            if (type(_post_req_json["Title"]) == str) and (_post_req_json["Title"] == 'Unauthorized Access'):
                self._logger.error(f'["Title"]: The API Call {api} failed because of {_post_req_json}')
                # Resetting the Session ID for the Instance; forcing a new login/SessionID
                # self._AMPHandler._session_IDs.pop(amp_instance.InstanceID)
                # self._SessionID = None
                self._session_id = "0"
                # FIXME -- May need to raise an exception here;
                raise PermissionError(self.UNAUTHORIZED_ACCESS)
                # return False
        return _post_req_json

    def _val_settings(self):
        """Validates the .env settings and if we should use 2FA or not."""
        self._logger.info("Validating your .env file...")
        reset = False

        # if not self.args.token:
        if not self._cwd.joinpath(".env").exists():
            self._logger.critical("**ERROR** Missing our .env, please rename .envtemplate to .env")
            reset = True

        # if -dev is enabled; lets use our DEV information inside our .env file.
        if self._args.dev:  # type:ignore
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
        # async with aiohttp.ClientSession() as session:
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
            input("Press any Key to Exit")
            sys.exit(0)

    def login(self):
        if self._session_id == '0':
            # if self._session_id in self._SESSION_IDS:
            #     self.AMPHandler.SessionIDlist[self.InstanceID] = self.SessionID
            #     return

            self._logger.info(f'AMP API Logging in {self._InstanceName}')

            # We are using 2FA
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
                'token': self._AMP2FACTOR,  # get current 2Factor Code
                'rememberMe': True}

            try:
                result = self._call_api('Core/Login', parameters)
                if isinstance(result, BaseException):
                    return result

                elif hasattr(result, "sessionID"):
                    self._session_id = result['sessionID']
                    #self._SESSION_IDS[self._InstanceID] = self._session_id
                    self.Running = True

                else:
                    self._logger.warning(f'{self._InstanceName} - Instance is Offline')
                    self.Running = False
                    return False

            except Exception as e:
                self._logger.dev(f'Core/Login Exception: {traceback.format_exc()}')
                self._logger.dev(result)

                self._logger.warning(f'{self._InstanceName} - Instance is Offline')
                self.Running = False
                return False

        return True

    def getInstances(self) -> dict[str, dict[str, str]]:
        """This gets all Instances on AMP."""
        self.login()
        parameters = {}
        result = self._call_api('ADSModule/GetInstances', parameters)
        return result

    def consoleUpdate(self) -> dict:
        """Returns `{'ConsoleEntries':[{'Contents': 'String','Source': 'Server thread/INFO','Timestamp': '/Date(1651703130702)/','Type': 'Console'}]`\n
        Will post all updates from previous API call of console update"""
        self.login()
        parameters = {}
        result = self._call_api('Core/GetUpdates', parameters)
        return result

    # def ConsoleMessage_withUpdate(self, msg: str) -> dict:
    #     """This will call Console Update after sending the Console Message (Use this for Commands that require feedback)"""
    #     self.login()
    #     parameters = {'message': msg}
    #     self._call_api('Core/SendConsoleMessage', parameters)
    #     time.sleep(.2)
    #     update = self.ConsoleUpdate()
    #     return update

    def consoleMessage(self, msg: str):
        """Basic Console Message"""
        self.login()
        parameters = {'message': msg}
        self._call_api('Core/SendConsoleMessage', parameters)
        return

    def startInstance(self):
        """Starts AMP Instance"""
        self.login()
        parameters = {}
        self._call_api('Core/Start', parameters)
        return

    def stopInstance(self):
        """Stops AMP Instance"""
        self.login()
        parameters = {}
        self._call_api('Core/Stop', parameters)
        return

    def restartInstance(self):
        """Restarts AMP Instance"""
        self.login()
        parameters = {}
        self._call_api('Core/Restart', parameters)
        return

    def killInstance(self):
        """Kills AMP Instance"""
        self.login()
        parameters = {}
        self._call_api('Core/Kill', parameters)
        return

    def getStatus(self) -> Union[bool, dict]:
        """AMP Instance Status Information"""
        self.login()
        parameters: dict = {}
        result = self._call_api('Core/GetStatus', parameters)
        # This happens because _call_api returns False when it fails permissions.
        if result == False:
            return result

        return result

    def getUserList(self) -> list[str]:
        """Returns a List of connected users."""
        self.login()
        parameters = {}
        result = self._call_api('Core/GetUserList', parameters)
        user_list = []
        for user in result['result']:
            user_list.append(result['result'][user])
        return user_list

    def getSchedule(self) -> dict:
        self.login()
        parameters = {}
        result = self._call_api('Core/GetScheduleData', parameters)
        return result['result']['PopulatedTriggers']

    def setFriendlyName(self, name: str, description: str) -> str:
        """This is used to change an Instance's Friendly Name and or Description. Retains all previous settings. \n
        `This requires the instance to be Offline!`"""
        self.login()
        parameters = {
            'InstanceId': self.InstanceID,
            'FriendlyName': name,
            'Description': description,
            'StartOnBoot': self.DaemonAutostart,
            'Suspended': self.Suspended,
            'ExcludeFromFirewall': self.ExcludeFromFirewall,
            'RunInContainer': self.IsContainerInstance,
            'ContainerMemory': self.ContainerMemoryMB,
            'MemoryPolicy': self.ContainerMemoryPolicy,
            'ContainerMaxCPU': self.ContainerCPUs}
        response = f'{self.FriendlyName} is about to be changed to {name}; this will restart the instance.'
        self._call_api('ADSModule/UpdateInstanceInfo', parameters)
        return response

    def getAPItest(self):
        """Test AMP API calls with this function"""
        self.login()
        parameters = {}
        result = self._call_api('Core/GetModuleInfo', parameters)

        return result

    def copyFile(self, source: str, destination: str):
        self.login()
        parameters = {
            'Origin': source,
            'TargetDirectory': destination
        }
        self._call_api('FileManagerPlugin/CopyFile', parameters)
        return

    def renameFile(self, original: str, new: str):
        self.login()
        parameters = {
            'Filename': original,
            'NewFilename': new
        }
        self._call_api('FileManagerPlugin/RenameFile', parameters)
        return

    def getDirectoryListing(self, directory: str) -> list:
        self.login()
        parameters = {
            'Dir': directory
        }
        result = self._call_api('FileManagerPlugin/GetDirectoryListing', parameters)
        return result

    def getFileChunk(self, name: str, position: int, length: int):
        self.login()
        parameters = {
            'Filename': name,
            'Position': position,
            'Length': length
        }
        result = self._call_api('FileManagerPlugin/GetFileChunk', parameters)
        return result

    def writeFileChunk(self, filename: str, position: int, data: str):
        self.login()
        parameters = {
            'Filename': filename,
            'Position': position,
            'Data': data
        }
        self._call_api('FileManagerPlugin/WriteFileChunk', parameters)
        return

    def endUserSession(self, sessionID: str):
        """Ends specified User Session"""
        self.login()
        parameters = {
            'Id': sessionID
        }
        self._call_api('Core/EndUserSession', parameters)
        return

    def getActiveAMPSessions(self) -> dict:
        """Returns currently active AMP Sessions"""
        self.login()
        parameters = {}
        result = self._call_api('Core/GetActiveAMPSessions', parameters)
        return result

    def getInstanceStatus(self) -> dict:
        """Returns AMP Instance Status"""
        self.login()
        parameters = {}
        result = self._call_api('ADSModule/GetInstanceStatuses', parameters)
        return result

    def trashDirectory(self, dirname: str):
        """Moves a directory to trash, files must be trashed before they can be deleted."""
        self.login()
        parameters = {
            'DirectoryName': dirname
        }
        self._call_api('FileManagerPlugin/TrashDirectory', parameters)
        return

    def trashFile(self, filename: str):
        """Moves a file to trash, files must be trashed before they can be deleted."""
        self.login()
        parameters = {
            'Filename': filename
        }
        self._call_api('FileManagerPlugin/TrashFile', parameters)
        return

    def emptyTrash(self, trashdir: str):
        """Empties a trash bin for the AMP Instance"""
        self.login()
        parameters = {
            'TrashDirectoryName': trashdir
        }
        self._call_api('FileManagerPlugin/EmptyTrash', parameters)
        return

    def takeBackup(self, title: str, description: str, sticky: bool = False):
        """Takes a backup of the AMP Instance; default `sticky` is False!"""
        self.login()
        parameters = {
            "Title": title,
            "Description": description,
            "Sticky": sticky
        }
        self._call_api('LocalFileBackupPlugin/TakeBackup', parameters)
        return

    def getAMPUserInfo(self, name: str) -> Union[str, dict]:
        """Gets AMP user info. if IdOnly is True; returns AMP User ID only!"""
        self.login()
        parameters = {
            'Username': name
        }
        result = self._call_api('Core/GetAMPUserInfo', parameters)
        return result

    def CurrentSessionHasPermission(self, PermissionNode: str) -> dict:
        """Gets current Sessions permission spec"""
        self.login()
        parameters = {
            'PermissionNode': PermissionNode
        }
        result = self._call_api('Core/CurrentSessionHasPermission', parameters)

        if result != False:
            return result['result']

        return result

    def getAMPRolePermissions(self, RoleID: str) -> dict:
        """Gets full permission spec for Role (returns permission nodes)"""
        self.login()
        parameters = {
            'RoleId': RoleID
        }
        result = self._call_api('Core/GetAMPRolePermissions', parameters)
        return result

    def getPermissions(self) -> dict:
        """Gets full Permission spec for self"""
        self.login()
        parameters = {}
        result = self._call_api('Core/GetPermissionsSpec', parameters)
        return result

    def getRoleIds(self) -> dict:
        """Gets a List of all Roles, if set_roleID is true; it checks for `Gatekeeper` and `Super Admins`. Sets them to self.AMP_BotRoleID and self.super_AdminID"""
        self.login()
        parameters = {}
        result = self._call_api('Core/GetRoleIds', parameters)
        return result['result']

    def createRole(self, name: str, AsCommonRole=False):
        """Creates a AMP User role"""
        self.login()
        parameters = {
            'Name': name,
            'AsCommonRole': AsCommonRole
        }
        result = self._call_api('Core/CreateRole', parameters)
        return result

    def getRole(self, Roleid: str):
        """Gets the AMP Role"""
        self.login()
        parameters = {
            'RoleId': Roleid
        }
        result = self._call_api('Core/GetRole', parameters)
        return result

    def setAMPUserRoleMembership(self, UserID: str, RoleID: str, isMember: bool):
        """ Sets the AMP Users Role Membership"""
        self.login()
        parameters = {
            'UserId': UserID,
            'RoleId': RoleID,
            'IsMember': isMember
        }
        result = self._call_api('Core/SetAMPUserRoleMembership', parameters)
        return result

    def setAMPRolePermissions(self, RoleID: str, PermissionNode: str, Enabled: bool):
        """Sets the AMP Role permission Node eg `Core.RoleManagement.DeleteRoles`"""
        self.login()
        parameters = {
            'RoleId': RoleID,
            'PermissionNode': PermissionNode,
            'Enabled': Enabled
        }
        result = self._call_api('Core/SetAMPRolePermission', parameters)

        if result['result']['Status'] == False:
            self.logger.critical(f'Unable to Set Permission Node __{PermissionNode}__ to `{Enabled}` for {RoleID}')
            return False

        return True
