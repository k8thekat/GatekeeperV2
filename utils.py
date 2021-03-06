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

import discord
from discord.ext import commands
from discord.ui import Button,View
import asyncio

import DB
import AMP

async def async_rolecheck(context:commands.Context):
    DBHandler = DB.getDBHandler()
    DBConfig = DBHandler.DBConfig
    logger = logging.getLogger(__name__)

    #This fast tracks role checks for Admins, which also allows the bot to still work without a Staff Role set in the DB
    admin = context.author.guild_permissions.administrator
    if admin == True:
        logger.info(f'Permission Check Okay on {context.author}')
        return True
    
    if DBConfig.Staff == None:
        await context.send(f'Please have an Adminstrator run `/bot setup (admin role)`.')
        logger.error(f'DBConfig Staff role has not been set yet!')
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

        if guild_roles[i].id == DBConfig.Staff:
            staff_role = i
            
    if author_top_role > staff_role:
        logger.info(f'Permission Check Okay on {author}')
        return True
        
    else:
        logger.info(f'Permission Check Failed on {author}')
        await context.send('You do not have permission to use that command...')
        return False

def role_check():
    """Use this before any Commands that require a Staff/Mod level permission Role, this will also check for Administrator"""
    return commands.check(async_rolecheck)

class CustomButton(Button):
    """ utils.CustomButton(server,view,server.StartInstance,'Start',callback_label='Starting...',callback_disabled=True)"""
    def __init__(self,server,view,function,label:str,callback_label:str,callback_disabled:bool,style=discord.ButtonStyle.green,context=None):
        super().__init__(label=label, style=style, custom_id=label)
        self.server = server
        self.context = context
        self._label = label

        self.callback_label = callback_label
        self.callback_disabled = callback_disabled

        self._function = function
        self._view = view
        view.add_item(self)

    async def callback(self,interaction):
        """This is called when a button is interacted with."""
        if not await async_rolecheck(interaction.user):
            return
        self._interaction = interaction
        self.label = self.callback_label
        self.disabled = self.callback_disabled
        await interaction.response.edit_message(view=self._view)
        self._function()
        await asyncio.sleep(30)
        await self.reset()

    #@tasks.loop(seconds=30.0)
    async def reset(self):
        print('Resetting Buttons...')
        self.label = self._label
        self.disabled = False
        await self._interaction.followup.edit_message(message_id=self._interaction.message.id,view=self._view)

class StartButton(CustomButton):
    def __init__(self,server,view,function):
        super().__init__(server=server,view=view,function=function,label='Start', callback_label='Starting...',callback_disabled=True,style=discord.ButtonStyle.green)

class StopButton(CustomButton):
    def __init__(self,server,view,function):
        super().__init__(server=server,view=view,function=function,label='Stop', callback_label='Stopping...',callback_disabled=True,style=discord.ButtonStyle.red)

class RestartButton(CustomButton):
    def __init__(self,server,view,function):
        super().__init__(server=server,view=view,function=function,label='Restart', callback_label='Restarting...',callback_disabled=True,style=discord.ButtonStyle.blurple)

class KillButton(CustomButton):
    def __init__(self,server,view,function):
        super().__init__(server=server,view=view,function=function,label='Kill', callback_label='Killed...', callback_disabled=True,style=discord.ButtonStyle.danger)
    
class StatusView(View):
    def __init__(self,timeout=180):
        super().__init__(timeout=timeout)

    async def on_timeout(self):
        """This Removes all the Buttons after timeout has expired"""
        #!TODO! Find an alternative to stop.
        self.stop()

