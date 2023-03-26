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
import os
import logging
from typing import Union

import discord
from discord.ext import commands
from discord import app_commands

import utils
import utils_ui
import amp_handler
import db

# This is used to force cog order to prevent missing methods.
Dependencies = None


class DB_Server(commands.Cog):
    def __init__(self, client: discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()  # Point all print/logging statments here!

        self.AMPHandler = amp_handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = db.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.uiBot = utils_ui
        self.dBot = utils.discordBot(client)
        self.logger.info(f'**SUCCESS** Initializing {self.name.title().replace("Db","DB")}')

    async def autocomplete_db_servers(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Database Server Names for Change Instance IDs"""
        db_server_list = self.DB.GetAllServers()
        for key, value in self.DB.GetAllServers().items():
            if key in self.AMPInstances:
                db_server_list.pop(key)
        return [app_commands.Choice(name=f"{value} | ID: {key}", value=key)for key, value in db_server_list.items()][:25]

    @commands.hybrid_group(name='dbserver')
    @utils.role_check()
    async def db_server(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=30)

    @db_server.command(name='cleanup')
    @utils.role_check()
    async def db_server_cleanup(self, context: commands.Context):
        """This is used to remove un-used DBServer entries."""
        self.logger.command(f'{context.author.name} used Database Clean-Up in progress...')

        amp_instance_keys = self.AMPInstances.keys()
        db_server_list = self.DB.GetAllServers()
        found_server = False
        for key, value in db_server_list.items():
            db_server = self.DB.GetServer(InstanceID=key)
            if db_server != None and db_server.InstanceID not in amp_instance_keys:
                db_server.delServer()
                found_server = True
                await context.send(f'Removing Server: **{db_server.InstanceName}** from the DB', ephemeral=True, delete_after=self._client.Message_Timeout)

        if not found_server:
            await context.send('Hmm, it appears you don\'t have any Servers to cleanup..', ephemeral=True, delete_after=self._client.Message_Timeout)

    @db_server.command(name='change_instance_id')
    @utils.role_check()
    @app_commands.autocomplete(from_server=autocomplete_db_servers)  # The DB Information we want to copy onto the Destination Server
    @app_commands.autocomplete(to_server=utils.autocomplete_servers)
    @app_commands.describe(from_server='The DB Server Information we are moving')
    @app_commands.describe(to_server='The Server you want the DB Server Information to belong too.')
    async def db_server_changeinstanceid(self, context: Union[commands.Context, discord.Interaction], from_server: str, to_server: str):
        """This will be used to replace a DB Instance ID with an existing AMP Instance"""
        self.logger.command(f'{context.author.name} used Database Instance swap...')

        from_db_server = self.DB.GetServer(InstanceID=from_server)

        to_db_server = self.DB.GetServer(to_server)

        content = f'We are going to move **{from_db_server.InstanceName}** information to **{to_db_server.InstanceName}**, which will remove the **{to_db_server.InstanceName}** Information from the Database.'
        message = await context.send(content, delete_after=self._client.Message_Timeout, ephemeral=True)

        _view = self.uiBot.DB_Instance_ID_Swap(discord_message=message, timeout=self._client.Message_Timeout, from_db_server=from_db_server, to_db_server=to_db_server)
        await message.edit(view=_view)


async def setup(client):
    await client.add_cog(DB_Server(client))
