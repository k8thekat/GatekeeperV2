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
import time

import discord
from discord import app_commands
import discord.ext.commands
from discord.ext import commands,tasks
from discord.app_commands import Choice

#Custom scripts
from AMP_Handler import AMPHandler
import DB
from typing import Union

from utils.permissions import Gatekeeper_Permissions
from utils.check import role_check
from utils.name_converters import name_to_uuid_MC
from utils.emojis import Gatekeeper_Emojis

Version = 'beta-4.5.4'

class Gatekeeper(commands.Bot):
    def __init__(self, Version:str):
        self._logger = logging.getLogger()
        self.DBHandler = DB.getDBHandler()
        self.DB = DB.getDBHandler().DB
        self.DBConfig = self.DBHandler.DBConfig

        self.guild_id = None 
        if self.DBConfig.GetSetting('Guild_ID') != None:
            self.guild_id = int(self.DBConfig.GetSetting('Guild_ID'))

        self.Bot_Version = self.DBConfig.GetSetting('Bot_Version')
        if self.Bot_Version == None:
            self.DBConfig.SetSetting('Bot_Version', Version)

        self.AMPHandler = AMPHandler()
        self.AMP = self.AMPHandler.AMP
        #Simple Datastore of Emojis to use.
        self._emojis = Gatekeeper_Emojis()

        #Discord Specific
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        self.prefix: str = '$'
        self._start_time = time.time()
        self._version = Version
        super().__init__(intents= intents, command_prefix= self.prefix)
        self.Message_Timeout: int = self.DBConfig.Message_timeout or 60
        self.uBot = utils.botUtils(client= self)
        self.uiBot = utils_ui
        self.eBot = utils_embeds.botEmbeds(client= self)
        self.Whitelist_wait_list: dict[int, str] = {}

    async def setup_hook(self):
        if self.Bot_Version != Version:
            self.update_loop.start()
            
        import loader
        self.Handler = loader.Handler(self)
        await self.Handler.module_auto_loader()
        await self.Handler.cog_auto_loader()
        

        #This Creates the Bot_perms Object and validates the File. Also Adds the Command.
        if self.DBConfig.GetSetting('Permissions') == 'Custom':
            await self.permissions_update()
    
    def self_check(self, message: discord.Message) -> bool:
        return message.author == client.user
    
    async def on_command_error(self, context:commands.Context, exception: Union[discord.errors.ClientException, discord.errors.Forbidden, discord.errors.DiscordException]) -> None:
        self._logger.error(f'We ran into an issue. {exception}')
        await context.send(content= f'We uhh.. ran into an issue {exception}')
        traceback.print_exception(exception)
        traceback.print_exc()

    async def on_command(self, context: commands.Context) -> None:
        self._logger.command(f'{context.author.name} used {context.command}...') #type:ignore

    async def on_ready(self):
        self._logger.info('Are you the Keymaster?...I am the Gatekeeper')
       
    @tasks.loop(seconds= 30)
    async def update_loop(self):
        self._logger.warn(f'Waiting to Update Bot Version to {Version}...')
        await client.wait_until_ready()
        self._logger.warn(f'Currently Updating Bot Version to {Version}...')
        self.DBConfig.SetSetting('Bot_Version', Version)
        if self.guild_id != None:
            self.tree.copy_global_to(guild= self.get_guild(self.guild_id)) #type:ignore
            await self.tree.sync(guild= self.get_guild(self.guild_id))
            self._logger.warn(f'Syncing Commands via update_loop to guild: {self.get_guild(self.guild_id).name if self.get_guild(self.guild_id)!= None} {await self.tree.sync(guild= self.get_guild(self.guild_id))}')
        else:
            self._logger.error(f'It appears I cannot Sync your commands for you, please run {self.prefix}bot utils sync or `/bot utils sync` to update your command tree. Please see the readme if you encounter issues.')
        self.update_loop.stop()
    
    async def permissions_update(self):
        """Loads the Custom Permission Cog and Validates the File."""
        try:
            await self.load_extension('cogs.Permissions_cog')

        except discord.ext.commands.errors.ExtensionAlreadyLoaded:
            pass
        
        except Exception as e:
            self._logger.error(f'We ran into an Error Loading the Permissions_Cog. Error - {traceback.format_exc()}')
            return False
        
        self._bPerms: Gatekeeper_Permissions = Gatekeeper_Permissions()
        return True

