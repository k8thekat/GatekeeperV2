import traceback
from typing import Union
import os
import sys

import discord
from discord import Interaction, app_commands
from discord.app_commands import Choice
from Gatekeeper import Gatekeeper

from utils.cogs.base_cog import Gatekeeper_Cog
from utils.name_converters import name_to_uuid_MC
from utils.embed import bot_about_embed, bot_settings_embed

from utils.permissions import Gatekeeper_Default_Permissions


class Util_cog(Gatekeeper_Cog):
    gatekeeper_group = app_commands.Group(name="gk",
                                          description="Gatekeepers util command group",
                                          nsfw=False,
                                          default_permissions=Gatekeeper_Default_Permissions,
                                          guild_only=True)
    cog_util_group = app_commands.Group(name="cog",
                                        description="Gatekeepers cog command group",
                                        parent=gatekeeper_group)

    async def autocomplete_loadedcogs(self, interaction: Interaction, current: str) -> list[Choice[str]]:
        """Cog Autocomplete template."""
        choice_list: list[str] = []
        for key in self._client.cogs:
            if key not in choice_list:
                choice_list.append(key)
        return [Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

    # @main_bot.group(name='cog')
    # async def bot_cog(context: commands.Context) -> None:
    #     """Cog Group Commands"""
    #     if context.invoked_subcommand is None:
    #         await context.send('Invalid command passed...', ephemeral=True, delete_after=client.Message_Timeout)

    @cog_util_group.command(name='load')
    async def util_cog_load(self, interaction: Interaction, cog: str) -> None:
        """Load a specific cog, must provide path using '.' as a seperator. eg: 'cogs.my_cog'"""

        try:
            await self._client.load_extension(name=cog)
        except Exception as e:
            await interaction.response.send_message(f'**ERROR** Loading Extension `{cog}` - `{traceback.format_exc()}`', ephemeral=True, delete_after=self._client._message_timeout)
        else:
            await interaction.response.send_message(f'**SUCCESS** Loading Extension `{cog}`', ephemeral=True, delete_after=self._client._message_timeout)

    @cog_util_group.command(name='unload')
    @app_commands.autocomplete(cog=autocomplete_loadedcogs)
    async def util_cog_unload(self, interaction: Interaction, cog: str) -> None:
        """Un-load a specific cog."""

        try:
            my_cog = self._client.cogs[cog]
            await my_cog.cog_unload()
            # await client.unload_extension(name=cog)
        except Exception as e:
            await interaction.response.send_message(f'**ERROR** Un-Loading Extension `{cog}` - `{traceback.format_exc()}`', ephemeral=True, delete_after=self._client._message_timeout)
        else:
            await interaction.response.send_message(f'**SUCCESS** Un-Loading Extension `{cog}`', ephemeral=True, delete_after=self._client._message_timeout)

    @cog_util_group.command(name='reload')
    async def util_cog_reload(self, interaction: Interaction) -> None:
        """Reloads all loaded Cogs inside the cogs folder."""

        await self._client._module_handler.cog_auto_loader(reload=True)
        await interaction.response.send_message(f'**SUCCESS** Reloading All Extensions ', ephemeral=True, delete_after=self._client._message_timeout)

    # @main_bot.group(name='utils')
    # @role_check()
    # async def bot_utils(context: commands.Context) -> None:
    #     if context.invoked_subcommand is None:
    #         await context.send('Invalid command passed...', ephemeral=True, delete_after=client.Message_Timeout)

    @gatekeeper_group.command(name='clear')
    # @app_commands.choices(all=[Choice(name='True', value=1), Choice(name='False', value=0)])
    @app_commands.describe(all='Default\'s to False, removes ALL commands from selected Channel regardless of sender when TRUE.')
    @app_commands.describe(channel='Default\'s to the Channel the command was run; otherwise applies to the channel selected')
    # @role_check()
    async def clear(self, interaction: discord.Interaction, channel: Union[discord.VoiceChannel, discord.TextChannel, discord.Thread, None], amount: app_commands.Range[int, 0, 100] = 15, all: bool = False):
        """Cleans up Messages sent by anyone. Limit 100"""
        await interaction.response.defer()

        assert isinstance(
            interaction.channel, (discord.VoiceChannel, discord.TextChannel, discord.Thread))
        channel = channel or interaction.channel
        messages: list[discord.Message]
        if all:
            messages = await channel.purge(limit=amount, bulk=False)
        else:
            messages = await channel.purge(limit=amount, check=self._client._self_check, bulk=False)

        return await channel.send(f'Cleaned up **{len(messages)} {"messages" if len(messages) > 1 else "message"}**. Wow, look at all this space!', delete_after=self._client._message_timeout)

    @gatekeeper_group.command(name='roleid')
    # @role_check()
    async def roleid(self, interaction: Interaction, role: discord.Role) -> None:
        """Returns the role id for the specified role."""
        await interaction.response.send_message(f'**{role.name}** has the Discord role id of: `{role.id}`', ephemeral=True, delete_after=self._client._message_timeout)

    @gatekeeper_group.command(name='channelid')
    # @role_check()
    async def channelid(self, interaction: Interaction, channel: discord.abc.GuildChannel) -> None:
        """Returns the channel id for the specified channel."""
        await interaction.response.send_message(f'**{channel.name}** has the channel id of: `{channel.id}`', ephemeral=True, delete_after=self._client._message_timeout)

    @gatekeeper_group.command(name='userid')
    # @role_check()
    async def userid(self, interaction: Interaction, user: Union[discord.User, discord.Member]) -> None:
        """Returns the user id for the specified user."""
        await interaction.response.send_message(f'**{user.name} // {user.display_name}** has the user id of: `{user.id}`', ephemeral=True, delete_after=self._client._message_timeout)

    #!TODO! Need to finish developing this command.
    # @bot_utils.command(name='steamid')
    # @utils.role_check()
    # async def bot_utils_steamid(context:commands.Context, name:str):
    #     """Gets the SteamID of the Name provided."""
    #     client._logger.command(f'{context.author.name} used Bot Utils SteamID...') #type:ignore
    #     steam_id = client.uBot.name_to_steam_id(steamname= name)
    #     if steam_id:
    #         await context.send(content= f'**{name}** has the Steam ID of `{steam_id}`', ephemeral= True, delete_after= client.Message_Timeout)
    #     else:
    #         await context.send(content= f'Well I was unable to find that Steam User {name}.', ephemeral= True, delete_after= client.Message_Timeout)

    @gatekeeper_group.command(name='uuid')
    # @role_check()
    async def uuid(self, interaction: Interaction, mc_ign: str) -> None:
        """This will convert a Minecraft IGN to a UUID if it exists"""
        await interaction.response.send_message(f'The UUID of **{mc_ign}** is: `{name_to_uuid_MC(mc_ign)}`', ephemeral=True, delete_after=self._client._message_timeout)

    @gatekeeper_group.command(name='ping')
    # @role_check()
    async def ping(self, interaction: Interaction) -> None:
        """Pong..."""
        await interaction.response.send_message(f'Pong {round(self._client.latency * 1000)}ms', ephemeral=True, delete_after=self._client._message_timeout)

    @gatekeeper_group.command(name='disconnect')
    # @role_check()
    async def stop(self, interaction: Interaction) -> None:
        """Closes the connection to Discord."""
        await interaction.response.send_message('Disconnecting from the Server...', ephemeral=True, delete_after=self._client._message_timeout)
        return await self._client.close()

    @gatekeeper_group.command(name='restart')
    async def restart(self, interaction: Interaction):
        """This is the Gatekeeper restart function\n"""
        await interaction.response.send_message(f'**Currently Restarting the Bot, please wait...**', ephemeral=True, delete_after=self._client._message_timeout)
        sys.stdout.flush()
        os.execv(sys.executable, ['python3'] + sys.argv)

    @gatekeeper_group.command(name='status')
    async def status(self, interaction: Interaction):
        """Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)"""
        await interaction.response.send_message(embed=await bot_about_embed(self._client))
        # await interaction.response.send_message(content= f"""**Discord Version**: {discord.__version__}  //  **Python Version**: {sys.version}\n**Gatekeeperv2 Version**: {Version} // **SQL Database Version**: {client.DBHandler.DB_Version}\n**AMP Connected**: {client.AMPHandler.SuccessfulConnection} // **SQL Database**: {client.DBHandler.SuccessfulDatabase}""", ephemeral= True, delete_after= self._client._message_timeout)

    @gatekeeper_group.command(name='message_timeout')
    @app_commands.describe(time='Default is 60 seconds')
    async def message_timeout(self, interaction: Interaction, time: int = 60):
        """Sets the Delete After time in seconds for ephemeral messages sent from Gatekeeperv2"""

        self._client._DBConfig.SetSetting('Message_Timeout', f'{time}')  # FIXME -- change to lowercase with rework of DB
        self._client._message_timeout = time

        content_str: str = f'will be deleted `{time}` seconds'
        if time == None:
            content_str = f'will no longer be deleted'

        await interaction.response.send_message(content=f'**Ephemeral Messages** {content_str} after being sent.', ephemeral=True, delete_after=self._client._message_timeout)

    @gatekeeper_group.command(name='donator')
    async def bot_donator(self, interaction: Interaction, role: discord.Role) -> None:
        """Sets the Donator Role for Donator Only AMP Server access."""
        self._client._logger.command(f'{context.author.name} used Bot Donator Role...')  # type:ignore
        self._client._DBConfig.SetSetting('Donator_role_id', role.id)
        await interaction.response.send_message(f'You are all set! Donator Role is now set to {role.mention}', ephemeral=True, delete_after=self._client._message_timeout)

    @gatekeeper_group.command(name='settings')
    async def bot_settings(self, interaction: Interaction) -> None:
        """Displays currently set Bot settings"""
        await interaction.response.send_message(embed=bot_settings_embed(interaction=interaction), ephemeral=True, delete_after=(self._client._message_timeout * 3))  # Tripled the delay to help sort times.


async def setup(client: Gatekeeper) -> None:
    await client.add_cog(Util_cog(client))
