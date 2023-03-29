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
import sys
import logging
import traceback
import time
import os
import sys

import discord
from discord import app_commands, Intents, Guild
import discord.ext.commands
from discord.ext import commands, tasks
from discord.app_commands import Choice

# Custom scripts
from amp_handler import AMPHandler
from amp_instance import AMPInstance
from typing import Union

from utils.permissions import Gatekeeper_Permissions
from utils.context import GatekeeperGuildContext
from utils.embed import bot_settings_embed, bot_about_embed
from utils.check import role_check
from utils.name_converters import name_to_uuid_MC
from utils.emojis import Gatekeeper_Emojis

from argparse import ArgumentParser

Version = 'beta-4.5.4'


class Gatekeeper(commands.Bot):
    # FIXME -- Move all DB related vars to here
    def __init__(self, Version: str) -> None:
        self._logger = logging.getLogger()
        self.DBHandler: DBHandler = db.getDBHandler()
        self.DB: Database = db.getDBHandler().DB
        self.DBConfig: DBConfig = self.DBHandler.DBConfig

        self.guild_id = None
        if self.DBConfig.GetSetting('Guild_ID') != None:
            self.guild_id = int(self.DBConfig.GetSetting('Guild_ID'))

        self.Bot_Version: str = self.DBConfig.GetSetting('Bot_Version')
        if self.Bot_Version == None:
            self.DBConfig.SetSetting('Bot_Version', Version)

        self.AMPHandler = AMPHandler()
        self.AMP: AMPInstance = self.AMPHandler.AMP
        # Simple Datastore of Emojis to use.
        self._emojis = Gatekeeper_Emojis()

        # Discord Specific
        intents: Intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        self.prefix: str = '$'
        self._start_time: float = time.time()
        self._version: str = Version
        super().__init__(intents=intents, command_prefix=self.prefix)
        self.Message_Timeout: int = self.DBConfig.Message_timeout or 60
        self.Whitelist_wait_list: dict[int, str] = {}

    async def setup_hook(self) -> None:

        self._logger.info(f'Discord Version: {discord.__version__}  // Gatekeeper v2 Version: {client.Bot_Version} // Python Version {sys.version}')
        if self.Bot_Version != Version:
            self.update_loop.start()

        import loader
        self.Handler = loader.Handler(self)
        await self.Handler.module_auto_loader()
        await self.Handler.cog_auto_loader()

        # This Creates the Bot_perms Object and validates the File. Also Adds the Command.
        if self.DBConfig.GetSetting('Permissions') == 'Custom':
            await self.permissions_update()

    def self_check(self, message: discord.Message) -> bool:
        return message.author == client.user

    async def on_command_error(self, context: commands.Context, exception: Union[discord.errors.ClientException, discord.errors.Forbidden, discord.errors.DiscordException]) -> None:
        self._logger.error(f'We ran into an issue. {exception}')
        await context.send(content=f'We uhh.. ran into an issue {exception}')
        traceback.print_exception(exception)
        traceback.print_exc()

    async def on_command(self, context: commands.Context) -> None:
        self._logger.command(f'{context.author.name} used {context.command}...')  # type:ignore

    async def on_ready(self) -> None:
        self._logger.info('Are you the Keymaster?...I am the Gatekeeper')

    @tasks.loop(seconds=30)
    async def update_loop(self) -> None:
        self._logger.warn(f'Waiting to Update Bot Version to {Version}...')
        await client.wait_until_ready()
        self._logger.warn(f'Currently Updating Bot Version to {Version}...')
        self.DBConfig.SetSetting('Bot_Version', Version)
        if self.guild_id != None:
            cur_guild: Guild | None = self.get_guild(self.guild_id)
            if isinstance(cur_guild, Guild):
                self.tree.copy_global_to(guild=cur_guild)  # type:ignore
                await self.tree.sync(guild=cur_guild)
                self._logger.warn(f'Syncing Commands via update_loop to guild: {cur_guild.name if cur_guild != None else "None"} {await self.tree.sync(guild= cur_guild)}')
        else:
            self._logger.error(f'It appears I cannot Sync your commands for you, please run {self.prefix}bot utils sync or `/bot utils sync` to update your command tree. Please see the readme if you encounter issues.')
        self.update_loop.stop()

    async def permissions_update(self) -> bool:
        """Loads the Custom Permission Cog and Validates the File."""
        try:
            await self.load_extension('cogs.Permissions_cog')

        except discord.ext.commands.errors.ExtensionAlreadyLoaded:
            pass

        except Exception as e:
            self._logger.error(f'We ran into an Error Loading the Permissions_Cog. Error - {traceback.format_exc()}')
            return False

        self._bPerms: Gatekeeper_Permissions = Gatekeeper_Permissions()
        return True


