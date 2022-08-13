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
import discord
from discord.ext import commands
import os
import logging

import utils
import AMP as AMP
import DB as DB


class Minecraft(commands.Cog):
    def __init__(self, client: commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)  # Utilities Class for Embed's and other functionality.
        self.dBot = utils.discordBot(client)  # Common Discord Bot functionality (messages/reactions/users)

        self.DBConfig.AddSetting('Minecraft_Multiverse_Core', False)
        self.logger.info(f'**SUCCESS** Initializing Module **{self.name.capitalize()}**')

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self, user_before, user_after: discord.User):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.dev(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before, user_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')

        db_user = self.DB.GetUser(str(member.id))
        if db_user is not None and db_user.InGameName is not None:
            for server in self.AMPInstances:
                if self.AMPInstances[server].Module == 'Minecraft':
                    self.AMPInstances[server].removeWhitelist(db_user.InGameName)

        return member


async def setup(client):
    await client.add_cog(Minecraft(client))
