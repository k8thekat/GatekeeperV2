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
from datetime import timedelta, datetime, timezone

import utils
import AMP
import logging
import DB
from modules.parser import Parser

import discord
from discord.ext import commands, tasks


class AMP_Cog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()

        self.AMPHandler = AMP.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances

        self.AMPInstances_Console_Channels = []
        self.AMPInstances_Chat_Channels = []

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.Parser = Parser()
        self.logger.info(f'**SUCCESS** Initializing {self.name.replace("amp","AMP")}')

        # This should help prevent errors in older databases.
        try:
            self.attr_update()

        except Exception:
            self.DBHandler.dbWhitelistSetup()
            self.attr_update()

        self.failed_whitelist = []
        self.WL_wait_list = []  # Layout = [{'author': message.author.name, 'msg' : message, 'ampserver' : amp_server, 'dbuser' : db_user}]

        self.update_loop.start()
        self.logger.dev('AMP_Cog Update Loop Running:' + str(self.update_loop.is_running()))

        self.amp_server_console_messages_send.start()
        self.logger.dev('AMP_Cog Console Message Handler Running: ' + str(self.amp_server_console_messages_send.is_running()))

        self.amp_server_console_chat_messages_send.start()
        self.logger.dev('AMP_Cog Console Chat Message Handler Running:' + str(self.amp_server_console_chat_messages_send.is_running()))

    @tasks.loop(seconds=5)
    async def update_loop(self):
        # This is to keep everything up to date when we change the settings in the DB
        self.attr_update()
        #This is to check for any new instances that have been created since the bot was running.
        #self.AMPHandler.AMP_instanceCheck()
        self.logger.dev('Updating AMP_Cog Attributes!')

    def attr_update(self):
        self.Auto_WL = self.DBConfig.Auto_whitelist
        self.WL_channel = self.DBConfig.Whitelist_channel  # DBConfig is Case sensitive.
        self.WL_delay = self.DBConfig.Whitelist_wait_time  # Should only be an INT value; all values in Minutes.
        self.WL_Pending_Emoji = self.DBConfig.Whitelist_emoji_pending
        self.WL_Finished_Emoji = self.DBConfig.Whitelist_emoji_done

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        context = await self._client.get_context(message)
        if message.webhook_id is not None:
            return message
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            self.logger.dev(f'On Message Event for {self.name}')
            if self.WL_channel is not None:
                if message.channel.id == int(self.WL_channel):  # This is AMP Specific; for handling whitelist requests to any server.
                    await self.on_message_whitelist(message, context)

            if not self.webhook_verify(message):

                for amp_server in self.AMPInstances:
                    self.AMPServer = self.AMPInstances[amp_server]

                        if self.AMPServer.Discord_Console_Channel == str(message.channel.id):
                            if utils.async_rolecheck(context,'server.console.interact'):
                                self.AMPServer.ConsoleMessage(message.content)

                        if self.AMPServer.Discord_Chat_Channel == str(message.channel.id):
                            self.AMPServer.send_message(message) #This calls the generic AMP Function; each server will handle this differently.
                        
            return message
    # This is called when a message in any channel of the guild is edited. Returns <message> object.

    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self, message_before: discord.Message, message_after: discord.Message):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            # This handles edited whitelist requests!
            if message_before in self.failed_whitelist and message_before.channel.id == self.WL_channel:
                context = await self._client.get_context(message_before)
                await self.on_message_whitelist(message_after, context)

            self.logger.dev(f'Edited Message Event for {self.name}')
            return message_before, message_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')
        for index in len(0, self.WL_wait_list):
            if member.name == self.WL_wait_list[index]['author']:
                self.WL_wait_list.pop(index)
                self.logger.info(f'Removed {member.name} from Whitelist Wait List.')
        return member

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self.logger.dev(f'Reaction Add {self.name}: {user} Reaction: {reaction}')
        return reaction, user

    @commands.Cog.listener('on_reaction_remove')
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
        self.logger.dev(f'Reaction Remove {self.name}: {user} Reaction: {reaction}')
        return reaction, user

    def webhook_verify(self, message: discord.Message):
        """This checks the message against ourselves to make sure we don't reply or send our own message back."""
        for webhook in self.webhook_list:
            if webhook.id == message.author.id:
                self.logger.debug(f'Found a Matching Webhook ID to Message Author ID; ignoring Message Webhook:{webhook.id} Author:{message.author.id}')
                return True
            else:
                continue
        return False

    @tasks.loop(seconds=1)
    async def amp_server_console_messages_send(self):
        if self._client.is_ready():
            for amp_server in self.AMPInstances:
                self.AMPServer = self.AMPInstances[amp_server]
                self.AMP_Server_Console = self.AMPServer.Console

                if self.AMPServer.Discord_Console_Channel is None:
                    continue

                channel = self._client.get_channel(int(self.AMPServer.Discord_Console_Channel))
                if channel is None:
                    continue

                self.AMP_Server_Console.console_message_lock.acquire()
                console_messages = self.AMP_Server_Console.console_messages
                self.AMP_Server_Console.console_messages = []
                self.AMP_Server_Console.console_message_lock.release()

                # This setup is for getting/used old webhooks and allowing custom avatar names per message.
                self.webhook_list = await channel.webhooks()
                self.logger.debug(f'*AMP Console Message* webhooks {self.webhook_list}')
                console_webhook = None
                for webhook in self.webhook_list:
                    if webhook.name == f"{self.AMPInstances[amp_server].FriendlyName} Console":
                        self.logger.debug(f'*AMP Console Message* found an old webhook, reusing it {self.AMPInstances[amp_server].FriendlyName}')
                        console_webhook = webhook
                        break

                if console_webhook is None:
                    self.logger.dev(f'*AMP Console Message* creating a new webhook for {self.AMPInstances[amp_server].FriendlyName}')
                    console_webhook = await channel.create_webhook(name=f'{self.AMPInstances[amp_server].FriendlyName} Console')

                if len(console_messages) != 0:
                    for message in console_messages:
                        if self.AMPServer.DisplayName is not None:  # Lets check for a Display name and use that instead.
                            self.logger.dev('*AMP Console Message* sending a message with displayname')
                            await console_webhook.send(message, username=self.AMPInstances[amp_server].DisplayName, avatar_url=self._client.user.avatar)
                        else:
                            self.logger.dev('*AMP Console Message* sending a message with friendlyname')
                            await console_webhook.send(message, username=self.AMPInstances[amp_server].FriendlyName, avatar_url=self._client.user.avatar)

                    self.AMP_Server_Console.console_messages = []

    @tasks.loop(seconds=1)
    async def amp_server_console_chat_messages_send(self):
        if self._client.is_ready():
            for amp_server in self.AMPInstances:
                self.AMPServer = self.AMPInstances[amp_server]
                self.AMP_Server_Console = self.AMPServer.Console

                if self.AMPServer.Discord_Chat_Channel is None:
                    continue

                channel = self._client.get_channel(int(self.AMPServer.Discord_Chat_Channel))
                if channel is None:
                    continue

                self.AMP_Server_Console.console_chat_message_lock.acquire()
                chat_messages = self.AMP_Server_Console.console_chat_messages
                self.AMP_Server_Console.console_chat_messages = []
                self.AMP_Server_Console.console_chat_message_lock.release()

                # This setup is for getting/used old webhooks and allowing custom avatar names per message.
                self.webhook_list = await channel.webhooks()
                self.logger.debug(f'*AMP Chat Message* webhooks {self.webhook_list}')
                chat_webhook = None
                for webhook in self.webhook_list:
                    if webhook.name == f"{self.AMPInstances[amp_server].FriendlyName} Chat":
                        self.logger.debug(f'*AMP Chat Message* found an old webhook, reusing it {self.AMPInstances[amp_server].FriendlyName}')
                        chat_webhook = webhook
                        break

                if chat_webhook is None:
                    self.logger.dev(f'*AMP Chat Message* creating a new webhook for {self.AMPInstances[amp_server].FriendlyName}')
                    chat_webhook = await channel.create_webhook(name=f'{self.AMPInstances[amp_server].FriendlyName} Chat')

                if len(chat_messages) != 0:
                    for message in chat_messages:
                        author = None
                        author_db = self.DB.GetUser(message['Source'])

                        if author_db is not None:
                            # This is a default method in each Server, returns False for no customization
                            if self.AMPServer.discord_message(author_db):
                                self.logger.dev('*AMP Chat Message* sending a message with Instance specific configuration')
                                name, avatar = self.AMPServer.discord_message(author_db)
                                await chat_webhook.send(message['Contents'], username=name, avatar_url=avatar)
                                continue
                            else:
                                author = self._client.get_user(int(author_db.DiscordID))

                        # This will use discord Information for there Display name and Avatar if possible.
                        if author is not None:
                            self.logger.dev('*AMP Chat Message* sending a message with discord information')
                            await chat_webhook.send(message['Contents'], username=author.name, avatar_url=author.avatar)
                            continue
                        else:
                            self.logger.dev('*AMP Chat Message* sending a message with default information')

                            await chat_webhook.send(message['Contents'], username=message['Source'])
                            continue

                    self.AMP_Server_Console.console_chat_messages = []

    async def on_message_whitelist(self, message: discord.Message, context: commands.context):
        """This handles on_message whitelist requests."""
        user_ign, user_servers = self.Parser.ParseIGNServer(message.content)
        self.logger.command(f'Whitelist Request: ign: {user_ign} servers: {user_servers}')
        amp_servers = []

        if user_ign is None or len(user_servers) == 0:
            await message.reply('Hey! I was unable to understand your request, please edit your previous message or send another message with the updated information!')
            self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
            self.failed_whitelist.append(message)
            return

        for server in user_servers:
            index = 0
            amp_server = self.uBot.serverparse(server, message, message.guild.id)
            if amp_server is None:
                #!TODO! "index + 1" has no effect - possible bug? Maybe "index += 1"?
                index + 1
                if len(user_servers) - 1 == index:
                    await message.reply('Hey! I was unable to Whitelist you on the servers you requested, please edit your previous message or send another message with the updated information!')
                    self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
                    self.failed_whitelist.append(message)
                    return
                else:
                    continue

            if amp_server is not None:
                # user_servers.pop(server) #Lets pop off the server we FOUND and replace it with the AMP Server object!
                amp_servers.append(amp_server)

            user_UUID = amp_server.name_Conversion(user_ign)  # Returns None if Multiple or incorrect.
            if user_UUID is None:
                await message.reply('Hey! I am having trouble finding your IGN, please edit your previous message or send another message with the correct information!')
                self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
                self.failed_whitelist.append(message)
                return

        db_user = self.DB.GetUser(message.author.name)
        if db_user is None:
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
        if not db_server.Whitelist:
            if db_server.DisplayName is not None:
                server_name = db_server.DisplayName
            else:
                server_name = db_server.InstanceName

            await message.reply(f'Ooops, it appears that the server {server_name} has their Whitelisting Closed. If this is an error please contact a Staff Member.')
            return

        if db_server.Donator and not db_user.Donator:
            await message.reply('*Waves* Hey this server is for Donator Access Only, it appears you do not have Donator. If this is an error please contact a Staff Member.')
            return

        # This handles Whitelist Delays if set.
        if self.WL_delay != 0:
            self.WL_wait_list.append({'author': message.author.name, 'msg': message, 'ampserver': amp_server, 'dbuser': db_user, 'context': context})

            if self.WL_Pending_Emoji is not None:
                await self.dBot.messageAddReaction(message, self.WL_Pending_Emoji)

            self.logger.command(f'Added {message.author} to Whitelist Wait List.')
            emoji = self._client.get_emoji(self.WL_Pending_Emoji)
            if emoji is not None:
                await message.add_reaction(emoji)  # This should point to bot_config Emoji

            # Checks if the Tasks is running, if not starts the task.
            if not self.whitelist_waitlist_handler.is_running():
                self.whitelist_waitlist_handler.start()
            return

        if amp_server.Running and db_server.Whitelist:
            amp_server.addWhitelist(db_user.MC_IngameName)
            await message.reply(embed=self.uBot.server_whitelist_embed(message, amp_server))
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

        for index in range(0, len(self.WL_wait_list)):
            cur_message = self.WL_wait_list[index]

            # This should compare datetime objects and if the datetime of when the message was created plus the wait time is greater than or equal the cur_time they get whitelisted.
            if cur_message['msg'].created_at + wait_time <= cur_time:
                cur_message['ampserver'].addWhitelist(cur_message['dbuser'].MC_IngameName)
                await cur_message['msg'].reply(embed=self.uBot.server_whitelist_embed(cur_message['context'], cur_message['ampserver']))
                self.logger.command(f'Whitelisting {cur_message["author"]} on {cur_message["ampserver"].FriendlyName}')


async def setup(client: commands.Bot):
    await client.add_cog(AMP_Cog(client))
