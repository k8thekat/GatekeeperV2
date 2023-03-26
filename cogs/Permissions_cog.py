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
from discord import app_commands
from discord.ext import commands

from typing import Union

import utils
from db import DBUser
from utils.cogs.base_cog import Gatekeeper_Cog
from utils.permissions import Gatekeeper_Permissions

# FIXME This may break, circular import.
from Gatekeeper import Gatekeeper
from utils.check import role_check

# This is used to force cog order to prevent missing methods.
Dependencies = ["DB_user_cog.py"]


class Permissions(Gatekeeper_Cog):
    def __init__(self, client: Gatekeeper):
        super().__init__(client=client)
        self._bPerms: Gatekeeper_Permissions = Gatekeeper_Permissions()
        self._command_helper.sub_command_handler('user', self.user_role)  # This is used to add a sub command(self,parent_command,sub_command)

    async def autocomplete_permission_roles(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """This is for roles inside of the bot_perms file. Returns a list of all the roles.."""

        choice_list: list[str] = self._bPerms.get_roles()
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    @commands.hybrid_command(name='role')
    @role_check()
    @app_commands.autocomplete(role=autocomplete_permission_roles)
    async def user_role(self, context: commands.Context, user: Union[discord.User, discord.Member], role: str):
        """Set a users Permission Role for commands."""
        self._logger.command(f'{context.author.name} used User Role Function')  # type:ignore

        db_user: DBUser | None = self._DB.GetUser(str(user.id))
        if db_user != None:
            db_user.Role = role
            await context.send(f"We set the User: **{user.name}** permission's role to `{role}`.", ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(f'We failed to find the User: {user.name}, please make sure they are in the DB.', ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client):
    await client.add_cog(Permissions(client))