class discordBot():
    def __init__(self,client:discord.Client):
        self.botLogger = logging.getLogger(__name__)
        self._client = client
        self.botLogger.debug(f'Utils Discord Loaded')
    
    async def userAddRole(self, user: discord.user, role: discord.role, reason:str=None):
        """Adds a Role to a User.\n
        Requires a `<user`> and `<role>` discord object.\n
        Supports `reason`(Optional)"""
        
        self.botLogger.info('Add Users Discord Role Called...')
        await user.add_roles(role,reason)

    async def userRemoveRole(self, user: discord.user, role: discord.role, reason:str=None):
        """Removes a Role from the User.\n
        Requires a `<user>` and `<role>` discord object.\n
        Supports `reason`(Optional)"""

        self.botLogger.info('Remove Users Discord Role Called...')
        print(type(user),type(role))
        await user.remove_roles(role,reason)

    async def delMessage(self,message: discord.message, delay: float=None):
        """Deletes the message.\n
        Your own messages could be deleted without any proper permissions. However to delete other people's messages, you need the `manage_messages` permission.\n
        Supports `delay[float]`(Optional)"""

        self.botLogger.info('Delete Discord Message Called...')
        await message.delete(delay=delay)

    async def channelHistory(self,channel:discord.TextChannel,limit:int=10,before:datetime=None,after:datetime=None,around:datetime=None,oldest_first:bool=False):
        """This will be used to access channel history up to 100. Simple scraper with datetime support."""
        if limit > 100:
            limit = 100
        messages = await channel.history(limit,before,after,around,oldest_first).flatten()
        return messages

    async def editMessage(self,message: discord.message ,content: str=None, delete_after:float=None):
        """Edits the message.\n
        The content must be able to be transformed into a string via `str(content)`.\n
        Supports `delete_after[float]`(Optional)"""

        self.botLogger.info('Edit Discord Message Called...')
        await message.edit(content,delete_after)

    async def sendMessage(self, parameter:object, content:str,*, tts:bool=False,embed=None, file:discord.file=None, files:list=None, delete_after:float=None, nonce= None, allowed_mentions=None, reference:object=None):
        #content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, allowed_mentions=None, reference=None, mention_author=None
        """Sends a message to the destination with the content given.\n
        The content must be a type that can convert to a string through `str(content)`. If the content is set to `None` (the default), then the embed parameter must be provided.\n
        To upload a single file, the `file` parameter should be used with a single File object. To upload multiple files, the `files` parameter should be used with a `list` of `File` objects. Specifying both parameters will lead to an exception.\n
        `NOTE:` Using `file` - await channel.send(file=discord.File('my_file.png')) or 
            with open('my_file.png', 'rb') as fp:
                await channel.send(file=discord.File(fp, 'new_filename.png')) 
        `NOTE:` Using `files` - my_files = [discord.File('result.zip'), discord.File('teaser_graph.png')] await channel.send(files=my_files)"""

        self.botLogger.info('Member Send Message Called...')
        await parameter.send(content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce, allowed_mentions=allowed_mentions, reference=reference)

    async def messageAddReaction(self,message: discord.message, reaction_id:str):
        """The name and ID of a custom emoji can be found with the client by prefixing ':custom_emoji:' with a backslash. \n
            For example, sending the message '\:python3:' with the client will result in '<:python3:232720527448342530>'.
            `NOTE` Can only use Emoji's the bot has access too"""

        self.botLogger.info('Message Add Reaction Called...')
        if reaction_id.isnumeric():
            emoji = self._client.get_emoji(int(reaction_id))

        if not reaction_id.startswith('<') and not reaction_id.endswith('>'):
            emoji = discord.utils.get(self._client.emojis, name= reaction_id)

        else:
            emoji = reaction_id

        await message.add_reaction(emoji)

    async def cog_load(self,context,cog:str):
        try:
            self._client.load_extension(name= cog)
        except Exception as e:
            await context.send(f'**ERROR** Loading Extension {cog} - {e}')
        else:
            await context.send(f'**SUCCESS** Loading Extension {cog}')
        
    async def cog_unload(self,context,cog:str):
        try:
            self._client.unload_extension(name= cog)
        except Exception as e:
            await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
        else:
            await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

