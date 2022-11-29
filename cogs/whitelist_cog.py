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
from datetime import datetime,timedelta,timezone
import os
import logging
import random

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands,tasks

import AMP
import DB
from modules.parser import Parser
import utils
import utils_embeds
import utils_ui


class Whitelist(commands.Cog):
    def __init__(self,client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()

        self.AMPHandler = AMP.getAMPHandler()
       
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        self.eBot = utils_embeds.botEmbeds(client)
        self.Parser = Parser()
        

        self.Whitelist_Channel = None
        
        self.failed_whitelist = []
        self.WL_wait_list = [] # Layout = [{'author': message.author.name, 'msg' : message, 'ampserver' : amp_server, 'dbuser' : db_user}]

        self.uBot.sub_command_handler('server', self.server_whitelist)
    
        self.logger.info(f'**SUCCESS** Initializing {self.name.capitalize()}')

    def __getattribute__(self, __name: str):
        if __name == 'Whitelist_Channel':
            db_get = self.DBConfig.GetSetting('Whitelist_Channel')
            if db_get != None:
                db_get = int(db_get)
            return db_get
        return super().__getattribute__(__name)

    def whitelist_reply_handler(self,message:str, context:commands.Context, server:AMP.AMPInstance=None) -> str:
        """Handles the reply message for the whitelist event\n
        Supports the following: \n
        `<user>` - Uses the Message Author's Name/IGN \n
        `<server>` - Uses the AMP Server Name \n 
        `<guild>` - Uses the Guild Name \n"""
    
        if message.find('<user>') != -1:
            message = message.replace('<user>',context.author.name)
        if message.find('<guild>') != -1:
            message = message.replace('<guild>',context.guild.name)
        if message.find('<server>') != -1 and server is not None:
            server_name = server.FriendlyName
            if server.DisplayName != None: 
                server_name = server.DisplayName
            message = message.replace('<server>',server_name)
        return message

    # Discord Auto Completes ----------------------------------------------------------------------------------------------------------------
    async def autocomplete_servers(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for AMP Instance Names"""
        choice_list = self.AMPHandler.get_AMP_instance_names()
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

    async def autocomplete_whitelist_replies(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Whitelist Replies"""
        choice_list = self.DB.GetAllWhitelistReplies()
        return [app_commands.Choice(name=self.whitelist_reply_formatter(choice), value=self.whitelist_reply_formatter(choice)) for choice in choice_list if current.lower() in choice.lower()]

    def whitelist_reply_formatter(self, parameter:str):
        if len(parameter) > 100:
            return parameter[0:96] + '...'
        return parameter

    # Discord Listener Events --------------------------------------------------------------------------------------------------------------
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self, message_before:discord.Message, message_after:discord.Message):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            #This handles edited whitelist requests!
            if message_before in self.failed_whitelist and message_before.channel.id == self.Whitelist_Channel:
                context = await self._client.get_context(message_before)
                await self.on_message_whitelist(message_after,context)

            self.logger.dev(f'Edited Message Event for {self.name}')
            return message_before,message_after
            
    @commands.Cog.listener('on_message')
    async def on_message(self, message:discord.Message):
        
        #This is purely for testing!
        if message.content.startswith('test_emoji') and message.author.id == 144462063920611328: #This is my Discord ID(k8_thekat)
            if self.DBConfig.Whitelist_emoji_pending != None:
                emoji = self._client.get_emoji(int(self.DBConfig.GetSetting('Whitelist_Emoji_Pending')))
                await message.add_reaction(emoji)
                emoji = self._client.get_emoji(int(self.DBConfig.GetSetting('Whitelist_Emoji_Done')))
                await message.add_reaction(emoji)
       
        if self.Whitelist_Channel is not None and message.author != self._client.user:
            if message.channel.id == self.Whitelist_Channel:  # This is AMP Specific; for handling whitelist requests to any server.
                self.logger.dev(f'On Message Event for {self.name}')
                context = await self._client.get_context(message)
                await self.on_message_whitelist(message, context)
     
    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')
        
        for index in range(0, len(self.WL_wait_list)):
            if member.name == self.WL_wait_list[index]['author']:
                self.WL_wait_list.pop(index)
                self.logger.info(f'Removed {member.name} from Whitelist Wait List.')
                break
       

    #Server Whitelist Commands ------------------------------------------------------------
    @commands.hybrid_group(name='whitelist')
    @utils.role_check()
    async def server_whitelist(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral= True, delete_after= self._client.Message_Timeout)

    @server_whitelist.command(name='true')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def dbserver_whitelist_true(self, context:commands.Context, server):
        """Set Servers Whitelist Allowed to True"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist True...')
     
        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Whitelist = True
            amp_server._setDBattr() #This will update the AMPInstance Attributes
        await context.send(f"Server: **{server}**, Whitelist set to : `True`", ephemeral= True, delete_after= self._client.Message_Timeout)

    @server_whitelist.command(name='false')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def dbserver_whitelist_false(self, context:commands.Context, server):
        """Set Servers Whitelist Allowed to False"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist False...')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Whitelist = False
            amp_server._setDBattr() #This will update the AMPInstance Attributes
        await context.send(f"Server: **{server}**, Whitelist set to : `False`", ephemeral= True, delete_after= self._client.Message_Timeout)

    @server_whitelist.command(name='disabled')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.choices(flag= [Choice(name='False', value= 0), Choice(name='True', value= 1)])
    async def dbserver_whitelist_disabled(self, context:commands.Context, server, flag:Choice[int]):
        """Disables the Servers Whitelist Functionality"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist Disabled...')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Whitelist_disabled = flag.value
            amp_server._setDBattr() #This will update the AMPInstance Attributes
        await context.send(f"Server: **{server}**, Whitelist set to : `{flag.name}`", ephemeral= True, delete_after= self._client.Message_Timeout)

    @server_whitelist.command(name='add')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_whitelist_add(self, context:commands.Context, server, name):
        """Adds User to Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Add...')

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            whitelist = amp_server.addWhitelist(name)
            if whitelist:
                await context.send(f'**{server}**: Whitelisted `{name}`', ephemeral= True, delete_after= self._client.Message_Timeout)
            if whitelist == False:
                await context.send(f'I was unable to find the UUID of that **{name}**', ephemeral= True, delete_after= self._client.Message_Timeout)
            if whitelist == None:
                await context.send(f'Oops, it appears this user is already whitelisted! **{name}** is good to go~', ephemeral= True, delete_after= self._client.Message_Timeout)
            
    @server_whitelist.command(name='remove')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_whitelist_remove(self, context:commands.Context, server, name):
        """Remove a User from the Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Remove...')

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            whitelist = amp_server.removeWhitelist(name= name)
            if whitelist:
                await context.send(f'Oops, it appears this user is not whitelisted! **{name}** is not here~', ephemeral= True, delete_after= self._client.Message_Timeout)
            if whitelist == False:
                await context.send(f'I was unable to find the UUID of that **{name}**', ephemeral= True, delete_after= self._client.Message_Timeout)
            if whitelist == None:
                await context.send(f'**{server}**: Removed `{name}` from the Whitelist', ephemeral= True, delete_after= self._client.Message_Timeout)

    #All DBConfig Whitelist Specific function settings --------------------------------------------------------------
    @commands.hybrid_group(name='whitelist')
    @utils.role_check()
    async def db_bot_whitelist(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral= True, delete_after= self._client.Message_Timeout)

    @db_bot_whitelist.group(name='reply')
    @utils.role_check()
    async def db_bot_whitelist_reply(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral= True, delete_after= self._client.Message_Timeout)

    @db_bot_whitelist_reply.command(name='add')
    @utils.role_check()
    async def db_bot_whitelist_reply_add(self, context:commands.Context, message:str):
        """Add a Reply for the Bot to use during Whitelist Requests"""
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply Add...')

        self.DB.AddWhitelistReply(message)
        await context.send('Woohoo! I can now use a new reply! How does it look?!', ephemeral= True, delete_after= self._client.Message_Timeout)
        message = self.whitelist_reply_handler(message, context)
        await context.send(f'{message}', ephemeral= True, delete_after= self._client.Message_Timeout)
    
    @db_bot_whitelist_reply.command(name='remove')
    @utils.role_check()
    @app_commands.autocomplete(message= autocomplete_whitelist_replies)
    async def db_bot_whitelist_reply_remove(self, context:commands.Context, message:str):
        """Remove a Reply for the Bot to use during Whitelist Requests"""
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply Remove...')
        reply_list = self.DB.GetAllWhitelistReplies()
        for reply in reply_list:
            if message in reply:
                self.DB.DeleteWhitelistReply(reply)
                return await context.send('Awwww! It looks like I can no longer use that reply, shucks~', ephemeral= True, delete_after= self._client.Message_Timeout)
            else:
                continue
        return await context.send('Oops! I can\'t find that reply, sorry~', ephemeral= True, delete_after= self._client.Message_Timeout)
        
    @db_bot_whitelist_reply.command(name='list')
    @utils.role_check()
    async def db_bot_whitelist_reply_list(self, context:commands.Context):
        """List all the Replies for the Bot to use during Whitelist Requests"""
        self.logger.command(f'{context.author.name} used Database Bot Whitelist Reply List...')

        replies = self.DB.GetAllWhitelistReplies()
        await context.send('Here are all the replies I can use:', ephemeral= True, delete_after= self._client.Message_Timeout)
        for reply in replies:
            await context.send(f'{reply}', ephemeral= True, delete_after= self._client.Message_Timeout)
 
    @db_bot_whitelist.command(name='channel')
    @utils.role_check()
    async def db_bot_whitelist_channel_set(self, context:commands.Context, channel:discord.abc.GuildChannel):
        """Sets the Whitelist Channel for the Bot to monitor"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Channel Set...')
    
        self.DBConfig.SetSetting('Whitelist_channel',channel.id)
        await context.send(f'Set Bot Channel Whitelist to **{channel.name}**', ephemeral= True, delete_after= self._client.Message_Timeout)
    
    @db_bot_whitelist.command(name='waittime')
    @utils.role_check()
    @app_commands.describe(time= 'Time in minutes Gatekeeper will wait before handling a Whitelist request.')
    async def db_bot_whitelist_wait_time_set(self, context:commands.Context, time:app_commands.Range[int, 0, 60]= 5):
        """Set Gatekeeper's Whitelist wait time , this value is in minutes!"""
        self.logger.command(f'{context.author.name} used Bot Whitelist wait time Set...')
        
        if time.isnumeric():
            self.DBConfig.Whitelist_wait_time = time
            await context.send(f'Whitelist wait time has been set to **{time} minutes**.', ephemeral= True, delete_after= self._client.Message_Timeout)
        else:
            await context.send('Please use only numbers when setting the wait time. All values are in minutes!', ephemeral= True, delete_after= self._client.Message_Timeout)

    @db_bot_whitelist.command(name='auto')
    @utils.role_check()
    @app_commands.choices(flag= [Choice(name='True', value= 1), Choice(name='False', value= 0)])
    async def db_bot_whitelist_auto_whitelist(self, context:commands.Context, flag:Choice[int]):
        """This turns on or off Auto-Whitelisting"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Auto Whitelist...')
       
        if flag.value.lower() == 'true':
            self.DBConfig.SetSetting('Auto_Whitelist', flag)
            return await context.send('Woohoo! Let me handle all your Whitelisting requests.', ephemeral= True, delete_after= self._client.Message_Timeout)
        if flag.value.lower() == 'false':
            self.DBConfig.SetSetting('Auto_Whitelist', flag)
            return await context.send('Waaah? Looks like I am not handling Whitelisting anymore.', ephemeral= True, delete_after= self._client.Message_Timeout)

    @db_bot_whitelist.command(name='pending_emoji')
    @utils.role_check()
    async def db_bot_whitelist_pending_emjoi_set(self, context:commands.Context):
        """This sets the Whitelist pending emoji, you MUST ONLY use your Servers Emojis'"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Pending Emoji...')
      
        message = await context.send('Please react to this message with the emoji you want for pending Whitelist requests!\n Only use Emojis from this Discord Server!', ephemeral= True, delete_after= self._client.Message_Timeout)
        
        def check(reaction:discord.Reaction, user:discord.Member):
            if self._client.get_emoji(reaction.emoji.id) != None:
                if user == context.author:
                    self.DBConfig.SetSetting('Whitelist_emoji_pending', reaction.emoji.id)
                    return True
            else:
                raise Exception('Emoji not found!')
        try:
            reaction, user = await self._client.wait_for('reaction_add', check=check)
            await message.edit(content = f'Woohoo! Set your **Whitelist Pending Emoji** to {reaction}', ephemeral= True, delete_after= self._client.Message_Timeout)
        except Exception as e:
            self.logger.error(f'Error: {e}')
            await message.edit(content= 'Failed to set the Whitelist done emoji, it must be apart of this Discord Server!', ephemeral= True, delete_after= self._client.Message_Timeout)    

    @db_bot_whitelist.command(name='done_emoji')
    @utils.role_check()
    async def db_bot_whitelist_done_emjoi_set(self, context:commands.Context):
        """This sets the Whitelist completed emoji, you MUST ONLY use your Servers Emojis'"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Done Emoji...')

        message = await context.send('Please react to this message with the emoji you want for completed Whitelist requests!\n Only use Emojis from this Discord Server!', ephemeral= True, delete_after= self._client.Message_Timeout)

        def check(reaction:discord.Reaction, user:discord.Member):
            if self._client.get_emoji(reaction.emoji.id) != None:
                if user == context.author:
                    self.DBConfig.SetSetting('Whitelist_emoji_done', reaction.emoji.id)
                    return True
            else:
                raise Exception('Emoji not found!')
        try:
            reaction, user = await self._client.wait_for('reaction_add', check=check)
            await message.edit(content = f'Woohoo! Set your **Whitelist Pending Emoji** to {reaction}', ephemeral= True, delete_after= self._client.Message_Timeout)
        except Exception as e:
            self.logger.error(f'Error: {e}')
            await message.edit(content= 'Failed to set the Whitelist done emoji, it must be apart of this Discord Server!', ephemeral= True, delete_after= self._client.Message_Timeout)      

    async def on_message_whitelist(self, message:discord.Message, context:commands.Context):
        """This handles on_message whitelist requests."""
        user_ign, user_servers = self.Parser.ParseIGNServer(message.content)
        user_servers = self.Parser.serverName_match(user_servers)

        if user_ign == None and len(user_servers) == 0:
            return
        elif user_ign == None:
            #await message.channel.send('Oops, it appears you are missing some information. Please edit your previous message or send another message with the updated information!',reference= message, ephemeral= True)
            await message.reply('Oops, it appears you are missing some information. Please edit your previous message or send another message with the updated information!')
            self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
            self.failed_whitelist.append(message)
            return
        elif len(user_servers) == 0:
            self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
            self.failed_whitelist.append(message)
            return await message.reply(f'Aww shucks, it looks like your Whitelist request has an invalid server name, please edit your previous message or send another message with the updated information!')#, ephemeral=True)

        self.logger.command(f'Whitelist Request: ign: {user_ign} servers: {user_servers}')
        amp_servers = []

        if not self.DBConfig.GetSetting('Auto_Whitelist'):
            return self.logger.error('Hey a Whitelist request came in, but Auto-Whitelisting is currently disabled!')

        db_user = self.DB.GetUser(context.author.name)
        if db_user == None:
            self.DB.AddUser(DiscordID=context.author.id, DiscordName=context.author.name)

        for server in user_servers:
            index = 0
            amp_server = self.uBot.serverparse(server, message, message.guild.id)

            db_server = self.DB.GetServer(amp_server.InstanceID)
            server_name = amp_server.FriendlyName
            if db_server.DisplayName != None:
                server_name = db_server.DisplayName

            if db_server.Whitelist == False:
                await message.reply(f'Ooops, it appears that the server **{server_name}** has their Whitelisting Closed. If this is an error please contact a Staff Member.')#, ephemeral=True)
                return
            
            if amp_server != None:
                #user_servers.pop(server) #Lets pop off the server we FOUND and replace it with the AMP Server object!
                amp_servers.append(amp_server)    

            if not amp_server.whitelist_intake(context.author, user_ign):
                self.logger.error(f'Failed Whitelist Request, adding {message.author.name} to Failed Whitelist list.')
                self.failed_whitelist.append(message)
                return await message.reply(f'Hey! I am having trouble validating your In-Game Name/Display Name, please edit your previous message or send another message with the correct information!')#, ephemeral=True)
                
            if amp_server.check_Whitelist(context.author) == None:
                self.logger.error(f'Discord User: {message.author.name} is already Whitelisted on {server_name}')
                return await message.reply(f'You are already Whitelisted on **{server_name}**. If this is an error contact Staff, otherwise have fun! <3')#, ephemeral=True)
            
            if db_server.Donator == True:
                author_roles = []
                for role in message.author.roles:
                    author_roles.append(role.id)
                    if self.DBConfig.GetSetting('Donator_Role')!= None:
                        if int(self.DBConfig.GetSetting('Donator_role_id')) not in author_roles:
                            return await message.reply(f'*Waves* Hey **{server_name}** is for Donator Access Only, it appears you do not have Donator. If this is an error please contact a Staff Member.')#, ephemeral=True)
                    else:
                        return await message.reply(f'Well it appears that the Staff have not set a Donator Role yet, Please inform Staff of this error.')#, ephemeral=True)
            
            # This handles Whitelist Delays if set.
           # if self.WL_delay != 0:
            if self.DBConfig.GetSetting('Whitelist_Wait_Time') != 0:
                self.WL_wait_list.append({'author': message.author.name, 'msg': message, 'ampserver': amp_server, 'dbuser': db_user, 'context': context})
                    
                self.logger.command(f'Added {message.author} to Whitelist Wait List.')
                #emoji = self._client.get_emoji(self.WL_Pending_Emoji)
                emoji = self._client.get_emoji(self.DBConfig.GetSetting('Whitelist_Emoji_Pending'))
                if emoji != None:
                    await message.add_reaction(emoji) #This should point to bot_config Emoji

                #Checks if the Tasks is running, if not starts the task.
                if not self.whitelist_waitlist_handler.is_running():
                    self.whitelist_waitlist_handler.start()
                return

            if amp_server.Running and db_server.Whitelist:
                if amp_server.addWhitelist(name= user_ign):
                    whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
                    await message.reply(content= self.whitelist_reply_handler(whitelist_reply, context), embed= await self.uBot.server_whitelist_embed(context, amp_server))#, ephemeral=True)
                    if db_server.Discord_Role != None:
                        discord_role = self.uBot.roleparse(db_server.Discord_Role, context, context.guild.id)
                        await context.author.add_roles(discord_role, reason= 'Auto Whitelisting')

                    #emoji = self._client.get_emoji(self.WL_Finished_Emoji)
                    emoji = self._client.get_emoji(self.DBConfig.GetSetting('Whitelist_Emoji_Done'))
                    if emoji != None:
                        await message.add_reaction(emoji) #This should point to bot_config Emoji

                    self.logger.command(f'Whitelisting {message.author.name} on {amp_server.FriendlyName}')
                    return

    @tasks.loop(seconds=60)
    async def whitelist_waitlist_handler(self):
        """This is the Whitelist Wait list handler, every 60 seconds it will check the list and whitelist them after the alotted wait time."""
        self.logger.command('Checking the Whitelist Wait List...')
        if len(self.WL_wait_list) == 0:
            self.whitelist_waitlist_handler.stop()

        cur_time = datetime.now(timezone.utc)
        try:
            wait_time = timedelta(minutes=self.DBConfig.GetSetting('Whitelist_Wait_Time'))  # This may error if someone changes the wait time to 0 inbetween a loop..
            #wait_time = timedelta(minutes=self.WL_delay)  # This may error if someone changes the wait time to 0 inbetween a loop..
        except Exception:
            wait_time = timedelta(minutes=1)  # Fallback to 1 min delay if somehow the value fails to get parsed.

        for index in range(0,len(self.WL_wait_list)):
            cur_message = self.WL_wait_list[index]

            #This should compare datetime objects and if the datetime of when the message was created plus the wait time is greater than or equal the cur_time they get whitelisted.
            if cur_message['msg'].created_at + wait_time <= cur_time: 
                
                db_server = self.DB.GetServer(cur_message['ampserver'].FriendlyName)
                #This handles all the Discord Role stuff.
                if db_server != None and db_server.Discord_Role != None:
                    discord_role = self.uBot.roleparse(db_server.Discord_Role, cur_message['context'], cur_message['context'].guild_id)
                    discord_user = self.uBot.userparse(cur_message['author'].name, cur_message['context'], cur_message['context'].guild_id)
                    await discord_user.add_roles(discord_role, reason= 'Auto Whitelisting')

                emoji = self._client.get_emoji(self.DBConfig.GetSetting('Whitelist_Emoji_Done'))
                if emoji != None:
                    await cur_message['msg'].add_reaction(emoji) #This should point to bot_config Emoji

                server_embed = await self.eBot.server_whitelist_embed(cur_message['context'], cur_message['ampserver'])
                whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
                await cur_message['msg'].reply(content= self.whitelist_reply_handler(whitelist_reply), embed=server_embed)#, ephemeral=True)

                cur_message['ampserver'].addWhitelist(discord_user = cur_message['context'].author)
                self.logger.command(f'Whitelisting {cur_message["author"]} on {cur_message["ampserver"].FriendlyName}')
                self.WL_wait_list.pop(index)

async def setup(client:commands.Bot):
    await client.add_cog(Whitelist(client))