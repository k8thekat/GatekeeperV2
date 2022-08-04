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
import os,sys
import asyncio
import logging

#Custom scripts
import logger
import utils
import AMP
import DB

Version = 'beta-1.0.1'
logger = logging.getLogger(__name__)

#Discord Specific
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
prefix = '$'
client = commands.Bot(command_prefix= prefix, intents = intents)
guild_id = None
#command_tree = app_commands.CommandTree(client = client)


@client.event
async def setup_hook():
    await initbot()
    
@client.event
async def on_ready():
    logger.info('Are you the Keymaster?...I am the Gatekeeper')
    if guild_id != None:
        guild = client.get_guild(int(guild_id))
        logger.info(f'Syncing Commands locally to guild: {guild.name}')
        client.tree.copy_global_to(guild=guild)
        await client.tree.sync(guild=guild)
    return

@client.event
async def on_user_update(user_before,user_after):
    logger.info(f'Edited User: {user_before} into {user_after}')
    return user_before,user_after

@client.listen('on_message')
async def on_message(message):
    if message.webhook_id != None:
            return message
    if message.content.startswith(prefix):
        return message
    if message.author != client.user:
        logger.info(f'On Message Event for {os.path.basename(__file__)}')
        return message

    await client.process_commands(message)

@client.event
async def on_message_edit(message_before,message_after):
    """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
    if message_before.author != client.user:
        logger.info(f'Edited Message {os.path.basename(__file__)}: {message_before} into {message_after}')
        return message_before,message_after

@client.event
async def on_reaction_add(reaction,user):
    """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
    logger.info(f'{user} Added the Reaction {os.path.basename(__file__)}: {reaction}')
    return reaction,user

@client.event
async def on_reaction_remove(reaction,user):
    """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
    logger.info(f'{user} Removed the Reaction {os.path.basename(__file__)}: {reaction}')
    return reaction,user

#This is called when a User/Member leaves a Discord Guild. Returns a <member> object.
@client.event
async def on_member_remove(member):
    logger.info(f'Member Removed {os.path.basename(__file__)}: {member}')
    return member

@client.hybrid_group(name='bot')
@utils.role_check()
async def main_bot(context):
    #print('Bot Command')
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...')

@main_bot.command(name='setup')
@commands.has_guild_permissions(administrator=True)
async def bot_setup(context:commands.Context,staff_role):
    #print(context,context.guild.id)
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
    # print(dir(context.interaction))
    # print(dir(context.interaction.followup))
    # print(dir(context.interaction.user))
    # print(dir(context.interaction.guild))
    # print(dir(context.interaction.response))
    # print(dir(context.interaction.message))
    await context.send('Test Function Used')
    #await client.load_extension('modules.cogs.testcog')
    #await client.load_extension('modules.cogs.testcog2')

@main_bot.command(name='ping',description='Pong...')
@utils.role_check()
async def bot_ping(context):
    """Pong.."""
    await context.send(f'Pong {round(client.latency * 1000)}ms')

@main_bot.command(name='load',description='Loads a Cog')
@utils.role_check()
async def bot_cog_loader(context,cog:str):
    """Use this function for loading a cog manually."""
    try:
        client.load_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

@main_bot.command(name='unload',description='Unloads a Cog')
@utils.role_check()
async def bot_cog_unloader(context,cog:str):
    """Use this function to un-load a cog manually."""
    try:
        client.unload_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

@main_bot.command(name='disconnect',description='Closes the connection to Discord')
@utils.role_check()
async def bot_stop(context):
    """Closes the connection to Discord."""
    logger.info('Bot Stop Called...')
    await context.send('Disconnecting from the Server...')
    return await client.close()

@main_bot.command(name='restart',description='Restarts the bot...')
@utils.role_check()
async def bot_restart(context):
    """This is the discordBot restart function\n
    Requires the discordBot to be run in a Command/PowerShell Window ONLY!"""
    logger.info('Bot Restart Called...')
    import os
    import sys
    await context.send(f'**Currently Restarting the Bot, please wait...**')
    sys.stdout.flush()
    os.execv(sys.executable, ['python3'] + sys.argv)

@main_bot.command(name='status',description='Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)')
@utils.role_check()
async def bot_status(context):
    """Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)"""
    await context.send(f'Discord Version: {discord.__version__}  // Bot Version: {Version} // Python Version {sys.version}\nAMP Connected: {main_AMP.AMPHandler.SuccessfulConnection} // SQL Database: {main_DB.DBHandler.SuccessfulDatabase}')

@main_bot.command(name='sync',description='Syncs Bot Commands to the current guild this command was used in.')
@utils.role_check()
async def bot_sync(context):
    """Syncs Bot Commands to the current guild this command was used in."""
    client.tree.copy_global_to(guild=context.guild)
    logger.info(f'Bot Commands Sync: {await client.tree.sync(guild=context.guild)}')
    await context.send('Successfully Syncd Bot Commands')
    
@main_bot.command(name='update',description='Checks for gitHub Updates...')
@utils.role_check()
async def bot_update(context):
    """Checks for gitHub Updates..."""
    #!TODO! Not currently working
    #import dev.gitUpdate as gitUpdate
    #gitUpdate.githubUpdate
    await context.send('Updating the Bot...')

@main_bot.command(name='log',description='Changes the Bot Logging level to specified level')
@utils.role_check()
async def bot_log_level(context,level:str):
    """This needs more Testing, Use this to adjust Logging Level"""
    logger.info(f'Set Logging level %s',level.upper())
    logger.setLevel(level.upper())
    await context.send(f'Adjusted Logging Level to {level.upper()}')


async def initbot():
    """This is the main startup function..."""
    global main_AMP,main_DB,main_DB_Config
    #gitUpdate.init(Version)
    main_DBHandler = DB.getDBHandler()
    main_DB = main_DBHandler.DB
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

def client_start():
    """`*** DO NOT USE ***`"""
    global async_loop
    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)
    async_loop.run_until_complete(client.start(tokens.token, reconnect = True, bot = True))

def client_run(args):
    global guild_id
    guild_id = args.guildID
    logger.info('Bot Intializing...')
    logger.info(f'Discord Version: {discord.__version__}  // Bot Version: {Version} // Python Version {sys.version}')
    client.run(tokens.token, reconnect = True)# bot = True)


#client_run()
