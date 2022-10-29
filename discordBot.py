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
from discord.ext import commands,tasks
import tokens
import sys
import logging

#Custom scripts
import utils
import AMP
import DB

Version = 'beta-4.2.2'

class Gatekeeper(commands.Bot):
    def __init__(self, Version:str):
        self.logger = logging.getLogger()
        self.DBHandler = DB.getDBHandler()
        self.DB = DB.getDBHandler().DB
        self.DBConfig = self.DB.GetConfig()

        self.guild_id = None 
        if self.DBConfig.GetSetting('Guild_ID') != None:
            self.guild_id = int(self.DBConfig.GetSetting('Guild_ID'))

        self.Bot_Version = self.DBConfig.GetSetting('Bot_Version')
        if self.Bot_Version == None:
            self.DBConfig.SetSetting('Bot_Version', Version)

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = AMP.getAMPHandler().AMP
    
        #This validates and checks bot_perms.json()
        if self.DBConfig.GetSetting('Permissions') == 'Custom':
            self.bPerms = utils.get_botPerms()

        #Discord Specific
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        self.prefix = '$'
        super().__init__(intents= intents, command_prefix= self.prefix)
        self.uBot = utils.botUtils(client=self)

    async def setup_hook(self):
        if self.Bot_Version != Version:
            self.update_loop.start()

        import loader
        Handler = loader.Handler(self)
        await Handler.module_auto_loader()
        await Handler.cog_auto_loader()
    
    async def on_ready(self):
        self.logger.info('Are you the Keymaster?...I am the Gatekeeper')
        
    # async def on_guild_join(self, join_guild:discord.Guild):
    #     self.DBConfig.SetSetting('Guild_ID',join_guild.id)
    #     self.tree.copy_global_to(guild=join_guild)
    #     self.logger.info(f'Syncing Commands via on_guild_join locally to guild: {join_guild.name} {await self.tree.sync(guild=join_guild)}')
    
    @tasks.loop(seconds= 30)
    async def update_loop(self):
        self.logger.info(f'Waiting to Update Bot Version to {Version}...')
        await client.wait_until_ready()
        self.logger.info(f'Currently Updatting Bot Version to {Version}...')
        self.DBConfig.SetSetting('Bot_Version', Version)
        if self.guild_id != None:
            self.tree.copy_global_to(guild= self.get_guild(self.guild_id))
            await self.tree.sync(guild= self.get_guild(self.guild_id))
            self.logger.info(f'Syncing Commands via update_loop to guild: {self.get_guild(self.guild_id).name} {await self.tree.sync(guild= self.get_guild(self.guild_id))}')
        else:
            self.logger.error(f'It appears I cannot Sync your commands for you, please run {self.prefix}bot sync or `/bot sync` to update your command tree. Please see the readme if you encounter issues.')
        self.update_loop.stop()
    
