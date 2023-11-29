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
import sys
import logging
import traceback

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.app_commands import Choice

# Custom scripts
import utils
import utils_embeds
import utils_ui
import AMP_Handler
import DB
from typing import Union

Version = 'beta-4.6.1'


class Gatekeeper(commands.Bot):
    def __init__(self, Version: str):
        self.logger = logging.getLogger()
        self.DBHandler = DB.getDBHandler()
        self.DB = DB.getDBHandler().DB
        self.DBConfig = self.DBHandler.DBConfig

        self.guild_id = None
        if self.DBConfig.GetSetting('Guild_ID') != None:
            self.guild_id = int(self.DBConfig.GetSetting('Guild_ID'))

        self.Bot_Version = self.DBConfig.GetSetting('Bot_Version')
        if self.Bot_Version == None:
            self.DBConfig.SetSetting('Bot_Version', Version)

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = AMP_Handler.getAMPHandler().AMP

        # Discord Specific
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        self.prefix = '$'
        super().__init__(intents=intents, command_prefix=self.prefix)
        self.Message_Timeout = self.DBConfig.Message_timeout
        self.uBot = utils.botUtils(client=self)
        self.uiBot = utils_ui
        self.eBot = utils_embeds.botEmbeds(client=self)

    async def setup_hook(self):
        if self.Bot_Version != Version:
            self.update_loop.start()

        import loader
        self.Handler = loader.Handler(self)
        await self.Handler.module_auto_loader()
        await self.Handler.cog_auto_loader()

        # This Creates the Bot_perms Object and validates the File. Also Adds the Command.
        if self.DBConfig.GetSetting('Permissions') == 'Custom':
            await self.permissions_update()

    def self_check(self, message: discord.Message) -> bool:
        return message.author == client.user

    async def on_command_error(self, context: commands.Context, exception: discord.errors) -> None:
        self.logger.error(f'We ran into an issue. {exception}')
        traceback.print_exception(exception)
        traceback.print_exc()

    async def on_ready(self):
        self.logger.info('Are you the Keymaster?...I am the Gatekeeper')

    @tasks.loop(seconds=30)
    async def update_loop(self):
        self.logger.warn(f'Waiting to Update Bot Version to {Version}...')
        await client.wait_until_ready()
        self.logger.warn(f'Currently Updating Bot Version to {Version}...')
        self.DBConfig.SetSetting('Bot_Version', Version)
        if self.guild_id != None:
            self.tree.copy_global_to(guild=self.get_guild(self.guild_id))
            await self.tree.sync(guild=self.get_guild(self.guild_id))
            self.logger.warn(f'Syncing Commands via update_loop to guild: {self.get_guild(self.guild_id).name} {await self.tree.sync(guild=self.get_guild(self.guild_id))}')
        else:
            self.logger.error(f'It appears I cannot Sync your commands for you, please run {self.prefix}bot utils sync or `/bot utils sync` to update your command tree. Please see the readme if you encounter issues.')
        self.update_loop.stop()

    async def permissions_update(self):
        """Loads the Custom Permission Cog and Validates the File."""
        try:
            await self.load_extension('cogs.Permissions_cog')

        except discord.ext.commands.errors.ExtensionAlreadyLoaded:
            pass

        except Exception as e:
            self.logger.error(f'We ran into an Error Loading the Permissions_Cog. Error - {traceback.format_exc()}')
            return False

        self.bPerms = utils.get_botPerms()
        return True


