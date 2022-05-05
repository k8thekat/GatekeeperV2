import os
import datetime
from re import U

import utils
import modules.AMP as AMP
import logging
import pprint

import discord
from discord.ext import commands
from discord.ui import Button,View

class AMP_Module(commands.Cog):
    def __init__ (self,client):
        self._client = client
        self.logger = logging.getLogger()
        self.AMPInstances = AMP.AMP_Instances
        self.logger.info('AMP Intigration Module Loaded')
        #self.sub_command_handler()
        self.uBot = utils.botUtils(client)
        
    @commands.Cog.listener('on_message')
    async def on_message(self,message):
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author == self._client.user:
            return message
        self.logger.info(f'On Message {os.path.basename(__file__)}: {message}')

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before,user_after):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.info(f'User Update {os.path.basename(__file__)}: {user_before} into {user_after}')
        return user_before,user_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Removed {os.path.basename(__file__)}: {member}')
        return member

    @commands.group(name='server')
    @utils.role_check() #Only Needed on the group Command
    async def server(self,context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...')

    @server.command(name='list',description='Retrieves a list of AMP Instances')
    async def server_list(self,context):
        #Check DB for Nicknames and add them to the list; possibly swap out? Rank dependent?
        for server in self.AMPInstances:
            #server is the InstanceID (use it as a dictionary key)
            await context.send(self.AMPInstances[server].FriendlyName)

    @server.command(name='start',description='Starts the AMP Instance')
    async def server_start(self,context,*server):
        self.logger.info('AMP Server Start Initiated...')
        server = await self.uBot.serverparse(context,context.guild.id,server)
        server.StartInstance()
        await context.send(f'Starting the AMP Instance {server.FriendlyName}')
    
    @server.command(name='stop',description='Stops the AMP Instance')
    async def server_stop(self,context,*server):
        server = await self.uBot.serverparse(context,context.guild.id,server)
        server.StopInstance()
        await context.send(f'Stopping the AMP Instance {server.FriendlyName}')

    @server.command(name='restart',description='Restarts the AMP Instance')
    async def server_restart(self,context,*server):
        server = await self.uBot.serverparse(context,context.guild.id,server)
        server.RestartInstance()
        await context.send(f'Restarting the AMP Instance {server.FriendlyName}')
    
    @server.command(name='kill',description='Kills the AMP Instance')
    async def server_kill(self,context,*server):
        server = await self.uBot.serverparse(context,context.guild.id,server)
        server.KillInstance()
        await context.send(f'Killing the AMP Instance {server.FriendlyName}')

    @server.command(name='msg',description='AMP Console Message/Commands')
    async def server_message(self,context,server:str,*message):
        server = await self.uBot.serverparse(context,context.guild.id,server)
        console_reply = server.ConsoleMessage(message)
        msg_to_send = []
        for message in console_reply['ConsoleEntries']:
            msg_to_send.append(message['Contents'])
        await context.send('\n'.join(msg_to_send))

    @server.command(name='backup',description='AMP Console Message/Commands')
    async def server_backup(self,context,server):
        server = await self.uBot.serverparse(context,context.guild.id,(server))
        title = f'%s generated backup',context.author.display_name
        description = f'Created at %s by %s',datetime.datetime.now(),context.author.display_name
        server.takeBackup(title=title,description=description)
        await context.send(f'Backup' + description)
        
    @server.command(name='status',description='AMP Instance Status(TPS, Player Count, CPU Usage, Memory Usage and Online Players)')
    async def server_status(self,context,*param):
        parameter = ' '.join(param)
        server = await self.uBot.serverparse(context,context.guild.id,(parameter))
        tps,Users,cpu,Memory,Uptime = server.getStatus()
        Users_online = ', '.join(server.getUserList())
        if len(Users_online) == 0:
            Users_online = 'None'
        await context.send(embed= self.uBot.server_status_embed(context,server,tps,Users,cpu,Memory,Uptime,Users_online))

    @server.command(name='test',description='AMP test Function')
    async def server_test(self,context,*param):
        parameter = ' '.join(param)
        print(parameter)
        server = await self.uBot.serverparse(context,context.guild.id,(parameter))
        view = utils.StatusView()
        utils.CustomButton(server,view,'Start',callback_label='Starting...',callback_disabled=True)
        utils.StopButton(server,view)
        msg = self.uBot.default_embedmsg(context,title= server.FriendlyName,description='Test Embed',field='Status',field_value='**6/10 Players**')
        await context.send(embed=msg)
        await context.send(view=view)

    @server.command(name='users',description='AMP Instance User List(Display Names)')
    async def server_users_list(self,context,*param):
        parameter = ' '.join(param)
        server = await self.uBot.serverparse(context,context.guild.id,(parameter))
        await context.send(', '.join(server.getUserList()))
        

def setup(client):
    client.add_cog(AMP_Module(client))