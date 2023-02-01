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
from discord.app_commands import Choice

import utils
import utils_ui
import utils_embeds
import AMP_Handler
import DB as DB
import modules.banner_creator as BC


class Banner(commands.Cog):
    def __init__ (self, client:discord.Client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger() #Point all print/logging statments here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP #Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances #Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DB.DBConfig

        self.uBot = utils.botUtils(client)
        self.uiBot = utils_ui
        self.dBot = utils.discordBot(client)
        self.BC = BC

        #Leave this commented out unless you need to create a sub-command.
        self.uBot.sub_command_handler('server', self.amp_banner) #This is used to add a sub command(self,parent_command,sub_command)
        self.uBot.sub_command_handler('bot', self.banner)
        self.logger.info(f'**SUCCESS** Loading Module **{self.name.title()}**')
        
    async def autocomplete_banners(self, interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """This is for a file listing of the `resources/banners` path."""
        banners = []
        _cwd = pathlib.Path.cwd().joinpath('resources/banners')
        banner_file_list = _cwd.iterdir()
        for entry in banner_file_list:
            banners.append(entry.name)
        return [app_commands.Choice(name=banner, value=banner) for banner in banners if current.lower() in banner.lower()]

    async def banner_editor(self, context:commands.Context, amp_server:AMP_Handler.AMP.AMPInstance, db_server_banner=None):
        """Handles sending the banner."""
        db_server = self.DB.GetServer(amp_server.InstanceID)

        db_server_banner = db_server.getBanner()
        #Send a message so we can have a message.id to eidt later.
        sent_msg = await context.send('Creating Banner Editor...', ephemeral= True, delete_after= 60)

        #Create my View first
        editor_view = self.uiBot.Banner_Editor_View(db_banner=db_server_banner, amp_server= amp_server, banner_message = sent_msg)
        banner_file = self.uiBot.banner_file_handler(self.BC.Banner_Generator(amp_server, db_server.getBanner())._image_())
        await sent_msg.edit(content= '**Banner Editor**', attachments= [banner_file], view= editor_view)
   
    @commands.hybrid_group(name='banner')
    @utils.role_check()
    async def amp_banner(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral= True, delete_after= 30)

    @amp_banner.command(name='background')
    @app_commands.autocomplete(server= utils.autocomplete_servers)
    @app_commands.autocomplete(image= autocomplete_banners)
    @utils.role_check()
    async def amp_banner_background(self, context:commands.Context, server, image):
        """Sets the Background Image for the selected Server."""
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral= True, delete_after= self._client.Message_Timeout)

        db_server = self.DB.GetServer(amp_server.InstanceID)
        banner = db_server.getBanner()
        image_path = pathlib.Path.cwd().joinpath('resources/banners').as_posix() + '/' + image
        banner.background_path = image_path
        amp_server._setDBattr()
        my_image = Image.open(image_path)
        await context.send(content= f'Set **{amp_server.FriendlyName}** Banner Image to', file = self.uiBot.banner_file_handler(my_image), ephemeral= True, delete_after= self._client.Message_Timeout)
    
    @amp_banner.command(name= 'settings')
    @utils.role_check()
    @app_commands.autocomplete(server= utils.autocomplete_servers)
    async def amp_banner_settings(self, context:commands.Context, server):
        """Prompts the Banner Editor Menu"""
        self.logger.command(f'{context.author.name} used Server Banner Settings Editor...')
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral= True, delete_after= self._client.Message_Timeout)

        await self.banner_editor(context, amp_server)

    @commands.hybrid_group(name='banner_settings')
    async def banner(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after= self._client.Message_Timeout)

    @banner.command(name='auto_update')
    @utils.role_check()
    @app_commands.choices(flag= [Choice(name='True', value= 1), Choice(name='False', value= 0)])
    async def banner_autoupdate(self, context:commands.Context, flag: Choice[int]= 1):
        """Toggles Auto Updating of Banners On or Off. (Only for `/server Display`)"""
        self.logger.command(f'{context.author.name} used Bot Display Banners Auto Update...')
        
        if flag.value == 1:
            self.DBConfig.SetSetting('Banner_Auto_Update', True)
            return await context.send(f'All set! The bot will __Auto Update the Banners__ from `/server display` every minute.', ephemeral= True, delete_after= self._client.Message_Timeout)
        if flag.value == 0:
            self.DBConfig.SetSetting('Banner_Auto_Update', False)
            return await context.send(f"Well, I guess I won't update the Banners anymore.", ephemeral= True, delete_after= self._client.Message_Timeout)
        else:
            return await context.send('Hey! You gotta pick `True` or `False`.', ephemeral= True, delete_after= self._client.Message_Timeout)

    @banner.command(name='type')
    @utils.role_check()
    @app_commands.choices(type= [Choice(name='Custom Banner Images', value= 1), Choice(name='Discord Embeds', value= 0)])
    async def banner_type(self, context:commands.Context, type:Choice[int]= 0):
        """Selects which type of Server Banner(s) to Display, either Embeds or Images"""
        self.logger.command(f'{context.author.name} used Bot Banners Type...')
        
        if type.value == 0:
            self.DBConfig.SetSetting('Banner_Type', 0)
            return await context.send('Look at me, using **Discord Embeds**.. psht..I mean they atleast work.', ephemeral= True, delete_after= self._client.Message_Timeout)

        if type.value == 1:
            self.DBConfig.SetSetting('Banner_Type', 1)
            return await context.send('Looks like we are going to be using **Custom Banner Images**! Oooooh yea~', ephemeral= True, delete_after= self._client.Message_Timeout) 


async def setup(client):
    await client.add_cog(Banner(client))