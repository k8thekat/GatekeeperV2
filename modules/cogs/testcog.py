import discord
from discord.ext import commands
import time
import asyncio

import utils as botclass
import logging



class test_cog(commands.Cog):
    def __init__ (self,client):
        global dBot,uBot,testclient
        self.logger = logging.getLogger(__name__)
        self.logger.info('Loading Testcog.py...')
        self._client = client
        testclient = client
        #dBot = botclass.discordBot(client)
        #uBot = botclass.botUtils(client)
        #self._client.load_extension('modules.cogs.testcog2')
        #self._client.load_extension('modules.cogs.testcog2')
        #testing = self._client.get_command("user")
        #print(testing,dir(testing))
        #print(dir(testing.command))
        #testing.add_command(help)

    async def test(self):
        global dBot,uBot
        client_guild = 602285328320954378
        discord_role = uBot.roleparse(client_guild,'Test')
        print(type(discord_role),discord_role.name,discord_role.id)
        discord_user = uBot.userparse(client_guild,'k8thekat#1357')
        print(type(discord_user),discord_user.name,discord_user.id)
        discord_channel = uBot.channelparse(client_guild,'botchannel')
        print(type(discord_channel),discord_channel.name,discord_channel.id)
    

def setup(client):
    client.add_cog(test_cog(client))