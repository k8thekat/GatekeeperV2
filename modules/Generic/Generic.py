import os
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands,tasks

import utils
import AMP as AMP
import DB as DB
from modules.message_parser import ParseIGNServer



class Generic(commands.Cog):
    def __init__ (self,client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__) #Point all print/logging statments here!
        self.logger.info(f'**SUCCESS** Loading Module **{self.name}**')

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP #Main AMP object
        
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        #self.uBot.sub_command_handler(self,'user',self.info)

    @commands.Cog.listener('on_message')
    async def on_message(self,message:discord.Message):
        if message.content.startswith(self._client.command_prefix):
            return message

        if message.author != self._client.user:
            self.logger.info(f'On Message Event for {self.name}')
            return message

        
        
    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before:discord.User,user_after:discord.User):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.info(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before,user_after

    #This is called when a message in any channel of the guild is edited. Returns <message> object.
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self,message_before:discord.Message,message_after:discord.Message):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
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
    async def on_member_remove(self,member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Leave {self.name}: {member.name} {member}')
        return member

   
        
async def setup(client):
    await client.add_cog(Generic(client))