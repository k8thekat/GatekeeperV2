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
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import os
import logging

import utils
import AMP_Handler
import DB as DB

DisplayImageSources = ['steam:211820']


class Starbound(commands.Cog):
    def __init__(self, client: commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        # use DBHandler for all DB related needs.
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBCOnfig = self.DB.DBConfig

        # utils.botUtils provide access to utility functions such as serverparse,role_parse,channel_parse,user_parse.
        self.uBot = utils.botUtils(client)
        # utils.discordBot provides access to utility functions such as sending/deleting messages, kicking/ban users.
        self.dBot = utils.discordBot(client)

        # Leave this commented out unless you need to create a sub-command.
        # self.uBot.sub_command_handler('user',self.info) #This is used to add a sub command(self,parent_command,sub_command)
        self.logger.info(f'**SUCCESS** Loading Module **{self.name.capitalize()}**')


async def setup(client):
    await client.add_cog(Starbound(client))
