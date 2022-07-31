import discord
from discord.ext import commands
import os
import logging

import utils
import AMP
import DB


class Terraria(commands.Cog):
    def __init__ (self,client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__) #Point all print/logging statments here!

        
        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP #Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        #self.uBot.sub_command_handler(self,'user',self.info)
        self.logger.info(f'**SUCCESS** Initializing Module **{self.name}**')

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before,user_after):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.info(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before,user_after


    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self,reaction,user):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self.logger.info(f'Reaction Add {self.name}: {user} Reaction: {reaction}')
        return reaction,user

    @commands.Cog.listener('on_reaction_remove')
    async def on_reaction_remove(self,reaction,user):
        """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
        self.logger.info(f'Reaction Remove {self.name}: {user} Reaction: {reaction}')
        return reaction,user

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Leave {self.name}: {member.name} {member}')
        return member

    # #Any COMMAND needs a ROLE CHECK prior unless its a sub_command
    # @commands.command(name='cog_temp',description = 'cog template command')
    # @utils.role_check()
    # async def temp(self,context):
    #     self.logger.info('test')

    # #Example group command for a cog.
    # @commands.group(name='cog')
    # @utils.role_check()
    # async def cog_temp(self,context):
    #     print('cog temp test')
    
    # #Example sub_command for a cog.
    # @cog_temp.command(name='init')
    # async def bot_init(self,context):
    #     print('cog init test')

async def setup(client):
    await client.add_cog(Terraria(client))