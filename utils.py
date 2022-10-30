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
import logging
import json
import requests
import pathlib
import aiohttp
import sys
import re
import io
import PIL
from PIL import Image

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button,View,Select,Modal,TextInput
import asyncio

import DB
import AMP
import modules.banner_creator as BC

async def async_rolecheck(context:commands.Context, perm_node:str=None):
    DBHandler = DB.getDBHandler()
    DBConfig = DBHandler.DBConfig
    logger = logging.getLogger(__name__)
    logger.dev(f'Permission Context command node {str(context.command).replace(" ",".")}')
   
    author = context
    if type(context) != discord.Member:
        author = context.author

    #This fast tracks role checks for Admins, which also allows the bot to still work without a Staff Role set in the DB
    admin = author.guild_permissions.administrator
    if admin == True:
        logger.command(f'Permission Check Okay on {author}')
        return True

    #This handles Custom Permissions for people with the flag set.
    #print('Permission Setting', DBConfig.GetSetting('Permissions'))
    if DBConfig.GetSetting('Permissions') == 'Custom':
        if perm_node == None:
            perm_node = str(context.command).replace(" ",".")
        #print(perm_node)
        bPerms = get_botPerms()
        bPerms.perm_node_check(perm_node,context)
        if bPerms.perm_node_check == False:
            logger.command(f'Permission Check Failed on {author} missing {perm_node}')
            return False
        else:
            logger.command(f'Permission Check Okay on {author}')
            return True

    #This is the final check before we attempt to use the "DEFAULT" permissions setup.
    if DBConfig.GetSetting('Moderator_role_id') == None:
        await context.send(f'Please have an Adminstrator run `/bot moderator (role)` or consider setting up Custom Permissons.', ephemeral=True)
        logger.error(f'DBConfig Moderator role has not been set yet!')
        return False

    staff_role,author_top_role = 0,0
    guild_roles = context.guild.roles

    if type(context) == discord.member.Member:
        top_role_id = context.top_role.id
        author = context.name
    else:
        top_role_id = context.message.author.top_role.id
        author = context.message.author

    for i in range(0,len(guild_roles)):
        if guild_roles[i].id == top_role_id:
            author_top_role = i

        if str(guild_roles[i].id) == DBConfig.Moderator_role_id:
            staff_role = i
            
    if author_top_role > staff_role:
        logger.command(f'Permission Check Okay on {author}')
        return True
        
    else:
        logger.command(f'Permission Check Failed on {author}')
        await context.send('You do not have permission to use that command...', ephemeral=True)
        return False

def role_check():
    """Use this before any Commands that require a Staff/Mod level permission Role, this will also check for Administrator"""
    #return commands.check(async_rolecheck(permission_node=perm))
    return commands.check(async_rolecheck)            

def author_check(user_id:int=None):
    """Checks if User ID matchs Context User ID"""
    async def predicate(context:commands.Context):
        if context.author.id == user_id:
            return True
        else:
            await context.send('You do not have permission to use that command...', ephemeral=True)
            return False
    return commands.check(predicate)

def guild_check(guild_id:int=None):
    """Use this before any commands to limit it to a certain guild usage."""
    async def predicate(context:commands.Context):
        if context.guild.id == guild_id:
            return True
        else:
            await context.send('You do not have permission to use that command...', ephemeral=True)
            return False
    return commands.check(predicate)

