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
from datetime import datetime, timezone
from multiprocessing import Value
from threading import Thread

import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from discord import Message

from utils.banner_creator import Banner_Generator
from utils.check import validate_avatar, serverCheck, role_check
from utils.helper.parser import serverparse
from utils.autocomplete import autocomplete_servers
from utils.cogs.base_cog import Gatekeeper_Cog
from utils.amp_server.embed import server_status_embed, server_info_embed
from utils.amp_server.view import StatusView
from discordBot import Gatekeeper
from DB import DBServer
from AMP import AMPInstance


# This is used to force cog order to prevent missing methods.
Dependencies = None


class AMP_Server(Gatekeeper_Cog):
    def __init__(self, client: Gatekeeper):
        super().__init__(client=client)
        self._AMPThreads: dict[str, Thread] = self._AMPHandler.AMP_Console_Threads
        self._AMPInstances: dict[str, AMPInstance] = self._AMPHandler.AMP_Instances
        self._Banner_Generator: Banner_Generator
        # TODO -- See about implimenting/converting all commands to app_commands.Group()
        #server_group = app_commands.Group(name="server", description="All AMP Server related Commands", guild_only=True, default_permissions=Permissions.general())

    async def autocomplete_regex(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Regex Pattern Names"""
        choice_list: list[str] = []
        regex_patterns: dict[str, dict[str, str]] = self._DB.GetAllRegexPatterns()

        for regex in regex_patterns:
            choice_list.append(regex_patterns[regex]["Name"])
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    async def autocomplete_server_regex(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Regex Pattern Names"""
        choice_list: list[str] = []
        regex_patterns = {}
        if interaction.namespace.server != None:
            db_server: DBServer | None = self._DB.GetServer(InstanceID=interaction.namespace.server)
            if isinstance(db_server, DBServer):
                regex_patterns: dict[str, dict[str, str]] = db_server.GetServerRegexPatterns()

            if len(regex_patterns):
                for regex in regex_patterns:
                    choice_list.append(regex_patterns[regex]["Name"])
            else:
                choice_list.append('None')

        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    @commands.hybrid_group(name="server")
    @role_check()
    async def server(self, context: commands.Context) -> None:
        print()

    @server.command(name='update')
    @role_check()
    async def amp_server_update(self, context: commands.Context) -> None:
        """Updates the bot with any freshly created AMP Instances"""
        new_server: None = self._AMPHandler._instanceValidation(AMP=self._AMP)
        if new_server:
            await context.send(f'Found a new Server: {new_server}', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send('Uhh.. No new instances were found. Hmmm...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='broadcast')
    @role_check()
    @app_commands.choices(prefix=[Choice(name=x, value=x) for x in ['Announcement', 'Broadcast', 'Maintenance', 'Info', 'Warning']])
    async def amp_server_broadcast(self, context: commands.Context, prefix: Choice[str], message: str) -> None:
        """This sends a message to every online AMP Server"""
        discord_message: Message = await context.send('Sending Broadcast...', ephemeral=True)
        for amp_server in self._AMPInstances:
            if self._AMPInstances[amp_server].Running:
                if self._AMPInstances[amp_server]._ADScheck():
                    self._AMPInstances[amp_server].Broadcast_Message(message, prefix=prefix.value)

        await discord_message.edit(content=f'{prefix.value} Sent!')
        await discord_message.delete(delay=self._client.Message_Timeout)


# This section is AMP Server Commands ----------------------------------------------------------------------------------------------------------------------------------------------------------------

    @server.command(name='start')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_start(self, context: commands.Context, server) -> Message | None:
        """Starts an AMP Instance"""
        await context.defer(ephemeral=True)

        amp_server: AMPInstance | None = serverparse(server)
        if isinstance(amp_server, AMPInstance) and not amp_server._ADScheck():
            amp_server.StartInstance()
            amp_server.ADS_Running = True
            await context.send(f'Starting the AMP Dedicated Server **{amp_server.InstanceName}**', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            return await context.send(f'Hmm it appears the server is already `Running..`', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='stop')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_stop(self, context: commands.Context, server) -> Message | None:
        """Stops an AMP Instance"""
        await context.defer(ephemeral=True)

        amp_server = serverCheck(context, server)
        if isinstance(amp_server, AMPInstance) and amp_server._ADScheck():
            amp_server.StopInstance()
            amp_server.ADS_Running = False
            await context.send(f'Stopping the AMP Dedicated Server **{amp_server.InstanceName}**', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            return await context.send(f'Hmm it appears the server is not `Running..`', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='restart')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_restart(self, context: commands.Context, server) -> None:
        """Restarts the AMP Instance"""
        await context.defer(ephemeral=True)

        amp_server = serverCheck(context, server)
        if isinstance(amp_server, AMPInstance):
            amp_server.RestartInstance()
            amp_server.ADS_Running = True
            await context.send(f'Restarting the AMP Dedicated Server **{amp_server.InstanceName}**', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='kill')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_kill(self, context: commands.Context, server) -> None:
        """Kills the AMP Instance"""
        await context.defer(ephemeral=True)

        amp_server = serverCheck(context, server)
        if isinstance(amp_server, AMPInstance):
            amp_server.KillInstance()
            amp_server.ADS_Running = False
            await context.send(f'Killing the AMP Dedicated Server **{amp_server.InstanceName}**', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='msg')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_message(self, context: commands.Context, server, message: str) -> None:
        """Sends a message to the Console, can be anything the Server Console supports.(Commands/Messages)"""

        amp_server = serverCheck(context, server)
        if isinstance(amp_server, AMPInstance):
            amp_server.ConsoleMessage(message)
            await context.send(f'Sent {message} to {amp_server.InstanceName}', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(f'{self._client._emojis.WARNING_SIGN} Failed to send {message} to {server}', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server.command(name='backup')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_backup(self, context: commands.Context, server):
        """Creates a Backup of the Server in its current state, setting the title to the Users display name."""

        amp_server = serverCheck(context, server)
        if isinstance(amp_server, AMPInstance):
            title: str = f"Backup by {context.author.display_name}"
            time = str(datetime.now(tz=timezone.utc))
            description: str = f"Created at {time} by {context.author.display_name}"
            display_description = f'Created at **{str(datetime.now(tz= timezone.utc).strftime("%Y-%m-%d %H:%M"))}**(utc) by **{context.author.display_name}**'
            await context.send(f'{self._client._emojis.FLOPPY_DISK} - Creating a backup of **{server.InstanceName}**  // **Description**: {display_description}', ephemeral=True, delete_after=self._client.Message_Timeout)
            amp_server.takeBackup(title, description)

    @server.command(name='status')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_status(self, context: commands.Context, server) -> Message | None:
        """AMP Instance Status(TPS, Player Count, CPU Usage, Memory Usage and Online Players)"""
        await context.defer(ephemeral=True)

        amp_server: AMPInstance | None = serverparse(server)
        if not isinstance(amp_server, AMPInstance):
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True, delete_after=self._client.Message_Timeout)

        if amp_server.Running == False:
            await context.send(f'Well this is awkward, it appears the **{amp_server.InstanceName}** is `Offline`.', ephemeral=True, delete_after=self._client.Message_Timeout)

        if amp_server._ADScheck():
            server_embed: discord.Embed | None = server_status_embed(context, amp_server)  # FIXME This may need to be adjusted #type:ignore
            status_view = StatusView(context=context, amp_server=amp_server)
            await context.send(embed=server_embed, view=status_view)

        else:
            server_embed: discord.Embed | None = server_status_embed(context, amp_server)  # FIXME This may need to be adjusted #type:ignore
            status_view = StatusView(context=context, amp_server=amp_server)
            await context.send(embed=server_embed, view=status_view)

    @server.command(name='users')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_users_list(self, context: commands.Context, server) -> None:
        """Shows a list of the currently connected Users to the Server."""

        amp_server = serverCheck(context, server)
        if isinstance(amp_server, AMPInstance):
            cur_users = (', ').join(amp_server.getUserList())
            if len(cur_users) != 0:
                await context.send("**Server Users**" + '\n' + cur_users, ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send('The Server currently has no online players.', ephemeral=True, delete_after=self._client.Message_Timeout)

# This Section is AMP/DB Server Settings -----------------------------------------------------------------------------------------------------
    @server.group(name='settings')
    @role_check()
    async def amp_server_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='info')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_settings_info(self, context: commands.Context, server) -> None:
        """Displays Specific Server Information."""

        await context.defer(ephemeral=True)

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            embed = await server_info_embed(amp_server, context)
            await context.send(embed=embed, ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='avatar')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_avatar(self, context: commands.Context, server, url: str) -> Message | None:
        """Sets the Servers Avatar via url. Supports `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated."""
        await context.defer()

        if not url.startswith('http://') and not url.startswith('https://'):
            return await context.send('Ooops, please provide a valid url. It must start with either `http://` or `https://`', ephemeral=True, delete_after=self._client.Message_Timeout)

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(InstanceID=amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Avatar_url = url
            if url == 'None' or len(url) == 0:
                await context.send(f"Removed **{amp_server.InstanceName}** Avatar Icon.", ephemeral=True, delete_after=self._client.Message_Timeout)
                amp_server._setDBattr()
                return
            if isinstance(db_server, DBServer) and await validate_avatar(db_server) != None:
                amp_server._setDBattr()  # This will update the AMPInstance Attributes
                await context.send(f"Set **{amp_server.InstanceName}** Avatar Icon. {url}", ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send(f'I encountered an issue using that url, please try again. Heres your url: {url}', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='displayname')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_displayname(self, context: commands.Context, server, name: str):
        """Sets the Display Name for the provided Server"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(InstanceID=amp_server.InstanceID)
            if isinstance(db_server, DBServer) and db_server.setDisplayName(name) != False:
                amp_server._setDBattr()  # This will update the AMPInstance Attributes
                await context.send(f"Set **{amp_server.InstanceName}** Display Name to `{name}`", ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send(f'The Display Name provided is not unique, this server or another server already has this name.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='host')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_host(self, context: commands.Context, server, hostname: str):
        """Sets the host for the provided Server"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(InstanceID=amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Host = hostname
            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            await context.send(f"Set **{amp_server.InstanceName}** Host to `{hostname}`", ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='donator')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_donator(self, context: commands.Context, server, flag: bool = False):
        """Sets the Donator Only flag for the provided server."""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(InstanceID=amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Donator = flag
            amp_server._setDBattr()  # This will update the AMPConsole Attributes
            return await context.send(f"Set **{amp_server.InstanceName}** Donator Only to `{flag.name if type(flag) == Choice else bool(flag)}`", ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='role')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_discord_role_set(self, context: commands.Context, server, role: discord.Role) -> None:
        """Sets the Discord Role for the provided Server"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Discord_Role = role.id
            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            await context.send(f'Set **{amp_server.InstanceName}** Discord Role to `{role.name}`', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='prefix')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_discord_prefix_set(self, context: commands.Context, server, server_prefix: str) -> None:
        """Sets the Discord Chat Prefix for the provided Server"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Discord_Chat_Prefix = server_prefix
            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            await context.send(f'Set **{amp_server.InstanceName}** Discord Chat Prefix to `{server_prefix}`', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_settings.command(name='hidden')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_hidden(self, context: commands.Context, server, flag: bool) -> Message | None:
        """Hides the server from Banner Display via `/server display`"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(InstanceID=amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Hidden = flag
            amp_server._setDBattr()  # This will update the AMPConsole Attributes
            return await context.send(f"The **{amp_server.InstanceName}** will now be {'Hidden' if flag else 'Shown'}", ephemeral=True, delete_after=self._client.Message_Timeout)

# This section is AMP Server Console Specific Settings -------------------------------------------------------------------------------------------------------------------------------------------------
    @server.group(name='console')
    @role_check()
    async def amp_server_console_settings(self, context: commands.Context) -> None:
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_console_settings.command(name='channel')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_console_channel(self, context: commands.Context, server, channel: discord.abc.GuildChannel) -> None:
        """Sets the Console Channel for the provided Server"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(InstanceID=amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Discord_Console_Channel = channel.id
            amp_server._setDBattr()  # This will update the AMPConsole Attribute
            await context.send(f'Set **{amp_server.InstanceName}** Console channel to {channel.mention}', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_console_settings.command(name='filter')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    @app_commands.choices(filter_type=[Choice(name='Blacklist', value=0), Choice(name='Whitelist', value=1)])
    async def amp_server_console_filter(self, context: commands.Context, server, flag: bool, filter_type: Choice[int]) -> Message | None:
        """Sets the Console Filter type to either Blacklist or Whitelist"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(InstanceID=amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Console_Filtered = flag
            db_server.Console_Filtered_Type = bool(filter_type.value)
            amp_server._setDBattr()  # This will update the AMPConsole Attributes
            return await context.send(f'Set **{amp_server.InstanceName}** Console Filtering to `{flag}` using `{filter_type.name}` filtering.', ephemeral=True, delete_after=self._client.Message_Timeout)

# This section is AMP Server Chat Specific Settings -------------------------------------------------------------------------------------------------------------------------------------------------
    @server.group(name='chat')
    @role_check()
    async def amp_server_chat_settings(self, context: commands.Context) -> None:
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_chat_settings.command(name='channel')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_chat_channel(self, context: commands.Context, server, channel: discord.abc.GuildChannel) -> None:
        """Sets the Chat Channel for the provided Server"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Discord_Chat_Channel = channel.id
            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            await context.send(f'Set **{amp_server.InstanceName}** Chat channel to {channel.mention}', ephemeral=True, delete_after=self._client.Message_Timeout)

# This section is AMP Server Event Specific Settings -------------------------------------------------------------------------------------------------------------------------------------------------
    @server.group(name='event')
    @role_check()
    async def amp_server_event_settings(self, context: commands.Context) -> None:
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_server_event_settings.command(name='channel')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def amp_server_event_channel_set(self, context: commands.Context, server, channel: discord.abc.GuildChannel) -> None:
        """Sets the Event Channel for the provided Server"""

        amp_server = serverCheck(context, server, False)
        if isinstance(amp_server, AMPInstance):
            db_server: DBServer | None = self._DB.GetServer(amp_server.InstanceID)
            if not isinstance(db_server, DBServer):
                raise ValueError('Failed to find a DBServer object')
            db_server.Discord_Event_Channel = channel.id
            amp_server._setDBattr()  # This will update the AMPInstance Attributes
            await context.send(f'Set **{amp_server.InstanceName}** Event channel to {channel.mention}', ephemeral=True, delete_after=self._client.Message_Timeout)

# This section is AMP Server Regex Specific Settings ------------------------------------------------------------------------------------------------------------------------------
    @server.group(name='regex')
    @role_check()
    async def server_regex_settings(self, context: commands.Context) -> None:
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server_regex_settings.command(name='add')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    @app_commands.autocomplete(name=autocomplete_regex)
    async def server_regex_add(self, context: commands.Context, server, name: str) -> None:
        """Adds a Regex Pattern to the Server Regex List."""

        amp_server: AMPInstance | None = serverparse(server)
        if not isinstance(amp_server, AMPInstance):
            raise ValueError('Unable to find the AMP Instance')

        db_server: DBServer | None = self._DB.GetServer(InstanceID=server)
        if db_server == None:
            raise ValueError("Unable to find the DB Server")

        pattern_type: str = "None"
        if db_server != None:
            if db_server.AddServerRegexPattern(Name=name):
                regex: dict[str, str] | bool = self._DB.GetRegexPattern(Name=name)
                if type(regex) == dict and "Type" in regex:
                    if regex['Type'] == 0:
                        pattern_type = 'Console'
                    if regex['Type'] == 1:
                        pattern_type = 'Events'
                else:
                    raise ValueError("Failed to retrieve Regex Pattern")

                await context.send(f'We added the Regex Pattern `{name}` to the `{amp_server.InstanceName}`. \n __**Name**__: {regex["Name"]} \n __**Type**__: {pattern_type} \n __**Pattern**__: {regex["Pattern"]}', ephemeral=True, delete_after=self._client.Message_Timeout)
            else:
                await context.send(f'Uhh, I ran into an issue adding the pattern `{name}` to `{amp_server.InstanceName}`. It looks like the Server already has this pattern.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server_regex_settings.command(name='delete')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    @app_commands.autocomplete(name=autocomplete_server_regex)
    async def server_regex_delete(self, context: commands.Context, server, name) -> None:
        """Deletes a Regex Pattern from the Server Regex List"""

        amp_server: AMPInstance | None = serverparse(server)
        if not isinstance(amp_server, AMPInstance):
            raise ValueError('Unable to find the AMP Instance')

        db_server: DBServer | None = self._DB.GetServer(InstanceID=server)
        if db_server == None:
            raise ValueError("Unable to find the DB Server")

        if db_server.DelServerRegexPattern(Name=name):
            await context.send(f'We Removed the Regex Pattern `{name}` from the `{amp_server.InstanceName}`', ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            await context.send(f'Uhh, I ran into an issue removing the pattern `{name}` to `{amp_server.InstanceName}`', ephemeral=True, delete_after=self._client.Message_Timeout)

    @server_regex_settings.command(name='list')
    @role_check()
    @app_commands.autocomplete(server=autocomplete_servers)
    async def server_regex_list(self, context: commands.Context, server: str) -> Message | None:
        """Displays an Embed list of all the Server Regex patterns."""

        db_server: DBServer | None = self._DB.GetServer(InstanceID=server)
        if db_server == None:
            return

        regex_patterns: dict = {}
        regex_patterns = db_server.GetServerRegexPatterns()
        if not regex_patterns:
            return await context.send(content='Hmph.. trying to get a list of Regex Patterns, but you dont have any yet.. ', ephemeral=True, delete_after=self._client.Message_Timeout)

        embed_field = 0
        embed_list: list[discord.Embed] = []
        embed = discord.Embed(title='**Regex Patterns**')
        pattern_type: str = ""
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


async def setup(client: Gatekeeper) -> None:
    await client.add_cog(AMP_Server(client))
