import asyncio
from http import client
import os
import datetime
from pprint import pprint

import utils
import AMP
import logging
import DB

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

        self.logger.info(f'**SUCCESS** Loading {self.name.replace("amp","AMP")}')
   
        self.uBot = utils.botUtils(client)
        self.amp_server_console_messages_send.start()
        self.logger.info('AMP_Cog Console Message Handler Running:' + str(self.amp_server_console_messages_send.is_running()))


        
    @commands.Cog.listener('on_message')
    async def on_message(self,message:discord.Message):
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            self.logger.info(f'On Message Event for {self.name}')

            if not self.webhook_verify(message):

                for amp_server in self.AMPInstances:
                    self.AMPServer = self.AMPInstances[amp_server]

                    if self.AMPServer.Discord_Console_Channel == str(message.channel.id):
                        self.AMPServer.ConsoleMessage(message.content)

                    if self.AMPServer.Discord_Chat_Channel == str(message.channel.id):
                        self.AMPServer.send_message(message.content) #This calls the generic AMP Function; each server will handle this differently.
                        
            return message


    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Removed {self.name}: {member.name}')
        return member

    def webhook_verify(self,message:discord.Message):
        """This checks the message against ourselves to make sure we don't reply or send our own message back."""
        for webhook in self.webhook_list:
            if webhook.id == message.author.id:
                self.logger.debug(f'Found a Matching Webhook ID to Message Author ID; ignoring Message Webhook:{webhook.id} Author:{message.author.id}')
                return True
            else:
                continue
        return False

    async def amp_server_console_messages_listen(self):
        print()

    @tasks.loop(seconds= 1)
    async def amp_server_console_messages_send(self):
        if self._client.is_ready():
            for amp_server in self.AMPInstances:
                self.AMPServer = self.AMPInstances[amp_server]
                self.AMP_Server_Console = self.AMPServer.Console

                if self.AMPServer.Discord_Console_Channel == None:
                    continue

                channel = self._client.get_channel(int(self.AMPServer.Discord_Console_Channel))
                if channel == None:
                    continue

                self.AMP_Server_Console.console_message_lock.acquire()
                console_messages = self.AMP_Server_Console.console_messages
                self.AMP_Server_Console.console_messages = []
                self.AMP_Server_Console.console_message_lock.release()

                #This setup is for getting/used old webhooks and allowing custom avatar names per message.
                self.webhook_list = await channel.webhooks()
                self.logger.debug(f'webhooks {self.webhook_list}')
                if len(self.webhook_list) == 0:
                    self.logger.debug(f'creating a new webhook for {self.AMPInstances[amp_server].FriendlyName}')
                    webhook = await channel.create_webhook(name= f'{self.AMPInstances[amp_server].FriendlyName} Console')
                else:
                    for webhook in self.webhook_list:
                        if webhook.name == f"{self.AMPInstances[amp_server].FriendlyName} Console":
                            self.logger.debug(f'found an old webhook, reusing it {self.AMPInstances[amp_server].FriendlyName}')
                            webhook = webhook

                if len(console_messages) != 0:
                    for message in console_messages:
                            if self.AMPServer.DisplayName != None: #Lets check for a Display name and use that instead.
                                self.logger.debug('sending a message with displayname')
                                await webhook.send(message, username= self.AMPInstances[amp_server].DisplayName,avatar_url=self._client.user.avatar)
                            else:
                                self.logger.debug('sending a message with friendlyname')
                                await webhook.send(message, username= self.AMPInstances[amp_server].FriendlyName,avatar_url=self._client.user.avatar)

                    self.AMP_Server_Console.console_messages = []


    @tasks.loop(seconds= 1)
    async def amp_server_console_chat_messages_send(self):
        print()



async def setup(client:commands.Bot):
    await client.add_cog(AMP_Cog(client))