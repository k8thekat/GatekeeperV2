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
from pprint import pprint

import utils
import AMP
import logging
import DB

import discord
from discord.ext import commands,tasks

class AMP_Cog(commands.Cog):
    def __init__ (self, client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()
        
        self.AMPHandler = AMP.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.logger.info(f'**SUCCESS** Initializing {self.name.replace("amp","AMP")}')
        
        self.amp_server_console_messages_send.start()
        self.logger.dev('AMP_Cog Console Message Handler Running: ' + str(self.amp_server_console_messages_send.is_running()))
       
        self.amp_server_console_chat_messages_send.start()
        self.logger.dev('AMP_Cog Console Chat Message Handler Running: ' + str(self.amp_server_console_chat_messages_send.is_running()))

        self.amp_server_console_event_messages_send.start()
        self.logger.dev('AMP_Cog Console Event Message Handler Running: ' + str(self.amp_server_console_event_messages_send.is_running()))

        self.amp_server_instance_check.start()
        self.logger.dev('AMP_Cog Instance Check Event Loop: ' + str(self.amp_server_instance_check.is_running()))
        
    @commands.Cog.listener('on_message')
    async def on_message(self, message:discord.Message):
        context = await self._client.get_context(message)
        if message.content.startswith(self._client.command_prefix):
            return message
        
        if message.author == self._client.user:
            self.logger.dev('AMP_Tasks_Cog Found my own Message, oops')
            return

        for amp_server in self.AMPInstances:
            self.AMPServer = self.AMPInstances[amp_server]
            if not self.AMPServer.Running:
                continue
            self.AMPServer._ADScheck()

            #Check and see if our Discord Console Channel matches the current message.id
            if self.AMPServer.Discord_Console_Channel == message.channel.id:
                
                #Makes sure we are not responding to a webhook message (ourselves/bots/etc)
                if message.webhook_id == None:
                    #This checks user permissions. Just in case.
                    if await utils.async_rolecheck(context=context, perm_node='server.console.interact'):
                        self.AMPServer.ConsoleMessage(message.content)
                        return

            #Check and see if our Discord Chat channel matches the message.id
            if self.AMPServer.Discord_Chat_Channel == message.channel.id:
                if message.author == self._client.user:
                    self.logger.dev('AMP_Tasks_Cog Found my own Message, oops')
                    return
                #If its NOT a webhook (eg a bot/outside source uses webhooks) send the message as normal. This is usually a USER sending a message..
                if message.webhook_id == None:
                    #This fetch's a users prefix from the bot_perms.json file.
                    author_prefix = await self.bPerms.get_role_prefix(str(message.author.id))
                  
                    #This calls the generic AMP Function; each server will handle this differently
                    self.AMPServer.Chat_Message(message.content, author= message.author.name, author_prefix= author_prefix)
                       
        return message

    @tasks.loop(seconds=30)
    async def amp_server_instance_check(self):
        """Checks for new AMP Instances every 30 seconds.."""
        self.logger.dev('Checking AMP Instance(s) Status...')
        self.AMPHandler.AMP._instanceValidation()
        self.AMPHandler.AMP._instance_ThreadManager()

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

                    channel = self._client.get_channel(AMPServer.Discord_Console_Channel)
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
                        if webhook.name == f"{AMPServer.FriendlyName} Console":
                            self.logger.debug(f'*AMP Console Message* found an old webhook, validating {AMPServer.FriendlyName} webhook')
                            if webhook.channel_id == AMPServer.Discord_Console_Channel:
                                console_webhook = webhook
                            else:
                                await webhook.edit(channel= channel)
                                self.logger.dev(f'**Editing Console Webhook for {AMPServer.FriendlyName} // ID: {webhook.id} // Channel: {webhook.channel_id}')
                                console_webhook = webhook
                            break

                    if console_webhook == None:
                        self.logger.dev(f'*AMP Console Message* creating a new webhook for {AMPServer.FriendlyName}')
                        console_webhook = await channel.create_webhook(name=f'{AMPServer.FriendlyName} Console')

                    if AMPServer.DisplayName is not None:  # Lets check for a Display name and use that instead.
                        self.logger.dev('*AMP Console Message* sending a message with displayname')
                        await console_webhook.send(message, username= AMPServer.DisplayName, avatar_url= AMPServer.Avatar_url)
                    else:
                        self.logger.dev('*AMP Console Message* sending a message with friendlyname')
                        await console_webhook.send(message, username= AMPServer.FriendlyName, avatar_url= AMPServer.Avatar_url)

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

                    channel = self._client.get_channel(AMPServer_Event.Discord_Event_Channel)
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
                    self.logger.debug(f'*AMP Event Message* webhooks {webhook_list}')
                    console_webhook = None
                    for webhook in webhook_list:
                        if webhook.name == f"{AMPServer_Event.FriendlyName} Events":
                            self.logger.debug(f'*AMP Event Message* found an old webhook, reusing it {AMPServer_Event.FriendlyName}')
                            if webhook.channel_id == AMPServer_Event.Discord_Event_Channel:
                                console_webhook = webhook
                            else:
                                await webhook.edit(channel= channel)
                                self.logger.dev(f'**Editing Event Webhook for {AMPServer_Event.FriendlyName} ID: {webhook.id} Channel: {webhook.channel_id}')
                                console_webhook = webhook
                            break

                    if console_webhook == None:
                        self.logger.dev(f'*AMP Event Message* creating a new webhook for {AMPServer_Event.FriendlyName}')
                        console_webhook = await channel.create_webhook(name=f'{AMPServer_Event.FriendlyName} Events')

                    if AMPServer_Event .DisplayName is not None:  # Lets check for a Display name and use that instead.
                        self.logger.dev('*AMP Event Message* sending a message with displayname')
                        await console_webhook.send(message, username= AMPServer_Event.DisplayName, avatar_url= AMPServer_Event.Avatar_url)
                    else:
                        self.logger.dev('*AMP Event Message* sending a message with friendlyname')
                        await console_webhook.send(message, username= AMPServer_Event.FriendlyName, avatar_url= AMPServer_Event.Avatar_url)

    @tasks.loop(seconds=1)
    async def amp_server_console_chat_messages_send(self):
        """This handles IN game chat messages and sends them to discord."""
        if self._client.is_ready():
            AMPChatChannels = {}
            for amp_server in self.AMPInstances:
                AMPServer = self.AMPInstances[amp_server]

                if AMPServer.Discord_Chat_Channel == None:
                    continue

                if AMPServer.Discord_Chat_Channel not in AMPChatChannels:
                    AMPChatChannels[AMPServer.Discord_Chat_Channel] = []
                AMPChatChannels[AMPServer.Discord_Chat_Channel].append(AMPServer)

            Sent_Data = True
            while(Sent_Data):
                Sent_Data = False
                for amp_server in self.AMPInstances:
                    AMPServer_Chat = self.AMPInstances[amp_server]
                    AMP_Server_Console_Chat = AMPServer_Chat.Console

                    if AMPServer_Chat.Discord_Chat_Channel == None:
                        continue

                    channel = self._client.get_channel(AMPServer_Chat.Discord_Chat_Channel)
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
                        if webhook.name == f"{AMPServer_Chat.FriendlyName} Chat":
                            self.logger.debug(f'*AMP Chat Message* found an old webhook, reusing it {AMPServer_Chat.FriendlyName}')
                            if webhook.channel_id == AMPServer_Chat.Discord_Chat_Channel:
                                chat_webhook = webhook
                            else:
                                await webhook.edit(channel= channel)
                                self.logger.dev(f'**Editing Chat Webhook for {AMPServer_Chat.FriendlyName} ID: {webhook.id} Channel: {webhook.channel_id}')
                                chat_webhook = webhook
                            break

                    if chat_webhook == None:
                        self.logger.dev(f'*AMP Chat Message* creating a new webhook for {AMPServer_Chat.FriendlyName}')
                        chat_webhook = await channel.create_webhook(name=f'{AMPServer_Chat.FriendlyName} Chat')

                    #This is the person who wrote the In-Game Message
                    author = message['Source']
                    author_prefix = None

                    message_contents = message['Contents'].replace('\n', ' ')
                    server_prefix = AMPServer_Chat.Discord_Chat_Prefix

                    db_author = self.DB.GetUser(author)
                    if db_author != None:
                        author_prefix = await self.bPerms.get_role_prefix(db_author.DiscordID)

                        if AMPServer_Chat.get_IGN_Avatar(db_user= db_author):
                            self.logger.dev('Using AMP Server Information')
                            name, avatar = AMPServer_Chat.get_IGN_Avatar(db_user= db_author)

                        else:
                            discord_user = self._client.get_user(db_author.DiscordID) 
                            if discord_user != None:
                                self.logger.dev('Using Discord Server Information')
                                name, avatar = discord_user.name, discord_user.avatar

                    if db_author == None:
                        self.logger.dev('Using Message Information')
                        name, avatar = author, AMPServer_Chat.Avatar_url

                    if author_prefix != None:
                        self.logger.dev('Adding Author Prefix to Name')
                        name = f'[{author_prefix}] ' + name
                     
                    if server_prefix != None:
                        self.logger.dev('Adding Server Prefix to Name')
                        name = f'[{server_prefix}] - ' + name

                    await chat_webhook.send(content= message_contents, username= name, avatar_url= avatar)

                    #This is the Chat Relay to seperate AMP Servers.
                    if chat_webhook.channel.id in AMPChatChannels:
                        self.logger.dev('Found another Server Chat Channel Listening to this Discord channel.')
                        for Server in AMPChatChannels[chat_webhook.channel.id]:
                            
                            #Dont re-send the Console Chat message we sent to Discord to the same server.
                            if AMPServer_Chat == Server:
                                continue

                            self.logger.dev(f'Sending the Mesage from {AMPServer_Chat.FriendlyName} to Other Server: {Server.FriendlyName}')
                            Server.Chat_Message(message= message_contents, author_prefix= author_prefix, author= author, server_prefix= AMPServer_Chat.Discord_Chat_Prefix)

async def setup(client:commands.Bot):
    await client.add_cog(AMP_Cog(client))