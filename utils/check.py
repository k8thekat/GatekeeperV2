import logging
from typing import Union
import asyncio
import aiohttp

import discord
from discord import Member, Interaction, Guild
from discord.ext import commands

import db
from db import DBHandler, DBServer
from utils.permissions import Gatekeeper_Permissions
from utils.helper.parser import serverparse
from amp import AMPInstance


async def async_rolecheck(context: Union[commands.Context, Interaction, Member], perm_node: str = None):
    _DBHandler: DBHandler = db.getDBHandler()
    _DBConfig = _DBHandler.DBConfig
    _mod_role = _DBConfig.GetSetting('Moderator_role_id')
    _logger = logging.getLogger(__name__)
    _logger.dev(f'Permission Context command node {perm_node if perm_node != None else str(context.command).replace(" ",".")}')  # type: ignore

    author = context
    if type(context) != discord.Member:
        # This is used for `discord.ext.commands.Context` objects
        if hasattr(context, 'author'):
            top_role_id = context.author.top_role.id
            author = context.author

        # This is used for `discord.Interaction` objects
        elif hasattr(context, 'user'):
            top_role_id = context.user.top_role.id
            author = context.user

    #!TODO! Not sure which one triggers this action.
    elif type(context) == discord.member.Member:
        print('Triggered discord.member.Member in Role_check()')
        top_role_id = context.top_role.id
        author = context.name
    else:
        # This is for on_message commands
        top_role_id = context.message.author.top_role.id
        author = context.message.author

    # This fast tracks role checks for Admins, which also allows the bot to still work without a Staff Role set in the DB
    admin = author.guild_permissions.administrator
    if admin == True:
        _logger.command(f'*Admin* Permission Check Okay on {author}')  # type:ignore
        return True

    # This handles Custom Permissions for people with the flag set.

    if _DBConfig.GetSetting('Permissions') == 1:  # 0 is Default, 1 is Custom
        if perm_node == None:
            perm_node = str(context.command).replace(" ", ".")

        _bPerms: Gatekeeper_Permissions = Gatekeeper_Permissions()
        _bPerms.perm_node_check(perm_node, context)
        if _bPerms.perm_node_check == False:
            _logger.command(f'*Custom* Permission Check Failed on {author} missing {perm_node}')  # type:ignore
            return False
        else:
            _logger.command(f'*Custom* Permission Check Okay on {author}')  # type:ignore
            return True

    # This is the final check before we attempt to use the "DEFAULT" permissions setup.
    if _mod_role == None:
        await context.send(f'Please have an Adminstrator run `/bot moderator (role)` or consider setting up Custom Permissons.', ephemeral=True)
        _logger.error(f'DBConfig Moderator role has not been set yet!')
        return False

    staff_role, author_top_role = 0, 0
    guild_roles = context.guild.roles
    # Guild Roles is a heirachy tree;
    # So here I am comparing if the author/user's top role is greater than or equal to the `_mod_role` in terms of index values from the list.
    for i in range(0, len(guild_roles)):
        if guild_roles[i].id == top_role_id:
            author_top_role = i

        if guild_roles[i].id == _mod_role:
            staff_role = i

    if author_top_role >= staff_role:
        _logger.command(f'*Default* Permission Check Okay on {author}')  # type: ignore
        return True

    _logger.command(f'*Default* Permission Check Failed on {author}')  # type:ignore
    await context.send('You do not have permission to use that command...', ephemeral=True)
    return False


def role_check():
    """Use this before any Commands that require a Staff/Mod level permission Role, this will also check for Administrator"""
    # return commands.check(async_rolecheck(permission_node=perm))
    return commands.check(async_rolecheck)


def author_check(user_id: int = None):
    """Checks if User ID matchs Context User ID"""
    async def predicate(context: commands.Context):
        if context.author.id == user_id:
            return True
        else:
            await context.send('You do not have permission to use that command...', ephemeral=True)
            return False
    return commands.check(predicate)


def guild_check(guild_id: int):
    """Use this before any commands to limit it to a certain guild usage."""
    async def predicate(context: commands.Context) -> bool:

        if isinstance(context.guild, Guild):
            guild_id: int = context.guild.id
            return True
        else:
            await context.send('You do not have permission to use that command...', ephemeral=True)
            return False
    return commands.check(predicate)


async def validate_avatar(db_server: DBServer) -> Union[str, None]:
    """This checks the DB Server objects Avatar_url and returns the proper object type. \n
    Must be either `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated."""
    if db_server.Avatar_url == None:
        return None
    # This handles web URL avatar icon urls.
    if db_server.Avatar_url.startswith("https://") or db_server.Avatar_url.startswith("http://"):
        if db_server.Avatar_url not in self.AMPServer_Avatar_urls:
            await asyncio.sleep(.5)
            # Validating if the URL actually works/exists via response.status codes.
            async with aiohttp.ClientSession() as session:
                async with session.get(db_server.Avatar_url) as response:
                    if response.status == 200:
                        self.AMPServer_Avatar_urls.append(db_server.Avatar_url)
                        return db_server.Avatar_url
                    else:
                        self.logger.error(f'We are getting Error Code {response.status}, not sure whats going on...')
                        return None
        else:
            return db_server.Avatar_url
    else:
        return None


async def serverCheck(context: commands.Context, server, online_only: bool = True) -> Union[AMPInstance, bool]:
    """Verifies if the AMP Server exists and if its Instance is running and its ADS is Running"""
    amp_server = serverparse(server, context, context.guild.id)

    if online_only == False:
        return amp_server

    if amp_server.Running and amp_server._ADScheck():
        return amp_server

    await context.send(f'Well this is awkward, it appears the **{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}** is `Offline`.', ephemeral=True, delete_after=self._client.Message_Timeout)
    return False
