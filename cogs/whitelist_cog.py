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
from datetime import datetime,timedelta,timezone
import os
import logging
import random

import discord
from discord import app_commands
from discord.ext import commands,tasks

import AMP
import DB
from modules.parser import Parser
import utils


class Whitelist(commands.Cog):
    def __init__(self,client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()

        self.AMPHandler = AMP.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMP_Instance_Names = self.AMPHandler.AMP_Instances_Names

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        self.Parser = Parser()
        self.bPerms = utils.botPerms()

        self.attr_update()
        
        self.failed_whitelist = []
        self.WL_wait_list = [] # Layout = [{'author': message.author.name, 'msg' : message, 'ampserver' : amp_server, 'dbuser' : db_user}]
        self.whitelist_emoji_message = '' 
        self.whitelist_emoji_pending = False
        self.whitelist_emoji_done = False

        self.update_loop.start()
        self.logger.dev('Whitelist Module Update Loop Running:' + str(self.update_loop.is_running()))
        self.logger.info(f'**SUCCESS** Initializing {self.name.capitalize()}')

    @tasks.loop(seconds=5)
    async def update_loop(self):
        #This is to keep everything up to date when we change the settings in the DB
        self.attr_update()
        self.logger.dev('Updating AMP_Cog Attributes!')

    def attr_update(self):
        self.Auto_WL = self.DBConfig.Auto_whitelist
        self.WL_channel = self.DBConfig.Whitelist_channel #DBConfig is Case sensitive.
        self.WL_delay = self.DBConfig.Whitelist_wait_time #Should only be an INT value; all values in Minutes.
        self.WL_Pending_Emoji = self.DBConfig.Whitelist_emoji_pending
        self.WL_Finished_Emoji = self.DBConfig.Whitelist_emoji_done

    def whitelist_reply_handler(self,message:str, context:commands.Context, server:AMP.AMPInstance=None) -> str:
        """Handles the reply message for the whitelist event\n
        Supports the following: \n
        `<user>` - Uses the Message Author's Name/IGN \n
        `<server>` - Uses the AMP Server Name \n 
        `<guild>` - Uses the Guild Name \n"""
    
        if message.find('<user>') != -1:
            message = message.replace('<user>',context.author.name)
        if message.find('<guild>') != -1:
            message = message.replace('<guild>',context.guild.name)
        if message.find('<server>') != -1 and server is not None:
            server_name = server.FriendlyName
            if server.DisplayName != None: 
                server_name = server.DisplayName
            message = message.replace('<server>',server_name)
        return message

    # Discord Auto Completes ----------------------------------------------------------------------------------------------------------------
    async def autocomplete_servers(self,interaction:discord.Interaction,current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for AMP Instance Names"""
        choice_list = self.AMP_Instance_Names
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

    async def autocomplete_whitelist_replies(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Whitelist Replies"""
        choice_list = self.DB.GetAllWhitelistReplies()
        return [app_commands.Choice(name=self.whitelist_reply_formatter(choice), value=self.whitelist_reply_formatter(choice)) for choice in choice_list if current.lower() in choice.lower()]

    def whitelist_reply_formatter(self, parameter:str):
        if len(parameter) > 100:
            return parameter[0:96] + '...'
        return parameter

    # Discord Listener Events --------------------------------------------------------------------------------------------------------------
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self, message_before:discord.Message, message_after:discord.Message):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            #This handles edited whitelist requests!
            if message_before in self.failed_whitelist and message_before.channel.id == self.WL_channel:
                context = await self._client.get_context(message_before)
                await self.on_message_whitelist(message_after,context)

            self.logger.dev(f'Edited Message Event for {self.name}')
            return message_before,message_after
            
    @commands.Cog.listener('on_message')
    async def on_message(self, message:discord.Message):
        
        #This is purely for testing!
        if message.content.startswith('test_emoji') and message.author.id == 144462063920611328: #This is my Discord ID(k8_thekat)
            if self.DBConfig.Whitelist_emoji_pending != None:
                emoji = self._client.get_emoji(int(self.WL_Pending_Emoji))
                await message.add_reaction(emoji)
                emoji = self._client.get_emoji(int(self.WL_Finished_Emoji))
                await message.add_reaction(emoji)
       
        if self.WL_channel is not None and message.author != self._client.user:
            context = await self._client.get_context(message)
            self.logger.dev(f'On Message Event for {self.name}')
            if message.channel.id == int(self.WL_channel):  # This is AMP Specific; for handling whitelist requests to any server.
                await self.on_message_whitelist(message, context)
     
    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')
        for index in len(0,self.WL_wait_list):
            if member.name == self.WL_wait_list[index]['author']:
                self.WL_wait_list.pop(index)
                self.logger.info(f'Removed {member.name} from Whitelist Wait List.')
        return member

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self, reaction:discord.Reaction, user:discord.User):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self.logger.dev(f'Reaction Add {self.name}: {user} Reaction: {reaction}')

        #This is for setting the Whitelist_Emoji_pending after using the command!
        if reaction.message.id == self.whitelist_emoji_message:
            #This is for pending whitelist requests
            if self.whitelist_emoji_pending:
                self.DBConfig.Whitelist_emoji_pending = reaction.emoji.id
                self.whitelist_emoji_pending = False
                emoji = self._client.get_emoji(reaction.emoji.id)
                await reaction.message.edit(content = f'Woohoo! Set your **Whitelist Pending Emoji** to {emoji}')

            #This is for completed whitelist requests
            if self.whitelist_emoji_done:
                self.DBConfig.Whitelist_emoji_done = reaction.emoji.id
                self.whitelist_emoji_done = False
                emoji = self._client.get_emoji(reaction.emoji.id)
                await reaction.message.edit(content = f'Woohoo! Set your **Whitelist Done Emoji** to {emoji}')

        return reaction,user

    #All DBConfig Whitelist Specific function settings --------------------------------------------------------------
    @commands.hybrid_group(name='whitelist')
    @utils.role_check()
    async def db_bot_whitelist(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_bot_whitelist.group(name='reply')
    @utils.role_check()
    async def db_bot_whitelist_reply(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_bot_whitelist_reply.command(name='add')
    @utils.role_check()
    async def db_bot_whitelist_reply_add(self, context:commands.Context, message:str):
        """Add a Reply for the Bot to use during Whitelist Requests"""
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply Add...')

        self.DB.AddWhitelistReply(message)
        await context.send(f'Woohoo! I can now use a new reply! How does it look?!')
        message = self.whitelist_reply_handler(message, context)
        await context.send(f'{message}')
    
    @db_bot_whitelist_reply.command(name='remove')
    @utils.role_check()
    @app_commands.autocomplete(message= autocomplete_whitelist_replies)
    async def db_bot_whitelist_reply_remove(self, context:commands.Context, message:str):
        """Remove a Reply for the Bot to use during Whitelist Requests"""
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply Remove...')
        reply_list = self.DB.GetAllWhitelistReplies()
        for reply in reply_list:
            if message in reply:
                self.DB.DeleteWhitelistReply(reply)
                return await context.send(f'Awwww! It looks like I can no longer use that reply, shucks~')
            else:
                continue
        return await context.send(f'Oops! I can\'t find that reply, sorry~')
        
    @db_bot_whitelist_reply.command(name='list')
    @utils.role_check()
    async def db_bot_whitelist_reply_list(self, context:commands.Context):
        """List all the Replies for the Bot to use during Whitelist Requests"""
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply List...')

        replies = self.DB.GetAllWhitelistReplies()
        await context.send(f'Here are all the replies I can use:')
        for reply in replies:
            await context.send(f'{reply}')
 
    @db_bot_whitelist.command(name='channel')
    @utils.role_check()
    @app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
    async def db_bot_whitelist_channel_set(self, context:commands.Context, channel:str):
        """Sets the Whitelist Channel for the Bot to monitor"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Channel Set...')
      
        channel = self.uBot.channelparse(channel,context,context.guild.id)
        if channel == None:
            return await context.reply(f'Unable to find the Discord Channel: {channel}')
        else:
            self.DBConfig.SetSetting('Whitelist_channel',channel.id)
            await context.send(f'Set Bot Channel Whitelist to {channel.name}')
    
    @db_bot_whitelist.command(name='waittime')
    @utils.role_check()
    @app_commands.describe(time= 'Time in minutes to wait before Whitelisting a User')
    async def db_bot_whitelist_wait_time_set(self, context:commands.Context, time:str):
        """Set the Bots Whitelist wait time , this value is in minutes!"""
        self.logger.command(f'{context.author.name} used Bot Whitelist wait time Set...')
        
        if time.isnumeric():
            self.DBConfig.Whitelist_wait_time = time
            await context.send(f'Whitelist wait time has been set to {time} minutes.')
        else:
            await context.send('Please use only numbers when setting the wait time. All values are in minutes!')

    @db_bot_whitelist.command(name='auto')
    @utils.role_check()
    @app_commands.autocomplete(flag= utils.autocomplete_bool)
    async def db_bot_whitelist_auto_whitelist(self, context:commands.Context, flag:str):
        """This turns on or off Auto-Whitelisting"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Auto Whitelist...')
    
        #flag_reg = re.search("(true|false)",flag.lower())
        if flag == None:
            return await context.send(f'Please use `true` or `false` for your flag.')
        if flag.lower() == 'true':
            self.DBConfig.SetSetting('Auto_Whitelist', True)
            return await context.send('Enabling Auto-Whitelist.')
        if flag.lower() == 'false':
            self.DBConfig.SetSetting('Auto_Whitelist', False)
            return await context.send('Disabling Auto-Whitelist')

    @db_bot_whitelist.command(name='pending_emoji')
    @utils.role_check()
    async def db_bot_whitelist_pending_emjoi_set(self, context:commands.Context):
        """This sets the Whitelist pending emoji, you MUST ONLY use your Servers Emojis'"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Pending Emoji...')
      
        flag = 'pending Whitelist requests!'
        await context.send('Please react to this message with the emoji you want for pending Whitelist requests!\n Only use Emojis from this Discord Server!')
        channel = self._client.get_channel(context.channel.id)
        messages = [message async for message in channel.history(limit=5)]
        for message in messages:
            if flag in message.content:
                self.whitelist_emoji_message = messages[0].id

        self.whitelist_emoji_pending = True

    @db_bot_whitelist.command(name='done_emoji')
    @utils.role_check()
    async def db_bot_whitelist_done_emjoi_set(self, context:commands.Context):
        """This sets the Whitelist completed emoji, you MUST ONLY use your Servers Emojis'"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Done Emoji...')

        flag = 'completed Whitelist requests!'
        await context.send('Please react to this message with the emoji you want for completed Whitelist requests!\n Only use Emojis from this Discord Server!')
        channel = self._client.get_channel(context.channel.id)
        messages = [message async for message in channel.history(limit=5)]
        for message in messages:
            if flag in message.content:
                self.whitelist_emoji_message = messages[0].id

        self.whitelist_emoji_done = True

    async def on_message_whitelist(self, message:discord.Message, context:commands.Context):
        """This handles on_message whitelist requests."""
        user_ign,user_servers = self.Parser.ParseIGNServer(message.content)
        self.logger.command(f'Whitelist Request: ign: {user_ign} servers: {user_servers}')
        amp_servers = []

        if user_ign == None or len(user_servers) == 0:
            await message.reply(f'Hey! I was unable to understand your request, please edit your previous message or send another message with the updated information!')
            self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
            self.failed_whitelist.append(message)
            return

        if not self.Auto_WL:
            return self.logger.error('Hey a Whitelist request came in, but Auto-Whitelisting is currently disabled!')

        db_user = self.DB.GetUser(context.author.name)
        if db_user == None:
            self.DB.AddUser(DiscordID=context.author.id, DiscordName=context.author.name)
            
        for server in user_servers:
            index = 0
            amp_server = self.uBot.serverparse(server,message,message.guild.id)
            if amp_server == None:
                index=+1
                if len(user_servers)-1 == index:
                    self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
                    self.failed_whitelist.append(message)
                    return await message.reply(f'Hey! I was unable to Whitelist you on the servers you requested, please edit your previous message or send another message with the updated information!')
                else:
                    continue

            if amp_server != None:
                #user_servers.pop(server) #Lets pop off the server we FOUND and replace it with the AMP Server object!
                amp_servers.append(amp_server)    

            if not amp_server.whitelist_intake(context.author,user_ign):
                self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
                self.failed_whitelist.append(message)
                return await message.reply(f'Hey! I am having trouble handling your whitelist message, please edit your previous message or send another message with the correct information!')

            if amp_server.check_Whitelist(context.author):
                self.logger.error(f'Discord User: {message.author.name} is already Whitelisted on {amp_server.FriendlyName}')
                return await message.reply(f'You are already Whitelisted on {amp_server.FriendlyName}. If this is an error contact Staff, otherwise have fun! <3')

            db_server = self.DB.GetServer(amp_server.InstanceID)
            if db_server.Whitelist == False:
                if db_server.DisplayName != None:
                    server_name = db_server.DisplayName
                else:
                    server_name = db_server.InstanceName

                await message.reply(f'Ooops, it appears that the server {server_name} has their Whitelisting Closed. If this is an error please contact a Staff Member.')
                return

            if db_server.Donator == True:
                author_roles = []
                for role in message.author.roles:
                    author_roles.append(str(role.id))
                    if self.DBConfig.GetSetting('Donator_Role')!= None:
                        if self.DBConfig.GetSetting('Donator_role_id') not in author_roles:
                            return await message.reply(f'*Waves* Hey this server is for Donator Access Only, it appears you do not have Donator. If this is an error please contact a Staff Member.')
                    else:
                        return await message.reply(f'Well it appears that the Staff have not set a Donator Role yet, Please inform Staff of this error.')
            
        # This handles Whitelist Delays if set.
        if self.WL_delay != 0:
            self.WL_wait_list.append({'author': message.author.name, 'msg': message, 'ampserver': amp_server, 'dbuser': db_user, 'context': context})
                
            self.logger.command(f'Added {message.author} to Whitelist Wait List.')
            emoji = self._client.get_emoji(self.WL_Pending_Emoji)
            if emoji != None:
                await message.add_reaction(emoji) #This should point to bot_config Emoji

            #Checks if the Tasks is running, if not starts the task.
            if not self.whitelist_waitlist_handler.is_running():
                self.whitelist_waitlist_handler.start()
            return

        if amp_server.Running and db_server.Whitelist:
            if amp_server.addWhitelist(context.author):
                whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
                await message.reply(content= self.whitelist_reply_handler(whitelist_reply), embed= await self.uBot.server_whitelist_embed(message, amp_server))
                discord_role = self.uBot.roleparse(db_server.Discord_Role, context, context.guild.id)
                await context.author.add_roles(discord_role, reason= 'Auto Whitelisting')

                emoji = self._client.get_emoji(self.WL_Finished_Emoji)
                if emoji != None:
                    await message.add_reaction(emoji) #This should point to bot_config Emoji

                self.logger.command(f'Whitelisting {message.author.name} on {amp_server.FriendlyName}')
                return

    @tasks.loop(seconds=60)
    async def whitelist_waitlist_handler(self):
        """This is the Whitelist Wait list handler, every 60 seconds it will check the list and whitelist them after the alotted wait time."""
        self.logger.command('Checking the Whitelist Wait List...')
        if len(self.WL_wait_list) == 0:
            self.whitelist_waitlist_handler.stop()

        cur_time = datetime.now(timezone.utc)
        try:
            wait_time = timedelta(minutes=self.WL_delay)  # This may error if someone changes the wait time to 0 inbetween a loop..
        except Exception:
            wait_time = timedelta(minutes=1)  # Fallback to 1 min delay if somehow the value fails to get parsed.

        for index in range(0,len(self.WL_wait_list)):
            cur_message = self.WL_wait_list[index]

            #This should compare datetime objects and if the datetime of when the message was created plus the wait time is greater than or equal the cur_time they get whitelisted.
            if cur_message['msg'].created_at + wait_time <= cur_time: 
                
                db_server = self.DB.GetServer(cur_message['ampserver'].FriendlyName)
                #This handles all the Discord Role stuff.
                if db_server != None and db_server.Discord_Role != None:
                    
                    discord_role = self.uBot.roleparse(db_server.Discord_Role,cur_message['context'],cur_message['context'].guild_id)
                    discord_user = self.uBot.userparse(cur_message['author'].name,cur_message['context'],cur_message['context'].guild_id)
                    await discord_user.add_roles(discord_role, reason= 'Auto Whitelisting')

                emoji = self._client.get_emoji(self.WL_Finished_Emoji)
                if emoji != None:
                    await cur_message['msg'].add_reaction(emoji) #This should point to bot_config Emoji

                server_embed = await self.uBot.server_whitelist_embed(cur_message['context'], cur_message['ampserver'])
                whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
                await cur_message['msg'].reply(content= self.whitelist_reply_handler(whitelist_reply), embed=server_embed)

                cur_message['ampserver'].addWhitelist(cur_message['context'].author)
                self.logger.command(f'Whitelisting {cur_message["author"]} on {cur_message["ampserver"].FriendlyName}')
                self.WL_wait_list.pop(index)

async def setup(client:commands.Bot):
    await client.add_cog(Whitelist(client))