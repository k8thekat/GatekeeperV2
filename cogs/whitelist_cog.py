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
from datetime import datetime, timedelta, timezone
import os
import logging
import random

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks

import AMP
import DB

import utils
import utils_embeds
import utils_ui

class Whitelist(commands.Cog):
    def __init__(self,client:discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()

        self.AMPHandler = AMP.getAMPHandler()
       
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.uiBot = utils_ui
        self.dBot = utils.discordBot(client)
        self.eBot = utils_embeds.botEmbeds(client)

        self.Whitelist_Request_Channel = None
        
        self.failed_whitelist = []
        self._client.Whitelist_wait_list = {} #[message.id] : {'ampserver' : amp_server, 'context' : context, 'dbuser' : db_user}

        self.uBot.sub_command_handler('server', self.server_whitelist)
    
        self.logger.info(f'**SUCCESS** Initializing {self.name.capitalize()}')

    def __getattribute__(self, __name: str):
        if __name == 'Whitelist__Request_Channel':
            db_get = self.DBConfig.GetSetting('Whitelist_Request_Channel')
            if db_get != None:
                db_get = int(db_get)
            return db_get
        return super().__getattribute__(__name)

    # Discord Auto Completes ---------------------------------------------------------------------------------------------------------------
    async def autocomplete_whitelist_replies(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for Whitelist Replies"""
        choice_list = self.DB.GetAllWhitelistReplies()
        return [app_commands.Choice(name=self.whitelist_reply_formatter(choice), value=self.whitelist_reply_formatter(choice)) for choice in choice_list if current.lower() in choice.lower()]

    def whitelist_reply_formatter(self, parameter:str):
        if len(parameter) > 100:
            return parameter[0:96] + '...'
        return parameter

    # Discord Listener Events -------------------------------------------------------------------------------------------------------------
    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')
        
        for key, value in self._client.Whitelist_wait_list.items():
            if member.id == value['context'].message.author.id:
                self._client.Whitelist_wait_list.pop(key)
                self.logger.info(f'Removed {member.name} from Whitelist Wait List.')
       
    #Server Whitelist Commands ------------------------------------------------------------
    @commands.hybrid_group(name='whitelist')
    @utils.role_check()
    async def server_whitelist(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral= True, delete_after= self._client.Message_Timeout)

    @server_whitelist.command(name='true')
    @utils.role_check()
    @app_commands.autocomplete(server= utils.autocomplete_servers)
    async def dbserver_whitelist_true(self, context:commands.Context, server):
        """Set Servers Whitelist Allowed to True"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist True...')
     
        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Whitelist = True
            amp_server._setDBattr() #This will update the AMPInstance Attributes
        await context.send(f"Server: **{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}**, Whitelist set to : `True`", ephemeral= True, delete_after= self._client.Message_Timeout)

    @server_whitelist.command(name='false')
    @utils.role_check()
    @app_commands.autocomplete(server= utils.autocomplete_servers)
    async def dbserver_whitelist_false(self, context:commands.Context, server):
        """Set Servers Whitelist Allowed to False"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist False...')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Whitelist = False
            amp_server._setDBattr() #This will update the AMPInstance Attributes
        await context.send(f"Server: **{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}**, Whitelist set to : `False`", ephemeral= True, delete_after= self._client.Message_Timeout)

    @server_whitelist.command(name='disabled')
    @utils.role_check()
    @app_commands.autocomplete(server= utils.autocomplete_servers)
    @app_commands.choices(flag= [Choice(name='False', value= 0), Choice(name='True', value= 1)])
    async def dbserver_whitelist_disabled(self, context:commands.Context, server, flag:Choice[int]):
        """Disables the Servers Whitelist Functionality"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist Disabled...')

        amp_server = await self.uBot._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Whitelist_disabled = flag.value
            amp_server._setDBattr() #This will update the AMPInstance Attributes
        await context.send(f"Server: **{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}**, Whitelist set to : `{flag.name}`", ephemeral= True, delete_after= self._client.Message_Timeout)

    @server_whitelist.command(name='add')
    @utils.role_check()
    @app_commands.autocomplete(server= utils.autocomplete_servers)
    async def amp_server_whitelist_add(self, context:commands.Context, server, name):
        """Adds User to Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Add...')

        amp_server = await self.uBot._serverCheck(context, server)
        if amp_server:
            whitelist = amp_server.addWhitelist(name)
            if whitelist:
                await context.send(f'**{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}**: Whitelisted `{name}`', ephemeral= True, delete_after= self._client.Message_Timeout)
            if whitelist == False:
                await context.send(f'I was unable to find the UUID of that **{name}**', ephemeral= True, delete_after= self._client.Message_Timeout)
            if whitelist == None:
                await context.send(f'Oops, it appears this user is already whitelisted! **{name}** is good to go~', ephemeral= True, delete_after= self._client.Message_Timeout)
            
    @server_whitelist.command(name='remove')
    @utils.role_check()
    @app_commands.autocomplete(server= utils.autocomplete_servers)
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
                await context.send(f'**{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}**: Removed `{name}` from the Whitelist', ephemeral= True, delete_after= self._client.Message_Timeout)

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
        message = self.uBot.whitelist_reply_handler(message, context)
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
 
    @db_bot_whitelist.command(name='request_channel')
    @utils.role_check()
    async def db_bot_whitelist_request_channel_set(self, context:commands.Context, channel:discord.abc.GuildChannel):
        """Sets the Whitelist Request Channel for the Bot to send Whitelist Requests for Staff Approval"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Channel Set...')
    
        self.DBConfig.SetSetting('Whitelist_request_channel',channel.id)
        await context.send(f'Set Bot Whitelist Request Channel to **{channel.name}**', ephemeral= True, delete_after= self._client.Message_Timeout)
    
    @db_bot_whitelist.command(name='wait_time')
    @utils.role_check()
    @app_commands.describe(time= 'Time in minutes Gatekeeper will wait before handling a Whitelist request.')
    async def db_bot_whitelist_wait_time_set(self, context: commands.Context, time: app_commands.Range[int, 0, 60]= 5):
        """Set Gatekeeper's Whitelist wait time , this value is in minutes!"""
        self.logger.command(f'{context.author.name} used Bot Whitelist wait time Set...')
        self.DBConfig.Whitelist_wait_time = time
        await context.send(f'Whitelist wait time has been set to **{time} {"minutes" if time > 1 else "minute"}**.', ephemeral= True, delete_after= self._client.Message_Timeout)
        
    @db_bot_whitelist.command(name='auto')
    @utils.role_check()
    @app_commands.choices(flag= [Choice(name='True', value= 1), Choice(name='False', value= 0)])
    async def db_bot_whitelist_auto_whitelist(self, context:commands.Context, flag:Choice[int]):
        """This turns on or off Auto-Whitelisting"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Auto Whitelist...')
       
        if flag.value == 1:
            self.DBConfig.SetSetting('Auto_Whitelist', flag.value)
            return await context.send('Woohoo! Let me handle all your Whitelisting needs.', ephemeral= True, delete_after= self._client.Message_Timeout)
        if flag.value == 0:
            self.DBConfig.SetSetting('Auto_Whitelist', flag.value)
            return await context.send('Waaah? Looks like I am not handling Whitelisting anymore.', ephemeral= True, delete_after= self._client.Message_Timeout)

    @db_bot_whitelist.command(name= 'request')
    @app_commands.autocomplete(server = utils.autocomplete_servers)
    async def db_bot_whitelist_request(self, context:commands.Context, server, ign:str= None):
        """Allows a user to request  Whitelist for a Specific Server."""
        self.logger.command(f'{context.author.name} used Bot Whitelist Request...')
        amp_server = await self.uBot._serverCheck(context, server)

        if amp_server:
            #if this succeeds, then we can check if the user is whitelisted since we have updated the DB
            message = await context.send('Handling your request, please wait...', ephemeral= True)# delete_after= self._client.Message_Timeout)
            for key, value in self._client.Whitelist_wait_list.items():
                if value['context'].author.id == context.author.id and value['ampserver'].InstanceID == amp_server.InstanceID:
                    await context.send(f'Hey, I already have a whitelist request pending from you on {amp_server.InstanceName if amp_server.FriendlyName == None else amp_server.FriendlyName}')

            await self.whitelist_request_handler(context = context, message= message, discord_user= context.author, server= amp_server, ign= ign)
    
    async def whitelist_request_handler(self, context:commands.Context, message: discord.Message, discord_user:discord.Member, server:AMP.AMPInstance, ign:str= None):
        """Whitelist request handler checks for a DB User, checks for their IGN, checks if they are Whitelisted and any other required checks to whitelist a user. """
        self.logger.command(f'Whitelist Request: ign: {ign} servers: {server.FriendlyName} user: {discord_user.name}')

        if not self.DBConfig.GetSetting('Auto_Whitelist'):
            self.logger.error('Hey a Whitelist request came in, but Auto-Whitelisting is currently disabled!')
            return await message.edit(content= f'Hey {discord_user.name}, we are unable to handle your request at this time, please contact a Staff Member.')

        server_name = f"{server.FriendlyName if server.FriendlyName != None else server.InstanceName}"
        db_user = self.DB.GetUser(discord_user.id)
 
        if db_user == None:
            db_user = self.DB.AddUser(DiscordID= discord_user.id, DiscordName= discord_user.name)
            self.logger.info(f'Added new user to the DB: {discord_user.name}')

        exists = server.check_Whitelist(db_user, ign)
        if exists == False:
            return await message.edit(content= f'Well I am unable to handle your request, {f"the IGN: {ign} appears to be invalid." if ign != None else "I need your IGN to handle your request."}')
    
        elif exists == None:
                return await message.edit(content= f'Hey it looks like you are already whitelisted on **{server_name}**~ Have fun.')

        db_server = self.DB.GetServer(server.InstanceID)
        if db_server.DisplayName != None:
            server_name = db_server.DisplayName

        if db_server.Whitelist == False:
            return await message.edit(content= f'Ooops, it appears that the server **{server_name}** has their Whitelisting Closed. If this is an error please contact a Staff Member.')
             
        if db_server.Donator == True:
            author_roles = []
            for role in discord_user.author.roles:
                author_roles.append(role.id)
                if self.DBConfig.GetSetting('Donator_Role')!= None:
                    if int(self.DBConfig.GetSetting('Donator_role_id')) not in author_roles:
                        return await message.edit(content= f'*Waves* Hey **{server_name}** is for Donator Access Only, it appears you do not have Donator. If this is an error please contact a Staff Member.')
                        
                else:
                    return await message.edit(content= f'Well it appears that the Staff have not set a Donator Role yet, Please inform Staff of this error.')
                    
        wait_time_value = self.DBConfig.GetSetting("Whitelist_Wait_Time")
        if wait_time_value != 0:
            cur_time = datetime.now(timezone.utc)
            display_time = discord.utils.format_dt((cur_time + timedelta(minutes= wait_time_value)))
            await message.edit(content= f'Your whitelist request has been accepted and is awaiting __Staff Approval__. \n> If no approval by {display_time}, your request will be auto-approved.')

            self._client.Whitelist_wait_list[context.message.id] = {'ampserver': server, 'context': context, 'dbuser' : db_user}
            self.logger.info(f'Added {context.author} to Whitelist Wait List. Current wait time is {wait_time_value} {"minutes" if wait_time_value > 1 else "minute"}')
            self.logger.dev(f'MessageID: {context.message.id}')
            
            #Send view to specific channel
            whitelist_request_channel = self._client.get_channel(self.DBConfig.GetSetting('Whitelist_Request_Channel')) #Whitelist Channel #This will point to a Staff Channel/Similar
            whitelist_request_message = await whitelist_request_channel.send(content= f'Whitelist Request from `{message.author.name}` for Server: **{server.FriendlyName}**...')
            await whitelist_request_message.edit(view= self.uiBot.Whitelist_view(client= self._client, discord_message= whitelist_request_message, whitelist_message= context.message, amp_server= server, context= context, timeout= wait_time_value))

            #Checks if the Tasks is running, if not starts the task.
            if not self.whitelist_waitlist_handler.is_running():
                self.whitelist_waitlist_handler.start()
            return
        
        server.addWhitelist(db_user = db_user)
        if len(self.DB.GetAllWhitelistReplies()) != 0:
            whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
            await message.edit(content= self.uBot.whitelist_reply_handler(whitelist_reply, context, server))
        else:
            await message.edit(content= f'You are all set! We whitelisted `{context.author.name}` on **{db_server.FriendlyName}**')
        if db_server.Discord_Role != None:
            discord_role = self.uBot.roleparse(db_server.Discord_Role, context, context.guild.id)
            await context.author.add_roles(discord_role, reason= 'Auto Whitelisting')

        self.logger.command(f'Whitelisting {context.author.name} on {server.FriendlyName}')

    @tasks.loop(seconds= 30)
    async def whitelist_waitlist_handler(self):
        """This is the Whitelist Wait list handler, every 30 seconds it will check the list and whitelist them after the alotted wait time."""
        self.logger.command('Checking the Whitelist Wait List...')
        if len(self._client.Whitelist_wait_list) == 0:
            self.logger.dev(f'It Appears the Whitelist Wait List is empty; stopping the Task loop.')
            self.whitelist_waitlist_handler.stop()

        cur_time = datetime.now(timezone.utc)
        try:
            wait_time = timedelta(minutes= self.DBConfig.GetSetting('Whitelist_Wait_Time'))  # This may error if someone changes the wait time to 0 inbetween a loop..
        except Exception:
            wait_time = timedelta(minutes= 1)  # Fallback to 1 min delay if somehow the value fails to get parsed.

        for key, value in self._client.Whitelist_wait_list.items():
            cur_message = value['context'].channel.get_partial_message(key)
            cur_amp_server = value['ampserver'] #AMPInstance Object
            cur_message_context = value['context']
            cur_db_user = value['dbuser'] #This is the DB User object

            #This should compare datetime objects and if the datetime of when the message was created plus the wait time is greater than or equal the cur_time they get whitelisted.
            if cur_message.created_at + wait_time <= cur_time:
                if cur_amp_server.check_Whitelist(cur_db_user):
                    db_server = self.DB.GetServer(value['ampserver'].InstanceID)
                    self.logger.dev(f'Whitelist Request time has come up; Attempting to Whitelist {cur_message_context.author.name} on {db_server.FriendlyName}')

                    #This handles all the Discord Role stuff.
                    if db_server != None and db_server.Discord_Role != None:
                        discord_role = self.uBot.roleparse(db_server.Discord_Role, cur_message_context, cur_message_context.guild.id)
                        discord_user = self.uBot.userparse(cur_message.author.id, cur_message_context, cur_message_context.guild.id)
                        await discord_user.add_roles(discord_role, reason= 'Auto Whitelisting')

                    #This is for all the Replies
                    if len(self.DB.GetAllWhitelistReplies()) != 0:
                        whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
                        #
                        await cur_message_context.channel.send(content= f'{cur_message_context.author.mention} \n{self.uBot.whitelist_reply_handler(whitelist_reply, cur_message_context, cur_amp_server)}', reference= cur_message, delete_after= self._client.Message_Timeout)
                    else:
                        await cur_message_context.channel.send(content= f'You are all set! We whitelisted {cur_message_context.author.mention} on **{db_server.FriendlyName}** ', reference= cur_message, delete_after= self._client.Message_Timeout)

                    cur_amp_server.addWhitelist(db_user = cur_db_user)
                    self.logger.command(f'Whitelisting {cur_message_context.author.name} on {cur_amp_server.FriendlyName}')
                    self._client.Whitelist_wait_list.pop(key)

async def setup(client:commands.Bot):
    await client.add_cog(Whitelist(client))