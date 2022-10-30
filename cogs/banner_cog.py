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
import io
import logging
import pathlib
from PIL import Image
import re

import discord
from discord import app_commands
from discord.ext import commands

import utils
import AMP as AMP
import DB as DB
import modules.banner_creator as BC


class Banner(commands.Cog):
    def __init__ (self, client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger() #Point all print/logging statments here!

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP #Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances #Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBCOnfig = self.DB.GetConfig()

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        self.BC = BC

        #Leave this commented out unless you need to create a sub-command.
        self.uBot.sub_command_handler('server', self.amp_banner) #This is used to add a sub command(self,parent_command,sub_command)
        self.logger.info(f'**SUCCESS** Loading Module **{self.name}**')

    async def autocomplete_servers(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for AMP Instance Names"""
        choice_list = self.AMPHandler.get_AMP_instance_names()
        return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

    async def autocomplete_banners(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """This is for a file listing of the `resources/banners` path."""
        banners = []
        _cwd = pathlib.Path.cwd().joinpath('resources/banners')
        banner_file_list = _cwd.iterdir()
        for entry in banner_file_list:
            banners.append(entry.name)
        return [app_commands.Choice(name=banner, value=banner) for banner in banners if current.lower() in banner.lower()]

    async def banner_editor(self, context:commands.Context, amp_server:AMP.AMPInstance, db_server_banner=None):
        """Handles sending the banner."""
        db_server = self.DB.GetServer(amp_server.InstanceID)

        db_server_banner = db_server.getBanner()
        #Send a message so we can have a message.id to eidt later.
        sent_msg = await context.send('Creating Banner Editor...', ephemeral= True)

        #Create my View first
        editor_view = utils.Banner_Editor_View(db_banner=db_server_banner, amp_server= amp_server, banner_message = sent_msg)
        banner_file = utils.banner_file_handler(self.BC.Banner_Generator(amp_server, db_server.getBanner())._image_())
        await sent_msg.edit(content= '**Banner Editor**', attachments= [banner_file], view= editor_view)
   
    @commands.hybrid_group(name='banner')
    @utils.role_check()
    async def amp_banner(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True)

    @amp_banner.command(name= 'test')
    @app_commands.autocomplete(server = autocomplete_servers)
    #@app_commands.autocomplete(path= autocomplete_banners)
    @utils.author_check(144462063920611328)
    async def amp_banner_test(self, context:commands.Context, server):
        """ Usage case is for test display of banners based upon the picked Server."""
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True)

        db_server = self.DB.GetServer(amp_server.InstanceID)
        await context.send(file= utils.banner_file_handler(self.BC.Banner_Generator(amp_server, db_server.getBanner())._image_()))

    @amp_banner.command(name='background')
    @app_commands.autocomplete(server= autocomplete_servers)
    @app_commands.autocomplete(image= autocomplete_banners)
    @utils.role_check()
    async def amp_banner_background(self, context:commands.Context, server, image):
        """Sets the Background Image for the selected Server."""
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True)

        db_server = self.DB.GetServer(amp_server.InstanceID)
        banner = db_server.getBanner()
        image_path = pathlib.Path.cwd().joinpath('resources/banners').as_posix() + '/' + image
        banner.background_path = image_path
        my_image = Image.open(image_path)
        await context.send(content= f'Set **{amp_server.FriendlyName}** Banner Image to', file = utils.banner_file_handler(my_image))
    
    @amp_banner.command(name= 'settings')
    @utils.role_check()
    @app_commands.autocomplete(server= autocomplete_servers)
    async def amp_banner_settings(self, context:commands.Context, server):
        """Prompts the Banner Editor Menu"""
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True)

        await self.banner_editor(context, amp_server)

async def setup(client):
    await client.add_cog(Banner(client))