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
from datetime import datetime
import discord
from discord.ext import commands
import tokens
import os,sys
import threading
import asyncio
import time
import logging

#Custom scripts
import logger as bot_logger
import bot_config
import gitUpdate
import utils
import modules.AMP as AMP
import modules.database as database

Version = 'alpha-0.0.1'

#Discord Specific
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

prefix = '$'
client = commands.Bot(command_prefix= prefix, intents = intents)
logger = logging.getLogger(__name__)

@client.event
async def on_ready():
    logger.info('Are you the Keymaster?...I am the Gatekeeper')
    #client.is_ready() #Lets wait to start this until the bot has fully setup.
    return

@client.event
async def on_user_update(user_before,user_after):
    logger.info(f'Edited User: {user_before} into {user_after}')
    return user_before,user_after

#This will be my on_message event handler..
@client.listen('on_message')
#@client.event()
async def on_message(message):
    if message.content.startswith(prefix):
        return message
    if message.author == client.user:
        return message
    logger.info(f'On Message Event {os.path.basename(__file__)}: {message}')
    #print(message.content)
    return message

#This is called when a message in any channel of the guild is edited. Returns <message> object.
@client.event
async def on_message_edit(message_before,message_after):
    """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
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

@client.group()
@utils.role_check()
async def bot(context):
    print('Bot Command')
    if context.invoked_subcommand is None:
        await context.send('Invalid command passed...')

@bot.command(name='test',description='Test Async Function...')
async def test(context):
    """ This is my TEST command"""
    logger.setLevel(logger.DEBUG)
    #cog = test_cog(client)
    #await cog.test()
    #client.load_extension('modules.cogs.testcog')
    #import bot_test
    #tBot = bot_test.TestingBot(client)
    #await tBot.test()

@bot.command(name='ping',description='Pong...')
async def bot_ping(context):
    await context.send(f'Pong {round(client.latency * 1000)}ms')

@bot.command(name='load',description='Loads a Cog')
async def bot_cog_loader(self,context,cog:str):
    try:
        self._client.load_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

@bot.command(name='unload',description='Unloads a Cog')
async def bot_cog_unloader(self,context,cog:str):
    try:
        self._client.unload_extension(name= cog)
    except Exception as e:
        await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
    else:
        await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

@bot.command(name='settings',description='Settings to control specific features of the discordBot.')
async def bot_setting(context,*parameter):
    """This will access and house all the bot specific settings."""
    logger.info('Bot Settings Called...')
    return

@bot.command(name='disconnect',description='Closes the connection to Discord')
async def bot_stop(context,*args):
    """Closes the connection to Discord."""
    logger.info('Bot Stop Called...')
    await client.close()

@bot.command(name='restart',description='Restarts the bot...')
async def bot_restart(context,*args):
    """This is the discordBot restart function\n
    Requires the discordBot to be run in a Command/PowerShell Window ONLY!"""
    logger.info('Bot Restart Called...')
    import os
    import sys
    await context.send(f'**Currently Restarting the Bot, please wait...**')
    sys.stdout.flush()
    os.execv(sys.executable, ['python3'] + sys.argv)

@bot.command(name='status',description='Status of the bot...')
async def bot_status(context, *args):
    print('Bot Status')

@bot.command(name='sync',description='Syncs Bot Commands...')
async def bot_sync(context,*args):
    client.tree.copy_global_to(guild=context.guild)
    await client.tree.sync(guild=context.guild)
    
@bot.command(name='update',description='Checks for Updates...')
async def bot_update(context,*args):
    gitUpdate.githubUpdate

@bot.command(name='log',description='Bot Debugging')
async def bot_log_level(context,*args):
    """This needs more Testing, Use this to adjust Logging Level"""
    logger.info(f'Set Logging level %s',args[0].upper())
    logger.setLevel(args[0].upper())

@client.group()
@utils.role_check()
async def user(context):
    if context.invoked_subcommand is None:
        await context.send('Please try your command again...')

@user.command(name='test')
async def userTest(context,user:str=None):
    """User Test Function"""
    print(dir(context))
    logger.info('User Test Function')
    await context.send('User Test')

@user.command(name = 'pardon')
async def userPardon(context,user:str, reason:str=None):
    """Un-Bans a User from the Guild/Server.\n
    Requires a `<user>` discord object.\n
    Supports `reason`(Optional)"""
    logger.info('Removing a Users Ban Status...')
    await context.guild.unban(user,reason)

@user.command(name = 'ban')
async def userBan(context,user:str ,reason:str=None):
    """Bans a User from the Guild/Server.\n
    Requires a `<user>` discord object.\n
    Supports `reason`(Optional)"""
    logger.info('Banning User from Server...')
    await context.guild.ban(user,reason)

@user.command(name = 'kick')
async def userKick(user: str,reason:str=None):
    """Kicks a User from the guild.
    The `<user>` must be a discord user object.\n
    Supports `reason`(Optional)"""
    logger.info('Kick Discord User Called...')
    await client.kick(user,reason)

@client.group()
@utils.role_check()
async def gatekeeper(context):
    if context.invoked_subcommand is None:
        await context.send('Please try your command again...')

@gatekeeper.command(name='test')
async def testing(context):
    logger.info('Gatekeeper Testing Function')

def initbot():
    """This is the main startup function..."""
    global Version
    bot_logger.init()
    logger.info('Bot Intializing...')
    logger.info(f'Discord Version: {discord.__version__}  // Bot Version: {Version} // Python Version {sys.version}')
    #print(f'Bot Intializing...Discord Version: {discord.__version__} Bot Version: {Version}')
    gitUpdate.init(Version)
    main_DB = database.init()
    #!TODO! Currently set to False in database.py
    if main_DB:
        client.load_extension('modules.db_module')

    main_AMP = AMP.init()
    if main_AMP:
        client.load_extension('modules.amp_module')

def bot_test():
    """`*** DO NOT USE ***`"""
    client.load_extension('modules.cogs.testcog')
    client.load_extension('modules.cogs.testcog2')
    #dBot = botclass.discordBot(client)
    #uBot = botclass.botUtils(client)
    #if bot_config.AMP == True:
        #client.load_extension('modules.module')
    import modules.module as module
    testing = threading.Thread(target=module.init, args = (client,))
    #testing = threading.Thread(target=module.ModuleHandler.__init__, args = (client,))
    testing.start()
    #testing = threading.Thread(target = bot_test.__init__,name = 'Test thread',args= (discordBot,botUtils))
    #testing.start()
    #print(async_loop_main)
    #global async_loop_main
    #bot_test.__init__(client)#,async_loop_main)
    #bot_test.test()


async def thread_loop():
    curtime = datetime.now()

def client_start():
    """`*** DO NOT USE ***`"""
    global async_loop
    async_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_loop)
    async_loop.run_until_complete(client.start(tokens.token, reconnect = True, bot = True))

def client_run():
    client.run(tokens.token, reconnect = True)# bot = True)

if __name__ == '__main__':
    initbot()
    bot_test()
    client_run()
