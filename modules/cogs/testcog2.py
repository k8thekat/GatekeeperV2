import logging
import discord
from discord.ext import commands

import utils
import bot_config
import modules.AMP as AMP
import logging

class Cog_Template(commands.Cog):
    def __init__(self,client):
        global AMPInstances
        self._client = client
        self.AMP = AMP.getAMP()
        self.logger = logging.getLogger(__name__)
        self.uBot = utils.botUtils(client)
        AMPInstances = self.AMP.getInstances()
        self.logger.info('Loading testcog2.py...')
        self._client.command_prefix #Use this to get the command_prefix
        self.uBot.sub_command_handler('user',self.info)
        # parent_command = self._client.get_command("user")
        # print(parent_command)
        # parent_command.add_command(self.info)

    # async def cog_load(self):
    #     print('Loading testcog2 via cog_load')
    #     parent_command = self.client.get_command("user")
    #     print(parent_command)
    #     #for command in self.walk_commands():
    #     parent_command.add_command(self.info)
                
    @commands.command()
    @utils.role_check()
    async def info(self, ctx):
        print('Cog Testing v2')


def setup(client):
    client.add_cog(Cog_Template(client))