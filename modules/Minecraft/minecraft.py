import discord
from discord.ext import commands
import os
import logging

import utils
import modules.AMP as AMP
import modules.database as DB
import modules.Minecraft.amp_minecraft as AMPMC
import bot_config
from modules.message_parser import ParseIGNServer


class Minecraft(commands.Cog):
    def __init__ (self,client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__) #Point all print/logging statments here!
        self.logger.info(f'{self.name.capitalize()} Module Loaded')

        self.AMP = AMP.getAMP() #Main AMP object
        self.AMPInstances = AMP.AMP_Instances #Main AMP Instance Dictionary

        self.DB = DB.getDatabase() #Main Database object
        self.DBconfig = self.DB.GetConfig()

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)

        self.failed_whitelist = []
        self.WL_format = bot_config.WhitelistFormat

        #This should help prevent errors in older databases.
        try:
            self.Auto_WL = self.DBconfig.auto_whitelist
            self.WL_channel = self.DBconfig.whitelist_channel
            self.WL_delay = self.DBconfig.whitelist_wait_time
        except:
            DB.dbWhitelistSetup()


    @commands.Cog.listener('on_message')
    async def on_message(self,message:discord.Message):
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            self.logger.info(f'On Message Event for {self.name}')
            return message
        if message.channel.id == self.DBconfig.WhitelistChannel:
            print('Minecraft Whitelist Channel Message Found')
            self.on_message_whitelist(message)
            #!TODO Call Whitelist Function Here!

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before,user_after:discord.User):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.info(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before,user_after

    #This is called when a message in any channel of the guild is edited. Returns <message> object.
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self,message_before:discord.Message,message_after:discord.Message):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            if message_before in self.failed_whitelist and message_before.channel.id in self.WL_channel:
                self.on_message_whitelist(message_after)

            self.logger.info(f'Edited Message Event for {self.name}')
            return message_before,message_after

    # @commands.Cog.listener('on_reaction_add')
    # async def on_reaction_add(self,reaction,user):
    #     """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
    #     self.logger.info(f'Reaction Add {self.name}: {user} Reaction: {reaction}')
    #     return reaction,user

    # @commands.Cog.listener('on_reaction_remove')
    # async def on_reaction_remove(self,reaction,user:discord.Member):
    #     """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
    #     self.logger.info(f'Reaction Remove {self.name}: {user} Reaction: {reaction}')
    #     return reaction,user

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Leave {self.name}: {member.name} {member}')

        db_user = self.DB.GetUser(str(member.id))
        if db_user != None and db_user.InGameName != None:
            for server in self.AMPInstances:
                if self.AMPInstances[server].Module == 'Minecraft':
                    self.AMPInstances[server].removeWhitelist(db_user.InGameName)

        return member


    async def on_message_whitelist(self,message:discord.Message):
        """This handles on_message whitelist requests; can be called from anywhere if needed."""
        user_ign,user_server = ParseIGNServer(message.content)
        if user_ign or user_server == None:
            await message.reply(f'Hey! I was unable to understand your request, please edit your previous message or send another message with this format! \n{self.WL_format}')
        
        user_UUID = await self.uBot.name_to_UUID(message,user_ign)
        if user_UUID == None:
            self.failed_whitelist.append(message)
            return
        
        db_user = self.DB.GetUser(message.author.name)
        if db_user == None:
            db_user = self.DB.AddUser(message.author.id,message.author.name,user_ign,user_UUID)
        
        amp_server = self.uBot.serverparse(message,message.guild.id,user_server)
        db_server = self.DB.GetServer(amp_server.InstanceID)
        if amp_server != None: #If we find the server.

            if amp_server.Module == 'Minecraft':
                if db_server.Whitelist != True:
                    await message.reply(f'Ooops, it appears that the server {db_server.Name} has their Whitelisting Closed. If this is an error please contact a Staff Member.')

                if db_server.Donator == True and db_user.Donator != True:
                    await message.reply(f'*Waves* Hey this server is for Donator Access Only, it appears you do not have Donator. If this is an error please contact a Staff Member.')

                if amp_server.Running and db_server.Whitelist == True:
                    #amp_server.addWhitelist(db_user.InGameName)
                    await message.reply(embed = self.uBot.server_whitelist_embed(message,amp_server))
            


async def setup(client):
    await client.add_cog(Minecraft(client))