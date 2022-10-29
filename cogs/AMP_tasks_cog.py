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
import asyncio

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
        self.bPerms = utils.botPerms()
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
            
        for amp_server in self.AMPInstances:
            self.AMPServer = self.AMPInstances[amp_server]
            if not self.AMPServer.Running:
                continue
            self.AMPServer._ADScheck()

            #Check and see if our Discord Console Channel matches the current message.id
            if self.AMPServer.Discord_Console_Channel == message.channel.id:
                if message.author == self._client.user:
                    return
                #Makes sure we are not responding to a webhook message (ourselves/bots/etc)
                if message.webhook_id == None:
                    #This checks user permissions. Just in case.
                    if await utils.async_rolecheck(context=context, perm_node='server.console.interact'):
                        self.AMPServer.ConsoleMessage(message.content)
                        return

            #Check and see if our Discord Chat channel matches the message.id
            if self.AMPServer.Discord_Chat_Channel == message.channel.id:
                
                #If its NOT a webhook (eg a bot/outside source uses webhooks) send the message as normal. This is usually a USER sending a message..
                if message.webhook_id == None:
                    #This fetch's a users prefix from the bot_perms.json file.
                    author_prefix = await self.bPerms.get_role_prefix(str(message.author.id))
                    #author_prefix = 'MOD'
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
    
                    author = None
                    author_db = self.DB.GetUser(message['Source'])
                    author_prefix = None

                    if AMPServer_Chat.Discord_Chat_Prefix != None:
                        contents = self.uBot.message_formatter(f"\x01[{AMPServer_Chat.Discord_Chat_Prefix}]\x02 : {message['Contents']}")
                    contents = message['Contents']

                    #If we have a DB user, lets try to send customized message.
                    if author_db != None:
                        #This is for if we exist in the DB, but don't have proper DB information (MC IGN or similar)
                        author = self._client.get_user(author_db.DiscordID) 

                        if author_db.Role in self.bPerms.permissions:
                            author_prefix = self.bPerms.permissions[author_db.Role]['prefix']

                        #This can return false to land into the else:
                        if AMPServer_Chat.get_IGN_Avatar(db_user= author_db):
                            self.logger.dev('*AMP Chat Message* sending a message with Instance specific configuration with DB Information')
                            name, avatar = AMPServer_Chat.get_IGN_Avatar(db_user= author_db)
                            webhook_username = name

                            #Lets attempt to use a Prefix set inside of bot_perms.json
                            if author_prefix:
                                if AMPServer_Chat.Discord_Chat_Prefix:
                                    server_prefix = self.uBot.message_formatter(f'\x01[{AMPServer_Chat.Discord_Chat_Prefix}]\x02')
                                    message['Contents'] = f'{server_prefix}{author_prefix}: {message["Contents"]}'
                                else:
                                    message['Contents'] = f'{author_prefix}: {message["Contents"]}'
                                await chat_webhook.send(contents= message['Contents'], username= name, avatar_url= avatar)
                                
                            else:
                                await chat_webhook.send(contents, username=name, avatar_url=avatar)
                                
                        #This will use discord Information after finding them in the DB, for there Display name and Avatar if possible.
                        elif author != None:
                            self.logger.dev('*AMP Chat Message** sending a message with discord information')
                            webhook_username = author.name
                            await chat_webhook.send(contents, username=author.name, avatar_url=author.avatar)
                            
                    #This fires if we cant find a DB user and the Discord User
                    else:
                        #This can return False to land into the pass through else:
                        if AMPServer_Chat.get_IGN_Avatar(user= message['Source']):
                            self.logger.dev('*AMP Chat Message* sending a message with Instance specific configuration without DB information')
                            name, avatar = AMPServer_Chat.get_IGN_Avatar(user= message['Source'])
                            webhook_username = name
                            await chat_webhook.send(contents, username=name, avatar_url=avatar)
                            
                        #This just sends the message as is with default information from the bot.
                        else:
                            self.logger.dev('**AMP Chat Message** sending message as is without changes.')
                            webhook_username = message['Source']
                            await chat_webhook.send(contents, username= message['Source'], avatar_url=self.AMPInstances[amp_server].Avatar_url)

                    #This is the Chat Relay to seperate AMP Servers.
                    if chat_webhook.channel.id in AMPChatChannels:
                        for Server in AMPChatChannels[chat_webhook.channel.id]:
                            #Dont re-send the Console Chat message we sent to Discord to the same server.
                            if AMPServer_Chat.Discord_Chat_Channel == chat_webhook.channel.id:
                                continue
                            if author_prefix:
                                Server.Chat_Message(message= Server.Chat_Message_Formatter(message['Contents']), author_prefix= author_prefix, author= webhook_username , server_prefix= Server.Discord_Chat_Prefix)
                                continue
                            Server.Chat_Message(message= Server.Chat_Message_Formatter(message['Contents']), author= webhook_username , server_prefix= Server.Discord_Chat_Prefix)

async def setup(client:commands.Bot):
    await client.add_cog(AMP_Cog(client))