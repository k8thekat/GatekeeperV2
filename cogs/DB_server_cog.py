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
        self.logger = logging.getLogger() #Point all print/logging statments here!

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP#Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances #Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)

    async def autocomplete_servers(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for AMP Instance Names"""
        choice_list = self.AMPHandler.get_AMP_instance_names()
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    async def autocomplete_db_servers(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Database Server Names"""
        choice_list = self.DB.GetAllServers()
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    @commands.hybrid_group(name='dbserver')
    @utils.role_check()
    async def db_server(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral= True, delete_after= 30)

    @db_server.command(name='cleanup')
    @utils.role_check()
    async def db_server_cleanup(self, context:commands.Context):
        """This is used to remove un-used DBServer entries."""
        self.logger.command(f'{context.author.name} used Database Clean-Up in progress...')

        amp_instance_keys = self.AMPInstances.keys()
        db_server_list = self.DB.GetAllServers()
        found_server = False
        for server in db_server_list:
            db_server = self.DB.GetServer(Name= server)
            if db_server != None and db_server.InstanceID not in amp_instance_keys:
                db_server.delServer()
                found_server = True
                await context.send(f'Removing Server: **{db_server.InstanceName}** from the DB', ephemeral= True, delete_after= self._client.Message_Timeout)
            
        if not found_server:
            await context.send('Hmm, it appears you don\'t have any Servers to cleanup..', ephemeral= True, delete_after= self._client.Message_Timeout)

    @db_server.command(name='test')
    @utils.role_check()
    @utils.guild_check(guild_id=602285328320954378)
    @app_commands.autocomplete(server= autocomplete_db_servers)
    @app_commands.autocomplete(replacement_server= autocomplete_servers)
    async def db_server_test(self, context:commands.Context, server:str, replacement_server:str):
        self.logger.command('Test Function for DB_Server')
      
        await context.send('Test Function for DB_Server used...', ephemeral= True, delete_after= self._client.Message_Timeout)

    @db_server.command(name='swap')
    #@utils.role_check()
    @utils.author_check(144462063920611328)
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

        #!TODO! Need to finish this command.
        #Replace the old_db server ID with the new one. This assume's that the AMP Instance is already gone.
        replacement_db_server  = self.DB.GetServer(server)
        if replacement_db_server != None:
            replacement_db_server.InstanceID = amp_server.InstanceID

async def setup(client):
    await client.add_cog(DB_Server(client))