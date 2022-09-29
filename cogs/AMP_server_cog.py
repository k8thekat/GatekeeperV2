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

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DBConfig = self.DBHandler.DBConfig

        self.Display_cache = False
        self.embed_reply = ''

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        
        if self.DBConfig.GetSetting('Embed_Auto_Update') == True:
            self.server_display_update.start()
            self.logger.dev(f'Server Embed Display Update is Running: {self.server_display_update.is_running()}')

        self.logger.info(f'**SUCCESS** Initializing {self.name.capitalize()}')

    async def autocomplete_servers(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for AMP Instance Names"""
        choice_list = self.AMPHandler.get_AMP_instance_names()
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    async def autocomplete_message_type(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        choice_list = ['Announcement','Broadcast','Maintenance','Info','Warning']
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

    async def _serverCheck(self, context:commands.Context, server, online_only:bool=True) -> AMP.AMPInstance:
        """Verifies if the AMP Server exists and if its Instance is running and its ADS is Running"""
        amp_server = self.uBot.serverparse(server,context,context.guild.id)
        
        if amp_server == None:
            await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True)
            return False

        if online_only == False:
            return amp_server

        if amp_server.Running and amp_server._ADScheck():
            return amp_server
        
        await context.send(f'Well this is awkward, it appears the **{server}** is `Offline`.', ephemeral=True)
        return False

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
                discord_guild = self._client.get_guild(embed['GuildID'])
                discord_channel = discord_guild.get_channel(embed['ChannelID'])
                discord_message = discord_channel.get_partial_message(embed['MessageID'])
                message_list.append(discord_message)

            embed_list = await self.uBot.server_display_embed(discord_guild)
            if len(embed_list) == 0:
                return

            for curpos in range(0, len(message_list)):
                try:
                    await message_list[curpos].edit(embeds=embed_list[curpos*10:(curpos+1)*10])
                except discord.errors.NotFound:
                    self.logger.error('Embed Messages were deleted, removing from DB and stopping the loop.')
                    self.DB.DelServerEmebed(discord_guild.id, discord_channel.id)
                    self.server_display_update.stop()
                await asyncio.sleep(5)

    @commands.hybrid_group(name='server')
    @utils.role_check()
    async def server(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...', ephemeral=True)
    
    @server.command(name='test')
    @utils.role_check()
    @utils.guild_check(guild_id=602285328320954378)
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(flag= utils.autocomplete_bool)
    async def amp_server_test(self, context:commands.Context, server, flag):
        """This is a test function."""
        self.logger.command(f'{context.author.name} used AMP Server Test')
        amp_server = self.uBot.serverparse(server,context,context.guild.id)
        await context.send(f'This is a test command **{server}**', ephemeral=True)

    @server.command(name='update')
    @utils.role_check()
    async def amp_server_update(self, context:commands.Context):
        """Updates the bot with any freshly created AMP Instances"""
        self.logger.command(f'{context.author.name} used AMP Server Update')
        new_server = self.AMPHandler.AMP._instanceValidation()
        if new_server:
            await context.send(f'Found a new Server: {new_server}', ephemeral= True)
        else:
            await context.send('Uhh.. No new instance was found. Hmmm...', ephemeral= True)

    @server.command(name='broadcast')
    @utils.role_check()
    @app_commands.autocomplete(type= autocomplete_message_type)
    async def amp_server_broadcast(self, context:commands.Context, type:str, message:str):
        """This sends a message to every online AMP Server"""
        self.logger.command(f'{context.author.name} used AMP Server Broadcast')
        discord_message = await context.send('Sending Broadcast...', ephemeral=True)
        for amp_server in self.AMPInstances:

            if self.AMPInstances[amp_server].Running:
                if self.AMPInstances[amp_server]._ADScheck():
                    self.AMPInstances[amp_server].Broadcast_Message(message, prefix= type)
                    await discord_message.edit(content='Broadcast Sent!')

                else:
                    await discord_message.edit(content=f'Oops, it appears **{self.AMPInstances[amp_server].FriendlyName}** is not Online.')

    @server.group(name='settings')
    @utils.role_check()
    async def server_settings(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...', ephemeral=True)

    @server_settings.command(name='info')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_info(self, context:commands.Context, server):
        """Displays Specific Server Information."""
        self.logger.command(f'{context.author.name} used AMP Server Info')
        await context.defer(ephemeral=True)

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            embed = await self.uBot.server_info_embed(amp_server, context)
            await context.send(embed=embed, ephemeral=True)
        else:
            return

    @server.command(name='display')
    @utils.role_check()
    async def amp_server_display(self, context:commands.Context):
        """Retrieves a list of all AMP Instances and displays them as embeds with constant updates."""
        self.logger.command(f'{context.author.name} used AMP Display List...')

        await context.defer()
        embed_list = await self.uBot.server_display_embed()
        if len(embed_list) == 0:
            return await context.send('Hey I encountered an issue trying to get the embeds. Please check your settings.', ephemeral=True)

        self.Server_Info_Embeds = []
        for curpos in range(0, len(embed_list), 10):
            sent_msg = await context.send(embeds= embed_list[curpos:curpos+10])
            self.Server_Info_Embeds.append(sent_msg.id)
               
        self.DB.AddServerEmbed(context.guild.id, sent_msg.channel.id, self.Server_Info_Embeds)
        if self.DBConfig.GetSetting('Embed_Auto_Update'):
            reply = await context.send('Pin the Server Info Embeds! and the bot will update the embeds every minute!', ephemeral=True)
            await reply.delete(delay=60)
            if not self.server_display_update.is_running():
                self.server_display_update.start()

    @server.command(name='start')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_start(self, context:commands.Context, server):
        """Starts the AMP Instance"""
        self.logger.command(f'{context.author.name} used AMP Server Started...')

        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True)

        if amp_server.Running == False:
            return await context.send(f'Well this is awkward, it appears the **{server}** is `Offline`.', ephemeral=True)

        if not amp_server._ADScheck():
            amp_server.StartInstance()
            amp_server.ADS_Running = True
            await context.send(f'Starting the AMP Dedicated Server **{server}**', ephemeral=True)
        else:
            return await context.send(f'Hmm it appears the server is already running..', ephemeral= True)
      
    @server.command(name='stop')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_stop(self, context:commands.Context, server):
        """Stops the AMP Instance"""
        self.logger.command(f'{context.author.name} used AMP Server Stopped...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            amp_server.StopInstance()
            amp_server.ADS_Running = False
            await context.send(f'Stopping the AMP Dedicated Server **{server}**', ephemeral=True)
        else:
            return

    @server.command(name='restart')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_restart(self, context:commands.Context, server):
        """Restarts the AMP Instance"""
        self.logger.command(f'{context.author.name} used AMP Server Restart...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            amp_server.RestartInstance()
            amp_server.ADS_Running = True
            await context.send(f'Restarting the AMP Dedicated Server **{server}**', ephemeral=True)
        else:
            return
    
    @server.command(name='kill')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_kill(self, context:commands.Context, server):
        """Kills the AMP Instance"""
        self.logger.command(f'{context.author.name} used AMP Server Kill...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            amp_server.KillInstance()
            amp_server.ADS_Running = False
            await context.send(f'Killing the AMP Dedicated Server **{server}**', ephemeral=True)
        else:
            return

    @server.command(name='msg')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_message(self, context:commands.Context, server, message:str):
        """Sends a message to the Console, can be anything the Server Console supports.(Commands/Messages)"""
        self.logger.command(f'{context.author.name} used AMP Server Message...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            amp_server.ConsoleMessage(message)
        else:
            return

    @server.command(name='backup')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_backup(self, context:commands.Context, server):
        """Creates a Backup of the Server in its current state, setting the title to the Users display name."""
        self.logger.command(f'{context.author.name} used AMP Server Backup...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            title = f"Backup by {context.author.display_name}"
            time = str(datetime.now(tz= timezone.utc))
            description = f"Created at {time} by {context.author.display_name}"
            display_description = f'Created at **{str(datetime.now(tz= timezone.utc))}**(utc) by **{context.author.display_name}**'
            await context.send(f'Creating a backup of **{server}**  // **Description**: {display_description}', ephemeral=True)
            amp_server.takeBackup(title, description)
        else:
            return
        
    @server.command(name='status')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_status(self, context:commands.Context, server):
        """AMP Instance Status(TPS, Player Count, CPU Usage, Memory Usage and Online Players)"""
        self.logger.command(f'{context.author.name} used AMP Server Status...')
        await context.defer(ephemeral=True)

        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True)

        if amp_server.Running == False:
            await context.send(f'Well this is awkward, it appears the **{server}** is `Offline`.', ephemeral=True)
        
        if amp_server._ADScheck():
            tps,Users,cpu,Memory,Uptime = amp_server.getStatus()
            Users_online = ', '.join(amp_server.getUserList())
            if len(Users_online) == 0:
                Users_online = 'None'
            server_embed = await self.uBot.server_status_embed(context, amp_server, tps, Users, cpu, Memory, Uptime, Users_online)
            view = utils.StatusView(context=context, amp_server= amp_server)
            utils.CustomButton(amp_server, view, amp_server.StartInstance,'Start',callback_label='Starting...',callback_disabled=True)
            utils.StopButton(amp_server, view, amp_server.StopInstance)
            utils.RestartButton(server, view, amp_server.RestartInstance)
            utils.KillButton(server, view, amp_server.KillInstance)
            await context.send(embed= server_embed, view=view, ephemeral=True)

        else:
            server_embed =  await self.uBot.server_status_embed(context,amp_server)
            view = utils.StatusView()
            utils.StartButton(amp_server, view, amp_server.StartInstance)
            utils.StopButton(amp_server, view, amp_server.StopInstance).disabled = True
            utils.RestartButton(amp_server, view, amp_server.RestartInstance).disabled = True
            utils.KillButton(amp_server, view, amp_server.KillInstance).disabled = True
            await context.send(embed= server_embed, view=view, ephemeral=True)

    @server.command(name='users')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_users_list(self, context:commands.Context, server):
        """Shows a list of the currently connected Users to the Server."""
        self.logger.command(f'{context.author.name} used AMP Server Connected Users...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            cur_users = (', ').join(amp_server.getUserList())
            if len(cur_users) != 0:
                await context.send("**Server Users**" + '\n' + cur_users, ephemeral=True)
            else:
                await context.send('The Server currently has no online players.', ephemeral=True)
        else:
            return

    @server.group(name='nickname')
    @utils.role_check()
    async def amp_server_nickname(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...', ephemeral=True)
    
    @amp_server_nickname.command(name='add')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_nickname_add(self, context:commands.Context, server, nickname:str):
        self.logger.command(f'{context.author.name} used AMP Server Nickname Add...')
        
        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            naughty_words = ['server','ign','whitelist']
            for word in naughty_words:
                if nickname.lower().find(word) == -1:
                    await context.send('Nicknames cannot contain the words `Server`, `IGN` or `Whitelist`, these are exclusive.')
            if db_server.AddNickname(nickname):
                await context.send(f'Added **{nickname}** to **{server}** Nicknames List.', ephemeral=True)
            else:
                await context.send(f"The nickname provided is not unique, this server or another server already has this nickname.", ephemeral=True)
        else:
            return
        
    @amp_server_nickname.command(name='remove')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_nickname_remove(self, context:commands.Context, server, nickname):
        self.logger.command(f'{context.author.name} used AMP Server Nickname remove...')

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            if nickname not in db_server.Nicknames:
                await context.send(f"The Server **{server}** doesn't have the nickname **{nickname}**.", ephemeral=True)
            else:
                db_server.RemoveNickname(nickname)
                await context.send(f'Removed **{nickname}** from **{server}** Nicknames List.', ephemeral=True)
        else:
            return

    @amp_server_nickname.command(name='list')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_nickname_list(self, context:commands.Context, server):
        self.logger.command(f'{context.author.name} used AMP Server Nickname list...')

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(amp_server.InstanceID)
            nicknames = ("\n").join(db_server.Nicknames)
            await context.send(f'__**Nicknames**__:\n {nicknames}', ephemeral=True)
        else:
            return
            
    # This Section is DBServer Attributes -----------------------------------------------------------------------------------------------------
    @server_settings.command(name='avatar')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_avatar_set(self, context:commands.Context, server, url:str):
        """Sets the Servers Avatar via url. Supports `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated."""
        self.logger.command(f'{context.author.name} used Database Server Avatar Set')
        await context.defer()

        if not url.startswith('http://') or not url.startswith('https://'):
            return await context.send('Ooops, please provide a valid url. It must start with either `http://` or `https://`', ephemeral=True)
            
        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(InstanceID= amp_server.InstanceID)
            db_server.Avatar_url = url
            if url == 'None':
                await context.send(f"Removed **{server}** Avatar Icon.", ephemeral=True)
                amp_server._setDBattr()
                return
            if await self.uBot.validate_avatar(db_server) != None:
                amp_server._setDBattr() #This will update the AMPInstance Attributes
                await context.send(f"Set **{server}** Avatar Icon url to `{url}`", ephemeral=True)
            else:
                await context.send(f'I encountered an issue using that url, please try again. Heres your url: {url}', ephemeral=True)
        else:
            return

    @server_settings.command(name='displayname')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_displayname_set(self, context:commands.Context, server, name:str):
        """Sets the Display Name for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Display Name')

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            db_server = self.DB.GetServer(InstanceID= amp_server.InstanceID)
            if db_server.setDisplayName(name) != False:
                amp_server._setDBattr() #This will update the AMPInstance Attributes
                await context.send(f"Set **{server}** Display Name to `{name}`", ephemeral=True)
            else:
                await context.send(f'The Display Name provided is not unique, this server or another server already has this name.', ephemeral=True)
        else:
            return

    @server_settings.command(name='description')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_description(self, context:commands.Context, server, desc:str):
        """Sets the Description for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Description')

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Description = desc
            amp_server._setDBattr() #This will update the AMPInstance Attributes
            await context.send(f"Set **{server}** Description to `{desc}`", ephemeral=True)
        else:
            return
        
    @server_settings.command(name='ip')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_ip(self, context:commands.Context, server, ip:str):
        """Sets the IP for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server IP')

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).IP = ip
            amp_server._setDBattr() #This will update the AMPInstance Attributes
            await context.send(f"Set **{server}** IP to `{ip}`", ephemeral=True)
        else:
            return

    @server_settings.command(name='donator')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(flag= utils.autocomplete_bool)
    async def db_server_donator(self, context:commands.Context, server, flag:str):
        """Sets the Donator Only flag for the provided server."""
        self.logger.command(f'{context.author.name} used Database Donator Flag')

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            flag_reg = re.search("(true|false)",flag.lower())
            if flag_reg == None:
                return await context.send('Please use `true` or `false` for your flag.', ephemeral=True)
            
            self.DB.GetServer(InstanceID= server.InstanceID).Donator = self.uBot.str_to_bool(flag)
            amp_server._setDBattr() #This will update the AMPConsole Attributes
            return await context.send(f"Set **{server}** Donator Only to `{flag.capitalize()}`", ephemeral=True) 
        else:
            return

    @server.group(name='console')
    @utils.role_check()
    async def db_server_console(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True)
   
    @db_server_console.command(name='channel')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
    async def db_server_console_channel_set(self, context:commands.Context, server, channel):
        """Sets the Console Channel for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Console Channel')

        discord_channel = self.uBot.channelparse(channel,context,context.guild.id)
        if discord_channel == None:
            return await context.send('Unable to find the provided channel, please try again.', ephemeral=True)
        
        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Discord_Console_Channel = discord_channel.id
            amp_server._setDBattr() #This will update the AMPConsole Attribute
            await context.send(f'Set **{server}** Console channel to `{discord_channel.name}`', ephemeral=True)
        else:
            return
    
    @db_server_console.command(name='filter')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(flag= utils.autocomplete_bool)
    async def db_server_console_filter(self, context:commands.Context, server, flag:str):
        """Sets the Console Filter"""
        self.logger.command(f'{context.author.name} used Database Server Console Filtered True...')

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            flag_reg = re.search("(true|false)",flag.lower())
            if flag_reg == None:
                return await context.send('Please use `true` or `false` for your flag.', ephemeral=True)

            self.DB.GetServer(InstanceID= amp_server.InstanceID).Console_Filtered = self.uBot.str_to_bool(flag)
            amp_server._setDBattr() #This will update the AMPConsole Attributes
            return await context.send(f'Set **{server}** Console Filtering to `{flag.capitalize()}`', ephemeral=True)
        else:
            return

    @server.group(name='chat')
    @utils.role_check()
    async def db_server_chat(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True)

    @db_server_chat.command(name='channel')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
    async def db_server_chat_channel_set(self, context:commands.Context, server, channel:str):
        """Sets the Chat Channel for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Chat Channel')


        discord_channel = self.uBot.channelparse(channel, context, context.guild.id)
        if discord_channel == None:
            return await context.send('Unable to find the provided channel, please try again.', ephemeral=True)

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(amp_server.InstanceID).Discord_Chat_Channel = discord_channel.id
            amp_server._setDBattr() #This will update the AMPInstance Attributes
            await context.send(f'Set **{server}** Chat channel to `{discord_channel.name}`', ephemeral=True)

    @server.group(name='event')
    @utils.role_check()
    async def db_server_event(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True)

    @db_server_event.command(name='channel')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(channel= utils.autocomplete_discord_channels)
    async def db_server_event_channel_set(self, context:commands.Context, server, channel:str):
        """Sets the Event Channel for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Event Channel')

        discord_channel = self.uBot.channelparse(channel, context, context.guild.id)
        if discord_channel == None:
            return await context.send('Unable to find the provided channel, please try again.', ephemeral=True)

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(amp_server.InstanceID).Discord_Event_Channel = discord_channel.id
            amp_server._setDBattr() #This will update the AMPInstance Attributes
            await context.send(f'Set **{server}** Event channel to `{discord_channel.name}`', ephemeral=True)

    @server_settings.command(name='role')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(role= utils.autocomplete_discord_roles)
    async def db_server_discord_role_set(self, context:commands.Context, server, role:str):
        """Sets the Discord Role for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Discord Role')
    
        discord_role = self.uBot.roleparse(role, context, context.guild.id)
        if discord_role == None:
            return await context.send('Unable to find the provided role, please try again.', ephemeral=True)

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(amp_server.InstanceID).Discord_Role = discord_role.id
            amp_server._setDBattr() #This will update the AMPInstance Attributes
            await context.send(f'Set **{server}** Discord Role to `{discord_role.name}`', ephemeral=True)

    @server_settings.command(name='prefix')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def db_server_discord_prefix_set(self, context:commands.Context, server, server_prefix:str):
        """Sets the Discord Chat Prefix for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Discord Chat Prefix')
    
        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            self.DB.GetServer(amp_server.InstanceID).Discord_Chat_prefix = server_prefix
            amp_server._setDBattr() #This will update the AMPInstance Attributes
            await context.send(f'Set **{server}** Discord Chat Prefix to `{server_prefix}`', ephemeral=True)


    @server_settings.command(name='hidden')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(flag= utils.autocomplete_bool)
    async def db_server_hidden(self, context:commands.Context, server, flag):
        """Hides the server from Embed Display via `/server display`"""
        self.logger.command(f'{context.author.name} used Database Server Hidden')

        amp_server = await self._serverCheck(context, server, False)
        if amp_server:
            flag_reg = re.search("(true|false)",flag.lower())
            if flag_reg == None:
                return await context.send('Please use `true` or `false` for your flag.', ephemeral= True)
            
            self.DB.GetServer(InstanceID= server.InstanceID).Hidden = self.uBot.str_to_bool(flag)
            amp_server._setDBattr() #This will update the AMPConsole Attributes
            if flag.lower() == 'true':
                return await context.send(f"The **{server}** will now be Hidden", ephemeral= True)
            else:
                return await context.send(f'The **{server}** will now be Shown', ephemeral= True)
        else:
            return

    #Whitelist Commands -----------------------------------------------------------------------------------------------------------------------
    @server.group(name='whitelist')
    @utils.role_check()
    async def server_whitelist(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True)

    @server_whitelist.command(name='true')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def dbserver_whitelist_true(self, context:commands.Context, server):
        """Set Servers Whitelist Allowed to True"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist True...')
     
        amp_server = await self._serverCheck(context, server)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Whitelist = True
            amp_server._setDBattr() #This will update the AMPInstance Attributes
        await context.send(f"Server: **{server}**, Whitelist set to : `True`", ephemeral=True)

    @server_whitelist.command(name='false')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def dbserver_whitelist_false(self, context:commands.Context, server):
        """Set Servers Whitelist Allowed to False"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist False...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            self.DB.GetServer(InstanceID= amp_server.InstanceID).Whitelist = False
            amp_server._setDBattr() #This will update the AMPInstance Attributes
        await context.send(f"Server: **{server}**, Whitelist set to : `False`", ephemeral=True)

    @server_whitelist.command(name='add')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_whitelist_add(self, context:commands.Context, server, name):
        """Adds User to Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Add...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            whitelist = amp_server.addWhitelist(name)
            if whitelist:
                await context.send(f'**{server}**: Whitelisted `{name}`', ephemeral=True)
            if whitelist == False:
                await context.send(f'I was unable to find the UUID of that **{name}**', ephemeral= True)
            if whitelist == None:
                await context.send(f'Oops, it appears this user is already whitelisted! **{name}** is good to go~', ephemeral= True)
            

    @server_whitelist.command(name='remove')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_server_whitelist_remove(self, context:commands.Context, server, name):
        """Remove a User from the Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Remove...')

        amp_server = await self._serverCheck(context, server)
        if amp_server:
            whitelist = amp_server.removeWhitelist(name= name)
            if whitelist:
                await context.send(f'Oops, it appears this user is not whitelisted! **{name}** is not here~', ephemeral= True)
            if whitelist == False:
                await context.send(f'I was unable to find the UUID of that **{name}**', ephemeral= True)
            if whitelist == None:
                await context.send(f'**{server}**: Removed `{name}` from the Whitelist', ephemeral=True)
           

async def setup(client):
    await client.add_cog(Server(client))