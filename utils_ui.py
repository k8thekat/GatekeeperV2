import logging
import re
import io
from PIL import Image
import random

import discord
from discord.ext import commands
from discord.ui import Button,View,Select,Modal,TextInput
import asyncio

import DB
import AMP_Handler
import modules.banner_creator as BC
import utils

class ServerButton(Button):
    """Custom Start Button for when Servers are Offline."""
    def __init__(self, server:AMP_Handler.AMP.AMPInstance, view:discord.ui.View, function, label:str, callback_label:str, callback_disabled:bool, style=discord.ButtonStyle.green, context=None):
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
        if not await utils.async_rolecheck(interaction, self.permission_node):
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
    def __init__(self, timeout=180, context:commands.Context=None, amp_server:AMP_Handler.AMP.AMPInstance=None):
        super().__init__(timeout=timeout)
        self.server = amp_server
        self.context = context
        self.uBot = utils.botUtils()

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
    def __init__(self, amp_server: AMP_Handler.AMP.AMPInstance, db_banner: DB.DBBanner, banner_message: discord.Message, timeout=None):
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
    def __init__(self, edited_db_banner: Edited_DB_Banner, view: Banner_Editor_View, amp_server: AMP_Handler.AMP.AMPInstance, banner_message: discord.Message, custom_id:str= None, min_values:int= 1, max_values:int= 1, row:int= None, disabled:bool= False, placeholder:str= None):
        self.logger = logging.getLogger()
        options = []
        self._banner_view = view

        self._edited_db_banner = edited_db_banner
        self._banner_message = banner_message

        self._amp_server = amp_server

        whitelist_options = [
            discord.SelectOption(label= "Whitelist Open Font Color", value= 'color_whitelist_open'),
            discord.SelectOption(label= "Whitelist Closed Font Color", value= 'color_whitelist_closed')]
        donator_options = [
            discord.SelectOption(label= "Donator Font Color", value= 'color_donator')]
        
        options = [
            discord.SelectOption(label= "Blur Background Intensity", value= 'blur_background_amount'),
            discord.SelectOption(label= "Header Font Color", value= 'color_header'),
            discord.SelectOption(label= "Body Font Color", value= 'color_body'),
            discord.SelectOption(label= "Host Font Color", value= 'color_host'),
            
            discord.SelectOption(label= "Server Online Font Color", value= 'color_status_online'),
            discord.SelectOption(label= "Server Offline Font Color", value= 'color_status_offline'),
            discord.SelectOption(label= "Player Limit Minimum Font Color", value= 'color_player_limit_min'),
            discord.SelectOption(label= "Player Limit Maximum Font Color", value= 'color_player_limit_max'),
            discord.SelectOption(label= "Players Online Font Color", value= 'color_player_online')
            ]
        
        #If Whitelist is disabled, remove the options from the list.
        if not self._amp_server.Whitelist_disabled:
            options = whitelist_options + options

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
    def __init__(self, input_type: str, select_value: str, title: str, view: Banner_Editor_View, edited_db_banner: Edited_DB_Banner, banner_message: discord.Message, amp_server: AMP_Handler.AMP.AMPInstance, timeout= None , custom_id= 'Banner Modal'):
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
                await interaction.response.send_message(content= f'Please provide a proper Hex color Code. {self._color_code_input._value}', ephemeral= True, delete_after= self._client.Message_Timeout)
                
          
        if self._input_type == 'int':
            if await self._int_code_input.callback() == False:
                await interaction.response.send_message(f'Please provide a Number only. {self._int_code_input.value}', ephemeral= True, delete_after= self._client.Message_Timeout)
                
        else:
            await interaction.response.defer()
        await self._banner_message.edit(attachments= [banner_file_handler(BC.Banner_Generator(self._amp_server, self._edited_db_banner)._image_())], view= self._banner_view)
 