async def permissions_autocomplete(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
    """This is for Default or Custom permission setting via /bot permissions"""
    types = ['Default', 'Custom']
    return [app_commands.Choice(name=permission, value=permission) for permission in types if current.lower() in permission.lower()]

async def banner_type_autocomplete(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
    """This is for Default or Custom permission setting via /bot permissions"""
    types = ['Discord Embeds', 'Custom Images']
    return [app_commands.Choice(name=permission, value=permission) for permission in types if current.lower() in permission.lower()]

async def autocomplete_bool(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
    """True or False Autocomplete reply"""
    booleans = ['True', 'False']
    return [app_commands.Choice(name=bool, value=bool) for bool in booleans if current.lower() in bool.lower()]

async def autocomplete_permission_roles(interaction:discord.Interaction,current:str) -> list[app_commands.Choice[str]]:
    """This is for roles inside of the bot_perms file. Returns a list of all the roles.."""
    bPerms = get_botPerms()
    choice_list = bPerms.get_roles()
    return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

async def autocomplete_discord_roles(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
    """This is for all the roles in the discord server. Returns the choice list"""
    choice_list = []
    for role in interaction.guild.roles:
        choice_list.append(role.name)
    return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

async def autocomplete_discord_channels(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
    """This is for all the channels in the discord server. Returns the choice list"""
    choice_list = []
    for channel in interaction.guild.channels:

        if channel.category != None:
            channel = f'{channel.category} -> ' + channel.name
            
            if channel not in choice_list:
                choice_list.append(channel)

        else:
            choice_list.append(channel.name)

    return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

async def autocomplete_discord_users(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
    """This is for all the users in the discord server. Returns the choice list"""
    choice_list = []
    for user in interaction.guild.members:
        choice_list.append(user.name)
    return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()][:25]

#This is my Template for Autocomplete
async def autocomplete_template(interaction:discord.Interaction, current:str, choice_list:list=None) -> list[app_commands.Choice[str]]:
    """Default Autocomplete template, simply pass in a list of strings and it will handle it."""
    return [app_commands.Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

class ServerButton(Button):
    """Custom Start Button for when Servers are Offline."""
    def __init__(self, server:AMP.AMPInstance, view:discord.ui.View, function, label:str, callback_label:str, callback_disabled:bool, style=discord.ButtonStyle.green, context=None):
        super().__init__(label=label, style=style, custom_id=label)
        self.logger = logging.getLogger()
        self.server = server
        self.context = context
        self._label = label
        self.permission_node = 'server.' + self._label.lower()

        self.callback_label = callback_label
        self.callback_disabled = callback_disabled

        self._function = function
        self._view = view
        view.add_item(self)

    async def callback(self, interaction):
        """This is called when a button is interacted with."""
        if not await async_rolecheck(interaction.user, self.permission_node):
            return
        self._interaction = interaction
        self.label = self.callback_label
        self.disabled = self.callback_disabled
        self._function()
        await interaction.response.edit_message(view=self._view)
        await asyncio.sleep(30)
        await self.reset()

    async def reset(self):
        self.logger.info('Resetting Buttons...')
        self.label = self._label
        self.disabled = False
        #server_embed = await self._view.update_view()
        await self._interaction.followup.edit_message(message_id=self._interaction.message.id, view=self._view)

class StartButton(ServerButton):
    def __init__(self, server, view, function):
        super().__init__(server=server, view=view, function=function, label='Start', callback_label='Starting...', callback_disabled=True, style=discord.ButtonStyle.green)

class StopButton(ServerButton):
    def __init__(self, server, view, function):
        super().__init__(server=server, view=view, function=function, label='Stop', callback_label='Stopping...', callback_disabled=True, style=discord.ButtonStyle.red)

class RestartButton(ServerButton):
    def __init__(self, server, view, function):
        super().__init__(server=server, view=view, function=function, label='Restart', callback_label='Restarting...', callback_disabled=True, style=discord.ButtonStyle.blurple)

class KillButton(ServerButton):
    def __init__(self, server, view, function):
        super().__init__(server=server, view=view, function=function, label='Kill', callback_label='Killed...', callback_disabled=True, style=discord.ButtonStyle.danger)
    
class StatusView(View):
    def __init__(self, timeout=180, context:commands.Context=None, amp_server:AMP.AMPInstance=None):
        super().__init__(timeout=timeout)
        self.server = amp_server
        self.context = context
        self.uBot = botUtils()

    async def on_timeout(self):
        """This Removes all the Buttons after timeout has expired"""
        self.stop()

def banner_file_handler(image:Image.Image):
    with io.BytesIO() as image_binary:
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        return discord.File(fp=image_binary, filename='image.png')

class Edited_DB_Banner():
    """DB_Banner for Banner Editor"""
    def __init__(self, db_banner:DB.DBBanner):
        self._db_banner = db_banner

        self.invalid_keys = ['_db','ServerID','background_path'] 
        self.reset_db()

    def save_db(self):
        for key in self._db_banner.attr_list:
            if key in self.invalid_keys:
                continue

            if getattr(self._db_banner, key) != getattr(self, key):
                setattr(self._db_banner, key, getattr(self, key))

        return self._db_banner
    
    def reset_db(self):
        for key in self._db_banner.attr_list:
            if key in self.invalid_keys:
                continue
            setattr(self, key, getattr(self._db_banner, key))
        return self._db_banner
    
class Banner_Editor_View(View):
    def __init__(self, amp_server: AMP.AMPInstance, db_banner: DB.DBBanner, banner_message: discord.Message, timeout=None):
        self.logger = logging.getLogger()

        self._original_db_banner = db_banner
        self._edited_db_banner = Edited_DB_Banner(db_banner)
        self._banner_message = banner_message #This is the message that the banner is attached to.
        self._amp_server = amp_server
        self._first_interaction = discord.Interaction
        self._first_interaction_bool = True
        
        self._banner_editor_select = Banner_Editor_Select(custom_id= 'banner_editor', edited_db_banner= self._edited_db_banner, banner_message= self._banner_message, view= self, amp_server= self._amp_server)
        super().__init__(timeout=timeout)
        self.add_item(self._banner_editor_select)
        self.add_item(Save_Banner_Button(banner_message= self._banner_message, edited_banner= self._edited_db_banner, server= self._amp_server))
        self.add_item(Reset_Banner_Button(banner_message= self._banner_message, edited_banner= self._edited_db_banner, server= self._amp_server))
        self.add_item(Cancel_Banner_Button(banner_message= self._banner_message))

class Banner_Editor_Select(Select):
    def __init__(self, edited_db_banner: Edited_DB_Banner, view: Banner_Editor_View, amp_server: AMP.AMPInstance, banner_message: discord.Message, custom_id:str= None, min_values:int= 1, max_values:int= 1, row:int= None, disabled:bool= False, placeholder:str= None):
        self.logger = logging.getLogger()
        self._banner_view = view

        self._edited_db_banner = edited_db_banner
        self._banner_message = banner_message

        self._amp_server = amp_server
        options = [
            discord.SelectOption(label= "Blur Background Intensity", value= 'blur_background_amount'),
            discord.SelectOption(label= "Header Font Color", value= 'color_header'),
            discord.SelectOption(label= "Nickname Font Color", value= 'color_nickname'),
            discord.SelectOption(label= "Body Font Color", value= 'color_body'),
            discord.SelectOption(label= "IP Font Color", value= 'color_IP'),
            discord.SelectOption(label= "Whitelist Open Font Color", value= 'color_whitelist_open'),
            discord.SelectOption(label= "Whitelist Closed Font Color", value= 'color_whitelist_closed'),
            discord.SelectOption(label= "Donator Font Color", value= 'color_donator'),
            discord.SelectOption(label= "Server Online Font Color", value= 'color_status_online'),
            discord.SelectOption(label= "Server Offline Font Color", value= 'color_status_offline'),
            discord.SelectOption(label= "Player Limit Minimum Font Color", value= 'color_player_limit_min'),
            discord.SelectOption(label= "Player Limit Maximum Font Color", value= 'color_player_limit_max'),
            discord.SelectOption(label= "Players Online Font Color", value= 'color_player_online')
            ]
        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'blur_background_amount':
            input_type = 'int'
        else:
            input_type = 'color'

        self._banner_modal = Banner_Modal(input_type= input_type, title= f'{self.values[0].replace("_", " ")}', select_value= self.values[0], edited_db_banner= self._edited_db_banner, banner_message= self._banner_message, view= self._banner_view, amp_server= self._amp_server)
        await interaction.response.send_modal(self._banner_modal)
        
        self._first_interaction = False

class Banner_Modal(Modal):
    def __init__(self, input_type: str, select_value: str, title: str, view: Banner_Editor_View, edited_db_banner: Edited_DB_Banner, banner_message: discord.Message, amp_server: AMP.AMPInstance, timeout= None , custom_id= 'Banner Modal'):
        self._edited_db_banner = edited_db_banner
        self._banner_message = banner_message
        self._banner_view = view

        self._amp_server = amp_server

        self._select_value = select_value #This is the Select Option Choice that was made.
        self._input_type = input_type
        super().__init__(title= title, timeout= timeout, custom_id= custom_id)

        if self._input_type == 'color':
            self._color_code_input = Banner_Color_Input(edited_db_banner= self._edited_db_banner, select_value= self._select_value, view= self._banner_view)
            self.add_item(self._color_code_input)

        if self._input_type == 'int':
            self._int_code_input = Banner_Blur_Input(edited_db_banner= self._edited_db_banner, select_value= self._select_value, view= self._banner_view)
            self.add_item(self._int_code_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self._input_type == 'color':
            if await self._color_code_input.callback() == False:
                await interaction.response.send_message(content= f'Please provide a proper Hex color Code. {self._color_code_input._value}', ephemeral= True)
                
          
        if self._input_type == 'int':
            if await self._int_code_input.callback() == False:
                await interaction.response.send_message(f'Please provide a Number only. {self._int_code_input.value}', ephemeral= True)
                
        else:
            await interaction.response.defer()
        await self._banner_message.edit(attachments= [banner_file_handler(BC.Banner_Generator(self._amp_server, self._edited_db_banner)._image_())], view= self._banner_view)
 
class Banner_Color_Input(TextInput):
    def __init__(self, view: Banner_Editor_View, edited_db_banner: Edited_DB_Banner, select_value: str, label: str= "Enter your Hex color code below.", style= discord.TextStyle.short, placeholder: str= '#000000', default: str= '#ffffff', required= True, min_length= 3, max_length= 8):
        self._edited_db_banner = edited_db_banner
        self._select_value = select_value
        self._banner_view = view
        super().__init__(label= label, style= style, placeholder= placeholder, default= default, required= required, min_length= min_length, max_length= max_length)

    async def callback(self):
        #Remove the Hex code for validation.
        self._value = self.value
        if self._value[0] == '#':
            self._value = self._value[1:]

        #Validate if Hex Color Code.
        if len(self._value) in [3,4,6,8] and re.search(f'([0-9a-f]{{{len(self._value)}}})$', self._value):
            self._banner_view.logger.dev(f'Set attr for {self._edited_db_banner} {self._select_value} # {self._value}')
            setattr(self._edited_db_banner, self._select_value, '#' + self._value)
            return True
        else:
            return False

class Banner_Blur_Input(TextInput):
    def __init__(self, view: Banner_Editor_View, edited_db_banner: Edited_DB_Banner, select_value: str, label: str= "Blur Background Intensity", style= discord.TextStyle.short, placeholder= 'Enter a Number', default:int= 2, required= True, min_length= 1, max_length= 2):
        self._edited_db_banner = edited_db_banner
        self._select_value = select_value
        self._banner_view = view
        super().__init__(label= label, style= style, placeholder= placeholder, default= default, required= required, min_length= min_length, max_length= max_length)

    async def callback(self):
        if self.value.isalnum() and int(self.value) <= 99:
            self._banner_view.logger.dev(f'Set attr for {self._edited_db_banner} {self._select_value} {self.value}')
            setattr(self._edited_db_banner, self._select_value, int(self.value[0]))
            return True
        else:
            return False

class Save_Banner_Button(Button):
    """Saves the Banners current settings to the DB."""
    def __init__(self, banner_message: discord.Message, server: AMP.AMPInstance, edited_banner: Edited_DB_Banner,  style=discord.ButtonStyle.green):
        super().__init__(label='Save', style=style, custom_id='Save_Button')
        self.logger = logging.getLogger()
        self._amp_server = server
        self._banner_message = banner_message
        self._edited_db_banner = edited_banner

    async def callback(self, interaction):
        """This is called when a button is interacted with."""
        saved_banner = self._edited_db_banner.save_db()
        await interaction.response.defer()
        file = banner_file_handler(BC.Banner_Generator(self._amp_server, saved_banner)._image_())
        await self._banner_message.edit(content='**Banner Settings have been saved.**', attachments= [file], view= None)

class Reset_Banner_Button(Button):
    """Resets the Banners current settings to the original DB."""
    def __init__(self, banner_message: discord.Message, server: AMP.AMPInstance, edited_banner: Edited_DB_Banner, style=discord.ButtonStyle.blurple):
        super().__init__(label='Reset', style=style, custom_id='Reset_Button')
        self.logger = logging.getLogger()
        self._amp_server = server
        self._banner_message = banner_message
        self._edited_db_banner = edited_banner

    async def callback(self, interaction):
        """This is called when a button is interacted with."""
        saved_banner = self._edited_db_banner.reset_db()
        await interaction.response.defer()
        file = banner_file_handler(BC.Banner_Generator(self._amp_server, saved_banner)._image_())
        await self._banner_message.edit(content='**Banner Settings have been reset.**', attachments= [file])

class Cancel_Banner_Button(Button):
    """Cancels the Banner Settings View"""
    def __init__(self, banner_message: discord.Message, style=discord.ButtonStyle.red):
        super().__init__(label='Cancel', style=style, custom_id='Cancel_Button')
        self.logger = logging.getLogger()
        self._banner_message = banner_message

    async def callback(self, interaction):
        """This is called when a button is interacted with."""
        await interaction.response.defer()
        await self._banner_message.edit(content='**Banner Settings Editor has been Cancelled.**', attachments= [], view= None)
    
class discordBot():
    def __init__(self, client:commands.Bot):
        self.botLogger = logging.getLogger(__name__)
        self._client = client
        self.botLogger.debug(f'Utils Discord Loaded')
    
    async def userAddRole(self, user:discord.Member, role:discord.Role, reason:str=None):
        """Adds a Role to a User.\n
        Requires a `<user`> and `<role>` discord object.\n
        Supports `reason`(Optional)"""
        
        self.botLogger.dev('Add Users Discord Role Called...')
        await user.add_roles(role,reason)

    async def userRemoveRole(self, user:discord.Member, role:discord.Role, reason:str=None):
        """Removes a Role from the User.\n
        Requires a `<user>` and `<role>` discord object.\n
        Supports `reason`(Optional)"""

        self.botLogger.dev('Remove Users Discord Role Called...')
        await user.remove_roles(role,reason)

    async def delMessage(self, message:discord.Message, delay:float=None):
        """Deletes the message.\n
        Your own messages could be deleted without any proper permissions. However to delete other people's messages, you need the `manage_messages` permission.\n
        Supports `delay[float]`(Optional)"""

        self.botLogger.dev('Delete Discord Message Called...')
        await message.delete(delay=delay)

    async def channelHistory(self, channel:discord.TextChannel, limit:int=10, before:datetime=None, after:datetime=None, around:datetime=None, oldest_first:bool=False):
        """This will be used to access channel history up to 100. Simple scraper with datetime support."""
        if limit > 100:
            limit = 100
        messages = await channel.history(limit,before,after,around,oldest_first).flatten()
        return messages

    async def editMessage(self ,message:discord.Message , content:str=None, embed:discord.Embed=None, embeds:list[discord.Embed]=None, delete_after:float=None):
        """Edits the message.\n
        The content must be able to be transformed into a string via `str(content)`.\n
        Supports `delete_after[float]`(Optional)"""
        
        self.botLogger.dev('Edit Discord Message Called...')
        await message.edit(content=content, embed=embed, embeds=embeds, delete_after=delete_after)

    async def sendMessage(self, parameter:object, content:str,*, tts:bool=False,embed=None, file:discord.file=None, files:list=None, delete_after:float=None, nonce= None, allowed_mentions=None, reference:object=None):
        #content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, allowed_mentions=None, reference=None, mention_author=None
        """Sends a message to the destination with the content given.\n
        The content must be a type that can convert to a string through `str(content)`. If the content is set to `None` (the default), then the embed parameter must be provided.\n
        To upload a single file, the `file` parameter should be used with a single File object. To upload multiple files, the `files` parameter should be used with a `list` of `File` objects. Specifying both parameters will lead to an exception.\n
        `NOTE:` Using `file` - await channel.send(file=discord.File('my_file.png')) or 
            with open('my_file.png', 'rb') as fp:
                await channel.send(file=discord.File(fp, 'new_filename.png')) 
        `NOTE:` Using `files` - my_files = [discord.File('result.zip'), discord.File('teaser_graph.png')] await channel.send(files=my_files)"""

        self.botLogger.dev('Member Send Message Called...')
        await parameter.send(content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce, allowed_mentions=allowed_mentions, reference=reference)

    async def messageAddReaction(self, message:discord.Message, reaction_id:str):
        """The name and ID of a custom emoji can be found with the client by prefixing ':custom_emoji:' with a backslash. \n
            For example, sending the message '\:python3:' with the client will result in '<:python3:232720527448342530>'.
            `NOTE` Can only use Emoji's the bot has access too"""

        self.botLogger.dev('Message Add Reaction Called...')
        if reaction_id.isnumeric():
            emoji = self._client.get_emoji(int(reaction_id))
            return await message.add_reaction(emoji)

        if not reaction_id.startswith('<') and not reaction_id.endswith('>'):
            emoji = discord.utils.get(self._client.emojis, name= reaction_id)
            return await message.add_reaction(emoji)

        else:
            emoji = reaction_id
            return await message.add_reaction(emoji)

class botUtils():
        def __init__ (self, client:commands.Bot=None):
            self._client = client
            self.logger = logging.getLogger(__name__)
            self.logger.debug('Utils Bot Loaded')

            self.DBHandler = DB.getDBHandler()
            self.DB = self.DBHandler.DB #Main Database object
            self.DBConfig = self.DBHandler.DBConfig

            self.AMPHandler = AMP.getAMPHandler()
            self.AMPInstances = self.AMPHandler.AMP_Instances
            self.AMPServer_Avatar_urls = []

        def str_to_bool(self, parameter:str):
            """Bool Converter"""
            return parameter.lower() == 'true'
            
        def message_formatter(self, message:str):
            """Formats the message for Discord \n
            `Bold = \\x01, \\x02` \n
            `Italic = \\x03, \\x04` \n
            `Underline = \\x05, \\x06` \n"""
            #Bold
            message = message.replace('\x01', '**')
            message = message.replace('\x02', '**')
            #Italic
            message = message.replace('\x03', '*')
            message = message.replace('\x04', '*')
            #Underline
            message = message.replace('\x05', '__')
            message = message.replace('\x06', '__')
            return message

        async def validate_avatar(self, db_server:AMP.AMPInstance):
            """This checks the DB Server objects Avatar_url and returns the proper object type. \n
            Must be either `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated."""
            if db_server.Avatar_url == None:
                return None
            #This handles web URL avatar icon urls.
            if db_server.Avatar_url.startswith("https://") or db_server.Avatar_url.startswith("http://"):
                if db_server.Avatar_url not in self.AMPServer_Avatar_urls:
                    await asyncio.sleep(.5)
                    async with aiohttp.ClientSession() as session:
                        async with session.get(db_server.Avatar_url) as response:
                            if response.status == 200:
                                self.AMPServer_Avatar_urls.append(db_server.Avatar_url)
                                return db_server.Avatar_url
                            else:
                                self.logger.error(f'We are getting Error Code {response.status}, not sure whats going on...')
                                return None
                else:
                    return db_server.Avatar_url
            else:
                return None

        def name_to_uuid_MC(self, name): 
            """Converts an IGN to a UUID/Name Table \n
            `returns 'uuid'` else returns `None`, multiple results return `None`"""
            url = 'https://api.mojang.com/profiles/minecraft'
            header = {'Content-Type': 'application/json'}
            jsonhandler = json.dumps(name)
            post_req = requests.post(url, headers=header, data=jsonhandler)
            minecraft_user = post_req.json()

            if len(minecraft_user) == 0: 
                return None

            if len(minecraft_user) > 1:
                return None

            else:
                return minecraft_user[0]['id'] #returns [{'id': 'uuid', 'name': 'name'}] 

        def name_to_steam_id(self, steamname:str):
            """Converts a Steam Name to a Steam ID returns `STEAM_0:0:2806383`
            """
            #Really basic HTML text scan to find the Title; which has the steam ID in it. Thank you STEAMIDFINDER! <3
            #<title> Steam ID STEAM_0:0:2806383 via Steam ID Finder</title>
            r = requests.get(f'https://www.steamidfinder.com/lookup/{steamname}')
            self.logger.dev('Status Code',r.status_code)
            if r.status_code == 404:
                return None

            title = re.search('(<title>)',r.text)
            start,title_start = title.span()
            title = re.search('(</title>)',r.text)
            title_end,end = title.span()
            #turns into  " STEAM_0:0:2806383 "
            #This should work regardless of the Steam ID length; since we came from the end of the second title backwards.
            steam_id = r.text[title_start+9:title_end-20].strip() 
            self.logger.dev(f'Found Steam ID {steam_id}')
            return steam_id

        def roleparse(self, parameter:str, context:commands.Context, guild_id:int) -> discord.Role: 
            """This is the bot utils Role Parse Function\n
            It handles finding the specificed Discord `<role>` in multiple different formats.\n
            They can contain single quotes, double quotes and underscores. (" ",' ',_)\n
            returns `<role>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.dev('Role Parse Called...')
            #print(dir(self._client),self._client.get_guild(guild_id),guild_id)
            guild = self._client.get_guild(guild_id)
            role_list = guild.roles
            
            #Role ID catch
            if parameter.isnumeric():
                role = guild.get_role(int(parameter))
                self.logger.debug(f'Found the Discord Role {role}')
                return role
            else:
                #This allows a user to pass in a role in quotes double or single
                if parameter.find("'") != -1 or parameter.find('"'):
                    parameter = parameter.replace('"','')
                    parameter = parameter.replace("'",'')

                #If a user provides a role name; this will check if it exists and return the ID
                for role in role_list:
                    if role.name.lower() == parameter.lower():
                        self.logger.debug(f'Found the Discord Role {role}')
                        return role

                    #This is to handle roles with spaces
                    parameter.replace('_',' ')
                    if role.name.lower() == parameter.lower():
                        self.logger.debug(f'Found the Discord Role {role}')
                        return role

                #await context.reply(f'Unable to find the Discord Role: {parameter}')
                return None

        def channelparse(self, parameter:str, context:commands.Context=None, guild_id:int=None) -> discord.TextChannel:
            """This is the bot utils Channel Parse Function\n
            It handles finding the specificed Discord `<channel>` in multiple different formats, either numeric or alphanumeric.\n
            returns `<channel>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.dev('Channel Parse Called...')

            category_clear = parameter.find('->')
            if category_clear != -1:
                parameter = parameter[(category_clear + 2):].strip()
           
            if guild_id == None:
                channel = self._client.get_channel(parameter)
                self.logger.debug(f'Found the Discord Channel {channel}')
                return channel

            guild = self._client.get_guild(guild_id)
            channel_list = guild.channels
            if type(parameter) == int:
                channel = guild.get_channel(parameter)
                self.logger.debug(f'Found the Discord Channel {channel}')
                return channel
            else:
                for channel in channel_list:
                    if channel.name == parameter:
                        self.logger.debug(f'Found the Discord Channel {channel}')
                        return channel
                else:
                    self.logger.error('Unable to Find the Discord Channel')
                    #await context.reply(f'Unable to find the Discord Channel: {parameter}')
                    return None
        
        def userparse(self, parameter:str, context:commands.Context=None, guild_id:int=None) -> discord.Member:
            """This is the bot utils User Parse Function\n
            It handles finding the specificed Discord `<user>` in multiple different formats, either numeric or alphanumeric.\n
            It also supports '@', '#0000' and partial display name searching for user indentification (eg. k8thekat#1357)\n
            returns `<user>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.dev('User Parse Called...')

            #Without a guild_ID its harder to parse members.
            if guild_id == None:
                cur_member = self._client.get_user(int(parameter))
                self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            guild = self._client.get_guild(guild_id)
            #Discord ID catch
            if parameter.isnumeric():
                cur_member = guild.get_member(int(parameter))
                self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Profile Name Catch
            if parameter.find('#') != -1:
                cur_member = guild.get_member_named(parameter)
                self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Using @ at user and stripping
            if parameter.startswith('<@!') and parameter.endswith('>'):
                user_discordid = parameter[3:-1]
                cur_member = guild.get_member(int(user_discordid))
                self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            #DiscordName/IGN Catch(DB Get user can look this up)
            cur_member = guild.get_member_named(parameter)
            if cur_member != None:
                self.logger.dev(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Display Name Lookup
            else:
                cur_member = None
                for member in guild.members:
                    if member.display_name.lower().startswith(parameter.lower()) or (member.display_name.lower().find(parameter.lower()) != -1):
                        if cur_member != None:
                            self.logger.error(f'**ERROR** Found multiple Discord Members: {parameter}, Returning None')
                            return None

                        self.logger.dev(f'Found the Discord Member {member.display_name}')
                        cur_member = member
                return cur_member
                
        def serverparse(self, parameter, context:commands.Context=None, guild_id:int=None) -> AMP.AMPInstance:
            """This is the botUtils Server Parse function.
            **Note** Use context.guild.id \n
            Returns `AMPInstance[server] <object>`"""
            self.logger.dev('Bot Utility Server Parse')
            cur_server = None

            #This is to handle Instance Names or Display Names with spaces, also removes quotes.
            if type(parameter) == tuple:
                parameter = ' '.join(parameter)
            #parameter = parameter.replace(' ','_').replace("'",'').replace('"','')
            parameter = parameter.replace("'",'').replace('"','')

            #Lets check the DB First, this checks Nicknames and Display names.
            cur_server = self.DB.GetServer(Name = parameter)
            if cur_server != None:
                self.logger.dev(f'DBGetServer -> DisplayName: {cur_server.DisplayName} InstanceName: {cur_server.InstanceName}')
                #This converts the DB_Server object into our AMPInstance Object
                cur_server = self.AMPInstances[cur_server.InstanceID]
                return cur_server

            #Since the DB came up empty; lets continue and try all AMPInstances Friendly Names!
            for server in self.AMPInstances:
                var = self.AMPInstances[server].FriendlyName.lower().find(parameter.lower())
                self.logger.dev(f'{var}{self.AMPInstances[server].FriendlyName}')

                if var != -1: #When its FOUND an entry
                    if cur_server != None:
                        self.logger.error(f'**ERROR** Found multiple AMP Servers matching the provided name: {parameter}. Returning None')
                        #await context.reply('Found multiple AMP Servers matching the provided name, please be more specific.')
                        return None

                    self.logger.dev(f'Found the AMP Server {self.AMPInstances[server].FriendlyName}')
                    cur_server = self.AMPInstances[server]

            return cur_server #AMP instance object 

        def sub_command_handler(self, command:str, sub_command):
            """This will get the `Parent` command and then add a `Sub` command to said `Parent` command."""
            parent_command = self._client.get_command(command)
            self.logger.dev(f'Loading Parent Command: {parent_command}')
            parent_command.add_command(sub_command)
        
        def default_embedmsg(self, title, context:commands.Context, description=None, field=None, field_value=None):
            """This Embed has only one Field Entry."""
            embed=discord.Embed(title=title, description=description, color=0x808000) #color is RED 
            embed.set_author(name=context.author.display_name, icon_url=context.author.avatar)
            embed.add_field(name=field, value=field_value, inline=False)
            return embed

        async def server_info_embed(self, server:AMP.AMPInstance, context:commands.Context):
            """For Individual Server info embed replies"""
            db_server = self.DB.GetServer(InstanceID = server.InstanceID)
            server_name = db_server.InstanceName
            if db_server.DisplayName != None:
                server_name = db_server.DisplayName
            embed=discord.Embed(title=f'__**{server_name}**__', color=0x00ff00, description=server.Description)

            discord_role = db_server.Discord_Role
            if discord_role != None:
                discord_role = context.guild.get_role(int(db_server.Discord_Role)).name

            avatar = await self.validate_avatar(db_server)
            if avatar != None:
                embed.set_thumbnail(url=avatar)

            embed.add_field(name=f'Server IP: ', value=str(db_server.IP), inline=False)
            embed.add_field(name='Donator Only:', value= str(bool(db_server.Donator)), inline=True)
            embed.add_field(name='Whitelist Open:' , value= str(bool(db_server.Whitelist)), inline=True)
            embed.add_field(name='Role:', value= str(discord_role), inline=False)
            embed.add_field(name='Discord Chat Prefix:', value= str(db_server.Discord_Chat_Prefix), inline=True)
            embed.add_field(name='Filtered Console:', value= str(bool(db_server.Whitelist)), inline=True)

            if db_server.Discord_Console_Channel != None:
                discord_channel = self.channelparse(db_server.Discord_Console_Channel, context, context.guild.id)
                embed.add_field(name='Console Channel:', value= discord_channel.name, inline=False)
            else:
                embed.add_field(name='Console Channel:', value= db_server.Discord_Console_Channel, inline=False)

            if db_server.Discord_Chat_Channel != None:
                discord_channel = self.channelparse(db_server.Discord_Chat_Channel, context, context.guild.id)
                embed.add_field(name='Chat Channel:', value= discord_channel.name, inline=True)
            else:
                embed.add_field(name='Chat Channel:', value= db_server.Discord_Chat_Channel, inline=True)
            
            if db_server.Discord_Event_Channel != None:
                discord_channel = self.channelparse(db_server.Discord_Event_Channel, context, context.guild.id)
                embed.add_field(name='Event Channel:', value= discord_channel.name, inline=True)
            else:
                embed.add_field(name='Event Channel:', value= db_server.Discord_Event_Channel, inline=True)

            if len(db_server.Nicknames) != 0:
                embed.add_field(name='Nicknames:', value=(", ").join(db_server.Nicknames),inline=False)
            return embed

        async def server_display_embed(self, guild:discord.Guild=None) -> list:
            """Used for `/server display command`"""
            embed_list = []
            for server in self.AMPInstances:
                server = self.AMPInstances[server]
    
                db_server = self.DB.GetServer(InstanceID= server.InstanceID)
                if db_server != None and db_server.Hidden != 1:

                    status = 'Offline'
                    Users = None
                    User_list = None
                    if server.Running and server._ADScheck() and server.ADS_Running:
                        Users = server.getStatus(users_only= True)
                        if len(server.getUserList()) > 1:
                            User_list = (', ').join(server.getUserList())
                        status = 'Online'

                    embed_color = 0x71368a
                    if guild != None and db_server.Discord_Role != None:
                        db_server_role = guild.get_role(int(db_server.Discord_Role))
                        if db_server_role != None:
                            embed_color = db_server_role.color

                    server_name = server.FriendlyName
                    if server.DisplayName != None:
                        server_name = db_server.DisplayName

                    nicknames = None
                    if len(db_server.Nicknames) != 0:
                        nicknames = (", ").join(db_server.Nicknames)

                    embed=discord.Embed(title=f'**=======  {server_name}  =======**',description= db_server.Description, color=embed_color)
                    #This is for future custom avatar support.
                    avatar = await self.validate_avatar(db_server)
                    if avatar != None:
                        embed.set_thumbnail(url=avatar)
    
                    embed.add_field(name='**IP**:', value= str(db_server.IP), inline=True)
                    embed.add_field(name='**Status**:' , value= status, inline= True)
                    embed.add_field(name='**Donator Only**:', value= str(bool(db_server.Donator)), inline= True)
                    embed.add_field(name='**Whitelist Open**:', value= str(bool(db_server.Whitelist)), inline= True)
                    embed.add_field(name='**Nicknames**:' , value= str(nicknames) ,inline=True)
                    if Users != None:
                        embed.add_field(name=f'**Players**:', value= f'{Users[0]}/{Users[1]}',inline=True)
                    else:
                        embed.add_field(name='**Player Limit**:', value= str(Users), inline= True)
                    embed.add_field(name='**Players Online**:', value=str(User_list), inline=False)
                    embed_list.append(embed)
            
            return embed_list

        async def server_status_embed(self, context:commands.Context, server:AMP.AMPInstance, TPS=None, Users=None, CPU=None, Memory=None, Uptime=None, Users_Online=None) -> discord.Embed:
            """This is the Server Status Embed Message"""
            db_server = self.DB.GetServer(InstanceID= server.InstanceID)
          
            if server.ADS_Running:
                server_status = 'Online'
            else:
                server_status = 'Offline'

            embed_color = 0x71368a
            if db_server.Discord_Role != None:
                db_server_role = context.guild.get_role(int(db_server.Discord_Role))
                if db_server_role != None:
                    embed_color = db_server_role.color

            server_name = server.FriendlyName
            if server.DisplayName != None:
                server_name = db_server.DisplayName

            embed=discord.Embed(title=server_name, description=f'Dedicated Server Status: **{server_status}**', color=embed_color)
           
            avatar = await self.validate_avatar(db_server)
            if avatar != None:
                embed.set_thumbnail(url=avatar)

            if db_server.IP != None:
                embed.add_field(name=f'Server IP: ', value=db_server.IP, inline=False)

            if len(db_server.Nicknames) != 0:
                embed.add_field(name='Nicknames:' , value=db_server.Nicknames, inline=False)

            #embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False)
            embed.add_field(name='Donator Only:', value= str(bool(db_server.Donator)), inline=True)
            embed.add_field(name='Whitelist Open:' , value= str(bool(db_server.Whitelist)), inline=True)
            #embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False) #This Generates a BLANK Field entirely.

            if server.ADS_Running:
                embed.add_field(name='TPS', value=TPS, inline=True)
                embed.add_field(name='Player Count', value=f'{Users[0]}/{Users[1]}', inline=True)
                embed.add_field(name='Memory Usage', value=f'{Memory[0]}/{Memory[1]}', inline=False)
                embed.add_field(name='CPU Usage', value=f'{CPU}/100%', inline=True)
                embed.add_field(name='Uptime', value=Uptime, inline=True)
                embed.add_field(name='Players Online', value=Users_Online, inline=False)
            return embed
                   
        async def server_whitelist_embed(self, context:commands.Context, server:AMP.AMPInstance) -> discord.Embed:
            """Default Embed Reply for Successful Whitelist requests"""
            db_server = self.DB.GetServer(InstanceID= server.InstanceID)

            embed_color = 0x71368a
            if db_server != None:
                if db_server.Discord_Role != None:
                    db_server_role = context.guild.get_role(int(db_server.Discord_Role))
                    if db_server_role != None:
                        embed_color = db_server_role.color

                User_list = None
                if len(server.getUserList()) > 1:
                    User_list = (', ').join(server.getUserList())

                server_name = server.FriendlyName
                if server.DisplayName != None:
                    server_name = db_server.DisplayName

                embed=discord.Embed(title=f'**=======  {server_name}  =======**',description= db_server.Description, color=embed_color)
                avatar = await self.validate_avatar(db_server)
                if avatar != None:
                    embed.set_thumbnail(url=avatar)

                embed.add_field(name='**IP**:', value= str(db_server.IP), inline=True)
                embed.add_field(name='Users Online:' , value=str(User_list), inline=False)
                return embed
                
        def bot_settings_embed(self, context:commands.Context, settings:list) -> discord.Embed:
            """Default Embed Reply for command /bot settings, please pass in a List of Dictionaries eg {'setting_name': 'value'}"""
            embed=discord.Embed(title=f'**Bot Settings**', color=0x71368a)
            embed.set_thumbnail(url= context.guild.icon)
            embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False)
            for value in settings:
                key_value = list(value.values())[0]
                key = list(value.keys())[0]
                #print(key, key_value)

                if key == 'Whitelist_emoji_pending' or key == 'Whitelist_emoji_done':
                    if key_value != 'None':
                        emoji = self._client.get_emoji(int(key_value))
                        embed.add_field(name=f'{key.replace("_"," ")}', value=emoji, inline=True)
                    else:
                        embed.add_field(name=f'{key.replace("_"," ")}', value='None', inline=True)

                if key == 'Whitelist_wait_time':
                    embed.add_field(name='Whitelist Wait Time:', value=f'{key_value} Minutes', inline=False)

                if key.lower() == 'permissions':
                    embed.add_field(name='Permissions:', value=f'{key_value}', inline=True)

                if key.lower() == 'db_version':
                    embed.add_field(name='SQL Database Version:', value=f'{key_value}', inline=True)

                if key.lower() == 'bot_version':
                    embed.add_field(name='Gatekeeper Version:', value=f'{key_value}', inline=True)

                if key.lower() == 'guild_id':
                    if self._client != None:
                        key_value = f'**{self._client.get_guild(int(key_value)).name}**'
                        if key_value == None:
                            key_value = 'None'
                        embed.add_field(name='Guild ID:', value=f'{key_value}', inline=False)

                if key.lower() == 'moderator_role_id':
                    key_value = self.roleparse(key_value,context,context.guild.id)
                    if key_value == None:
                        key_value = 'None'
                    embed.add_field(name=f'Moderator Role:', value=f'{key_value}',inline=False)
                    
                if key.lower() == 'whitelist_channel':
                    channel = self.channelparse(key_value,context,context.guild.id)
                    if channel != None:
                        channel = f'<#{channel.id}>'
                    else:
                        channel = 'None'
                    embed.add_field(name='Whitelist Channel', value=f'{channel}',inline=False)

                if key_value == '0' or key_value == '1':
                    key_value = bool(key_value)
                    embed.add_field(name=f'{list(value.keys())[0].replace("_", " ")}', value=f'{key_value}',inline=False)

            return embed

        def user_info_embed(self, context:commands.Context, db_user:DB.DBUser, discord_user:discord.User):
            #print(db_user.DiscordID,db_user.DiscordName,db_user.MC_IngameName,db_user.MC_UUID,db_user.SteamID,db_user.Donator)
            embed=discord.Embed(title=f'{discord_user.name}',description=f'Discord ID: {discord_user.id}', color=discord_user.color)
            embed.set_thumbnail(url= discord_user.avatar.url)
            if db_user != None:
                embed.add_field(name='In Database:', value='True')
                if db_user.MC_IngameName != None:
                    embed.add_field(name='Minecraft IGN:', value=f'{db_user.MC_IngameName}',inline= False)
                if db_user.MC_UUID != None:
                    embed.add_field(name='Minecraft UUID:', value=f'{db_user.MC_UUID}',inline= True)
                if db_user.SteamID != None:
                    embed.add_field(name='Steam ID:', value=f'{db_user.SteamID}',inline=False)
                if db_user.Role != None:
                    embed.add_field(name='Permission Role:', value=f'{db_user.Role}', inline=False)
            return embed
                          
bPerms = None
def get_botPerms():
    global bPerms
    if bPerms == None:
        bPerms = botPerms()
    return bPerms

class botPerms():
    def __init__(self):
        self.logger = logging.getLogger()
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB

        self._last_modified = 0
        self.permissions = None
        self.permission_roles = []

        self.validate_and_load()
        self.get_roles()
        self.logger.info('**Success** Loading Bot Permissions')

    def validate_and_load(self):
        self.json_file = pathlib.Path.cwd().joinpath('bot_perms.json')
        if self.json_file.stat().st_mtime > self._last_modified:
            try:
                self.permissions = json.load(open(self.json_file, 'r'))
                self._last_modified = self.json_file.stat().st_mtime

                #Soft validation of the file to help with errors.
                for role in self.permissions['Roles']:
                    if len(role['name']) == 0:
                        self.logger.critical(f'You are missing a role name, please do not leave role names empty..')
                        sys.exit(0)

                    #Verifies each role has a numeric discord_role_id or is equal to none.
                    if not role['discord_role_id'].isalnum() or role['discord_role_id'] != "None":
                        self.logger.critical(f'Your Discord Role ID for {role["name"]} does not appear to be all numbers. Please double check your config.')
                        sys.exit(0) 

            except json.JSONDecodeError:
                self.permissions = None
                self.logger.critical('Unable to load your permissions file. Please check your formatting.')

    def perm_node_check(self, command_perm_node:str, context:commands.Context):
        """Checks a Users for a DB Role then checks for that Role inside of bot_perms.py, then checks that Role for the proper permission node."""
        #Lets get our DB user and check if they exist.
        DB_user = self.DB.GetUser(str(context.author.id))
        if DB_user == None:
            return False

        #Lets also check for their DB Role
        user_role = DB_user.Role 
        if user_role == None:
            return False

        #Need to turn author roles into a list of ints.
        user_discord_role_ids = []
        for user_roles in context.author.roles:
            user_discord_role_ids.append(str(user_roles.id))

        #This is to check for Super perm nodes such as `server.*`
        command_super_node = command_perm_node.split(".")[0] + '.*'

        if self.permissions == None:
            self.logger.error('**ATTENTION** Please verify your bot_perms file, it failed to load.')
            return False
            
        self.validate_and_load()
        self.logger.info('Validated and Loaded Permissions File.')
        roles = self.permissions['Roles']
        for role in roles:
            if user_role.lower() in role['name'].lower() or role['discord_role_id'] in user_discord_role_ids:
                #print('Found Role in permissions list',user_role,role['name'])
                if command_super_node in role['permissions']:
                    #print('Found Super perm node',command_super_node)
                    command_perm_node_false_check = '-' + command_perm_node
                    if command_perm_node_false_check in role['permissions']:
                        if command_perm_node_false_check[1:] == command_perm_node:
                            self.logger.dev('This perm node has been denied even though you have global permissions.',command_perm_node_false_check,command_perm_node)
                            return False

                if command_perm_node in role['permissions']:
                    self.logger.dev('Found command perm node in Roles Permissions list.',command_perm_node)
                    return True
    
    def get_roles(self):
        """Pre build my Permissions Role Name List"""
        self.permission_roles = []
        for role in self.permissions['Roles']:
            self.permission_roles.append(role['name'])
        return self.permission_roles

    async def get_role_prefix(self, user_id:str=None, context:commands.Context=None):
        """Use to get a Users Role Prefix for displaying."""

        #This grabs all a Users discord roles and makes a list of their ids
        discord_roles = []
        if context != None:
            for role in context.author.roles:
                discord_roles.append(str(role.id))

            #This works because you can only have one bot_perms role.
            for role in self.permissions['Roles']:
                if role['discord_role_id'] in discord_roles:
                    return role['prefix']

        db_user = self.DB.GetUser(user_id)
        if db_user != None and db_user.Role != None:
            rolename = db_user.Role    
            if rolename in self.permission_roles:
                for role in self.permissions['Roles']:
                    if role['name'] == rolename:
                        return role['prefix']
                    else:
                        continue
        return None