client: Gatekeeper = Gatekeeper(Version=Version)


@commands.hybrid_command(name='gk_sync')
# This needs to be a hybrid and a slash command so people can sync commands when they invite the bot.
@role_check()
async def bot_utils_sync(context: GatekeeperGuildContext, local: bool = True, reset: bool = False):
    """Syncs Bot Commands to the current guild this command was used in."""
    await context.defer()
    # This keeps our DB Guild_ID Current.
    if client.guild_id == None or context.guild.id != int(client.guild_id):
        client.DBConfig.SetSetting('Guild_ID', context.guild.id)

    if reset:
        if local:
            # Local command tree reset
            client.tree.clear_commands(guild=context.guild)
            client._logger.info(f'Bot Commands Reset Locally and Sync\'d: {await client.tree.sync(guild=context.guild)}')  # type:ignore
            return await context.send('**WARNING** Resetting Gatekeeper Commands Locally...', ephemeral=True, delete_after=client.Message_Timeout)

        elif context.author.id == 144462063920611328:
            # Global command tree reset, limited by k8thekat discord ID
            client.tree.clear_commands(guild=None)
            client._logger.info(f'Bot Commands Reset Global and Sync\'d: {await client.tree.sync(guild=None)}')  # type:ignore
            return await context.send('**WARNING** Resetting Gatekeeper Commands Globally...', ephemeral=True, delete_after=client.Message_Timeout)
        else:
            return await context.send('**ERROR** You do not have permission to reset the commands.', ephemeral=True, delete_after=client.Message_Timeout)

    if local:
        # Local command tree sync
        client.tree.copy_global_to(guild=context.guild)
        client._logger.info(f'Bot Commands Sync\'d Locally: {await client.tree.sync(guild=context.guild)}')  # type:ignore
        return await context.send(f'Successfully Sync\'d Gatekeeper Commands to {context.guild.name}...', ephemeral=True, delete_after=client.Message_Timeout)

    elif context.author.id == 144462063920611328:
        # Global command tree sync, limited by k8thekat discord ID
        client._logger.info(f'Bot Commands Sync\'d Globally: {await client.tree.sync(guild=None)}')  # type:ignore
        await context.send('Successfully Sync\'d Gatekeeper Commands Globally...', ephemeral=True, delete_after=client.Message_Timeout)


def client_run(tokens):
    # TODO - Maybe move all Namespace Parser logic to here?
    # -- Move logger init from start.py here
    # -- Move pip version check from start.py here
    # -- Move python version check from start.py here
    # -- Rename the thread here too.
    # Use action="store_true", then check the arg via "args.name" eg. "args.dev"
    # By default argparase has -h/--h.
    parser: ArgumentParser = ArgumentParser(description='Gatekeeper - AMP Discord Bot')
    parser.add_argument("-super", help='This leaves AMP Super Admin role intact *Warning* Potential security risk', required=False, action="store_true")
    # All the args below are used for development purpose.
    parser.add_argument("-dev", help='Enable development logger statments.', required=False, action="store_true")
    parser.add_argument("-debug", help='Enables DEBUGGING level for logging', required=False, action="store_true")
    parser.add_argument("arg1", action="store_true")
    client._args = parser.parse_args()
    client._logger.info('Gatekeeper v2 Intializing...')
    client.run(tokens.token, reconnect=True, log_handler=None)
