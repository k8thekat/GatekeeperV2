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
from discord.app_commands import Choice
from discord.ext import commands
import os
import logging
import re
import traceback

import utils
import amp_handler
import db as db
from utils.cogs.base_cog import Gatekeeper_Cog
from Gatekeeper import Gatekeeper
from utils.check import role_check

# This is used to force cog order to prevent missing methods.
Dependencies = None


class Regex(Gatekeeper_Cog):
    def __init__(self, client: Gatekeeper):
        self._command_helper.sub_command_handler('bot', self.regex_pattern)

    async def autocomplete_regex(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Regex Pattern Names"""
        choice_list: list[str] = []
        regex_patterns: dict[str, dict[str, str]] = self._DB.GetAllRegexPatterns()

        for regex in regex_patterns:
            choice_list.append(regex_patterns[regex]["Name"])
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    @commands.hybrid_group(name='regex_pattern')
    @role_check()
    async def regex_pattern(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @regex_pattern.command(name='add')
    @role_check()
    @app_commands.describe(name='The Name to associate to the Regex pattern')
    @app_commands.describe(filter_type='Either the Pattern will apply to `Server Console` or `Server Events`')
    @app_commands.describe(pattern='AMP uses `re.search(pattern)` for filtering.')
    @app_commands.choices(filter_type=[Choice(name='Console', value=0), Choice(name='Events', value=1)])
    async def regex_pattern_add(self, context: commands.Context, name: str, filter_type: Choice[int], pattern: str):
        """Add a Regex Pattern to the Database"""
        self._logger.command(f'{context.author.name} used Regex Pattern Add')  # type:ignore
        try:
            re.compile(pattern=pattern)
        except re.error as e:
            self._logger.error(e)
            return await context.send(content=f'The Pattern you provided is invalid. \n `{pattern}`', ephemeral=True, delete_after=self._client.Message_Timeout)

        if self._DB.AddRegexPattern(Name=name, Pattern=pattern, Type=filter_type.value):
            await context.send(content=f'Added the Regex - \n __**Name**:__ {name} \n __**Type**__: {filter_type.name} \n __**Pattern**:__ {pattern}', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(content=f'I was unable to add the entry; the Name `{name}` already exists in the Database. Please provide a unique Name for your Regex.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @regex_pattern.command(name='delete')
    @role_check()
    @app_commands.autocomplete(name=autocomplete_regex)
    async def regex_pattern_remove(self, context: commands.Context, name: str):
        """Remove a Regex Pattern from the Database"""
        self._logger.command(f'{context.author.name} used Regex Pattern Delete')  # type:ignore
        if self._DB.DelRegexPattern(Name=name):
            await context.send(content=f'I removed the Regex pattern `{name}` from the Database. Bye bye *waves*', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(content=f'Well this sucks, the Regex Pattern by the Name of `{name}` is not in my Database. Oops?', ephemeral=True, delete_after=self._client.Message_Timeout)

    @regex_pattern.command(name='update')
    @role_check()
    @app_commands.autocomplete(name=autocomplete_regex)
    @app_commands.choices(filter_type=[Choice(name='Console', value=0), Choice(name='Events', value=1)])
    async def regex_pattern_update(self, context: commands.Context, name: str, new_name: str = None, filter_type: Choice[int] = None, pattern: str = None):
        """Update a Regex Patterns Name, Pattern and or Type"""
        self._logger.command(f'{context.author.name} used Regex Pattern Update')  # type:ignore

        try:
            re.compile(pattern=pattern)
        except re.error as e:
            self._logger.error(f'Regex Error: {traceback.format_exc()}')
            return await context.send(content=f'The Pattern you provided is invalid. \n `{pattern}`', ephemeral=True, delete_after=self._client.Message_Timeout)

        filter_value = None
        filter_name = None
        content_str = ''
        if filter_type != None:
            filter_value = filter_type.value
            filter_name = filter_type.name
            content_str = f'\n__**Type**__: {filter_name}'

        if self._DB.UpdateRegexPattern(Pattern=pattern, Type=filter_value, Pattern_Name=name, Name=new_name):
            if new_name != None:
                name = new_name

            await context.send(content=f'Updated the Regex - \n__**Name**:__ {name}{content_str}\n __**Pattern**:__ {pattern}', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(content=f'It appears the Name `{name}` does not exist in the Database. Awkward..', ephemeral=True, delete_after=self._client.Message_Timeout)

    @regex_pattern.command(name='list')
    @role_check()
    async def regex_pattern_list(self, context: commands.Context):
        """Displays an Embed list of all Regex patterns"""
        self._logger.command(f'{context.author.name} used Regex Pattern List')  # type:ignore
        regex_patterns: dict[str, dict[str, str]] = self._DB.GetAllRegexPatterns()
        if not regex_patterns:
            return await context.send(content='Hmph.. trying to get a list of Regex Patterns, but you have none yet.. ', ephemeral=True, delete_after=self._client.Message_Timeout)

        embed_field = 0
        embed_list = []
        embed = discord.Embed(title='**Regex Patterns**')
        for pattern in regex_patterns:
            embed_field += 1
            if regex_patterns[pattern]['Type'] == 0:
                pattern_type = 'Console'
            if regex_patterns[pattern]['Type'] == 1:
                pattern_type = 'Events'

            embed.add_field(name=f"__**Name**:__ {regex_patterns[pattern]['Name']}\n__**Type**__: {pattern_type}", value=regex_patterns[pattern]['Pattern'], inline=False)

            if embed_field >= 25:
                embed_list.append(embed)
                embed = discord.Embed(title='**Regex Patterns**')
                embed_field = 1
                continue

            if embed_field >= len(regex_patterns):
                embed_list.append(embed)
                break

        await context.send(embeds=embed_list, ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client):
    await client.add_cog(Regex(client))
