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
from discord.ext import commands,tasks
import tokens
import sys
import logging

#Custom scripts
import utils
import AMP
import DB

Version = 'beta-4.0.1'

class Gatekeeper(commands.Bot):
    def __init__(self, Version:str):
        self.logger = logging.getLogger()
        self.DBHandler = DB.getDBHandler()
        self.DB = DB.getDBHandler().DB
        self.DBConfig = self.DB.GetConfig() 
        self.guild_id = self.DBConfig.GetSetting('Guild_ID')

        self.Bot_Version = self.DBConfig.GetSetting('Bot_Version')
        if self.Bot_Version == None:
            self.DBConfig.SetSetting('Bot_Version', Version)

        elif self.Bot_Version != Version:
            self.update_loop.start()

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = AMP.getAMPHandler().AMP
    
        #This validates and checks bot_perms.json()
        if self.DBConfig.GetSetting('Permissions') == 'Custom':
            self.bPerms = utils.get_botPerms()

        #Discord Specific
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        prefix = '$'
        super().__init__(intents= intents, command_prefix= prefix)
        self.uBot = utils.botUtils(self)

    async def setup_hook(self):
        import loader
        Handler = loader.Handler(self)
        await Handler.module_auto_loader()
        await Handler.cog_auto_loader()
    
    async def on_ready(self):
        client.logger.info('Are you the Keymaster?...I am the Gatekeeper')
        
    async def on_guild_join(self, join_guild:discord.Guild):
        client.DBConfig.SetSetting('Guild_ID',join_guild.id)
        client.tree.copy_global_to(guild=join_guild)
        client.logger.info(f'Syncing Commands via on_guild_join locally to guild: {join_guild.name} {await client.tree.sync(guild=join_guild)}')
    
    @tasks.loop(seconds=1, count=1)
    async def update_loop(self):
        self.logger.info(f'Updating Bot Version to {Version}')
        if client.wait_until_ready():
            client.tree.copy_global_to(guild= client.get_guild(client.guild_id))
            await client.tree.sync(guild= client.get_guild(client.guild_id))
            self.logger.info(f'Syncing Commands via update_loop to guild: {client.get_guild(client.guild_id).name} {await client.tree.sync(guild=client.get_guild(client.guild_id))}')

client = Gatekeeper(Version=Version)
    
