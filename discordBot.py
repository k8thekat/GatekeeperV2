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
import tokens
import sys,os
import logging

#Custom scripts
import logger
import utils
import AMP
import DB

Version = 'beta-1.1.0'
logger = logging.getLogger(__name__)
#logger.info(f'{user} Added the Reaction {os.path.basename(__file__)}: {reaction}')

#Discord Specific
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
prefix = '$'
client = commands.Bot(command_prefix= prefix, intents = intents)

@client.event
async def setup_hook():
    await initbot()
    
@client.event
async def on_ready():
    logger.info('Are you the Keymaster?...I am the Gatekeeper')
    guild_id = DB.getDBHandler().DBConfig.GetSetting('Guild_ID')
    if guild_id != None:
        local_guild = client.get_guild(int(guild_id))
        client.tree.copy_global_to(guild=local_guild)
        logger.info(f'Syncing Commands via on_ready locally to guild: {local_guild.name}')
        await client.tree.sync(guild=local_guild)

@client.event
async def on_guild_join(guild:discord.Guild):
    DB.getDBHandler().DBConfig.SetSetting('Guild_ID',guild.id)
    client.tree.copy_global_to(guild=guild)
    logger.info(f'Syncing Commands via on_guild_join locally to guild: {guild.name}')
    await client.tree.sync(guild=guild)


@client.hybrid_group(name='bot')
@utils.role_check()
async def main_bot(context:commands.Context):
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...')

@main_bot.command(name='setup')
@commands.has_guild_permissions(administrator=True)
async def bot_setup(context:commands.Context,staff_role:str):
    logger.info(f'Bot Setup')
    uBot = utils.botUtils(client)
    guild_role = uBot.roleparse(parameter=staff_role,context=context,guild_id=context.guild.id)
    if guild_role == None:
        await context.send(f'Unable to find role {staff_role}, please try again.')

    if main_DB_Config.Staff_role_id == None:
        main_DB_Config.Staff_role_id = guild_role.id
        
    await context.send(f'Set Staff Role to {guild_role.name}.')
   

@main_bot.command(name='test',description='Test Async Function...')
@utils.role_check()
async def bot_test(context:commands.Context):
    """Test Async Function...**DO NOT USE**"""
    await context.send('Test Function Used')

@main_bot.command(name='ping',description='Pong...')
@utils.role_check()
async def bot_ping(context:commands.Context):
    """Pong.."""
    perm_node = 'bot.ping'
    await context.send(f'Pong {round(client.latency * 1000)}ms')

@main_bot.command(name='load',description='Loads a Cog')
@utils.role_check()
async def bot_cog_loader(context:commands.Context,cog:str):
    """Use this function for loading a cog manually."""
    perm_node = 'bot.cogload'
    try:
        client.load_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

@main_bot.command(name='unload',description='Unloads a Cog')
@utils.role_check()
async def bot_cog_unloader(context:commands.Context,cog:str):
    """Use this function to un-load a cog manually."""
    perm_node = 'bot.cogunload'
    try:
        client.unload_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

@main_bot.command(name='disconnect',description='Closes the connection to Discord')
@utils.role_check()
async def bot_stop(context:commands.Context):
    """Closes the connection to Discord."""
    logger.info('Bot Stop Called...')
    perm_node = 'bot.stop'
    await context.send('Disconnecting from the Server...')
    return await client.close()

@main_bot.command(name='restart',description='Restarts the bot...')
@utils.role_check()
async def bot_restart(context:commands.Context):
    """This is the discordBot restart function\n
    Requires the discordBot to be run in a Command/PowerShell Window ONLY!"""
    logger.info('Bot Restart Called...')
    perm_node = 'bot.restart'
    import os
    import sys
    await context.send(f'**Currently Restarting the Bot, please wait...**')
    sys.stdout.flush()
    os.execv(sys.executable, ['python3'] + sys.argv)

@main_bot.command(name='status',description='Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)')
@utils.role_check()
async def bot_status(context:commands.Context):
    """Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)"""
    logger.info('Bot Status Called...')
    perm_node = 'bot.status'
    await context.send(f'Discord Version: {discord.__version__}  // Bot Version: {Version} // Python Version {sys.version}\nAMP Connected: {main_AMP.AMPHandler.SuccessfulConnection} // SQL Database: {main_DB.DBHandler.SuccessfulDatabase}')

@main_bot.command(name='sync',description='Syncs Bot Commands to the current guild this command was used in.')
@utils.role_check()
async def bot_sync(context:commands.Context):
    """Syncs Bot Commands to the current guild this command was used in."""
    perm_node = 'bot.sync'

    guild_id = DB.getDBHandler().DBConfig.GetSetting('Guild_ID')
    if guild_id == None or context.guild.id != int(guild_id):
        DB.getDBHandler().DBConfig.SetSetting('Guild_ID',context.guild.id)

    client.tree.copy_global_to(guild=context.guild)
    logger.info(f'Bot Commands Sync: {await client.tree.sync(guild=context.guild)}')
    await context.send('Successfully Syncd Bot Commands')
    

async def initbot():
    """This is the main startup function..."""
    global main_AMP,main_DB,main_DB_Config
    main_DB = DB.getDBHandler().DB
    main_DB_Config = main_DB.GetConfig() #Can point to here or main_DBHandler.DBConfig
   
    main_AMPHandler = AMP.getAMPHandler(client)
    main_AMP = main_AMPHandler.AMP

    if main_AMP:
        await client.load_extension('cogs.AMP_cog')

    if main_DB:
        await client.load_extension('cogs.DB_cog')

    import loader
    Handler = loader.Handler(client)
    await Handler.module_auto_loader()
    await Handler.cog_auto_loader()

def client_run():
    logger.info('Bot Intializing...')
    logger.info(f'Discord Version: {discord.__version__}  // Bot Version: {Version} // Python Version {sys.version}')
    client.run(tokens.token, reconnect = True)