async def autocomplete_loadedcogs(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
    """Cog Autocomplete template."""
    choice_list = []
    for key in client.cogs:
        if key not in choice_list:
            choice_list.append(key)
    return [app_commands.Choice(name= choice, value= choice) for choice in choice_list if current.lower() in choice.lower()]

client: Gatekeeper = Gatekeeper(Version= Version)
    
@client.hybrid_group(name='bot')
@role_check()
async def main_bot(context:commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...', ephemeral=True, delete_after= client.Message_Timeout)

@main_bot.command(name='donator')
@role_check()
async def bot_donator(context:commands.Context, role:discord.Role):
    """Sets the Donator Role for Donator Only AMP Server access."""
    client._logger.command(f'{context.author.name} used Bot Donator Role...') #type:ignore

    client.DBConfig.SetSetting('Donator_role_id', role.id)
    await context.send(f'You are all set! Donator Role is now set to {role.mention}', ephemeral= True, delete_after= client.Message_Timeout)

@main_bot.command(name='moderator')
@commands.has_guild_permissions(administrator= True)
async def bot_moderator(context:commands.Context, role:discord.Role):
    """Set the Discord Role for Bot Moderation"""
    client._logger.command(f'{context.author.name} used Bot Moderator...') #type:ignore

    client.DBConfig.SetSetting('Moderator_role_id', role.id)
    await context.send(f'Set Moderator Role to `{role.name}`.', ephemeral= True)

@main_bot.command(name='permissions')
@commands.has_guild_permissions(administrator= True)
@app_commands.choices(permission= [Choice(name='Default', value= 0), Choice(name='Custom', value= 1)])
async def bot_permissions(context:commands.Context, permission: Choice[int]):
    """Set the Bot to use Default Permissions or Custom"""
    client._logger.command(f'{context.author.name} used Bot Permissions...') #type:ignore

    #If we set to 0; we are using `Default` Permissions and need to unload the cog and commands related to custom permissions.
    if permission.value == 0:
        await context.send(f'You have selected `Default` permissions, removing permission commands...', ephemeral= True, delete_after= client.Message_Timeout)
        parent_command = client.get_command('user')
        if isinstance(parent_command, discord.ext.commands.Group):
            parent_command.remove_command('role')
        if 'cogs.Permissions_cog' in client.extensions:
            await client.unload_extension('cogs.Permissions_cog')

    #If we set to 1; we are using `Custom` Permissions. 
    elif permission.value == 1:
        await context.send(f'You have selected `Custom` permissions, validating `bot_perms.json`', ephemeral= True, delete_after= client.Message_Timeout)
        await context.send(f'Visit https://github.com/k8thekat/GatekeeperV2/blob/main/PERMISSIONS.md', ephemeral= True, delete_after= client.Message_Timeout)
        #This validates the `bot_perms.json` file.
        if not await client.permissions_update():
            return await context.send(f'Error loading the Permissions Cog, please check your Console for errors.', ephemeral= True, delete_after= client.Message_Timeout)

    #Depending on which permissions; this will sync the updated commands available.
    client.tree.copy_global_to(guild= client.get_guild(context.guild.id))
    await client.tree.sync(guild= client.get_guild(context.guild.id))
    client.DBConfig.Permissions = permission.name
    await context.send(f'Finished setting Gatekeeper permissions to `{permission.name}`!', ephemeral= True, delete_after= client.Message_Timeout)

@main_bot.command(name='settings')
@role_check()
async def bot_settings(context:commands.Context):
    """Displays currently set Bot settings"""
    client._logger.command(f'{context.author.name} used Bot Settings...') #type:ignore
    await context.send(embed= client.eBot.bot_settings_embed(context), ephemeral= True, delete_after= (client.Message_Timeout*3)) #Tripled the delay to help sort times.

@main_bot.group(name='utils')
@role_check()
async def bot_utils(context:commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...', ephemeral=True, delete_after= client.Message_Timeout)

@bot_utils.command(name='clear')
@app_commands.choices(all=[Choice(name='True', value=1), Choice(name='False', value=0)])
@app_commands.describe(all='Default\'s to False, removes ALL commands from selected Channel regardless of sender when TRUE.')
@app_commands.describe(channel='Default\'s to the Channel the command was run; otherwise applies to the channel selected')
@role_check()
async def clear(self, interaction: discord.Interaction, channel: Union[discord.VoiceChannel, discord.TextChannel, discord.Thread, None], amount: app_commands.Range[int, 0, 100] = 15, all: bool = False):
    """Cleans up Messages sent by anyone. Limit 100"""
    await interaction.response.defer()

    assert isinstance(
        interaction.channel, (discord.VoiceChannel, discord.TextChannel, discord.Thread))
    channel = channel or interaction.channel  # type:ignore

    if all:
        messages = await channel.purge(limit=amount, bulk=False)
    else:
        messages = await channel.purge(limit=amount, check=self._self_check, bulk=False)

    return await channel.send(f'Cleaned up **{len(messages)} {"messages" if len(messages) > 1 else "message"}**. Wow, look at all this space!', delete_after=self._client._message_timeout)

@bot_utils.command(name='roleid')
@role_check()
async def bot_utils_roleid(context: commands.Context, role: discord.Role):
    """Returns the role id for the specified role."""
    client._logger.command(f'{context.author.name} used Bot Utils Role ID...') #type:ignore

    await context.send(f'**{role.name}** has the Discord role id of: `{role.id}`', ephemeral=True, delete_after= client.Message_Timeout)

@bot_utils.command(name='channelid')
@utils.role_check()
async def bot_utils_channelid(context: commands.Context, channel: discord.abc.GuildChannel):
    """Returns the channel id for the specified channel."""
    client._logger.command(f'{context.author.name} used Bot Utils Channel ID...') #type:ignore
    
    await context.send(f'**{channel.name}** has the channel id of: `{channel.id}`', ephemeral=True, delete_after= client.Message_Timeout)

@bot_utils.command(name='userid')
@role_check()
async def bot_utils_userid(context: commands.Context, user: Union[discord.User, discord.Member]):
    """Returns the user id for the specified user."""
    client._logger.command(f'{context.author.name} used Bot Utils User ID...') #type:ignore

    await context.send(f'**{user.name} // {user.display_name}** has the user id of: `{user.id}`', ephemeral= True, delete_after= client.Message_Timeout)

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

@bot_utils.command(name='uuid')
@role_check()
async def bot_utils_uuid(context:commands.Context, mc_ign:str):
    """This will convert a Minecraft IGN to a UUID if it exists"""
    client._logger.command(f'{context.author.name} used Bot Utils UUID...') #type:ignore

    await context.send(f'The UUID of **{mc_ign}** is: `{name_to_uuid_MC(mc_ign)}`', ephemeral= True, delete_after= client.Message_Timeout)


@bot_utils.command(name='ping')
@role_check()
async def bot_utils_ping(context:commands.Context):
    """Pong..."""
    client._logger.command(f'{context.author.name} used Bot Ping...') #type:ignore

    await context.send(f'Pong {round(client.latency * 1000)}ms', ephemeral= True, delete_after= client.Message_Timeout)

@bot_utils.command(name='disconnect')
@role_check()
async def bot_utils_stop(context:commands.Context):
    """Closes the connection to Discord."""
    client._logger.command(f'{context.author.name} used Bot Stop Function...') #type:ignore

    await context.send('Disconnecting from the Server...', ephemeral= True, delete_after= client.Message_Timeout)
    return await client.close()

@bot_utils.command(name='restart')
@role_check()
async def bot_utils_restart(context:commands.Context):
    """This is the Gatekeeper restart function\n"""
    client._logger.command(f'{context.author.name} used Bot Restart Function...') #type:ignore

    import os
    import sys
    await context.send(f'**Currently Restarting the Bot, please wait...**', ephemeral= True, delete_after= client.Message_Timeout)
    sys.stdout.flush()
    os.execv(sys.executable, ['python3'] + sys.argv)

@bot_utils.command(name='status')
@role_check()
async def bot_utils_status(context:commands.Context):
    """Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)"""
    client._logger.command(f'{context.author.name} used Bot Status Function...') #type:ignore
    await context.send(embed= await client.eBot.bot_about_embed())
    #await context.send(content= f"""**Discord Version**: {discord.__version__}  //  **Python Version**: {sys.version}\n**Gatekeeperv2 Version**: {Version} // **SQL Database Version**: {client.DBHandler.DB_Version}\n**AMP Connected**: {client.AMPHandler.SuccessfulConnection} // **SQL Database**: {client.DBHandler.SuccessfulDatabase}""", ephemeral= True, delete_after= client.Message_Timeout)


@bot_utils.command(name='message_timeout')
@role_check()
@app_commands.describe(time = 'Default is 60 seconds')
async def bot_utils_message_timeout(context:commands.Context, time:Union[None, int]=60):
    """Sets the Delete After time in seconds for ephemeral messages sent from Gatekeeperv2"""
    client._logger.command(f'{context.author.name} used Bot Utils Message Timeout Function...') #type:ignore

    client.DBConfig.SetSetting('Message_Timeout', f'{time}')
    client.Message_Timeout = time

    content_str = f'will be deleted `{time}` seconds'
    if time == None:
        content_str = f'will no longer be deleted'

    await context.send(content= f'**Ephemeral Messages** {content_str} after being sent.', ephemeral= True, delete_after= client.Message_Timeout)


@bot_utils.command(name='sync')
@role_check()
@app_commands.choices(local= [Choice(name='True', value= 1), Choice(name='False', value= 0)])
@app_commands.choices(reset= [Choice(name='True', value= 1), Choice(name='False', value= 0)])
async def bot_utils_sync(context:commands.Context, local: Choice[int]= True, reset: Choice[int]= False):
    """Syncs Bot Commands to the current guild this command was used in."""
    client._logger.command(f'{context.author.name} used Bot Sync Function...') #type:ignore
    await context.defer()
    #This keeps our DB Guild_ID Current.
    if client.guild_id == None or context.guild.id != int(client.guild_id):
        client.DBConfig.SetSetting('Guild_ID',context.guild.id)
    
    if ((type(reset)) == bool and (reset == True)) or ((type(reset) == Choice) and (reset.value == 1)):
        if ((type(local) == bool) and (local == True)) or ((type(local)) == Choice and (local.value == 1)):
            #Local command tree reset
            client.tree.clear_commands(guild=context.guild)
            client._logger.command(f'Bot Commands Reset Locally and Sync\'d: {await client.tree.sync(guild=context.guild)}') #type:ignore
            return await context.send('**WARNING** Resetting Gatekeeper Commands Locally...', ephemeral= True, delete_after= client.Message_Timeout)

        elif context.author.id == 144462063920611328:
            #Global command tree reset, limited by k8thekat discord ID
            client.tree.clear_commands(guild=None)
            client._logger.command(f'Bot Commands Reset Global and Sync\'d: {await client.tree.sync(guild=None)}') #type:ignore
            return await context.send('**WARNING** Resetting Gatekeeper Commands Globally...', ephemeral= True, delete_after= client.Message_Timeout)
        else:
            return await context.sned('**ERROR** You do not have permission to reset the commands.', ephemeral= True, delete_after= client.Message_Timeout)

    if ((type(local) == bool) and (local == True)) or ((type(local) == Choice) and (local.value == 1)):
        #Local command tree sync
        client.tree.copy_global_to(guild=context.guild)
        client._logger.command(f'Bot Commands Sync\'d Locally: {await client.tree.sync(guild=context.guild)}') #type:ignore
        return await context.send(f'Successfully Sync\'d Gatekeeper Commands to {context.guild.name}...', ephemeral= True, delete_after= client.Message_Timeout)

    elif context.author.id == 144462063920611328:
        #Global command tree sync, limited by k8thekat discord ID
        client._logger.command(f'Bot Commands Sync\'d Globally: {await client.tree.sync(guild=None)}') #type:ignore
        await context.send('Successfully Sync\'d Gatekeeper Commands Globally...', ephemeral= True, delete_after= client.Message_Timeout)



#Cog Specific Bot Commands --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@main_bot.group(name='cog')
@role_check()
async def bot_cog(context:commands.Context):
    """Cog Group Commands"""
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...', ephemeral= True, delete_after= client.Message_Timeout)
   

@bot_cog.command(name='load')
@role_check()
async def bot_cog_loader(context:commands.Context, cog:str):
    """Load a specific cog, must provide path using '.' as a seperator. eg: 'cogs.my_cog'"""
    client.logger.command(f'{context.author.name} used Bot Cog Load Function...')

    try:
        await client.load_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Loading Extension `{cog}` - `{traceback.format_exc()}`', ephemeral= True, delete_after= client.Message_Timeout)
    else:
        await context.send(f'**SUCCESS** Loading Extension `{cog}`', ephemeral= True, delete_after= client.Message_Timeout)


@bot_cog.command(name='unload')
@role_check()
@app_commands.autocomplete(cog = autocomplete_loadedcogs)
async def bot_cog_unloader(context:commands.Context, cog: str):
    """Un-load a specific cog."""
    client.logger.command(f'{context.author.name} used Bot Cog Unload Function...')
    
    try:
        my_cog = client.cogs[cog]
        await my_cog.cog_unload()
        #await client.unload_extension(name=cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension `{cog}` - `{traceback.format_exc()}`', ephemeral= True, delete_after= client.Message_Timeout)
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension `{cog}`', ephemeral= True, delete_after= client.Message_Timeout)


@bot_cog.command(name='reload')
@role_check()
async def bot_cog_reload(context:commands.Context):
    """Reloads all loaded Cogs inside the cogs folder."""
    client.logger.command(f'{context.author.name} used Bot Cog Reload Function...')

    await client.Handler.cog_auto_loader(reload= True)
    await context.send(f'**SUCCESS** Reloading All Extensions ', ephemeral= True, delete_after= client.Message_Timeout) 


def client_run(tokens):
    client.logger.info('Gatekeeper v2 Intializing...')
    client.logger.info(f'Discord Version: {discord.__version__}  // Gatekeeper v2 Version: {client.Bot_Version} // Python Version {sys.version}')
    client.run(tokens.token, reconnect = True, log_handler= None)