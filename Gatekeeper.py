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
import sys
from typing import Union
from argparse import Namespace
from dotenv.main import load_dotenv
import os
from datetime import timedelta

import discord
from discord import Intents, Guild
import discord.ext.commands
from discord.ext import commands, tasks


# Custom scripts
from DB import Database, DBHandler, DBConfig
import loader
#from utils.permissions import Gatekeeper_Permissions
from utils.context import GatekeeperGuildContext
from utils.emojis import Gatekeeper_Emojis


Version = 'beta-4.5.4'


class Gatekeeper(commands.Bot):
    _logger = logging.getLogger()
    _args: Namespace
    _DBHandler: DBHandler = DBHandler()  #
    _DB: Database = _DBHandler._DB
    _DBConfig: DBConfig = _DBHandler._DBConfig

    def __init__(self, Version: str) -> None:
        self.guild_id = None
        if self._DBConfig.GetSetting('Guild_ID') != None:
            self.guild_id: int = int(self._DBConfig.GetSetting('Guild_ID'))

        self._bot_version: str = self._DBConfig.GetSetting('Bot_Version')
        self._old_bot_version: str = self._DBConfig.GetSetting("Bot_Version")
        if self._bot_version == None:
            self._DBConfig.SetSetting('Bot_Version', Version)

        # Simple Datastore of Emojis to use.
        self._emojis = Gatekeeper_Emojis()

        # Discord Specific
        intents: Intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        self._prefix: str = '$'
        super().__init__(intents=intents, command_prefix=self._prefix)

        self._message_timeout: int = self._DBConfig.GetSetting("Message_timeout") or 60
        self._whitelist_waitlist: dict[int, str] = {}
        self._start_time: float = time.time()
        self._version: str = Version

    async def setup_hook(self) -> None:
        self._logger.info(f'Gatekeeper Version: {client._old_bot_version} // Python Version {sys.version} // Discord Version: {discord.__version__}')
        if self._bot_version != Version:
            self.update_loop.start()

        self._module_handler = loader.Handler(self)
        await self._module_handler.cog_auto_loader()
        # await self.Handler.module_auto_loader()

        # This Creates the Bot_perms Object and validates the File. Also Adds the Command.
        # if self._DBConfig.GetSetting('Permissions') == 'Custom':
        #     await self.permissions_update()

    def _self_check(self, message: discord.Message) -> bool:
        return message.author == client.user

    @property
    def _uptime(self):
        return timedelta(seconds=(round(time.time() - self._start_time)))

    async def on_command_error(self, context: commands.Context, exception: Union[discord.errors.ClientException, discord.errors.Forbidden, discord.errors.DiscordException]) -> None:
        self._logger.error(f'We ran into an issue. {exception}')
        await context.send(content=f'We uhh.. ran into an issue {exception}')
        # traceback.print_exception(exception)
        traceback.print_exc()

    async def on_command(self, context: commands.Context) -> None:
        self._logger.info(f'{context.author.name} used {context.command}...')

    async def on_ready(self) -> None:
        self._logger.info('Are you the Keymaster?...I am the Gatekeeper')

    @tasks.loop(seconds=30)
    async def update_loop(self) -> None:
        #self._logger.warn(f'Waiting for Gatekeeper to finish starting up to Update Bot Version to {Version}...')
        self._logger.warn(f'Currently Updating Bot Version to {Version}...')
        await client.wait_until_ready()
        self._DBConfig.SetSetting('Bot_Version', Version)
        if self.guild_id != None:
            cur_guild: Guild | None = self.get_guild(self.guild_id)
            if isinstance(cur_guild, Guild):
                self.tree.copy_global_to(guild=cur_guild)
                await self.tree.sync(guild=cur_guild)
                self._logger.warn(f'Syncing Commands via update_loop to guild: {cur_guild.name if cur_guild != None else "None"} {await self.tree.sync(guild= cur_guild)}')
        else:
            self._logger.error(f'It appears I cannot Sync your commands for you, please run {self._prefix}sync or `/sync` to update your command tree. Please see the readme if you encounter issues.')
        self.update_loop.stop()


client: Gatekeeper = Gatekeeper(Version=Version)


# This needs to be a hybrid and a slash command so people can sync commands when they invite the bot.
@client.hybrid_command(name='sync')
# @commands.has_permissions(administrator=True)
async def bot_utils_sync(context: GatekeeperGuildContext, local: bool = True, reset: bool = False):
    """Syncs Bot Commands to the current guild this command was used in."""
    await context.defer()
    # This keeps our DB Guild_ID Current.
    if client.guild_id == None or context.guild.id != int(client.guild_id):
        client._DBConfig.SetSetting('Guild_ID', context.guild.id)

    if reset:
        if local:
            # Local command tree reset
            client.tree.clear_commands(guild=context.guild)
            client._logger.info(f"Bot Commands Reset Locally and Sync'd: {await client.tree.sync(guild=context.guild)}")
            return await context.send('**WARNING** Resetting Gatekeeper Commands Locally...', ephemeral=True, delete_after=client._message_timeout)

        elif context.author.id == 144462063920611328:
            # Global command tree reset, limited by k8thekat discord ID
            client.tree.clear_commands(guild=None)
            client._logger.info(f"Bot Commands Reset Global and Sync'd: {await client.tree.sync(guild=None)}")
            return await context.send('**WARNING** Resetting Gatekeeper Commands Globally...', ephemeral=True, delete_after=client._message_timeout)
        else:
            return await context.send('**ERROR** You do not have permission to reset the commands.', ephemeral=True, delete_after=client._message_timeout)

    if local:
        # Local command tree sync
        client.tree.copy_global_to(guild=context.guild)
        client._logger.info(f"Bot Commands Sync'd Locally: {await client.tree.sync(guild=context.guild)}")
        return await context.send(f"Successfully Sync'd Gatekeeper Commands to {context.guild.name}...", ephemeral=True, delete_after=client._message_timeout)

    elif context.author.id == 144462063920611328:
        # Global command tree sync, limited by k8thekat discord ID
        client._logger.info(f"Bot Commands Sync'd Globally: {await client.tree.sync(guild=None)}")
        await context.send("Successfully Sync'd Gatekeeper Commands Globally...", ephemeral=True, delete_after=client._message_timeout)


def client_run(args):
    load_dotenv()
    TOKEN: str = os.environ["TOKEN"].strip()

    client._args = args
    client._logger.info('Gatekeeper Intializing...')
    client.run(TOKEN, reconnect=True, log_handler=None)
