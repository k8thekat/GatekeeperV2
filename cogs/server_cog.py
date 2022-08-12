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
from datetime import datetime
import re

import discord
from discord.ext import commands

import AMP
import DB
import utils

class Server(commands.Cog):
    def __init__(self,client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()
        
        self.AMPHandler = AMP.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances
        self.AMPThreads = self.AMPHandler.AMP_Console_Threads

        #self.AMPHandler.set_discord_client(self._client)   #This is to get the Discord Client functionality into AMPHandler and AMPConsole class

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB 
        self.DBConfig = self.DBHandler.DBConfig

   
        self.uBot = utils.botUtils(client)
        #self.uBot.sub_command_handler('server',self.server_whitelist) 
        self.logger.info(f'**SUCCESS** Initializing {self.name.capitalize()}')


    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member:discord.Member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.dev(f'Member Leave {self.name}: {member.name} {member}')

        db_user = self.DB.GetUser(str(member.id))
        if db_user != None and db_user.InGameName != None:
            for server in self.AMPInstances:
                if self.AMPInstances[server].Module == 'Minecraft':
                    self.AMPInstances[server].removeWhitelist(db_user.InGameName)

    
    @commands.hybrid_group(name='server')
    @utils.role_check() #Only Needed on the group Command
    async def server(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...')
       

    @server.command(name='list',description='Retrieves a list of all AMP Instances')
    @utils.role_check()
    async def amp_server_list(self,context:commands.Context):
        self.logger.command(f'{context.author.name} used Server List...')
        perm_node = 'server.list'

        embed_list = self.uBot.server_list_embed(context)
        for embed in embed_list:
            await context.send(embed = embed)

    @server.command(name='start',description='Starts the AMP Instance')
    @utils.role_check()
    async def amp_server_start(self,context:commands.Context,server):
        self.logger.command(f'{context.author.name} used AMP Server Started...')
        perm_node = 'server.start'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            server.StartInstance()
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Starting the AMP Instance {server.FriendlyName}')
    
    @server.command(name='stop',description='Stops the AMP Instance')
    @utils.role_check()
    async def amp_server_stop(self,context:commands.Context,server):
        self.logger.command(f'{context.author.name} used AMP Server Stopped...')
        perm_node = 'server.stop'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            server.StopInstance()
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Stopping the AMP Instance {server.FriendlyName}')

    @server.command(name='restart',description='Restarts the AMP Instance')
    @utils.role_check()
    async def amp_server_restart(self,context:commands.Context,server):
        self.logger.command(f'{context.author.name} used AMP Server Restart...')
        permn_node = 'server.restart'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            server.RestartInstance()
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Restarting the AMP Instance {server.FriendlyName}')
    
    @server.command(name='kill',description='Kills the AMP Instance')
    @utils.role_check()
    async def amp_server_kill(self,context:commands.Context,server):
        self.logger.command(f'{context.author.name} used AMP Server Kill...')
        perm_node = 'server.kill'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            server.KillInstance()
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Killing the AMP Instance {server.FriendlyName}')

    @server.command(name='msg',description='AMP Console Message/Commands')
    @utils.role_check()
    async def amp_server_message(self,context:commands.Context,server,message:str):
        self.logger.command(f'{context.author.name} used AMP Server Message...')
        perm_node = 'server.msg'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            console_reply = server.ConsoleMessage(message)
            msg_to_send = []
            for message in console_reply['ConsoleEntries']:
                msg_to_send.append(message['Contents'])
            await context.send('\n'.join(msg_to_send))

    @server.command(name='backup',description='AMP Console Message/Commands')
    @utils.role_check()
    async def amp_server_backup(self,context:commands.Context,server):
        self.logger.command(f'{context.author.name} used AMP Server Backup...')
        perm_node = 'server.backup'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            title = f'%s generated backup',context.author.display_name
            description = f'Created at %s by %s',datetime.datetime.now(),context.author.display_name
            server.takeBackup(title=title,description=description)
            await context.send(f'{server.FriendlyName} Backup' + description)
        
    @server.command(name='status',description='AMP Instance Status(TPS, Player Count, CPU Usage, Memory Usage and Online Players)')
    @utils.role_check()
    async def amp_server_status(self,context:commands.Context,server):
        self.logger.command(f'{context.author.name} used AMP Server Status...')
        perm_node = 'server.status'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')
        if server != None and server.Running == False:
            view = utils.StatusView()
            utils.StartButton(server,view,server.StartInstance)
            utils.StopButton(server,view,server.StopInstance).disabled = True
            utils.RestartButton(server,view,server.RestartInstance).disabled = True
            utils.KillButton(server,view,server.KillInstance).disabled = True
            await context.send(embed= self.uBot.server_status_embed(context,server),view=view)

        if server != None and server.Running:
            tps,Users,cpu,Memory,Uptime = server.getStatus()
            Users_online = ', '.join(server.getUserList())
            if len(Users_online) == 0:
                Users_online = 'None'
            view = utils.StatusView()
            utils.CustomButton(server,view,server.StartInstance,'Start',callback_label='Starting...',callback_disabled=True)
            utils.StopButton(server,view,server.StopInstance)
            utils.RestartButton(server,view,server.RestartInstance)
            utils.KillButton(server,view,server.KillInstance)
            await context.send(embed= self.uBot.server_status_embed(context,server,tps,Users,cpu,Memory,Uptime,Users_online),view=view)


    @server.command(name='users',description='AMP Instance User List(Display Names)')
    @utils.role_check()
    async def amp_server_users_list(self,context:commands.Context,server):
        self.logger.command(f'{context.author.name} used AMP Server Connected Users...')
        perm_node = 'server.users'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None and server.Running:
            cur_users = server.getUserList()
            if len(cur_users) != 0:
                await context.send("**Server Users**" + '\n' + ', '.join(server.getUserList()))
            else:
                await context.send('The Server currently has no online players.')

    #This section is Whitelist Specific Server Commands --------------------------------------------------------------------------------
    @server.group(name='whitelist')
    @utils.role_check()
    async def server_whitelist(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @server_whitelist.command(name='true')
    @utils.role_check()
    async def dbserver_whitelist_true(self,context:commands.Context,server):
        """Set Servers Whitelist Allowed to True"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist True...')
        perm_node = 'server.whitelist.true'
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Whitelist = True
            server.attr_update() #This will update the AMPInstance Attributes
        await context.send(f"Server: {server.FriendlyName}, Whitelist set to : `True`")

    @server_whitelist.command(name='false')
    @utils.role_check()
    async def dbserver_whitelist_false(self,context:commands.Context,server):
        """Set Servers Whitelist Allowed to False"""
        self.logger.command(f'{context.author.name} used Database Server Whitelist False...')
        perm_node = 'server.whitelist.false'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')
        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Whitelist = False
            server.attr_update() #This will update the AMPInstance Attributes
        await context.send(f"Server: {server.FriendlyName}, Whitelist set to : `False`")

    @server_whitelist.command(name='test')
    @utils.role_check()
    async def dbserver_whitelist_test(self,context:commands.Context,server=None,user=None):
        """Server Whitelist Test function."""
        self.logger.command(f'{context.author.name} used Database Server Whitelist Test...')
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            user = server.name_Conversion(context,user)
            # server_whitelist = server.getWhitelist()
            # print(server_whitelist)
            await context.send(f'Test Function for Server Whitelist {server}{user[0]["name"]}')

    @server_whitelist.command(name='add')
    @utils.role_check()
    async def amp_server_whitelist_add(self,context:commands.Context,server,user):
        """Adds User to Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Add...')
        perm_node = 'server.whitelist.add'
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            user = server.name_Conversion(context,user)
            if user != None:
                server.addWhitelist(user[0]['name'])
                await context.send(f'User: {user[0]["name"]} was whitelisted on Server: {server.FriendlyName}')

    @server_whitelist.command(name='remove')
    @utils.role_check()
    async def amp_server_whitelist_remove(self,context:commands.Context,server,user):
        """Remove a User from the Servers Whitelist"""
        self.logger.command(f'{context.author.name} used AMP Server Whitelist Remove...')
        perm_node = 'server.whitelist.remove'
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            #Converts the name to the proper format depending on the server type
            user = server.name_Conversion(context,user)

            if user != None:
                server.removeWhitelist(user[0]['name'])
                await context.send(f'User: {user[0]["name"]} was removed from the Whitelist on Server: {server.FriendlyName}')


    #This Section is DBServer Attributes -----------------------------------------------------------------------------------------------------
    @server.command(name='displayname')
    @utils.role_check()
    async def db_server_displayname_set(self,context:commands.Context,server,name:str):
        """Sets the Display Name for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Display Name')
        perm_node = 'server.displayname'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).DisplayName = name
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f"Set {server.FriendlyName} Display Name to {name}")

    @server.command(name='description')
    @utils.role_check()
    async def db_server_description(self,context:commands.Context,server,desc:str):
        """Sets the Description for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Description')
        perm_node = 'server.description'
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Description = desc
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f"Set {server.FriendlyName} Description to {desc}")
        
    @server.command(name='ip')
    @utils.role_check()
    async def db_server_ip(self,context:commands.Context,server,ip:str):
        """Sets the IP for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server IP')
        perm_node = 'server.ip'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).IP = ip
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f"Set {server.FriendlyName} IP to {ip}")

    @server.group(name='donator')
    @utils.role_check()
    async def db_server_donator(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')
    
    @db_server_donator.command(name='true')
    @utils.role_check()
    async def db_server_donator_true(self,context:commands.Context,server):
        """Sets Donator Only to True for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Donator Only True')
        perm_node = 'server.donator.true'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Donator = True
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f"Set {server.FriendlyName} Donator Only to True")

    @db_server_donator.command(name='false')
    @utils.role_check()
    async def db_server_donator_false(self,context:commands.Context,server):
        """Sets Donator Only to True for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Donator Only False')
        perm_node = 'server.donator.false'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Donator = False
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f"Set {server.FriendlyName} Donator Only to False")

    @server.group(name='console')
    @utils.role_check()
    async def db_server_console(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')
    
    @db_server_console.command(name='on')
    @utils.role_check()
    async def db_server_console_on(self,context:commands.Context,server):
        """Turns the Console on for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Console On...')
        perm_node = 'server.console.on'
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Console_Flag = True
            server.attr_update() #This will update the AMPConsole Attributes

            if self.AMPThreads[server.InstanceID].console_thread_running != True:
                self.AMPThreads[server.InstanceID].console_thread.start()
                await context.send(f"Starting {server.FriendlyName} Console Thread.")

            await context.send(f'Console for {server.FriendlyName} is already running.')


    @db_server_console.command(name='off')      
    @utils.role_check()
    async def db_server_console_off(self,context:commands.Context,server):
        """Turns the Console off for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Console Off...')
        perm_node = 'server.console.off'

        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        if server != None:
            self.DB.GetServer(InstanceID= server.InstanceID).Console_Flag = False
            server.attr_update() #This will update the AMPConsole Attributes

            if self.AMPThreads[server.InstanceID].console_thread_running == True:
                self.AMPThreads[server.InstanceID].console_thread_running = False
                await context.send(f"Stopping {server.FriendlyName} Console Thread.")

            await context.send(f"Turned {server.FriendlyName} Console Off.")

    @db_server_console.command(name='channel')
    @utils.role_check()
    async def db_server_console_channel_set(self,context:commands.Context,server,channel):
        """Sets the Console Channel for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Console Channel')
        perm_node = 'server.console.channel'

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
    async def db_server_console_filter(self,context:commands.Context,server,flag:str):
        """Sets the Console Filter"""
        self.logger.command(f'{context.author.name} used Database Server Console Filtered True...')
        perm_node = 'server.console.filter'

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
    async def db_server_chat(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_server_chat.command(name='channel')
    @utils.role_check()
    async def db_server_chat_channel_set(self,context:commands.Context,server,channel:str):
        """Sets the Chat Channel for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Chat Channel')
        perm_node = 'server.chat.channel'

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

    @server.command(name='role')
    @utils.role_check()
    async def db_server_discord_role_set(self,context:commands.Context,server,role:str):
        """Sets the Discord Role for the provided Server"""
        self.logger.command(f'{context.author.name} used Database Server Discord Role')
        perm_node = 'server.role'
        server = self.uBot.serverparse(server,context,context.guild.id)
        if server == None:
            return await context.send(f'Unable to find a unique Server matching the provided name, please be more specific.')

        role = self.uBot.roleparse(role,context,context.guild.id)
        if role == None:
            return await context.send(f'Unable to find the provided role, please try again.')

        if server != None and role != None:
            self.DB.GetServer(server.InstanceID).Discord_Role = role.id
            server.attr_update() #This will update the AMPInstance Attributes
            await context.send(f'Set {server.FriendlyName} Discord Role to {role.name}')

        
async def setup(client):
    await client.add_cog(Server(client))