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
import datetime
from pprint import pprint
from datetime import timedelta,datetime,timezone
from sre_constants import IN

import utils
import AMP
import logging
import DB
from modules.parser import Parser

import discord
from discord.ext import commands,tasks
from discord.ui import Button,View

class AMP_Cog(commands.Cog):
    def __init__ (self,client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()
        
        self.AMPHandler = AMP.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances

        self.AMPInstances_Console_Channels = []
        self.AMPInstances_Chat_Channels = []

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

   
        self.uBot = utils.botUtils(client)
        self.Parser = Parser()
        self.bPerms = utils.botPerms()
        self.logger.info(f'**SUCCESS** Initializing {self.name.replace("amp","AMP")}')

        self.attr_update()
        
        self.failed_whitelist = []
        self.WL_wait_list = [] # Layout = [{'author': message.author.name, 'msg' : message, 'ampserver' : amp_server, 'dbuser' : db_user}]

        self.update_loop.start()
        self.logger.dev('AMP_Cog Update Loop Running:' + str(self.update_loop.is_running()))
        
        self.amp_server_console_messages_send.start()
        self.logger.dev('AMP_Cog Console Message Handler Running: ' + str(self.amp_server_console_messages_send.is_running()))
       
        self.amp_server_console_chat_messages_send.start()
        self.logger.dev('AMP_Cog Console Chat Message Handler Running:' + str(self.amp_server_console_chat_messages_send.is_running()))

        self.amp_server_console_event_messages_send.start()
        self.logger.dev('AMP_Cog Console Event Message Handler Running:' + str(self.amp_server_console_event_messages_send.is_running()))
        

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

    @commands.Cog.listener('on_message')
    async def on_message(self,message:discord.Message):
        context = await self._client.get_context(message)
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            self.logger.dev(f'On Message Event for {self.name}')
            if self.WL_channel is not None:
                if message.channel.id == int(self.WL_channel):  # This is AMP Specific; for handling whitelist requests to any server.
                    await self.on_message_whitelist(message, context)

        for amp_server in self.AMPInstances:
            self.AMPServer = self.AMPInstances[amp_server]
            #Check and see if our Discord Console Channel matches the current message.id
            if self.AMPServer.Discord_Console_Channel == str(message.channel.id):
                #Makes sure we are not responding to a webhook message (ourselves/bots/etc)
                if message.webhook_id == None:
                    #This checks user permissions. Just in case.
                    if await utils.async_rolecheck(context,'server.console.interact'):
                        self.AMPServer.ConsoleMessage(message.content)
                continue
            
            #Check and see if our Discord Chat channel matches the message.id
            if self.AMPServer.Discord_Chat_Channel == str(message.channel.id):
                #If its NOT a webhook (eg a bot/outside source) send the message as normal. This us usually a USER sending a message..
                if message.webhook_id == None:
                    author_prefix = self.bPerms.get_role_prefix(str(message.author.id))
                    self.AMPServer.send_message(message,prefix= author_prefix) #This calls the generic AMP Function; each server will handle this differently.
                else:
                    try:
                        cur_webhook = await self._client.fetch_webhook(message.webhook_id)
                    except:
                        return message
                    #Make sure the webhook ISNT our own; if it is continue.
                    if cur_webhook.name[:-5] == self.AMPServer.FriendlyName:
                        continue
                    #This ignores ANY Webhooks that are sending Event messages.
                    if cur_webhook.name == f'{self.AMPServer.FriendlyName} Events':
                        continue
                    #Check to make sure the server is running
                    if self.AMPServer.ADS_Running:
                        #See if the server has a prefix set.
                        if self.AMPServer.Discord_Chat_Prefix != None:
                            self.AMPServer.send_message(message, prefix=self.AMPServer.Discord_Chat_Prefix)
                        #Send the message without if its not set.
                        else:
                            self.AMPServer.send_message(message)
                    

        return message
    #This is called when a message in any channel of the guild is edited. Returns <message> object.
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self,message_before:discord.Message,message_after:discord.Message):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            #This handles edited whitelist requests!
            if message_before in self.failed_whitelist and message_before.channel.id == self.WL_channel:
                context = await self._client.get_context(message_before)
                await self.on_message_whitelist(message_after,context)

            self.logger.dev(f'Edited Message Event for {self.name}')
            return message_before,message_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')
        for index in len(0,self.WL_wait_list):
            if member.name == self.WL_wait_list[index]['author']:
                self.WL_wait_list.pop(index)
                self.logger.info(f'Removed {member.name} from Whitelist Wait List.')
        return member

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self,reaction:discord.Reaction,user:discord.User):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self.logger.dev(f'Reaction Add {self.name}: {user} Reaction: {reaction}')
        return reaction,user

    @commands.Cog.listener('on_reaction_remove')
    async def on_reaction_remove(self,reaction:discord.Reaction,user:discord.User):
        """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
        self.logger.dev(f'Reaction Remove {self.name}: {user} Reaction: {reaction}')
        return reaction,user

    @tasks.loop(seconds=1)
    async def amp_server_console_messages_send(self):
        """This handles AMP Console messages and sends them to discord."""
        if self._client.is_ready():
            Sent_Data = True
            while(Sent_Data):
                Sent_Data = False
                for amp_server in self.AMPInstances:
                    AMPServer = self.AMPInstances[amp_server]
                    AMP_Server_Console = AMPServer.Console

                    if AMPServer.Discord_Console_Channel == None:
                        continue

                    channel = self._client.get_channel(int(AMPServer.Discord_Console_Channel))
                    if channel == None:
                        continue
                    
                    if not len(AMP_Server_Console.console_messages):
                        continue

                    Sent_Data = True
                    AMP_Server_Console.console_message_lock.acquire()
                    message = AMP_Server_Console.console_messages.pop(0)
                    AMP_Server_Console.console_message_lock.release()

                    #This setup is for getting/used old webhooks and allowing custom avatar names per message.
                    webhook_list = await channel.webhooks()
                    self.logger.debug(f'*AMP Console Message* webhooks {webhook_list}')
                    console_webhook = None
                    for webhook in webhook_list:
                        if webhook.name == f"{self.AMPInstances[amp_server].FriendlyName} Console":
                            self.logger.debug(f'*AMP Console Message* found an old webhook, reusing it {self.AMPInstances[amp_server].FriendlyName}')
                            console_webhook = webhook
                            break

                    if console_webhook == None:
                        self.logger.dev(f'*AMP Console Message* creating a new webhook for {self.AMPInstances[amp_server].FriendlyName}')
                        console_webhook = await channel.create_webhook(name=f'{self.AMPInstances[amp_server].FriendlyName} Console')

                    if AMPServer.DisplayName is not None:  # Lets check for a Display name and use that instead.
                        self.logger.dev('*AMP Console Message* sending a message with displayname')
                        await console_webhook.send(message, username=self.AMPInstances[amp_server].DisplayName, avatar_url=self.AMPInstances[amp_server].Avatar_url)
                    else:
                        self.logger.dev('*AMP Console Message* sending a message with friendlyname')
                        await console_webhook.send(message, username=self.AMPInstances[amp_server].FriendlyName, avatar_url=self.AMPInstances[amp_server].Avatar_url)

    @tasks.loop(seconds=1)
    async def amp_server_console_event_messages_send(self):
        """This handles AMP Console Event messages and sends them to discord."""
        if self._client.is_ready():
            Sent_Data = True
            while(Sent_Data):
                Sent_Data = False
                for amp_server in self.AMPInstances:
                    AMPServer_Event = self.AMPInstances[amp_server]
                    AMP_Server_Console_Event = AMPServer_Event.Console

                    if AMPServer_Event.Discord_Event_Channel == None:
                        continue

                    channel = self._client.get_channel(int(AMPServer_Event.Discord_Event_Channel))
                    if channel == None:
                        continue
                    
                    if not len(AMP_Server_Console_Event.console_event_messages):
                        continue

                    Sent_Data = True
                    AMP_Server_Console_Event.console_event_message_lock.acquire()
                    message = AMP_Server_Console_Event.console_event_messages.pop(0)
                    AMP_Server_Console_Event.console_event_message_lock.release()

                    #This setup is for getting/used old webhooks and allowing custom avatar names per message.
                    webhook_list = await channel.webhooks()
                    self.logger.debug(f'*AMP Console Message* webhooks {webhook_list}')
                    console_webhook = None
                    for webhook in webhook_list:
                        if webhook.name == f"{self.AMPInstances[amp_server].FriendlyName} Events":
                            self.logger.debug(f'*AMP Console Message* found an old webhook, reusing it {self.AMPInstances[amp_server].FriendlyName}')
                            console_webhook = webhook
                            break

                    if console_webhook == None:
                        self.logger.dev(f'*AMP Console Message* creating a new webhook for {self.AMPInstances[amp_server].FriendlyName}')
                        console_webhook = await channel.create_webhook(name=f'{self.AMPInstances[amp_server].FriendlyName} Events')

                    if AMPServer_Event .DisplayName is not None:  # Lets check for a Display name and use that instead.
                        self.logger.dev('*AMP Console Message* sending a message with displayname')
                        await console_webhook.send(message, username=self.AMPInstances[amp_server].DisplayName, avatar_url=self.AMPInstances[amp_server].Avatar_url)
                    else:
                        self.logger.dev('*AMP Console Message* sending a message with friendlyname')
                        await console_webhook.send(message, username=self.AMPInstances[amp_server].FriendlyName, avatar_url=self.AMPInstances[amp_server].Avatar_url)

    @tasks.loop(seconds=1)
    async def amp_server_console_chat_messages_send(self):
        """This handles IN game chat messages and sends them to discord."""
        if self._client.is_ready():
            Sent_Data = True
            while(Sent_Data):
                Sent_Data = False
                for amp_server in self.AMPInstances:
                    AMPServer_Chat = self.AMPInstances[amp_server]
                    AMP_Server_Console_Chat = AMPServer_Chat.Console

                    if AMPServer_Chat.Discord_Chat_Channel == None:
                        continue

                    channel = self._client.get_channel(int(AMPServer_Chat.Discord_Chat_Channel))
                    if channel == None:
                        continue
                    
                    if not len(AMP_Server_Console_Chat.console_chat_messages):
                        continue
                    
                    Sent_Data = True
                    AMP_Server_Console_Chat.console_chat_message_lock.acquire()
                    message = AMP_Server_Console_Chat.console_chat_messages.pop(0)
                    AMP_Server_Console_Chat.console_chat_message_lock.release()

                    #This setup is for getting/used old webhooks and allowing custom avatar names per message.
                    webhook_list = await channel.webhooks()
                    self.logger.debug(f'*AMP Chat Message* webhooks {webhook_list}')
                    chat_webhook = None
                    for webhook in webhook_list:
                        if webhook.name == f"{self.AMPInstances[amp_server].FriendlyName} Chat":
                            self.logger.debug(f'*AMP Chat Message* found an old webhook, reusing it {self.AMPInstances[amp_server].FriendlyName}')
                            chat_webhook = webhook
                            break

                    if chat_webhook == None:
                        self.logger.dev(f'*AMP Chat Message* creating a new webhook for {self.AMPInstances[amp_server].FriendlyName}')
                        chat_webhook = await channel.create_webhook(name=f'{self.AMPInstances[amp_server].FriendlyName} Chat')

                    
                        
                    author = None
                    author_db = self.DB.GetUser(message['Source'])
                    author_prefix = None

                    #If we have a DB user, lets try to send customized message.
                    if author_db != None:
                        #This is for if we exist in the DB, but don't have proper DB information (MC IGN or similar)
                        author = self._client.get_user(int(author_db.DiscordID)) 

                        if author_db.Role in self.bPerms.permissions:
                            author_prefix = self.bPerms.permissions[author_db.Role]['prefix']

                        #This can return false to land into the else:
                        if AMPServer_Chat.discord_message(db_user= author_db):
                            self.logger.dev('*AMP Chat Message* sending a message with Instance specific configuration with DB Information')
                            name, avatar = AMPServer_Chat.discord_message(db_user= author_db)

                            #Lets attempt to use a Prefix set inside of bot_perms.json
                            if author_prefix:
                                await chat_webhook.send(contents = f'[{author_prefix}]{message["Contents"]}', username=name, avatar_url=avatar)
                                continue
                            else:
                                await chat_webhook.send(message['Contents'], username=name, avatar_url=avatar)
                                continue

                        #This will use discord Information after finding them in the DB, for there Display name and Avatar if possible.
                        if author != None:
                            self.logger.dev('*AMP Chat Message** sending a message with discord information')
                            await chat_webhook.send(message['Contents'], username=author.name, avatar_url=author.avatar)
                            continue

                    #This fires if we cant find a DB user and the Discord User
                    else:
                        #This can return False to land into the pass through else:
                        if AMPServer_Chat.discord_message(user= message['Source']):
                            self.logger.dev('*AMP Chat Message* sending a message with Instance specific configuration without DB information')
                            name, avatar = AMPServer_Chat.discord_message(user= message['Source'])
                            await chat_webhook.send(message['Contents'], username=name, avatar_url=avatar)
                            continue
                        #This just sends the message as is with default information from the bot.
                        else:
                            self.logger.dev('**AMP Chat Message** sending message as is without changes.')
                            await chat_webhook.send(message['Contents'], username= message['Source'], avatar_url=self.AMPInstances[amp_server].Avatar_url)
                            continue


    async def on_message_whitelist(self,message:discord.Message,context:commands.Context):
        """This handles on_message whitelist requests."""
        user_ign,user_servers = self.Parser.ParseIGNServer(message.content)
        self.logger.command(f'Whitelist Request: ign: {user_ign} servers: {user_servers}')
        amp_servers = []

        if user_ign == None or len(user_servers) == 0:
            await message.reply(f'Hey! I was unable to understand your request, please edit your previous message or send another message with the updated information!')
            self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
            self.failed_whitelist.append(message)
            return

        for server in user_servers:
            index = 0
            amp_server = self.uBot.serverparse(server,message,message.guild.id)
            if amp_server == None:
                index=+1
                if len(user_servers)-1 == index:
                    await message.reply(f'Hey! I was unable to Whitelist you on the servers you requested, please edit your previous message or send another message with the updated information!')
                    self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
                    self.failed_whitelist.append(message)
                    return
                else:
                    continue

            if amp_server != None:
                #user_servers.pop(server) #Lets pop off the server we FOUND and replace it with the AMP Server object!
                amp_servers.append(amp_server)    

            user_UUID = amp_server.name_Conversion(user_ign) #Returns None if Multiple or incorrect.
            if user_UUID == None:
                await message.reply(f'Hey! I am having trouble finding your IGN, please edit your previous message or send another message with the correct information!')
                self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
                self.failed_whitelist.append(message)
                return

        db_user = self.DB.GetUser(message.author.name)
        if db_user == None:
            self.logger.dev(f'Steam id Parser: {self.Parser.isSteam}')
            if self.Parser.isSteam:
                db_user = self.DB.AddUser(DiscordID=message.author.id, DiscordName=message.author.name, MC_IngameName=user_ign, SteamID=user_UUID)
            else:
                db_user = self.DB.AddUser(DiscordID=message.author.id, Discordname=message.author.name, MC_IngameName=user_ign, MC_UUID=user_UUID)

        if not self.Auto_WL:
            self.logger.error('Hey a Whitelist request came in, but Auto-Whitelisting is currently disabled!')
            return

        if amp_server.check_Whitelist(user_UUID):
            await message.reply(f'You are already Whitelisted on {amp_server.FriendlyName}. If this is an error contact Staff, otherwise have fun! <3')
            self.logger.error(f'Discord User: {message.author.name} is already Whitelisted on {amp_server.FriendlyName}')
            return

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
                if self.DBConfig.GetSetting('Donator_role_id') not in author_roles:
                    await message.reply(f'*Waves* Hey this server is for Donator Access Only, it appears you do not have Donator. If this is an error please contact a Staff Member.')
                    return

        # This handles Whitelist Delays if set.
        if self.WL_delay != 0:
            self.WL_wait_list.append({'author': message.author.name, 'msg': message, 'ampserver': amp_server, 'dbuser': db_user, 'context': context})

            if self.WL_Pending_Emoji != None:
                await self.dBot.messageAddReaction(message,self.WL_Pending_Emoji)
                
            self.logger.command(f'Added {message.author} to Whitelist Wait List.')
            emoji = self._client.get_emoji(self.WL_Pending_Emoji)
            if emoji != None:
                await message.add_reaction(emoji) #This should point to bot_config Emoji

            #Checks if the Tasks is running, if not starts the task.
            if not self.whitelist_waitlist_handler.is_running():
                self.whitelist_waitlist_handler.start()
            return

        if amp_server.Running and db_server.Whitelist:
            amp_server.addWhitelist(db_user.MC_IngameName)
            await message.reply(embed= await self.uBot.server_whitelist_embed(message, amp_server))
            discord_role = self.uBot.roleparse(db_server.Discord_Role, context, context.guild.id)
            await context.author.add_roles(discord_role, reason= 'Auto Whitelisting')
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
                cur_message['ampserver'].addWhitelist(cur_message['dbuser'].MC_IngameName)
                db_server = self.DB.GetServer(cur_message['ampserver'].FriendlyName)
                if db_server != None and db_server.Discord_Role != None:
                    #!TODO! Need to test roles!
                    print('Giving a user the DB role')
                    print(db_server.Discord_Role,cur_message['context'],cur_message['context'].guild_id, discord_role)
                    print(cur_message['author'].name, discord_user)
                    discord_role = self.uBot.roleparse(db_server.Discord_Role,cur_message['context'],cur_message['context'].guild_id)
                    discord_user = self.uBot.userparse(cur_message['author'].name,cur_message['context'],cur_message['context'].guild_id)
                    await discord_user.add_roles(discord_role, reason= 'Auto Whitelisting')
                await cur_message['msg'].reply(embed=self.uBot.server_whitelist_embed(cur_message['context'], cur_message['ampserver']))
                self.logger.command(f'Whitelisting {cur_message["author"]} on {cur_message["ampserver"].FriendlyName}')

    
async def setup(client:commands.Bot):
    await client.add_cog(AMP_Cog(client))