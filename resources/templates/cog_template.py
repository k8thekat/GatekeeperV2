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
from typing import Union

from Gatekeeper import Gatekeeper
from utils.cogs.base_cog import Gatekeeper_Cog
from utils.check import role_check, guild_check

from discord.ext import commands
from discord import Message, User, Member, Reaction, app_commands, Object


# This is used to force cog order to prevent missing methods.
# MUST USE ENTIRE FILENAME!
Dependencies: Union[list[str], None] = None  # Example - ["AMP_server_cog.py"]


class Cog_Template(Gatekeeper_Cog):
    def __init__(self, client: Gatekeeper) -> None:
        super().__init__(client=client)

    @commands.Cog.listener('on_message')
    async def on_message(self, message: Message):
        """Called when a Member/User sends a message in any Channel of the Guild."""
        if message.content.startswith(self._client.prefix):  # This prevents any {prefix}commands from interacting with on_message events
            return message

        if message.content.startswith('/'):  # This prevents /commands from interacting with on_message events
            return message

        if message.author != self._client.user:  # This prevents the bot from interacting/replying to itself with on_message events
            self._logger.info(f'On Message Event for {self._name}')
            return message

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self, user_before: Union[Member, User], user_after: Union[Member, User]) -> None:
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self._logger.info(f'User Update {self._name}: {user_before} into {user_after}')

    # This is called when a message in any channel of the guild is edited. Returns <message> object.

    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self, message_before, message_after) -> None:
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            self._logger.info(f'Edited Message Event for {self._name}')

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self, reaction: Reaction, user: User) -> None:
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self._logger.info(f'Reaction Add {self._name}: {user} Reaction: {reaction}')

    @commands.Cog.listener('on_reaction_remove')
    async def on_reaction_remove(self, reaction: Reaction, user: User) -> None:
        """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
        self._logger.info(f'Reaction Remove {self._name}: {user} Reaction: {reaction}')

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: Member) -> None:
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self._logger.info(f'Member Leave {self._name}: {member.name} {member}')

    # Any COMMAND needs a ROLE CHECK prior unless its a sub_command

    @commands.hybrid_command(name='cog_temp')
    @role_check()
    async def temp(self, context: commands.Context):
        """cog template command'"""
        self._logger.info('test')

    # Example group command for a cog.
    @commands.hybrid_group(name='cog')
    @role_check()
    async def cog_temp(self, context: commands.Context):
        """ Cog Template Group Command"""
        print('cog temp test')

    # Example sub_command for a cog.
    # @commands.app_commands.describe
    @cog_temp.command(name='init')
    async def cog_init(self, context: commands.Context):
        """Cog Template Init Command"""
        print('cog init test')

    @commands.hybrid_command()
    # This limits the command to sync to a specific guild.
    @app_commands.guilds(Object(id= ''))
    # This limits the command to sync to a specific guild (same as above). But shows the command globally.
    @guild_check(guild_id= 123456789) #Simply place your guild.id here to make it a specific guild command. (Custom cog or similar)
    # This will autocomplete the command with some premade lists inside of utils.py. You can make your own, see utils.py -> Autocomplete template
    @app_commands.autocomplete()
    async def cmd(self, ctx:commands.Context, param: int):
        # So if ctx.interaction is None will tell you whether they invoked it via prefix or slash
        # i.e. you can call ctx.defer(), which will defer a slash invocation but do nothing in a prefix invocation
        await ctx.reply("abcd", ephemeral=True)

async def setup(client: Gatekeeper) -> None:
    await client.add_cog(Cog_Template(client))
