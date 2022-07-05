import os
import datetime
from pprint import pprint

import utils
import AMP
import logging
import DB

import discord
from discord.ext import commands
from discord.ui import Button,View

class AMP_Cog(commands.Cog):
    def __init__ (self,client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()
        
        self.AMPHandler = AMP.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances

        #self.AMPHandler.set_discord_client(self._client)   #This is to get the Discord Client functionality into AMPHandler and AMPConsole class

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        #self.server_list = self.amp_server_list
        self.logger.info(f'**SUCCESS** Loading {self.name.replace("amp","AMP")}')
   
        self.uBot = utils.botUtils(client)
        
    @commands.Cog.listener('on_message')
    async def on_message(self,message:discord.Message):
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            self.logger.info(f'On Message Event for {self.name}')
            return message

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Removed {self.name}: {member.name}')
        return member

    async def amp_server_console_init(self):
        print()


async def setup(client):
    await client.add_cog(AMP_Cog(client))