#This is my Template for Autocomplete
async def autocomplete_loadedcogs(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
    """Default Autocomplete template, simply pass in a list of strings and it will handle it."""
    choice_list = []
    for key in client.cogs:
        if key not in choice_list:
            choice_list.append(key)
    return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

client = Gatekeeper(Version=Version)
    
@client.hybrid_group(name='bot')
@utils.role_check()
async def main_bot(context:commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...', ephemeral=True)

@main_bot.command(name='moderator')
@commands.has_guild_permissions(administrator=True)
async def bot_moderator(context:commands.Context, role:str):
    """Set the Discord Role for Bot Moderation"""
    client.logger.command(f'{context.author.name} used Bot Moderator...')

    guild_role = client.uBot.roleparse(parameter=role,context=context,guild_id=context.guild.id)
    if guild_role == None:
        await context.send(f'Unable to find role {role}, please try again.', ephemeral=True)

    if client.DBConfig.GetSetting('Moderator_role_id') == None:
        client.DBConfig.SetSetting('Moderator_role_id', guild_role.id)
        
    await context.send(f'Set Moderator Role to {guild_role.name}.', ephemeral=True)

@main_bot.command(name='permissions')
@commands.has_guild_permissions(administrator=True)
@app_commands.autocomplete(permission=utils.permissions_autocomplete)
async def bot_permissions(context:commands.Context, permission:str):
    """Set the Bot to use Default Permissions or Custom"""
    client.logger.command(f'{context.author.name} used Bot Permissions...')

    if permission.lower() == 'custom':
        await context.send(f'You have selected Custom Permissions, please make sure bot_perms.json is setup correctly!', ephemeral=True)
        await context.send(f'Visit https://github.com/k8thekat/GatekeeperV2/blob/main/PERMISSIONS.md', ephemeral=True)

    client.DBConfig.Permissions = permission
    await context.send(f'Looks like we set Bot Permissions to {permission}!', ephemeral=True)

@main_bot.command(name='settings')
@utils.role_check()
async def bot_settings(context:commands.Context):
    """Displays currently set Bot settings"""
    client.logger.command(f'{context.author.name} used Bot Settings...')

    dbsettings_list = client.DBConfig.GetSettingList()
    settings_list = []
    for setting in dbsettings_list:
        config = client.DBConfig.GetSetting(setting)
        settings_list.append({f'{setting.capitalize()}': f'{str(config)}'})
    await context.send(embed=client.uBot.bot_settings_embed(context, settings_list), ephemeral=True)

@main_bot.command(name='test')
@utils.role_check()
@utils.guild_check(guild_id=602285328320954378)
async def bot_test(context:commands.Context):
    client.logger.command(f'{context.author.name} used Bot Test...')
    """Test Async Function..."""
    await context.send('Test Function Used', ephemeral=True)

@main_bot.command(name='roleid')
@utils.role_check()
@app_commands.autocomplete(role= utils.autocomplete_discord_roles)
async def bot_roleid(context:commands.Context, role:str):
    """Returns the role id for the specified role."""
    client.logger.command(f'{context.author.name} used Bot Role ID...')

    await context.send(f'**{role}** has the role id of: {client.uBot.roleparse(parameter=role, context=context, guild_id=context.guild.id).id}', ephemeral=True)

@main_bot.command(name='channelid')
@utils.role_check()
@app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
async def bot_channelid(context:commands.Context, channel:str):
    """Returns the channel id for the specified channel."""
    client.logger.command(f'{context.author.name} used Bot Channel ID...')
    
    await context.send(f'**{channel}** has the channel id of: {client.uBot.channelparse(parameter=channel, context=context, guild_id=context.guild.id).id}', ephemeral=True)

@main_bot.command(name='userid')
@utils.role_check()
@app_commands.autocomplete(user= utils.autocomplete_discord_users)
async def bot_userid(context:commands.Context, user:str):
    """Returns the user id for the specified user."""
    client.logger.command(f'{context.author.name} used Bot Channel ID...')

    await context.send(f'**{user}** has the user id of: {client.uBot.userparse(parameter=user, context=context, guild_id=context.guild.id).id}', ephemeral=True)

@main_bot.group(name='embed')
@utils.role_check()
async def bot_embed(context:commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...', ephemeral=True)

@bot_embed.command(name='auto_update')
@utils.role_check()
@app_commands.autocomplete(flag= utils.autocomplete_bool)
async def bot_embed_auto_update(context:commands.Context, flag:str):
    """Toggles Auto Updating of Embeds On or Off. (Only for `/server Display`)"""
    client.logger.command(f'{context.author.name} used Bot Display Auto...')
    
    if flag.lower() == 'true':
        client.DBConfig.SetSetting('Embed_Auto_Update', True)
        return await context.send(f'All set! The bot will Auto Update the embeds from `/server display` every minute.', ephemeral=True)
    if flag.lower() == 'false':
        client.DBConfig.SetSetting('Embed_Auto_Update', False)
        return await context.send(f"Well, I guess I won't update the embeds anymore.", ephemeral=True)
    else:
        return await context.send('Hey! You gotta pick `True` or `False`.', ephemeral=True)

@main_bot.command(name='ping')
@utils.role_check()
async def bot_ping(context:commands.Context):
    """Pong..."""
    client.logger.command(f'{context.author.name} used Bot Ping...')

    await context.send(f'Pong {round(client.latency * 1000)}ms', ephemeral=True)

@main_bot.command(name='load')
@utils.role_check()
async def bot_cog_loader(context:commands.Context, cog:str):
    """Use this function for loading a cog manually."""
    client.logger.command(f'{context.author.name} used Bot Cog Load Function...')

    try:
        client.load_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}', ephemeral=True)
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}', ephemeral=True)

@main_bot.command(name='unload')
@utils.role_check()
@app_commands.autocomplete(cog = autocomplete_loadedcogs)
async def bot_cog_unloader(context:commands.Context, cog:str):
    """Use this function to un-load a cog manually."""
    client.logger.command(f'{context.author.name} used Bot Cog Unload Function...')

    try:
        client.unload_extension(name=cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}', ephemeral=True)
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}', ephemeral=True)

