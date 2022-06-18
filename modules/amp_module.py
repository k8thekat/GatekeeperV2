import os
import datetime
from pprint import pprint

import utils
import modules.AMP as AMP
import logging
import modules.database as DB


import discord
from discord.ext import commands
from discord.ui import Button,View

class AMP_Module(commands.Cog):
    def __init__ (self,client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()
        
        self.AMPHandler = AMP.getAMPHandler()
        self.AMPInstances = self.AMPHandler.AMP_Instances

        self.AMPHandler.set_discord_client(self._client)   #This is to get the Discord Client functionality into AMPHandler and AMPConsole class

        self.DB = DB.getDatabase()
        #self.DBconfig = self.DB.GetConfig()

        self.server_list = self.amp_server_list
        self.logger.info(f'**SUCCESS** Loading {self.name.replace("amp","AMP")}')
   
        self.uBot = utils.botUtils(client)
        
        
    @commands.Cog.listener('on_message')
    async def on_message(self,message):
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            self.logger.info(f'On Message Event for {self.name}')
            return message

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before,user_after):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.info(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before,user_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Removed {self.name}: {member}')
        return member

    @commands.hybrid_group(name='server')
    @utils.role_check() #Only Needed on the group Command
    async def amp_server(self,context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...')

    @amp_server.command(name='list',description='Retrieves a list of AMP Instances')
    @utils.role_check()
    async def amp_server_list(self,context):
        #Check DB for Nicknames and add them to the list; possibly swap out? Rank dependent?
        #server_list = []
        #for server in self.AMPInstances:
            #server_list.append(self.AMPInstances[server].FriendlyName)
            #server is the InstanceID (use it as a dictionary key)
        for embed in self.uBot.server_list_embed(context):
            await context.send(embed = embed)

    @amp_server.command(name='start',description='Starts the AMP Instance')
    @utils.role_check()
    async def amp_server_start(self,context,server):
        self.logger.info('AMP Server Start Initiated...')
        server = await self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            server.StartInstance()
            await context.send(f'Starting the AMP Instance {server.FriendlyName}')
    
    @amp_server.command(name='stop',description='Stops the AMP Instance')
    @utils.role_check()
    async def amp_server_stop(self,context,server):
        server = await self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            server.StopInstance()
            await context.send(f'Stopping the AMP Instance {server.FriendlyName}')

    @amp_server.command(name='restart',description='Restarts the AMP Instance')
    @utils.role_check()
    async def amp_server_restart(self,context,server):
        server = await self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            server.RestartInstance()
            await context.send(f'Restarting the AMP Instance {server.FriendlyName}')
    
    @amp_server.command(name='kill',description='Kills the AMP Instance')
    @utils.role_check()
    async def amp_server_kill(self,context,server):
        server = await self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            server.KillInstance()
            await context.send(f'Killing the AMP Instance {server.FriendlyName}')

    @amp_server.command(name='msg',description='AMP Console Message/Commands')
    @utils.role_check()
    async def amp_server_message(self,context,server:str,message:str):
        server = await self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            console_reply = server.ConsoleMessage(message)
            msg_to_send = []
            for message in console_reply['ConsoleEntries']:
                msg_to_send.append(message['Contents'])
            await context.send('\n'.join(msg_to_send))

    @amp_server.command(name='backup',description='AMP Console Message/Commands')
    @utils.role_check()
    async def amp_server_backup(self,context,server):
        server = await self.uBot.serverparse(context,context.guild.id,(server))
        if server != None:
            title = f'%s generated backup',context.author.display_name
            description = f'Created at %s by %s',datetime.datetime.now(),context.author.display_name
            server.takeBackup(title=title,description=description)
            await context.send(f'{server.FriendlyName} Backup' + description)
        
    @amp_server.command(name='status',description='AMP Instance Status(TPS, Player Count, CPU Usage, Memory Usage and Online Players)')
    @utils.role_check()
    async def amp_server_status(self,context,server):
        server = await self.uBot.serverparse(context,context.guild.id,(server))
        if server != None:
            tps,Users,cpu,Memory,Uptime = server.getStatus()
            Users_online = ', '.join(server.getUserList())
            if len(Users_online) == 0:
                Users_online = 'None'
            view = utils.StatusView()
            utils.CustomButton(server,view,server.StartInstance,'Start',callback_label='Starting...',callback_disabled=True)
            utils.StopButton(server,view,server.StopInstance)
            utils.RestartButton(server,view,server.RestartInstance)
            utils.KillButton(server,view,server.KillInstance)
            await context.send(embed= self.uBot.server_status_embed(context,server,tps,Users,cpu,Memory,Uptime,Users_online))
            await context.send(view=view)

    @amp_server.command(name='test',description='AMP test Function')
    @utils.role_check()
    async def amp_server_test(self,context,server):
        """This is my AMP_Module Server Test Function"""
        server = await self.uBot.serverparse(context,context.guild.id,(server))
        await context.send(embed = self.uBot.server_whitelist_embed(context,server))
        # if server != None:
        #     print(server)
        #     print(server.getAPItest)
        # view = utils.StatusView()
        # utils.CustomButton(server,view,server.StartInstance,'Start',callback_label='Starting...',callback_disabled=True)
        # utils.StopButton(server,view,server.StopInstance)
        # utils.RestartButton(server,view,server.RestartInstance)
        # utils.KillButton(server,view,server.KillInstance)
        # msg = self.uBot.default_embedmsg(context,title= server.FriendlyName,description='Test Embed',field='Status',field_value='**6/10 Players**')
        # await context.send(embed=msg)
        # await context.send(view=view)

    @amp_server.command(name='users',description='AMP Instance User List(Display Names)')
    @utils.role_check()
    async def amp_server_users_list(self,context,server):
        server = await self.uBot.serverparse(context,context.guild.id,(server))
        if server != None:
            await context.send(', '.join(server.getUserList()))

    
    async def amp_server_console_init(self):
        print()


async def setup(client):
    await client.add_cog(AMP_Module(client))