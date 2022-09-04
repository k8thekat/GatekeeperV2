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

import discord
from discord.ext import commands
from discord import app_commands

import utils
import AMP 
import DB

class DB_Server(commands.Cog):
    def __init__ (self,client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger(__name__) #Point all print/logging statments here!

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP#Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances #Main AMP Instance Dictionary
        self.AMP_Instance_Names = self.AMPHandler.AMP_Instances_Names

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)

    async def autocomplete_servers(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for AMP Instance Names"""
        choice_list = self.AMP_Instance_Names
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    async def autocomplete_db_servers(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Database Server Names"""
        choice_list = self.DB.GetAllServers()
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    @commands.hybrid_group(name='dbserver')
    @utils.role_check()
    async def db_server(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_server.command(name='cleanup')
    @utils.role_check()
    async def db_server_cleanup(self, context:commands.Context):
        """This is used to remove un-used DBServer entries and update names of existing servers."""
        self.logger.command(f'{context.author.name} used Database Clean-Up in progress...')
    
        db_server_list = self.DB.GetAllServers()
        for server in db_server_list:
            if server.InstanceID not in self.AMPInstances:
                db_server = self.DB.GetServer(InstanceID=server.InstanceID)
                db_server.delServer()
            if server.InstanceID in self.AMPInstances:
                for instance in self.AMPInstances:
                    if self.AMPInstances[instance].InstanceID == server.InstanceID:
                        server.FriendlyName = self.AMPInstances[instance].FriendlyName

    @db_server.command(name='test')
    @utils.role_check()
    @utils.guild_check(guild_id=602285328320954378)
    @app_commands.autocomplete(server= autocomplete_db_servers)
    @app_commands.autocomplete(replacement_server= autocomplete_servers)
    async def db_server_test(self, context:commands.Context, server:str, replacement_server:str):
        self.logger.command('Test Function for DB_Server')
        print(server,replacement_server)
        await context.send('Test Function for DB_Server used...')

    @db_server.command(name='swap')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_db_servers)
    @app_commands.autocomplete(replacement_server= autocomplete_servers)
    async def db_server_instance_swap(self, context:commands.Context, server:str, replacement_server:str):
        """This will be used to swap Instance ID's with an existing AMP Instance"""
        self.logger.command(f'{context.author.name} used Database Instance swap...')
        #Get the new AMP Instance ID Information and Object.
        amp_server = self.uBot.serverparse(replacement_server,context,context.guild.id)
        #Get its DB Object and Delete it from the DB
        db_server = self.DB.GetServer(amp_server.InstanceID)
        db_server.delServer()

        #Replace the old_db server ID with the new one. This assume's that the AMP Instance is already gone.
        replacement_db_server  = self.DB.GetServer(server)
        if replacement_db_server != None:
            replacement_db_server.InstanceID = amp_server.InstanceID

async def setup(client):
    await client.add_cog(DB_Server(client))