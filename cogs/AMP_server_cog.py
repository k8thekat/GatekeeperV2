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
import os
import logging
from datetime import datetime,timezone
import re
import asyncio

import discord
from discord.ext import commands,tasks
from discord import app_commands

import AMP
import DB
import utils

class Server(commands.Cog):
    def __init__(self, client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()
        
        self.AMPHandler = AMP.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMPThreads = self.AMPHandler.AMP_Console_Threads
        self.AMP_Instance_Names = self.AMPHandler.AMP_Instances_Names

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DBConfig = self.DBHandler.DBConfig

        self.Display_cache = False
        self.embed_reply = ''

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        
        self.logger.info(f'**SUCCESS** Initializing {self.name.capitalize()}')

        if self.DBConfig.GetSetting('Embed_Auto_Update') == True:
            self.server_display_update.start()
            self.logger.dev(f'Server Embed Display Update is Running: {self.server_display_update.is_running()}')

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')
    
    async def autocomplete_servers(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for AMP Instance Names"""
        choice_list = self.AMP_Instance_Names
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    async def autocomplete_message_type(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        choice_list = ['Announcement','Broadcast','Maintenance','Info','Warning']
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

    @tasks.loop(minutes=1)
    async def server_display_update(self):
        """This will handle the constant updating of Server Display Embeds"""
        if self._client.is_ready():
            if not self.DBConfig.GetSetting('Embed_Auto_Update'):
                return
            self.logger.info('Updating Server Display Embeds')
            server_embeds = self.DB.GetServerEmbeds()
            if len(server_embeds) == 0:
                self.logger.error('No Server Embeds to Update')
                self.server_display_update.stop()
                return
            message_list = []
            for embed in server_embeds:
                discord_guild = self._client.get_guild(int(embed['GuildID']))
                discord_channel = discord_guild.get_channel(int(embed['ChannelID']))
                discord_message = discord_channel.get_partial_message(int(embed['MessageID']))
                message_list.append(discord_message)

            embed_list = await self.uBot.server_display_embed(discord_guild)

            start,stop = 0,10
            for message in message_list:
                if len(embed_list[start:stop]) == 0:
                    return
                try:
                    await message.edit(embeds=embed_list[start:stop])
                except discord.errors.NotFound:
                    self.logger.error('Embed Messages were deleted, removing from DB and stopping the loop.')
                    self.DB.DelServerEmebed(discord_guild.id, discord_channel.id)
                    self.server_display_update.stop()
                await asyncio.sleep(5)
                start += 10 
                stop += 10 

    @commands.hybrid_group(name='server')
    @utils.role_check()
    async def server(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...')
    
    @server.command(name='test')
    @utils.role_check()
    @utils.guild_check(guild_id=602285328320954378)
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(flag= utils.autocomplete_bool)
    async def amp_server_test(self, context:commands.Context, server, flag):
        """This is a test function."""
        self.logger.command(f'{context.author.name} used AMP Server Test')
        amp_server = self.uBot.serverparse(server,context,context.guild.id)
        await context.send(f'This is a test command {amp_server}')

    @server.command(name='broadcast')
    @utils.role_check()
    @app_commands.autocomplete(type= autocomplete_message_type)
    async def amp_server_broadcast(self, context:commands.Context, type:str, message:str):
        """This sends a message to every online AMP Server"""
        self.logger.command(f'{context.author.name} used AMP Server Broadcast')
        discord_message = await context.send('Sending Broadcast...')
        for amp_server in self.AMPInstances:
            if self.AMPInstances[amp_server].ADS_Running:
                self.AMPInstances[amp_server].Broadcast_Message(message, prefix= type)
        await discord_message.edit(content='Broadcast Sent!')

    @server.command(name='info')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_info(self, context:commands.Context, server):
        """Displays Specific Server Information."""
        self.logger.command(f'{context.author.name} used AMP Server Info')
        await context.defer()
        amp_server = self.uBot.serverparse(server,context,context.guild.id)
        if amp_server == None:
            await context.send(f"Hey, we uhh can't find the server {server}. Please try again.")
        embed = await self.uBot.server_info_embed(amp_server,context)
        await context.send(embed=embed)

    @server.command(name='display')
    @utils.role_check()
    async def amp_server_display(self, context:commands.Context):
        """Retrieves a list of all AMP Instances and displays them as embeds with constant updates."""
        self.logger.command(f'{context.author.name} used AMP Display List...')

        await context.defer()
        embed_list = await self.uBot.server_display_embed()
        if len(embed_list) == 0:
            return await context.send('Hey I encountered an issue trying to get the embeds. Please check your settings.')

        self.Server_Info_Embeds = []
        if len(embed_list) <= 10:
            sent_msg = await context.send(embeds= embed_list[0:len(embed_list)-1])
            self.Server_Info_Embeds.append(sent_msg.id)
  
        start,stop = 0,10
        if len(embed_list) > 10:
            while stop <= len(embed_list): # 10 less than or equal to the len(embed_list)(12)
                sent_msg = await context.send(embeds= embed_list[start:stop]) #0,10 
                self.Server_Info_Embeds.append(sent_msg.id)
                start += 10 # 10 
                stop += 10 # 20 

            if stop > len(embed_list): #20 // 12
                sent_msg = await context.send(embeds= embed_list[start:len(embed_list)-1]) #0,10
                self.Server_Info_Embeds.append(sent_msg.id)
               
        self.DB.AddServerEmbed(context.guild.id, sent_msg.channel.id, self.Server_Info_Embeds)
        if self.DBConfig.GetSetting('Embed_Auto_Update'):
            reply = await context.send('Pin the Server Info Embeds! and the bot will update the embeds every minute! ')
            await reply.delete(delay=60)
            if not self.server_display_update.is_running():
                self.server_display_update.start()

    @server.command(name='start')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_start(self, context:commands.Context, server):
        """Starts the AMP Instance"""
        self.logger.command(f'{context.author.name} used AMP Server Started...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            server.StartInstance()
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Starting the AMP Instance {server.FriendlyName}')
    
    @server.command(name='stop')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_stop(self, context:commands.Context, server):
        """Stops the AMP Instance"""
        self.logger.command(f'{context.author.name} used AMP Server Stopped...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            server.StopInstance()
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Stopping the AMP Instance {server.FriendlyName}')

    @server.command(name='restart')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_restart(self, context:commands.Context, server):
        """Restarts the AMP Instance"""
        self.logger.command(f'{context.author.name} used AMP Server Restart...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            server.RestartInstance()
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Restarting the AMP Instance {server.FriendlyName}')
    
    @server.command(name='kill')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_kill(self, context:commands.Context, server):
        """Kills the AMP Instance"""
        self.logger.command(f'{context.author.name} used AMP Server Kill...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            server.KillInstance()
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Killing the AMP Instance {server.FriendlyName}')

    @server.command(name='msg')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_message(self, context:commands.Context, server, message:str):
        """Sends a message to the Console, can be anything the Server Console supports.(Commands/Messages)"""
        self.logger.command(f'{context.author.name} used AMP Server Message...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            console_reply = server.ConsoleMessage_withUpdate(message)
            msg_to_send = []
            for message in console_reply['ConsoleEntries']:
                msg_to_send.append(message['Contents'])
            await context.send('\n'.join(msg_to_send))

    @server.command(name='backup')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_backup(self, context:commands.Context, server):
        """Creates a Backup of the Server in its current state, setting the title to the Users display name."""
        self.logger.command(f'{context.author.name} used AMP Server Backup...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            title = f"Backup by {context.author.display_name}"
            time = str(datetime.now(tz= timezone.utc))
            description = f"Created at {time} by {context.author.display_name}"
            display_description = f'Created at **{str(datetime.now(tz= timezone.utc))}**(utc) by **{context.author.display_name}**'
            await context.send(f'Creating a backup of **{server.FriendlyName}**  // **Description**: {display_description}')
        
    @server.command(name='status')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_status(self, context:commands.Context, server):
        """AMP Instance Status(TPS, Player Count, CPU Usage, Memory Usage and Online Players)"""
        self.logger.command(f'{context.author.name} used AMP Server Status...')
        await context.defer()
        server = self.uBot.serverparse(server, context, context.guild.id)
        if server is None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')
        if server != None and server.Running == False:
            server_embed =  await self.uBot.server_status_embed(context,server)
            view = utils.StatusView()
            utils.StartButton(server,view,server.StartInstance)
            utils.StopButton(server,view,server.StopInstance).disabled = True
            utils.RestartButton(server,view,server.RestartInstance).disabled = True
            utils.KillButton(server,view,server.KillInstance).disabled = True
            await context.send(embed= server_embed, view=view)

        if server != None and server.Running:
            tps,Users,cpu,Memory,Uptime = server.getStatus()
            Users_online = ', '.join(server.getUserList())
            if len(Users_online) == 0:
                Users_online = 'None'
            server_embed = await self.uBot.server_status_embed(context,server,tps,Users,cpu,Memory,Uptime,Users_online)
            view = utils.StatusView(context=context,amp_server=server)
            utils.CustomButton(server,view,server.StartInstance,'Start',callback_label='Starting...',callback_disabled=True)
            utils.StopButton(server,view,server.StopInstance)
            utils.RestartButton(server,view,server.RestartInstance)
            utils.KillButton(server,view,server.KillInstance)
            await context.send(embed= server_embed, view=view)

    @server.command(name='users')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_users_list(self, context:commands.Context, server):
        """Shows a list of the currently connected Users to the Server."""
        self.logger.command(f'{context.author.name} used AMP Server Connected Users...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            cur_users = (', ').join(server.getUserList())
            if len(cur_users) != 0:
                await context.send("**Server Users**" + '\n' + cur_users)
            else:
                await context.send('The Server currently has no online players.')

    @server.group(name='nickname')
    @utils.role_check()
    async def amp_server_nickname(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...')
    
    @amp_server_nickname.command(name='add')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_nickname_add(self, context:commands.Context, server, nickname):
        self.logger.command(f'{context.author.name} used AMP Server Nickname Add...')
        amp_server = self.uBot.serverparse(server,context,context.guild.id)
        if amp_server == None:
            await context.send(f'Please try your selection again, Unable to find **{server}**')
        db_server = self.DB.GetServer(amp_server.InstanceID)
        if db_server.AddNickname(nickname):
            await context.send(f'Added **{nickname}** to **{server}** Nicknames List.')
        else:
            await context.send(f"The nickname provided is not unique, this server or another server already has this nickname.")
        
    @amp_server_nickname.command(name='remove')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_nickname_remove(self, context:commands.Context, server, nickname):
        self.logger.command(f'{context.author.name} used AMP Server Nickname remove...')
        amp_server = self.uBot.serverparse(server,context,context.guild.id)
        if amp_server == None:
            await context.send(f'Please try your selection again, Unable to find **{server}**')
        db_server = self.DB.GetServer(amp_server.InstanceID)
        if nickname not in db_server.Nicknames:
            await context.send(f"The Server **{server}** doesn't have the nickname **{nickname}**.")
        else:
            db_server.RemoveNickname(nickname)
            await context.send(f'Removed **{nickname}** from **{server}** Nicknames List.')

    @amp_server_nickname.command(name='list')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_nickname_list(self, context:commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Nickname list...')
        amp_server = self.uBot.serverparse(server,context,context.guild.id)
        if amp_server == None:
            await context.send(f'Please try your selection again, Unable to find **{server}**')
        db_server = self.DB.GetServer(amp_server.InstanceID)
        nicknames = ("\n").join(db_server.Nicknames)
        await context.send(f'__**Nicknames**__:\n {nicknames}')

    # This Section is DBServer Attributes -----------------------------------------------------------------------------------------------------
    @server.command(name='avatar')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_avatar_set(self, context:commands.Context, server, url:str):
        """Sets the Servers Avatar via url. Supports `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated."""
        self.logger.command(f'{context.author.name} used Database Server Avatar Set')
        await context.defer()

        if not url.startswith('http://') or not url.startswith('https://'):
            return await context.send(f'Ooops, please provide a valid url. It must start with either `http://` or `https://`')
            
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            db_server = self.DB.GetServer(InstanceID= server.InstanceID)
            db_server.Avatar_url = url
            if url == 'None':
                await context.send(f"Removed {server.FriendlyName} Avatar Icon.")
                server.attr_update() #This will update the AMPInstance Attributes
                return
            if await self.uBot.validate_avatar(db_server) != None:
                server.attr_update() #This will update the AMPInstance Attributes
                await context.send(f"Set {server.FriendlyName} Avatar Icon.{url}")
            else:
                await context.send(f'I encountered an issue using that url, please try again. Heres your url: {url}')

    @server.command(name='displayname')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_displayname_set(self, context:commands.Context, server, name:str):
        """Sets the Display Name for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Display Name')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).DisplayName = name
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f"Set {server.FriendlyName} Display Name to {name}")

    @server.command(name='description')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_description(self, context:commands.Context, server, desc:str):
        """Sets the Description for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Description')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Description = desc
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f"Set {server.FriendlyName} Description to {desc}")
        
    @server.command(name='ip')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_ip(self, context:commands.Context, server, ip:str):
        """Sets the IP for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server IP')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).IP = ip
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f"Set {server.FriendlyName} IP to {ip}")

    @server.command(name='donator')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(flag= utils.autocomplete_bool)
    async def db_server_donator(self, context:commands.Context, server, flag):
        """Sets the Donator Only flag for the provided server."""
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and flag != None:
            flag_reg = re.search("(true|false)",flag.lower())
            if flag_reg == None:
                return await context.send(f'Please use `true` or `false` for your flag.')
            
            if flag_reg.group() == 'true':
                self.DB.GetServer(InstanceID= server.InstanceID).Donator = True
                server.attr_update() #This will update the AMPConsole Attributes
                return await context.send(f"Set {server.FriendlyName} Donator Only to `True`")

            if flag_reg.group() == 'false':
                self.DB.GetServer(InstanceID= server.InstanceID).Donator = False
                server.attr_update() #This will update the AMPConsole Attributes
                return await context.send(f"Set {server.FriendlyName} Donator Only to `False`")

    @server.group(name='console')
    @utils.role_check()
    async def db_server_console(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')
   
    @db_server_console.command(name='channel')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
    async def db_server_console_channel_set(self, context:commands.Context, server, channel):
        """Sets the Console Channel for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Console Channel')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        channel = self.uBot.channelparse(channel,context,context.guild.id)
        if channel == None:
            return await context.send(f'Unable to find the provided channel, please try again.')
        
        if server != None and channel != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Discord_Console_Channel = str(channel.id)
            server.attr_update() #This will update the AMPConsole Attribute
            await context.send(f'Set {server.FriendlyName} Console channel to {channel.name}')
    
    @db_server_console.command(name='filter')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(flag= utils.autocomplete_bool)
    async def db_server_console_filter(self, context:commands.Context, server, flag):
        """Sets the Console Filter"""
        self.logger.command(f'{context.author.name} used Database Server Console Filtered True...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and flag != None:
            flag_reg = re.search("(true|false)",flag.lower())
            if flag_reg == None:
                return await context.send(f'Please use `true` or `false` for your flag.')
            
            if flag_reg.group() == 'true':
                self.DB.GetServer(InstanceID= server.InstanceID).Console_Filtered = True
                server.attr_update() #This will update the AMPConsole Attributes
                return await context.send(f'Filtering the Console for {server.FriendlyName}')

            if flag_reg.group() == 'false':
                self.DB.GetServer(InstanceID= server.InstanceID).Console_Filtered = False
                server.attr_update() #This will update the AMPConsole Attributes
                return await context.send(f'Not Filtering the Console for {server.FriendlyName}')
  
    @server.group(name='chat')
    @utils.role_check()
    async def db_server_chat(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_server_chat.command(name='channel')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
    async def db_server_chat_channel_set(self, context:commands.Context, server, channel:str):
        """Sets the Chat Channel for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Chat Channel')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        channel = self.uBot.channelparse(channel,context,context.guild.id)
        if channel == None:
            return await context.send(f'Unable to find the provided channel, please try again.')

        if server != None and channel != None:
            self.DB.GetServer(server.InstanceID).Discord_Chat_Channel = channel.id
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Set {server.FriendlyName} Chat channel to {channel.name}')

    @server.group(name='event')
    @utils.role_check()
    async def db_server_event(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_server_event.command(name='channel')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
    async def db_server_event_channel_set(self, context:commands.Context, server, channel:str):
        """Sets the Event Channel for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Event Channel')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        channel = self.uBot.channelparse(channel,context,context.guild.id)
        if channel == None:
            return await context.send(f'Unable to find the provided channel, please try again.')

        if server != None and channel != None:
            self.DB.GetServer(server.InstanceID).Discord_Event_Channel = channel.id
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Set {server.FriendlyName} Event channel to {channel.name}')

    @server.command(name='role')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(discord_role= utils.autocomplete_discord_roles)
    async def db_server_discord_role_set(self, context:commands.Context, server, discord_role:str):
        """Sets the Discord Role for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Discord Role')
    
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        discord_role = self.uBot.roleparse(discord_role,context,context.guild.id)
        if discord_role == None:
            return await context.send(f'Unable to find the provided role, please try again.')

        if server != None and discord_role != None:
            self.DB.GetServer(server.InstanceID).Discord_Role = discord_role.id
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Set {server.FriendlyName} Discord Role to {discord_role.name}')

    @server.command(name='prefix')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_discord_prefix_set(self, context:commands.Context, server, server_prefix:str):
        """Sets the Discord Chat Prefix for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Discord Chat Prefix')
    
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(server.InstanceID).Discord_Chat_prefix = server_prefix
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Set {server.FriendlyName} Discord Chat Prefix to {server_prefix}')

    #Whitelist Commands -----------------------------------------------------------------------------------------------------------------------
    @server.group(name='whitelist')
    @utils.role_check()
    async def server_whitelist(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @server_whitelist.command(name='true')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def dbserver_whitelist_true(self, context:commands.Context, server):
        """Set Servers Whitelist Allowed to True"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist True...')
     
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Whitelist = True
            server.attr_update() #This will update the AMPInstance Attributes
        await context.send(f"Server: {server.FriendlyName}, Whitelist set to : `True`")

    @server_whitelist.command(name='false')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def dbserver_whitelist_false(self, context:commands.Context, server):
        """Set Servers Whitelist Allowed to False"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist False...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')
        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Whitelist = False
            server.attr_update() #This will update the AMPInstance Attributes
        await context.send(f"Server: {server.FriendlyName}, Whitelist set to : `False`")

    @server_whitelist.command(name='add')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_whitelist_add(self, context:commands.Context, server, in_gamename):
        """Adds User to Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Add...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            reply = server.addWhitelist(in_gamename)
            await context.send(f'**{server.FriendlyName}**: {(",").join(reply)}')

    @server_whitelist.command(name='remove')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_whitelist_remove(self, context:commands.Context, server, in_gamename):
        """Remove a User from the Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Remove...')

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            reply = server.removeWhitelist(in_gamename)
            await context.send(f'**{server.FriendlyName}**: {(",").join(reply)}')

async def setup(client):
    await client.add_cog(Server(client))