class Banner_Color_Input(TextInput):
    #This is the Modal that appears when Inputing a color hexcode.
    def __init__(self, view: Banner_Editor_View, edited_db_banner: Edited_DB_Banner, select_value: str, label: str= "Enter your Hex color code below.", style= discord.TextStyle.short, placeholder: str= '#000000', default: str= '#ffffff', required= True, min_length= 3, max_length= 8):
        self._edited_db_banner = edited_db_banner
        self._select_value = select_value
        self._banner_view = view
        super().__init__(label= label, style= style, placeholder= placeholder, default= default, required= required, min_length= min_length, max_length= max_length)

    async def callback(self):
        #Remove the Hex code for validation.
        #Also lower the value for better comparison.
        self._value = self.value.lower()
        if self._value[0] == '#':
            self._value = self._value[1:]

        #Validate if Hex Color Code.
        if len(self._value) in [3,4,6,8] and re.search(f'([0-9a-f]{{{len(self._value)}}})$', self._value):
            self._banner_view.logger.dev(f'Set attr for {self._edited_db_banner} {self._select_value} #{self._value}')
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
        if self.value.isnumeric() and int(self.value) <= 99:
            self._banner_view.logger.dev(f'Set attr for {self._edited_db_banner} {self._select_value} {self.value}')
            setattr(self._edited_db_banner, self._select_value, int(self.value[0]))
            return True
        else:
            return False

class Save_Banner_Button(Button):
    """Saves the Banners current settings to the DB."""
    def __init__(self, banner_message: discord.Message, server: AMP_Handler.AMP.AMPInstance, edited_banner: Edited_DB_Banner,  style= discord.ButtonStyle.green):
        super().__init__(label='Save', style=style, custom_id='Save_Button')
        self.logger = logging.getLogger()
        self._amp_server = server
        self._banner_message = banner_message
        self._edited_db_banner = edited_banner

    async def callback(self, interaction: discord.Interaction):
        """This is called when a button is interacted with."""
        saved_banner = self._edited_db_banner.save_db()
        await interaction.response.defer()
        file = banner_file_handler(BC.Banner_Generator(self._amp_server, saved_banner)._image_())
        await self._banner_message.edit(content='**Banner Settings have been saved.**', attachments= [file], view= None)

class Reset_Banner_Button(Button):
    """Resets the Banners current settings to the original DB."""
    def __init__(self, banner_message: discord.Message, server: AMP_Handler.AMP.AMPInstance, edited_banner: Edited_DB_Banner, style= discord.ButtonStyle.blurple):
        super().__init__(label='Reset', style=style, custom_id='Reset_Button')
        self.logger = logging.getLogger()
        self._amp_server = server
        self._banner_message = banner_message
        self._edited_db_banner = edited_banner

    async def callback(self, interaction: discord.Interaction):
        """This is called when a button is interacted with."""
        saved_banner = self._edited_db_banner.reset_db()
        await interaction.response.defer()
        file = banner_file_handler(BC.Banner_Generator(self._amp_server, saved_banner)._image_())
        await self._banner_message.edit(content='**Banner Settings have been reset.**', attachments= [file])

class Cancel_Banner_Button(Button):
    """Cancels the Banner Settings View"""
    def __init__(self, banner_message: discord.Message, style= discord.ButtonStyle.red):
        super().__init__(label='Cancel', style=style, custom_id='Cancel_Button')
        self.logger = logging.getLogger()
        self._banner_message = banner_message

    async def callback(self, interaction: discord.Interaction):
        """This is called when a button is interacted with."""
        await interaction.response.defer()
        await self._banner_message.edit(content='**Banner Settings Editor has been Cancelled.**', attachments= [], view= None)
    
class Whitelist_view(View):
    """Whitelist Request View"""
    def __init__(self, client: discord.Client, discord_message: discord.Message, whitelist_message: discord.Message, amp_server: AMP_Handler.AMP.AMPInstance, context: commands.Context, timeout: float):
        self.logger = logging.getLogger()
        self.DB = DB.getDBHandler().DB
        self._client = client
        self._context = context
        self._whitelist_message = whitelist_message
        self._amp_server = amp_server
        super().__init__(timeout= (timeout * 60))
        self.add_item(Accept_Whitelist_Button(discord_message= discord_message, view= self, client= client, amp_server= amp_server))
        self.add_item(Deny_Whitelist_Button(discord_message= discord_message, view = self, client= client, amp_server= amp_server))
    
    async def _whitelist_handler(self):
        db_server = self.DB.GetServer(self._amp_server.InstanceID)
        self.logger.dev(f'Whitelist Request; Attempting to Whitelist {self._whitelist_message.author.name} on {db_server.FriendlyName}')
        #This handles all the Discord Role stuff.
        if db_server != None and db_server.Discord_Role != None:
            discord_role = self._client.uBot.role_parse(db_server.Discord_Role, self._context, self._context.guild.id)
            discord_user = self._client.uBot.user_parse(self._context.author.id, self._context, self._context.guild.id)
            await discord_user.add_roles(discord_role, reason= 'Auto Whitelisting')

        #This is for all the Replies
        if len(self.DB.GetAllWhitelistReplies()) != 0:
            whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
            await self._context.message.channel.send(content= f'{self._context.author.mention} \n{self._client.uBot.whitelist_reply_handler(message= whitelist_reply, context= self._context, server= self._amp_server)}', delete_after= self._client.Message_Timeout)
        else:
            await self._context.message.channel.send(content= f'You are all set! We whitelisted {self._context.author.mention} on **{db_server.FriendlyName}**', delete_after= self._client.Message_Timeout)