class botUtils():
        def __init__ (self,client:discord.Client=None):
            self._client = client
            self.logger = logging.getLogger(__name__)
            self.logger.debug('Utils Bot Loaded')

            self.DBHandler = DB.getDBHandler()
            self.DB = self.DBHandler.DB #Main Database object
            self.DBConfig = self.DBHandler.DBConfig

            self.AMPHandler = AMP.getAMPHandler()
            self.AMPInstances = self.AMPHandler.AMP_Instances


        def name_to_uuid_MC(self,name): 
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

        def roleparse(self,parameter:str,context,guild_id:int) -> discord.Role: 
            """This is the bot utils Role Parse Function\n
            It handles finding the specificed Discord `<role>` in multiple different formats.\n
            They can contain single quotes, double quotes and underscores. (" ",' ',_)\n
            returns `<role>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.info('Role Parse Called...')
            #print(dir(self._client),self._client.get_guild(guild_id),guild_id)
            guild = self._client.get_guild(guild_id)
            role_list = guild.roles
            
            #Role ID catch
            if parameter.isnumeric():
                role = guild.get_role(int(parameter))
                self.logger.debug('Found the Discord Role {role}')
                return role
            else:
                #This allows a user to pass in a role in quotes double or single
                if parameter.find("'") != -1 or parameter.find('"'):
                    parameter = parameter.replace('"','')
                    parameter = parameter.replace("'",'')

                #If a user provides a role name; this will check if it exists and return the ID
                for role in role_list:
                    if role.name.lower() == parameter.lower():
                        self.logger.debug('Found the Discord Role {role}')
                        return role

                    #This is to handle roles with spaces
                    parameter.replace('_',' ')
                    if role.name.lower() == parameter.lower():
                        self.logger.debug('Found the Discord Role {role}')
                        return role

                #await context.reply(f'Unable to find the Discord Role: {parameter}')
                return None

        def channelparse(self,parameter:str,context=None,guild_id:int=None) -> discord.TextChannel:
            """This is the bot utils Channel Parse Function\n
            It handles finding the specificed Discord `<channel>` in multiple different formats, either numeric or alphanumeric.\n
            returns `<channel>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.info('Channel Parse Called...')

            if guild_id == None:
                channel = self._client.get_channel(int(parameter))
                self.logger.debug(f'Found the Discord Channel {channel}')
                return channel

            guild = self._client.get_guild(guild_id)
            channel_list = guild.channels
            if parameter.isnumeric():
                channel = guild.get_channel(int(parameter))
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
        
        def userparse(self,parameter:str,context=None,guild_id:int=None) -> discord.Member:
            """This is the bot utils User Parse Function\n
            It handles finding the specificed Discord `<user>` in multiple different formats, either numeric or alphanumeric.\n
            It also supports '@', '#0000' and partial display name searching for user indentification (eg. k8thekat#1357)\n
            returns `<user>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.info('User Parse Called...')

            #Without a guild_ID its harder to parse members.
            if guild_id == None:
                cur_member = self._client.get_user(int(parameter))
                self.logger.debug(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            guild = self._client.get_guild(guild_id)
            #Discord ID catch
            if parameter.isnumeric():
                cur_member = guild.get_member(int(parameter))
                self.logger.debug(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Profile Name Catch
            if parameter.find('#') != -1:
                cur_member = guild.get_member_named(parameter)
                self.logger.debug(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Using @ at user and stripping
            if parameter.startswith('<@!') and parameter.endswith('>'):
                user_discordid = parameter[3:-1]
                cur_member = guild.get_member(int(user_discordid))
                self.logger.debug(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            #DiscordName/IGN Catch(DB Get user can look this up)
            cur_member = guild.get_member_named(parameter)
            if cur_member != None:
                self.logger.debug(f'Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Display Name Lookup
            else:
                cur_member = None
                for member in guild.members:
                    if member.display_name.lower().startswith(parameter.lower()) or (member.display_name.lower().find(parameter.lower()) != -1):
                        if cur_member != None:
                            self.logger.error(f'Found multiple Discord Members: {parameter}, Returning None')
                            #await context.reply('Found multiple Discord Members matching that name, please be more specific.')
                            return None

                        self.logger.debug(f'Found the Discord Member {member.display_name}')
                        cur_member = member
                return cur_member
                
        def serverparse(self,parameter,context=None,guild_id:int=None) -> AMP.AMPInstance:
            """This is the botUtils Server Parse function.
            **Note** Use context.guild.id \n
            Returns `AMPInstance[server] <object>`"""
            self.logger.info('Bot Utility Server Parse')
            cur_server = None

            #This is to handle Instance Names or Display Names with spaces, also removes quotes.
            if type(parameter) == tuple:
                parameter = ' '.join(parameter)
            parameter = parameter.replace(' ','_').replace("'",'').replace('"','')

            #Lets check the DB First, this checks Nicknames and Display names.
            cur_server = self.DB.GetServer(Name = parameter)
            if cur_server != None:
                self.logger.debug(f'DBGetServer -> DisplayName: {cur_server.DisplayName} InstanceName: {cur_server.InstanceName}')
                #This converts the DB_Server object into our AMPInstance Object
                cur_server = self.AMPInstances[cur_server.InstanceID]
                return cur_server

            #Since the DB came up empty; lets continue and try all AMPInstances Friendly Names!
            for server in self.AMPInstances:
                var = self.AMPInstances[server].FriendlyName.lower().find(parameter.lower())
                self.logger.debug(f'{var}{self.AMPInstances[server].FriendlyName}')

                if var != -1: #When its FOUND an entry
                    if cur_server != None:
                        self.logger.error(f'Found multiple AMP Servers matching the provided name: {parameter}. Returning None')
                        #await context.reply('Found multiple AMP Servers matching the provided name, please be more specific.')
                        return None

                    self.logger.debug(f'Found the AMP Server {self.AMPInstances[server].FriendlyName}')
                    cur_server = self.AMPInstances[server]

            return cur_server #AMP instance object 

        def sub_command_handler(self,command:str,sub_command):
            """This will get the `Parent` command and then add a `Sub` command to said `Parent` command."""
            parent_command = self._client.get_command(command)
            self.logger.info(f'Loading Parent Command: {parent_command}')
            parent_command.add_command(sub_command)
        
        def default_embedmsg(self,title,context,description=None,field=None,field_value=None):
            """This Embed has only one Field Entry."""
            embed=discord.Embed(title=title, description=description, color=0x808000) #color is RED 
            embed.set_author(name=context.author.display_name, icon_url=context.author.avatar)
            embed.add_field(name=field, value=field_value, inline=False)
            return embed

        def server_info_embed(self,server:AMP.AMPInstance, context:commands.Context):
            """For Individual Server info embed replies"""
            embed=discord.Embed(title=f'Server Info for {server.DisplayName}', color=0x00ff00, description=server.Description)
            db_server = self.DB.GetServer(InstanceID = server.InstanceID)
            if db_server != None:
                embed.set_thumbnail(url=context.guild.icon)
                embed.add_field(name='\u1CBC\u1CBC',value = f'========={server.DisplayName}=========',inline=False)

                if db_server.IP != None:
                    embed.add_field(name=f'Server IP: ', value=db_server.IP, inline=False)

                embed.add_field(name='Nicknames:' , value=db_server.Nicknames, inline=False)
                embed.add_field(name='Donator Only:', value= str(bool(db_server.Donator)), inline=True)
                embed.add_field(name='Whitelist Open:' , value= str(bool(db_server.Whitelist)), inline=True)

        #This was designed for smaller servers showing only a few embed messages, it does support up to the buffer limit of discord sending embeds currently.
        #See AMP_module for server list command that is text based.
        def server_list_embed(self,context:commands.Context) -> list:
            """Possibly an Option for Server Displays? Currently Un-used..."""
            embed=discord.Embed(title=f'Server List for {context.guild.name}', color=0x00ff00)
            embed_fieldindex = 0
            embed_list = []
            for server in self.AMPInstances:
                server = self.AMPInstances[server]
                
                db_server = self.DB.GetServer(InstanceID= server.InstanceID)
                if db_server != None:
                    embed.set_thumbnail(url=context.guild.icon)
                    embed.add_field(name='\u1CBC\u1CBC',value = f'========={server.DisplayName}=========',inline=False)
                    embed.add_field(name=f'**IP**: {db_server.IP}', value=f'**About**: {db_server.Description}', inline=False)
                    embed.add_field(name='Nicknames:' , value=db_server.Nicknames, inline=False)
                    embed.add_field(name='Donator Only:', value= str(bool(db_server.Donator)), inline=True)
                    embed.add_field(name='Whitelist Open:' , value= str(bool(db_server.Whitelist)), inline=True)
                embed_fieldindex += 5
                
                if embed_fieldindex == 25:
                    embed_list.append(embed)
                    embed_fieldindex = 0
                    embed=discord.Embed(title=f'Continued Server List for {context.guild.name}', color=0x00ff00)

            if embed_fieldindex != 0:
                embed_list.append(embed)
            return embed_list

        def server_status_embed(self,context:commands.Context,server:AMP.AMPInstance,TPS=None,Users=None,CPU=None,Memory=None,Uptime=None,Users_Online=None) -> discord.Embed:
            """This is the Server Status Embed Message"""
            db_server = self.DB.GetServer(InstanceID= server.InstanceID)
            if server.Server_Running:
                server_status = 'Online'
            else:
                server_status = 'Offline'

            if db_server.DisplayName == None:
                embed=discord.Embed(title=f'{db_server.InstanceName}', description=f'Dedicated Server Status: **{server_status}**', color=0x00ff40)
            else:
                embed=discord.Embed(title=f'{db_server.DisplayName}', description=f'Dedicated Server Status: **{server_status}**', color=0x00ff40)

            embed.set_thumbnail(url=context.guild.icon)
            if db_server.IP != None:
                embed.add_field(name=f'Server IP: ', value=db_server.IP, inline=False)

            if len(db_server.Nicknames) != 0:
                embed.add_field(name='Nicknames:' , value=db_server.Nicknames, inline=False)

            #embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False)
            embed.add_field(name='Donator Only:', value= str(bool(db_server.Donator)), inline=True)
            embed.add_field(name='Whitelist Open:' , value= str(bool(db_server.Whitelist)), inline=True)
            #embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False) #This Generates a BLANK Field entirely.

            if server.Server_Running:
                embed.add_field(name='TPS', value=TPS, inline=True)
                embed.add_field(name='Player Count', value=f'{Users[0]}/{Users[1]}', inline=True)
                embed.add_field(name='Memory Usage', value=f'{Memory[0]}/{Memory[1]}', inline=False)
                embed.add_field(name='CPU Usage', value=f'{CPU}/100%', inline=True)
                embed.add_field(name='Uptime', value=Uptime, inline=True)
                embed.add_field(name='Players Online', value=Users_Online, inline=False)
            return embed
                   


        def server_whitelist_embed(self,context:commands.Context,server:AMP.AMPInstance) -> discord.Embed:
            """Default Embed Reply for Successful Whitelist requests"""
            #!TODO! Update Database/Setup DisplayName for Title
            db_server = self.DB.GetServer(InstanceID= server.InstanceID)
            users_online = server.getUserList()

            embed=discord.Embed(title=f'{server.FriendlyName}', color=0x00ff00)
            if db_server != None:
                embed.set_thumbnail(url=context.guild.icon)
                if db_server.IP != None:
                    embed.add_field(name='IP: ', value=db_server.IP, inline=False)
                embed.add_field(name='Users Online:' , value=users_online, inline=False)
            return embed
                

        def bot_settings_embed(self,context:commands.Context,settings:list) -> discord.Embed:
            """Default Embed Reply for command /bot settings, please pass in a List of Dictionaries eg {'setting_name': 'value'}"""
            embed=discord.Embed(title=f'**Bot Settings**', color=0x00ff00)
            embed.set_thumbnail(url= context.guild.icon)
            embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False)
            for value in settings:
                key_value = list(value.values())[0]
                if key_value == '0' or key_value == '1':
                    key_value = bool(key_value)

                embed.add_field(name=f'{list(value.keys())[0].replace("_", " ")}', value=f'{key_value}',inline=False)
            return embed

        def user_info_embed(self,context:commands.Context,db_user:DB.DBUser,discord_user:discord.User):
            #print(db_user.DiscordID,db_user.DiscordName,db_user.MC_IngameName,db_user.MC_UUID,db_user.SteamID,db_user.Donator)
            embed=discord.Embed(title=f'{discord_user.name}',description=f'Discord ID: {discord_user.id}', color=0x00ff00)
            embed.set_thumbnail(url= discord_user.avatar.url)
            if db_user != None:
                embed.add_field(name='In Database', value='True')
                if db_user.Donator != None:
                    embed.add_field(name='Donator', value=f'{bool(db_user.Donator)}')
                if db_user.MC_IngameName != None:
                    embed.add_field(name='Minecraft IGN', value=f'{db_user.MC_IngameName}',inline= False)
                if db_user.MC_UUID != None:
                    embed.add_field(name='Minecraft UUID', value=f'{db_user.MC_UUID}',inline= True)
                if db_user.SteamID != None:
                    embed.add_field(name='Steam ID', value=f'{db_user.SteamID}',inline=False)
            return embed
                