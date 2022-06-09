import os
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands,tasks

import utils
import modules.AMP as AMP
import modules.database as DB
from modules.message_parser import ParseIGNServer
import bot_config


class Generic(commands.Cog):
    def __init__ (self,client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__) #Point all print/logging statments here!
        self.logger.info(f'{self.name} Module Loaded')

        self.AMP = AMP.getAMP() #Main AMP object
        self.DB = DB.getDatabase() #Main Database object
        self.DBConfig = self.DB.GetConfig() 

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        self.uBot.sub_command_handler('server',self.server_whitelist) 
        #self.uBot.sub_command_handler(self,'user',self.info)

        #This should help prevent errors in older databases.
        try:
            self.Auto_WL = self.DBConfig.auto_whitelist
            self.WL_channel = self.DBConfig.whitelist_channel
            self.WL_delay = self.DBConfig.whitelist_wait_time #Should only be an INT value; all values in Minutes.

        except:
            DB.dbWhitelistSetup()
        
        self.failed_whitelist = []
        self.WL_wait_list = [] # Layout = [{'author': message.author.name, 'msg' : message, 'ampserver' : amp_server, 'dbuser' : db_user}]
        self.WL_format = bot_config.WhitelistFormat
        self.WL_Pending_Emoji = bot_config.Whitelist_Pending_Emoji
        self.WL_Finished_Emoji = bot_config.Whitelist_Finished_Emoji



    @commands.Cog.listener('on_message')
    async def on_message(self,message):
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            self.logger.info(f'On Message Event for {self.name}')
            return message
        if message.channel.id == self.WL_channel:
            print('Minecraft Whitelist Channel Message Found')
            self.on_message_whitelist(message)

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before:discord.User,user_after:discord.User):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.info(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before,user_after

    #This is called when a message in any channel of the guild is edited. Returns <message> object.
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self,message_before:discord.Message,message_after:discord.Message):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            if message_before in self.failed_whitelist and message_before.channel.id == self.WL_channel:
                self.on_message_whitelist(message_after)

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
        for index in len(0,self.WL_wait_list):
            if member.name == self.WL_wait_list[index]['author']:
                self.WL_wait_list.pop(index)
                self.logger.info(f'Removed {member.name} from Whitelist Wait List.')
        return member

    @commands.hybrid_group(name='whitelist')
    @utils.role_check()
    async def server_whitelist(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @server_whitelist.command(name='true')
    @utils.role_check()
    async def server_whitelist_true(self,context:commands.Context,server):
        """Set Servers Whitelist Allowed to True"""
        server = self.uBot.serverparse(context,context.guild.id,server)
        self.DB.GetServer(server.FriendlyName).Whitelist = True
        await context.send(f"Server: {server.FriendlyName}, Whitelist set to : `True`")

    @server_whitelist.command(name='false')
    @utils.role_check()
    async def server_whitelist_false(self,context:commands.Context,server):
        """Set Servers Whitelist Allowed to False"""
        server = self.uBot.serverparse(context,context.guild.id,server)
        self.DB.getServer(server.FriendlyName).Whitelist = False
        await context.send(f"Server: {server.FriendlyName}, Whitelist set to : `False`")

    @server_whitelist.command(name='test')
    @utils.role_check()
    async def server_whitelist_test(self,context:commands.Context,server=None,user=None):
        """Server Whitelist Test function."""
        server = self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            user = server.name_Conversion(context,user)
            # server_whitelist = server.getWhitelist()
            # print(server_whitelist)
            await context.send(f'Test Function for Server Whitelist {server}{user[0]["name"]}')

    @server_whitelist.command(name='add')
    @utils.role_check()
    async def server_whitelist_add(self,context:commands.Context,server,user):
        """Adds User to Servers Whitelist"""
        server = self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            user = server.name_Conversion(context,user)
            if user != None:
                server.addWhitelist(user[0]['name'])
                await context.send(f'User: {user[0]["name"]} was whitelisted on Server: {server.FriendlyName}')

    @server_whitelist.command(name='remove')
    @utils.role_check()
    async def server_whitelist_remove(self,context:commands.Context,server,user):
        """Remove a User from the Servers Whitelist"""
        server = self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            #Converts the name to the proper format depending on the server type
            user = server.name_Conversion(context,user)

            if user != None:
                server.removeWhitelist(user[0]['name'])
                await context.send(f'User: {user[0]["name"]} was removed from the Whitelist on Server: {server.FriendlyName}')

    async def on_message_whitelist(self,message:discord.Message):
        """This handles on_message whitelist requests."""
        user_ign,user_server = ParseIGNServer(message.content)

        if user_ign or user_server == None:
            await message.reply(f'Hey! I was unable to understand your request, please edit your previous message or send another message with this format! \n{self.WL_format}')
        
        amp_server = self.uBot.serverparse(message,message.guild.id,user_server)
        if amp_server == None:
            return

        #!TODO! Need to Handle Failed Whitelist Requests Properply
        user_UUID = amp_server.name_Conversion(user_ign) #Returns None if Multiple or incorrect.
        if user_UUID == None:
            await message.reply(f'Hey! I am having trouble finding your IGN, please edit your previous message or send another message with an updated IGN')
            self.logger.info(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
            self.failed_whitelist.append(message)
            return
        
        db_user = self.DB.GetUser(message.author.name)
        if db_user == None:
            db_user = self.DB.AddUser(message.author.id,message.author.name,user_ign,user_UUID)
        
        db_server = self.DB.GetServer(amp_server.InstanceID)

        user_check = amp_server.checkWhitelist(user_UUID)
        if user_check == True:
            await message.reply(f'You are already Whitelisted on {amp_server.FriendlyName}. If this is an error contact Staff, otherwise Have fun! <3')
            self.logger.info(f'Discord User: {message.author.name} is already Whitelisted on {amp_server.FriendlyName}')
            return

        if not self.Auto_WL:
            return

        if db_server.Whitelist == False:
            await message.reply(f'Ooops, it appears that the server {db_server.Name} has their Whitelisting Closed. If this is an error please contact a Staff Member.')
            return

        if db_server.Donator == True and db_user.Donator != True:
            await message.reply(f'*Waves* Hey this server is for Donator Access Only, it appears you do not have Donator. If this is an error please contact a Staff Member.')
            return

        
        if self.WL_delay != 0: #This handles Whitelist Delays if set.
            self.WL_wait_list.append({'author': message.author.name, 'msg' : message, 'ampserver' : amp_server, 'dbuser' : db_user})
            await self.dBot.messageAddReaction(message,self.WL_Pending_Emoji)
            self.logger.info('Added {message.author} to Whitelist Wait List.')
            #self._client.get_emoji(self.WL_Pending_Emoji)
            #await message.add_reaction(self.WL_Pending_Emoji) #This should point to bot_config Emoji

            #Checks if the Tasks is running, if not starts the task.
            if not self.whitelist_waitlist_handler.is_running():
                self.whitelist_waitlist_handler.start()
                
            return

        if amp_server.Running and db_server.Whitelist == True:
            amp_server.addWhitelist(db_user.InGameName)
            await message.reply(embed = self.uBot.server_whitelist_embed(message,amp_server))
            self.logger.info(f'Whitelisting {message.author.name} on {amp_server.FriendlyName}')
            return

    @tasks.loop(seconds = 60)
    async def whitelist_waitlist_handler(self):
        """This is the Whitelist Wait list handler, every 60 seconds it will check the list and whitelist them after the alotted wait time."""
        self.logger.info(f'Checking the Whitelist Wait List.')
        if len(self.WL_wait_list) == 0:
            self.whitelist_waitlist_handler.stop()

        cur_time = datetime.now()
        try:
            wait_time = timedelta(minutes= self.WL_delay) #This may error if someone changes the wait time to 0 inbetween a loop..
        except:
            wait_time = timedelta(minutes= 1) #Fallback to 1 min delay if somehow the value fails to get parsed.

        for index in range(0,len(self.WL_wait_list)):
            cur_message = self.WL_wait_list[index]

            #!TODO! This math may fail; needs to be tested
            #This should compare datetime objects and if the datetime of when the message was created plus the wait time is greater than or equal the cur_time they get whitelisted.
            if cur_message['msg'].created_at + wait_time <= cur_time: 
                cur_message['ampserver'].addWhitelist(cur_message['dbuser'].InGameName)
                await cur_message.reply(embed = self.uBot.server_whitelist_embed(cur_message,cur_message['ampserver']))
                self.logger.info(f'Whitelisting {cur_message["author"]} on {cur_message["amp_server"].FriendlyName}')
        
async def setup(client):
    await client.add_cog(Generic(client))