class Accept_Whitelist_Button(Button):
    """Accepts the Whitelist Request"""
    def __init__(self, discord_message: discord.Message, view: Whitelist_view, client: discord.Client, amp_server: AMP_Handler.AMP.AMPInstance, style= discord.ButtonStyle.green):
        super().__init__(label= 'Accept', style= style, custom_id= 'Accept_Button')
        self._view = view
        self._discord_message = discord_message
        self._amp_server = amp_server
        self._client = client

    async def callback(self, interaction: discord.Interaction):
        if await utils.async_rolecheck(context= interaction, perm_node= 'whitelist_buttons'):
            self._view.logger.info(f'We Accepted a Whitelist Request by {self._view._whitelist_message.author.name}')
            await self._discord_message.edit(content= f'**{interaction.user.name}** -> Approved __{self._view._whitelist_message.author.name}__ Whitelist Request', view= None)
            await self._view._whitelist_handler()
            self._amp_server.addWhitelist(self._client.Whitelist_wait_list[self._view._whitelist_message.id]['dbuser'])
            self._client.Whitelist_wait_list.pop(self._view._whitelist_message.id)
            self.disabled = True

class Deny_Whitelist_Button(Button):
    """Denys the Whitelist Request"""
    def __init__(self, discord_message: discord.Message, view: Whitelist_view, client: discord.Client, amp_server: AMP_Handler.AMP.AMPInstance,  style= discord.ButtonStyle.red):
        super().__init__(label= 'Deny', style= style, custom_id= 'Deny_Button')
        self._view = view
        self._discord_message = discord_message
        self._amp_server = amp_server
        self._client = client

    async def callback(self, interaction: discord.Interaction):
        if await utils.async_rolecheck(context= interaction, perm_node= 'whitelist_buttons'):
            self._view.logger.info(f'We Denied a Whitelist Request by {self._view._whitelist_message.author.name}')
            await self._discord_message.edit(content= f'**{interaction.user.name}** -> Denied __{self._view._whitelist_message.author.name}__ Whitelist Request', view= None)
            await self._view._whitelist_message.channel.send(content= f'**{interaction.user.name}** Denied {self._view._whitelist_message.author.mention} whitelist request. Please contact a Staff Member.')
            self._client.Whitelist_wait_list.pop(self._view._whitelist_message.id)
            self.disabled = True

class DB_Instance_ID_Swap(View):
    """DB Instance ID Swap View"""
    def __init__(self, discord_message: discord.Message, timeout: float, from_db_server: DB.DBServer, to_db_server: DB.DBServer):
        super().__init__(timeout= timeout)
        self._from_db_server= from_db_server
        self._to_db_server = to_db_server
        self.add_item(Approve_Button(view= self, discord_message= discord_message))
        self.add_item(Cancel_Button(view= self, discord_message= discord_message))

class Approve_Button(Button):
    def __init__(self, view: View, discord_message: discord.Message, style= discord.ButtonStyle.green):
        self._view = view
        self.message = discord_message
        super().__init__(label= 'Approve', style= style, custom_id= 'Approve_Button')

    async def callback(self, interaction: discord.Interaction):
        to_db_server_ID = self._view._to_db_server.InstanceID
        to_db_server_Name= self._view._to_db_server.InstanceName
        self._view._to_db_server.delServer()
        self._view._from_db_server.InstanceID = to_db_server_ID
        await self.message.edit(content = f'Replaced **{self._view._from_db_server.InstanceName} ID: {self._view._from_db_server.InstanceID}** with **{to_db_server_Name} ID: {to_db_server_ID}**', view= None)
    
class Cancel_Button(Button):
    def __init__(self, view: View, discord_message: discord.Message, style= discord.ButtonStyle.red) :
        self._view = view
        self.message = discord_message
        super().__init__(label= 'Cancel', style= style, custom_id= 'Cancel_Button')

    async def callback(self, interaction: discord.Interaction):
        return await self.message.edit(content= f'Cancelling change of **{self._view._from_db_server.InstanceName}** Instance ID. ', view= None)
      
    

