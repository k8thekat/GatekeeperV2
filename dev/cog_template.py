import discord
from discord import app_commands
from discord.ext import commands
import os
import logging

import utils
import modules.AMP as AMP
import modules.database as DB


class Cog_Template(commands.Cog):
    def __init__ (self,client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__) #Point all print/logging statments here!
        self.logger.info(f'{self.name} Module Loaded')
        self.AMP = AMP.getAMP() #Main AMP object
        self.AMPInstances = AMP.AMP_Instances #Main AMP Instance Dictionary
        self.DB = DB.getDatabase() #Main Database object
        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        self.uBot.sub_command_handler('user',self.info) #This is used to add a sub command(self,parent_command,sub_command)

    @commands.Cog.listener('on_message')
    async def on_message(self,message):
        """Called when a Member/User sends a message in any Channel of the Guild."""
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            print(f'On Message Event for {self.name}')
            return message
           
    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before,user_after):
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
    async def temp(self,context):
        """cog template command'"""
        self.logger.info('test')

    #Example group command for a cog.
    @commands.hybrid_group(name='cog')
    @utils.role_check()
    async def cog_temp(self,context):
        """ Cog Template Group Command"""
        print('cog temp test')
    
    #Example sub_command for a cog.
    #@commands.app_commands.describe
    @cog_temp.command(name='init')
    async def cog_init(self,context):
        """Cog Template Init Command"""
        print('cog init test')

    @commands.hybrid_command()
    #@app_commands.guilds(discord.Object(id=...))
    async def cmd(self, ctx, param: int):
        #So if ctx.interaction is None will tell you whether they invoked it via prefix or slash
        #i.e. you can call ctx.defer(), which will defer a slash invocation but do nothing in a prefix invocation
        ctx.reply("abcd", ephemeral=True) 
        print('Test Hybrid Command')

async def setup(client):
    await client.add_cog(Cog_Template(client))