@main_bot.command(name='disconnect')
@utils.role_check()
async def bot_stop(context:commands.Context):
    """Closes the connection to Discord."""
    client.logger.command(f'{context.author.name} used Bot Stop Function...')

    await context.send('Disconnecting from the Server...', ephemeral=True)
    return await client.close()

@main_bot.command(name='restart')
@utils.role_check()
async def bot_restart(context:commands.Context):
    """This is the Gatekeeper restart function\n"""
    client.logger.command(f'{context.author.name} used Bot Restart Function...')

    import os
    import sys
    await context.send(f'**Currently Restarting the Bot, please wait...**', ephemeral=True)
    sys.stdout.flush()
    os.execv(sys.executable, ['python3'] + sys.argv)

@main_bot.command(name='status')
@utils.role_check()
async def bot_status(context:commands.Context):
    """Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)"""
    client.logger.command(f'{context.author.name} used Bot Status Function...')

    await context.send(f'**Discord Version**: {discord.__version__}  //  **Python Version**: {sys.version}', ephemeral=True)
    await context.send(f'**Gatekeeperv2 Version**: {Version} // **SQL Database Version**: {client.DBHandler.DB_Version}', ephemeral=True)
    await context.send(f'**AMP Connected**: {client.AMPHandler.SuccessfulConnection} // **SQL Database**: {client.DBHandler.SuccessfulDatabase}', ephemeral=True)

@main_bot.command(name='sync')
@utils.role_check()
@app_commands.autocomplete(reset= utils.autocomplete_bool)
@app_commands.autocomplete(local= utils.autocomplete_bool)
async def bot_sync(context:commands.Context, local:str='true', reset:str='false'):
    """Syncs Bot Commands to the current guild this command was used in."""
    client.logger.command(f'{context.author.name} used Bot Sync Function...')
    await context.defer()
    #This keeps our DB Guild_ID Current.
    if client.guild_id == None or context.guild.id != int(client.guild_id):
        client.DBConfig.SetSetting('Guild_ID',context.guild.id)
    
    if reset.lower() == 'true':
        if local.lower() == 'true':
            #Local command tree reset
            client.tree.clear_commands(guild=context.guild)
            client.logger.command(f'Bot Commands Reset Locally and Sync\'d: {await client.tree.sync(guild=context.guild)}')
            return await context.send('**WARNING** Resetting Gatekeeper Commands Locally...', ephemeral=True)

        elif context.author.id == 144462063920611328:
            #Global command tree reset
            client.tree.clear_commands(guild=None)
            client.logger.command(f'Bot Commands Reset Globall and Sync\'d: {await client.tree.sync(guild=None)}')
            return await context.send('**WARNING** Resetting Gatekeeper Commands Globally...', ephemeral=True)
        else:
            return await context.sned('**ERROR** You do not have permission to reset the commands.', ephemeral=True)

    if local.lower() == 'true':
        #Local command tree sync
        client.tree.copy_global_to(guild=context.guild)
        client.logger.command(f'Bot Commands Sync\'d Locally: {await client.tree.sync(guild=context.guild)}')
        return await context.send(f'Successfully Sync\'d Gatekeeper Commands to {context.guild.name}...', ephemeral=True)

    elif context.author.id == 144462063920611328:
        #Global command tree sync
        client.logger.command(f'Bot Commands Sync\'d Globally: {await client.tree.sync(guild=None)}')
        await context.send('Successfully Sync\'d Gatekeeper Commands Globally...', ephemeral=True)
    
def client_run():
    client.logger.info('Gatekeeper v2 Intializing...')
    client.logger.info(f'Discord Version: {discord.__version__}  // Gatekeeper v2 Version: {client.Bot_Version} // Python Version {sys.version}')
    client.run(tokens.token, reconnect = True, log_handler= None)