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
from future import __annotations__
import os
import logging
from typing import Union
import sqlite3

import discord
from discord.ext import commands

import utils
import utils_embeds
import AMP_Handler
import DB

# This is used to force cog order to prevent missing methods.
Dependencies = None


class DB_User(commands.Cog):
    def __init__(self, client: discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        self.eBot = utils_embeds.botEmbeds(client)

        self.logger.info(f'**SUCCESS** Initializing {self.name.title().replace("Db","DB")}')

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self, user_before: discord.User, user_after: discord.User):
        # Lets see if the name is different from before.
        if user_before.name != user_after.name:
            # Lets look up the previous ID to gaurentee a proper search, could use the newer user ID; both in theory should be the same.
            db_user = self.DB.GetUser(user_before.id)
            # If we found the DB User
            if db_user != None:
                db_user.DiscordName = user_after.name
            else:  # Lets Add them with the info we have!
                self.DB.AddUser(DiscordID=user_before.id, DiscordName=user_after.name)

            self.logger.dev(f'User Update {self.name}: {user_before.name} into {user_after.name}')
            return user_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        self.logger.dev(f'Member has left the server {member.name}')
        return member

    @utils.role_check()
    @commands.hybrid_group(name='user')
    async def user(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @user.command(name='info')
    @utils.role_check()
    async def user_info(self, context: commands.Context, user: Union[discord.Member, discord.User]):
        """Displays the Discord Users Database information"""
        self.logger.command(f'{context.author.name} used User Information')
        db_user = self.DB.GetUser(user.id)
        await context.send(embed=self.eBot.user_info_embed(db_user, user), ephemeral=True, delete_after=self._client.Message_Timeout)

    @user.command(name='add')
    @utils.role_check()
    async def user_add(self, context: commands.Context, user: Union[discord.Member, discord.User], mc_ign: str = None, mc_uuid: str = None, steamid: str = None):
        """Adds the Discord Users information to the Database"""
        self.logger.command(f'{context.author.name} used User Add Function')

        if mc_ign != None:
            mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)

        db_user = self.DB.GetUser(user.id)
        if db_user == None:
            self.DB.AddUser(DiscordID=user.id, DiscordName=user.name, MC_IngameName=mc_ign, MC_UUID=mc_uuid, SteamID=steamid)
            await context.send(f'Added **{user.name}** to the Database!', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(f'**{user.name}** already exists in the Database.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @user.command(name='update')
    @utils.role_check()
    async def user_update(self, context: commands.Context, user: Union[discord.Member, discord.User], mc_ign: str = None, steamid: str = None):
        """Updated a Discord Users information in the Database"""
        self.logger.command(f'{context.author.name} used User Update Function')

        db_user = None
        updated_vals = []
        params = locals()
        db_params = {'user': 'DiscordName',
                     'mc_ign': 'MC_IngameName',
                     'mc_uuid': 'MC_UUID',
                     'steamid': 'SteamID'
                     }

        params['mc_uuid'] = None
        if mc_ign != None:
            if mc_ign.lower() == 'none':
                params['mc_uuid'] = 'none'
            else:
                mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)
                params['mc_uuid'] = mc_uuid

        db_user = self.DB.GetUser(user.id)
        if db_user != None:
            for entry in db_params:
                if params[entry] == None:
                    continue
                elif entry == 'user':
                    continue
                elif params[entry].lower() == 'none':
                    setattr(db_user, db_params[entry], None)
                    updated_vals.append(f'> **{db_params[entry]}** - `None`')

                else:
                    try:
                        setattr(db_user, db_params[entry], params[entry])
                        updated_vals.append(f'> **{db_params[entry]}** -> {params[entry]}')

                    except sqlite3.IntegrityError as e:
                        if "UNIQUE constraint failed" in e.args[0]:
                            self.logger.error(f'SQLITE Exception {e}')
                            await context.send(f'The **{db_params[entry]}** must be Unique for {db_user.DiscordName}', ephemeral=True, delete_after=self._client.Message_Timeout)

            updated_vals = "\n".join(updated_vals)
            await context.send(f'We Updated the Database User: **{db_user.DiscordName}**\n{updated_vals}', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send('Looks like this user is not in the Database, please use `/user add`', ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client):
    await client.add_cog(DB_User(client))
