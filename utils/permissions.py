import logging
import db
import pathlib
import json
import sys

from discord.ext import commands

from typing import Union
from db import DBUser, DBHandler


class Gatekeeper_Permissions():
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Gatekeeper_Permissions, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        self.logger = logging.getLogger()
        self.DBHandler: DBHandler = db.getDBHandler()
        self.DB = self.DBHandler.DB

        self._last_modified: float = 0
        self.permissions = None
        self.permission_roles: list[str] = []

        self.validate_and_load()
        self.get_roles()
        self.logger.info('**SUCCESS** Loading Bot Permissions')

    def validate_and_load(self):
        """Validates the contents of bot_perms.json."""
        self.json_file = pathlib.Path.cwd().joinpath('bot_perms.json')
        if self.json_file.stat().st_mtime > self._last_modified:
            try:
                self.permissions = json.load(open(self.json_file, 'r'))
                self._last_modified = self.json_file.stat().st_mtime

                # Soft validation of the file to help with errors.
                # Verifies each role has a numeric discord_role_id or is equal to None and the name is not empty.
                for role in self.permissions['Roles']:
                    if len(role['name']) == 0:
                        self.logger.critical(f'You are missing a role name, please do not leave role names empty..')
                        sys.exit(0)

                    if role['discord_role_id'] == 'None':
                        continue

                    elif type(role['discord_role_id']) != str:
                        self.logger.critical(f'Your Discord Role ID for {role["name"]} does not appear to be string. Please check your bot_perms.json.')
                        sys.exit(0)

                    elif not role['discord_role_id'].isnumeric():
                        self.logger.critical(f'Your Discord Role ID for {role["name"]} does not appear to be all numbers. Please check your bot_perms.json.')
                        sys.exit(0)

            except json.JSONDecodeError:
                self.permissions = None
                self.logger.critical('Unable to load your permissions file. Please check your formatting.')

    def perm_node_check(self, command_perm_node: str, context: commands.Context) -> bool:
        """Checks a Users for a DB Role then checks for that Role inside of bot_perms.py, then checks that Role for the proper permission node."""
        # Lets get our DB user and check if they exist.
        DB_user: DBUser | None = self.DB.GetUser(str(context.author.id))
        if DB_user == None:
            return False

        # Lets also check for their DB Role
        user_role = DB_user.Role
        if user_role == None:
            return False

        # Need to turn author roles into a list of ints.
        user_discord_role_ids: list[str] = []
        for user_roles in context.author.roles:
            user_discord_role_ids.append(str(user_roles.id))

        # This is to check for Super perm nodes such as `server.*`
        command_super_node = command_perm_node.split(".")[0] + '.*'

        if self.permissions == None:
            self.logger.error('**ATTENTION** Please verify your bot_perms file, it failed to load.')
            return False

        self.validate_and_load()
        self.logger.info('Validated and Loaded Permissions File.')
        roles = self.permissions['Roles']
        for role in roles:
            if user_role.lower() in role['name'].lower() or role['discord_role_id'] in user_discord_role_ids:
                if command_super_node in role['permissions']:
                    command_perm_node_false_check = '-' + command_perm_node
                    if command_perm_node_false_check in role['permissions']:
                        if command_perm_node_false_check[1:] == command_perm_node:
                            self.logger.dev('This perm node has been denied even though you have global permissions.', command_perm_node_false_check, command_perm_node)  # type:ignore
                            return False

                if command_perm_node in role['permissions']:
                    self.logger.dev('Found command perm node in Roles Permissions list.', command_perm_node)  # type:ignore
                    return True

        # If all else fails.. return False
        return False

    def get_roles(self) -> list[str]:
        """Pre build my Permissions Role Name List"""
        self.permission_roles = []
        for role in self.permissions['Roles']:
            self.permission_roles.append(role['name'])
        return self.permission_roles

    async def get_role_prefix(self, user_id: str = None, context: commands.Context = None) -> Union[str, None]:
        """Use to get a Users Role Prefix for displaying."""

        # This grabs all a Users discord roles and makes a list of their ids
        discord_roles = []
        if context != None:
            for role in context.author.roles:
                discord_roles.append(str(role.id))

            # This works because you can only have one bot_perms role.
            for role in self.permissions['Roles']:
                if role['discord_role_id'] in discord_roles:
                    return role['prefix']

        db_user: DBUser | None = self.DB.GetUser(user_id)
        if db_user != None and db_user.Role != None:
            rolename = db_user.Role
            if rolename in self.permission_roles:
                for role in self.permissions['Roles']:
                    if role['name'] == rolename:
                        return role['prefix']
                    else:
                        continue
        return None


# Used to maintain a "Global" botPerms() object.
bPerms = None  # type:ignore


def get_botPerms() -> Gatekeeper_Permissions:
    """Returns the Global botPerms() object; otherwise creates it."""
    global bPerms
    if bPerms == None:
        bPerms: Gatekeeper_Permissions = Gatekeeper_Permissions()
    return bPerms
