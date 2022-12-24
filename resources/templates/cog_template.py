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
import discord
from discord import app_commands
from discord.ext import commands
import os
import logging

import utils
import AMP as AMP
import DB as DB


class Cog_Template(commands.Cog):
    def __init__ (self,client:discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger() #Point all print/logging statments here!

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP #Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances #Main AMP Instance Dictionary

        #use DBHandler for all DB related needs.
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBCOnfig = self.DB.DBConfig

        #utils.botUtils provide access to utility functions such as serverparse,roleparse,channelparse,userparse.
        self.uBot = utils.botUtils(client)
        #utils.discordBot provides access to utility functions such as sending/deleting messages, kicking/ban users.
        self.dBot = utils.discordBot(client)

        #Leave this commented out unless you need to create a sub-command.
        #self.uBot.sub_command_handler('user',self.info) #This is used to add a sub command(self,parent_command,sub_command)
        self.logger.info(f'**SUCCESS** Loading Module **{self.name}**')

    @commands.Cog.listener('on_message')
    async def on_message(self,message:discord.Message):
        """Called when a Member/User sends a message in any Channel of the Guild."""
        if message.content.startswith(self._client.command_prefix): #This prevents any {prefix}commands from interacting with on_message events
            return message

        if message.content.startswith('/'): #This prevents /commands from interacting with on_message events
            return message

        if message.author != self._client.user: #This prevents the bot from interacting/replying to itself with on_message events
            print(f'On Message Event for {self.name}')
            return message
           
    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before,user_after) -> discord.User:
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.info(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before,user_after

    #This is called when a message in any channel of the guild is edited. Returns <message> object.
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self,message_before,message_after) -> discord.Message:
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            self.logger.info(f'Edited Message Event for {self.name}')
            return message_before,message_after

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self,reaction:discord.Reaction,user:discord.User):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self.logger.info(f'Reaction Add {self.name}: {user} Reaction: {reaction}')
        return reaction,user

    @commands.Cog.listener('on_reaction_remove')
    async def on_reaction_remove(self,reaction:discord.Reaction,user:discord.User):
        """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
        self.logger.info(f'Reaction Remove {self.name}: {user} Reaction: {reaction}')
        return reaction,user

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member) -> discord.Member:
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Leave {self.name}: {member.name} {member}')
        return member

    #Any COMMAND needs a ROLE CHECK prior unless its a sub_command
    @commands.hybrid_command(name='cog_temp')
    @utils.role_check()
    async def temp(self,context:commands.Context):
        """cog template command'"""
        self.logger.info('test')

    #Example group command for a cog.
    @commands.hybrid_group(name='cog')
    @utils.role_check()
    async def cog_temp(self,context:commands.Context):
        """ Cog Template Group Command"""
        print('cog temp test')
    
    #Example sub_command for a cog.
    #@commands.app_commands.describe
    @cog_temp.command(name='init')
    async def cog_init(self,context:commands.Context):
        """Cog Template Init Command"""
        print('cog init test')

    @commands.hybrid_command()
    #This limits the command to sync to a specific guild.
    @app_commands.guilds(discord.Object(id=...)) 
    #This limits the command to sync to a specific guild (same as above). But shows the command globally.
    @utils.guild_check(guild_id=None) 
    #This will autocomplete the command with some premade lists inside of utils.py. You can make your own, see utils.py -> Autocomplete template
    @app_commands.autocomplete() 
    async def cmd(self, ctx, param: int):
        #So if ctx.interaction is None will tell you whether they invoked it via prefix or slash
        #i.e. you can call ctx.defer(), which will defer a slash invocation but do nothing in a prefix invocation
        ctx.reply("abcd", ephemeral=True) 
        print('Test Hybrid Command')

async def setup(client):
    await client.add_cog(Cog_Template(client))