@client.hybrid_group(name='bot')
@utils.role_check()
async def main_bot(context:commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...')

@main_bot.command(name='moderator')
@commands.has_guild_permissions(administrator=True)
async def bot_moderator(context:commands.Context, role:str):
    """Set the Discord Role for Bot Moderation"""
    client.logger.command(f'{context.author.name} used Bot Moderator...')

    guild_role = client.uBot.roleparse(parameter=role,context=context,guild_id=context.guild.id)
    if guild_role == None:
        await context.send(f'Unable to find role {role}, please try again.')

    if client.DBConfig.GetSetting('Moderator_role_id') == None:
        client.DBConfig.SetSetting('Moderator_role_id', guild_role.id)
        
    await context.send(f'Set Moderator Role to {guild_role.name}.')

@main_bot.command(name='permissions')
@commands.has_guild_permissions(administrator=True)
@app_commands.autocomplete(permission=utils.permissions_autocomplete)
async def bot_permissions(context:commands.Context, permission:str):
    """Set the Bot to use Default Permissions or Custom"""
    client.logger.command(f'{context.author.name} used Bot Permissions...')

    if permission.lower() == 'custom':
        await context.send(f'You have selected Custom Permissions, please make sure bot_perms.json is setup correctly!')
        await context.send(f'Visit https://github.com/k8thekat/GatekeeperV2/blob/main/PERMISSIONS.md')

    client.DBConfig.Permissions = permission
    await context.send(f'Looks like we set Bot Permissions to {permission}!')

@main_bot.command(name='test')
@utils.role_check()
@utils.guild_check(guild_id=602285328320954378)
async def bot_test(context:commands.Context):
    client.logger.command(f'{context.author.name} used Bot Test...')
    """Test Async Function..."""
    await context.send('Test Function Used')

@main_bot.command(name='roleid')
@utils.role_check()
@app_commands.autocomplete(role= utils.autocomplete_discord_roles)
async def bot_roleid(context:commands.Context, role:str):
    """Returns the role id for the specified role."""
    client.logger.command(f'{context.author.name} used Bot Role ID...')

    await context.send(f'**{role}** has the role id of: {client.uBot.roleparse(parameter=role, context=context, guild_id=context.guild.id).id}')

@main_bot.command(name='channelid')
@utils.role_check()
@app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
async def bot_channelid(context:commands.Context, channel:str):
    """Returns the channel id for the specified channel."""
    client.logger.command(f'{context.author.name} used Bot Channel ID...')
    
    await context.send(f'**{channel}** has the channel id of: {client.uBot.channelparse(parameter=channel, context=context, guild_id=context.guild.id).id}')

@main_bot.command(name='userid')
@utils.role_check()
@app_commands.autocomplete(user= utils.autocomplete_discord_users)
async def bot_userid(context:commands.Context, user:str):
    """Returns the user id for the specified user."""
    client.logger.command(f'{context.author.name} used Bot Channel ID...')

    await context.send(f'**{user}** has the user id of: {client.uBot.userparse(parameter=user, context=context, guild_id=context.guild.id).id}')

@main_bot.group(name='embed')
@utils.role_check()
async def bot_embed(context:commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...')

@bot_embed.command(name='auto_update')
@utils.role_check()
@app_commands.autocomplete(flag= utils.autocomplete_bool)
async def bot_embed_auto_update(context:commands.Context, flag:str):
    """Toggles Auto Updating of Embeds On or Off. (Only for `/server Display`)"""
    client.logger.command(f'{context.author.name} used Bot Display Auto...')
    
    client.DBConfig.SetSetting('Embed_Auto_Update', flag)
    if flag.lower() == 'true':
        await context.send(f'All set! The bot will Auto Update the embeds from `/server Display` every minute.')
    if flag.lower() == 'false':
        await context.send(f"Well, I guess I won't update the embeds anymore.")
    else:
        await context.send('Hey! You gotta pick `true` or `false`.')

@main_bot.command(name='ping')
@utils.role_check()
async def bot_ping(context:commands.Context):
    """Pong..."""
    client.logger.command(f'{context.author.name} used Bot Ping...')

    await context.send(f'Pong {round(client.latency * 1000)}ms')

@main_bot.command(name='load')
@utils.role_check()
async def bot_cog_loader(context:commands.Context, cog:str):
    """Use this function for loading a cog manually."""
    client.logger.command(f'{context.author.name} used Bot Cog Load Function...')

    try:
        client.load_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

@main_bot.command(name='unload')
@utils.role_check()
async def bot_cog_unloader(context:commands.Context, cog:str):
    """Use this function to un-load a cog manually."""
    client.logger.command(f'{context.author.name} used Bot Cog Unload Function...')

    try:
        client.unload_extension(name=cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

@main_bot.command(name='disconnect')
@utils.role_check()
async def bot_stop(context:commands.Context):
    """Closes the connection to Discord."""
    client.logger.command(f'{context.author.name} used Bot Stop Function...')

    await context.send('Disconnecting from the Server...')
    return await client.close()

@main_bot.command(name='restart')
@utils.role_check()
async def bot_restart(context:commands.Context):
    """This is the Gatekeeper restart function\n"""
    client.logger.command(f'{context.author.name} used Bot Restart Function...')

    import os
    import sys
    await context.send(f'**Currently Restarting the Bot, please wait...**')
    sys.stdout.flush()
    os.execv(sys.executable, ['python3'] + sys.argv)

@main_bot.command(name='status')
@utils.role_check()
async def bot_status(context:commands.Context):
    """Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)"""
    client.logger.command(f'{context.author.name} used Bot Status Function...')

    await context.send(f'**Discord Version**: {discord.__version__}  // **Gatekeeperv2 Version**: {Version} // **Python Version**: {sys.version}')
    await context.send(f'**SQL Database Version**: {client.DBHandler.DB_Version}')
    await context.send(f'**AMP Connected**: {client.AMPHandler.SuccessfulConnection} // **SQL Database**: {client.DBHandler.SuccessfulDatabase}')

@main_bot.command(name='sync')
@utils.role_check()
@app_commands.autocomplete(reset= utils.autocomplete_bool)
@app_commands.autocomplete(local= utils.autocomplete_bool)
async def bot_sync(context:commands.Context, reset:str='false', local:str='true'):
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
            return await context.send('**WARNING** Resetting Gatekeeper Commands Locally...')

        elif context.author.id == 144462063920611328:
            #Global command tree reset
            client.tree.clear_commands(guild=None)
            client.logger.command(f'Bot Commands Reset Globall and Sync\'d: {await client.tree.sync(guild=None)}')
            return await context.send('**WARNING** Resetting Gatekeeper Commands Globally...')
        else:
            return await context.sned('**ERROR** You do not have permission to reset the commands.')

    if local.lower() == 'true':

        #Local command tree sync
        client.tree.copy_global_to(guild=context.guild)
        client.logger.command(f'Bot Commands Sync\'d Locally: {await client.tree.sync(guild=context.guild)}')
        return await context.send(f'Successfully Sync\'d Gatekeeper Commands to {context.guild.name}...')

    elif context.author.id == 144462063920611328:
        #Global command tree sync
        client.logger.command(f'Bot Commands Sync\'d Globally: {await client.tree.sync(guild=None)}')
        await context.send('Successfully Sync\'d Gatekeeper Commands Globally...')
    
def client_run():
    client.logger.info('Gatekeeper v2 Intializing...')
    client.logger.info(f'Discord Version: {discord.__version__}  // Gatekeeper v2 Version: {client.Bot_Version} // Python Version {sys.version}')
    client.run(tokens.token, reconnect = True, log_handler= None)