async def autocomplete_loadedcogs(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Cog Autocomplete template."""
    choice_list = []
    for key in client.cogs:
        if key not in choice_list:
            choice_list.append(key)
    return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

client = Gatekeeper(Version=Version)


@client.hybrid_group(name='bot')
@utils.role_check()
async def main_bot(context: commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...', ephemeral=True, delete_after=client.Message_Timeout)


@main_bot.command(name='donator')
@utils.role_check()
async def bot_donator(context: commands.Context, role: discord.Role):
    """Sets the Donator Role for Donator Only AMP Server access."""
    client.logger.command(f'{context.author.name} used Bot Donator Role...')

    client.DBConfig.SetSetting('Donator_role_id', role.id)
    await context.send(f'You are all set! Donator Role is now set to {role.mention}', ephemeral=True, delete_after=client.Message_Timeout)


@main_bot.command(name='moderator')
@commands.has_guild_permissions(administrator=True)
async def bot_moderator(context: commands.Context, role: discord.Role):
    """Set the Discord Role for Bot Moderation"""
    client.logger.command(f'{context.author.name} used Bot Moderator...')

    client.DBConfig.SetSetting('Moderator_role_id', role.id)
    await context.send(f'Set Moderator Role to `{role.name}`.', ephemeral=True)


@main_bot.command(name='permissions')
@commands.has_guild_permissions(administrator=True)
@app_commands.choices(permission=[Choice(name='Default', value=0), Choice(name='Custom', value=1)])
async def bot_permissions(context: commands.Context, permission: Choice[int]):
    """Set the Bot to use Default Permissions or Custom"""
    client.logger.command(f'{context.author.name} used Bot Permissions...')

    # If we set to 0; we are using `Default` Permissions and need to unload the cog and commands related to custom permissions.
    if permission.value == 0:
        await context.send(f'You have selected `Default` permissions, removing permission commands...', ephemeral=True, delete_after=client.Message_Timeout)
        parent_command = client.get_command('user')
        parent_command.remove_command('role')
        if 'cogs.Permissions_cog' in client.extensions:
            await client.unload_extension('cogs.Permissions_cog')

    # If we set to 1; we are using `Custom` Permissions.
    elif permission.value == 1:
        await context.send(f'You have selected `Custom` permissions, validating `bot_perms.json`', ephemeral=True, delete_after=client.Message_Timeout)
        await context.send(f'Visit https://github.com/k8thekat/GatekeeperV2/blob/main/PERMISSIONS.md', ephemeral=True, delete_after=client.Message_Timeout)
        # This validates the `bot_perms.json` file.
        if not await client.permissions_update():
            return await context.send(f'Error loading the Permissions Cog, please check your Console for errors.', ephemeral=True, delete_after=client.Message_Timeout)

    # Depending on which permissions; this will sync the updated commands available.
    client.tree.copy_global_to(guild=client.get_guild(context.guild.id))
    await client.tree.sync(guild=client.get_guild(context.guild.id))
    client.DBConfig.Permissions = permission.name
    await context.send(f'Finished setting Gatekeeper permissions to `{permission.name}`!', ephemeral=True, delete_after=client.Message_Timeout)


@main_bot.command(name='settings')
@utils.role_check()
async def bot_settings(context: commands.Context):
    """Displays currently set Bot settings"""
    client.logger.command(f'{context.author.name} used Bot Settings...')
    await context.send(embed=client.eBot.bot_settings_embed(context), ephemeral=True, delete_after=(client.Message_Timeout * 3))  # Tripled the delay to help sort times.


@main_bot.group(name='utils')
@utils.role_check()
async def bot_utils(context: commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...', ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='clear')
@app_commands.choices(all=[Choice(name='True', value=1), Choice(name='False', value=0)])
@app_commands.describe(all='Default\'s to False, removes ALL commands from selected Channel regardless of sender when TRUE.')
@app_commands.describe(channel='Default\'s to the Channel the command was run; otherwise applies to the channel selected')
@utils.role_check()
async def bot_utils_clear(context: commands.Context, channel: discord.abc.GuildChannel = None, amount: app_commands.Range[int, 0, 100] = 50, all: Choice[int] = 0):
    """Cleans up Messages sent by the anyone. Limit 100 messages..."""
    client.logger.info(f'{context.author.name} used {context.command.name}...')
    client.context = context
    await context.defer()

    # Setting channel to the channel the command was run in as default.
    if channel == None:
        channel = context.channel

    if type(all) == Choice:
        all = all.value

    if all == 1:
        messages = await channel.purge(limit=amount, bulk=False)
    else:
        messages = await channel.purge(limit=amount, check=client.self_check, bulk=False)

    return await channel.send(f'Cleaned up **{len(messages)} {"messages" if len(messages) > 1 else "message"}**. Wow, look at all this space!', delete_after=client.Message_Timeout)


@bot_utils.command(name='roleid')
@utils.role_check()
async def bot_utils_roleid(context: commands.Context, role: discord.Role):
    """Returns the role id for the specified role."""
    client.logger.command(f'{context.author.name} used Bot Utils Role ID...')

    await context.send(f'**{role.name}** has the Discord role id of: `{role.id}`', ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='channelid')
@utils.role_check()
async def bot_utils_channelid(context: commands.Context, channel: discord.abc.GuildChannel):
    """Returns the channel id for the specified channel."""
    client.logger.command(f'{context.author.name} used Bot Utils Channel ID...')

    await context.send(f'**{channel.name}** has the channel id of: `{channel.id}`', ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='userid')
@utils.role_check()
async def bot_utils_userid(context: commands.Context, user: Union[discord.User, discord.Member]):
    """Returns the user id for the specified user."""
    client.logger.command(f'{context.author.name} used Bot Utils User ID...')

    await context.send(f'**{user.name} // {user.display_name}** has the user id of: `{user.id}`', ephemeral=True, delete_after=client.Message_Timeout)

#!TODO! Need to finish developing this command.
# @bot_utils.command(name='steamid')
# @utils.role_check()
# async def bot_utils_steamid(context:commands.Context, name:str):
#     """Gets the SteamID of the Name provided."""
#     client.logger.command(f'{context.author.name} used Bot Utils SteamID...')
#     steam_id = client.uBot.name_to_steam_id(steamname= name)
#     if steam_id:
#         await context.send(content= f'**{name}** has the Steam ID of `{steam_id}`', ephemeral= True, delete_after= client.Message_Timeout)
#     else:
#         await context.send(content= f'Well I was unable to find that Steam User {name}.', ephemeral= True, delete_after= client.Message_Timeout)


@bot_utils.command(name='uuid')
@utils.role_check()
async def bot_utils_uuid(context: commands.Context, mc_ign: str):
    """This will convert a Minecraft IGN to a UUID if it exists"""
    client.logger.command(f'{context.author.name} used Bot Utils UUID...')

    await context.send(f'The UUID of **{mc_ign}** is: `{client.uBot.name_to_uuid_MC(mc_ign)}`', ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='ping')
@utils.role_check()
async def bot_utils_ping(context: commands.Context):
    """Pong..."""
    client.logger.command(f'{context.author.name} used Bot Ping...')

    await context.send(f'Pong {round(client.latency * 1000)}ms', ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='disconnect')
@utils.role_check()
async def bot_utils_stop(context: commands.Context):
    """Closes the connection to Discord."""
    client.logger.command(f'{context.author.name} used Bot Stop Function...')

    await context.send('Disconnecting from the Server...', ephemeral=True, delete_after=client.Message_Timeout)
    return await client.close()


@bot_utils.command(name='restart')
@utils.role_check()
async def bot_utils_restart(context: commands.Context):
    """This is the Gatekeeper restart function\n"""
    client.logger.command(f'{context.author.name} used Bot Restart Function...')

    import os
    import sys
    await context.send(f'**Currently Restarting the Bot, please wait...**', ephemeral=True, delete_after=client.Message_Timeout)
    sys.stdout.flush()
    os.execv(sys.executable, ['python3'] + sys.argv)


@bot_utils.command(name='status')
@utils.role_check()
async def bot_utils_status(context: commands.Context):
    """Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)"""
    client.logger.command(f'{context.author.name} used Bot Status Function...')

    await context.send(f'**Discord Version**: {discord.__version__}  //  **Python Version**: {sys.version}', ephemeral=True, delete_after=client.Message_Timeout)
    await context.send(f'**Gatekeeperv2 Version**: {Version} // **SQL Database Version**: {client.DBHandler.DB_Version}', ephemeral=True, delete_after=client.Message_Timeout)
    await context.send(f'**AMP Connected**: {client.AMPHandler.SuccessfulConnection} // **SQL Database**: {client.DBHandler.SuccessfulDatabase}', ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='message_timeout')
@utils.role_check()
@app_commands.describe(time='Default is 60 seconds')
async def bot_utils_message_timeout(context: commands.Context, time: Union[None, int] = 60):
    """Sets the Delete After time in seconds for ephemeral messages sent from Gatekeeperv2"""
    client.logger.command(f'{context.author.name} used Bot Utils Message Timeout Function...')

    client.DBConfig.SetSetting('Message_Timeout', f'{time}')
    client.Message_Timeout = time

    content_str = f'will be deleted `{time}` seconds'
    if time == None:
        content_str = f'will no longer be deleted'

    await context.send(content=f'**Ephemeral Messages** {content_str} after being sent.', ephemeral=True, delete_after=client.Message_Timeout)


@bot_utils.command(name='sync')
@utils.role_check()
@app_commands.choices(local=[Choice(name='True', value=1), Choice(name='False', value=0)])
@app_commands.choices(reset=[Choice(name='True', value=1), Choice(name='False', value=0)])
async def bot_utils_sync(context: commands.Context, local: Choice[int] = True, reset: Choice[int] = False):
    """Syncs Bot Commands to the current guild this command was used in."""
    client.logger.command(f'{context.author.name} used Bot Sync Function...')
    await context.defer()
    # This keeps our DB Guild_ID Current.
    if client.guild_id == None or context.guild.id != int(client.guild_id):
        client.DBConfig.SetSetting('Guild_ID', context.guild.id)

    if ((type(reset)) == bool and (reset == True)) or ((type(reset) == Choice) and (reset.value == 1)):
        if ((type(local) == bool) and (local == True)) or ((type(local)) == Choice and (local.value == 1)):
            # Local command tree reset
            client.tree.clear_commands(guild=context.guild)
            client.logger.command(f'Bot Commands Reset Locally and Sync\'d: {await client.tree.sync(guild=context.guild)}')
            return await context.send('**WARNING** Resetting Gatekeeper Commands Locally...', ephemeral=True, delete_after=client.Message_Timeout)

        elif context.author.id == 144462063920611328:
            # Global command tree reset, limited by k8thekat discord ID
            client.tree.clear_commands(guild=None)
            client.logger.command(f'Bot Commands Reset Global and Sync\'d: {await client.tree.sync(guild=None)}')
            return await context.send('**WARNING** Resetting Gatekeeper Commands Globally...', ephemeral=True, delete_after=client.Message_Timeout)
        else:
            return await context.sned('**ERROR** You do not have permission to reset the commands.', ephemeral=True, delete_after=client.Message_Timeout)

    if ((type(local) == bool) and (local == True)) or ((type(local) == Choice) and (local.value == 1)):
        # Local command tree sync
        client.tree.copy_global_to(guild=context.guild)
        client.logger.command(f'Bot Commands Sync\'d Locally: {await client.tree.sync(guild=context.guild)}')
        return await context.send(f'Successfully Sync\'d Gatekeeper Commands to {context.guild.name}...', ephemeral=True, delete_after=client.Message_Timeout)

    elif context.author.id == 144462063920611328:
        # Global command tree sync, limited by k8thekat discord ID
        client.logger.command(f'Bot Commands Sync\'d Globally: {await client.tree.sync(guild=None)}')
        await context.send('Successfully Sync\'d Gatekeeper Commands Globally...', ephemeral=True, delete_after=client.Message_Timeout)


# Cog Specific Bot Commands --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@main_bot.group(name='cog')
@utils.role_check()
async def bot_cog(context: commands.Context):
    """Cog Group Commands"""
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...', ephemeral=True, delete_after=client.Message_Timeout)


@bot_cog.command(name='load')
@utils.role_check()
async def bot_cog_loader(context: commands.Context, cog: str):
    """Load a specific cog, must provide path using '.' as a seperator. eg: 'cogs.my_cog'"""
    client.logger.command(f'{context.author.name} used Bot Cog Load Function...')

    try:
        await client.load_extension(name=cog)
    except Exception as e:
        await context.send(f'**ERROR** Loading Extension `{cog}` - `{traceback.format_exc()}`', ephemeral=True, delete_after=client.Message_Timeout)
    else:
        await context.send(f'**SUCCESS** Loading Extension `{cog}`', ephemeral=True, delete_after=client.Message_Timeout)


@bot_cog.command(name='unload')
@utils.role_check()
@app_commands.autocomplete(cog=autocomplete_loadedcogs)
async def bot_cog_unloader(context: commands.Context, cog: str):
    """Un-load a specific cog."""
    client.logger.command(f'{context.author.name} used Bot Cog Unload Function...')

    try:
        my_cog = client.cogs[cog]
        await my_cog.cog_unload()
        # await client.unload_extension(name=cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension `{cog}` - `{traceback.format_exc()}`', ephemeral=True, delete_after=client.Message_Timeout)
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension `{cog}`', ephemeral=True, delete_after=client.Message_Timeout)


@bot_cog.command(name='reload')
@utils.role_check()
async def bot_cog_reload(context: commands.Context):
    """Reloads all loaded Cogs inside the cogs folder."""
    client.logger.command(f'{context.author.name} used Bot Cog Reload Function...')

    await client.Handler.cog_auto_loader(reload=True)
    await context.send(f'**SUCCESS** Reloading All Extensions ', ephemeral=True, delete_after=client.Message_Timeout)


def client_run(tokens):
    client.logger.info('Gatekeeper v2 Intializing...')
    client.logger.info(f'Discord Version: {discord.__version__}  // Gatekeeper v2 Version: {client.Bot_Version} // Python Version {sys.version}')
    client.run(tokens.token, reconnect=True, log_handler=None)
