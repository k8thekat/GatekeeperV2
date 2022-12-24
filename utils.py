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
from typing import Union

import discord
from discord import app_commands
from discord.ext import commands
import asyncio

import DB
import AMP

#GLOBAL VARS# DO NOT EDIT THESE! ONLY READ THEM
__AMP_Handler = AMP.getAMPHandler()
__DB_Handler = DB.getDBHandler()

async def async_rolecheck(context: Union[commands.Context, discord.Interaction, discord.member.Member], perm_node:str= None):
    DBHandler = DB.getDBHandler()
    DBConfig = DBHandler.DBConfig
    logger = logging.getLogger(__name__)
    logger.dev(f'Permission Context command node {str(context.command).replace(" ",".")}')
   
    author = context
    if type(context) != discord.Member:
        if hasattr(context, 'author'):
            top_role_id = context.author.top_role.id
            author = context.author

        elif hasattr(context, 'user'):
            top_role_id = context.user.top_role.id
            author = context.user
    
    elif type(context) == discord.member.Member:
        top_role_id = context.top_role.id
        author = context.name
    else:
        #This is for on_message commands
        top_role_id = context.message.author.top_role.id
        author = context.message.author

    #This fast tracks role checks for Admins, which also allows the bot to still work without a Staff Role set in the DB
    admin = author.guild_permissions.administrator
    if admin == True:
        logger.command(f'*Admin* Permission Check Okay on {author}')
        return True

    #This handles Custom Permissions for people with the flag set.

    if DBConfig.GetSetting('Permissions') == 1: #0 is Default, 1 is Custom
        if perm_node == None:
            perm_node = str(context.command).replace(" ",".")
       
        bPerms = get_botPerms()
        bPerms.perm_node_check(perm_node, context)
        if bPerms.perm_node_check == False:
            logger.command(f'*Custom* Permission Check Failed on {author} missing {perm_node}')
            return False
        else:
            logger.command(f'*Custom* Permission Check Okay on {author}')
            return True

    #This is the final check before we attempt to use the "DEFAULT" permissions setup.
    if DBConfig.GetSetting('Moderator_role_id') == None:
        await context.send(f'Please have an Adminstrator run `/bot moderator (role)` or consider setting up Custom Permissons.', ephemeral=True)
        logger.error(f'DBConfig Moderator role has not been set yet!')
        return False

    staff_role, author_top_role = 0,0
    guild_roles = context.guild.roles

    for i in range(0, len(guild_roles)):
        if guild_roles[i].id == top_role_id:
            author_top_role = i

        if guild_roles[i].id == DBConfig.Moderator_role_id:
            staff_role = i
            
    if author_top_role > staff_role:
        logger.command(f'*Default* Permission Check Okay on {author}')
        return True
        
    logger.command(f'*Default* Permission Check Failed on {author}')
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

async def autocomplete_servers(interaction:discord.Interaction, current:str) -> list[app_commands.Choice[str]]:
        """Autocomplete for AMP Instance Names"""
        choice_list = __AMP_Handler.get_AMP_instance_names()
        if await async_rolecheck(interaction, perm_node= 'Staff') == True:
            return [app_commands.Choice(name=f"{value} | ID: {key}", value= key)for key, value in choice_list.items()][:25]
        else:
            return [app_commands.Choice(name=f"{value}", value= key)for key, value in choice_list.items()][:25]

class discordBot():
    def __init__(self, client:discord.Client):
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
    """Gatekeeper Utility Class"""
    def __init__ (self, client:discord.Client= None):
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
    
    def whitelist_reply_handler(self,message:str, context:commands.Context, server:AMP.AMPInstance=None) -> str:
        """Handles the reply message for the whitelist event\n
        Supports the following: \n
        `<user>` - Uses the Message Author's Name/IGN \n
        `<server>` - Uses the AMP Server Name \n 
        `<guild>` - Uses the Guild Name \n"""
    
        if message.find('<user>') != -1:
            message = message.replace('<user>',context.author.name)
        if message.find('<guild>') != -1:
            message = message.replace('<guild>',context.guild.name)
        if message.find('<server>') != -1 and server is not None:
            server_name = server.FriendlyName
            if server.DisplayName != None: 
                server_name = server.DisplayName
            message = message.replace('<server>',server_name)
        return message

    async def validate_avatar(self, db_server:AMP.AMPInstance) -> Union[str, None]:
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

    def name_to_uuid_MC(self, name) -> Union[None, str]: 
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

    def name_to_steam_id(self, steamname:str) -> Union[None, str]:
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

    def roleparse(self, parameter:str, context:commands.Context, guild_id:int) -> Union[discord.Role, None]: 
        """This is the bot utils Role Parse Function\n
        It handles finding the specificed Discord `<role>` in multiple different formats.\n
        They can contain single quotes, double quotes and underscores. (" ",' ',_)\n
        returns `<role>` object if True, else returns `None`
        **Note** Use context.guild.id"""
        self.logger.dev('Role Parse Called...')
  
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

    def channelparse(self, parameter:Union[str, int], context:commands.Context=None, guild_id:int=None) -> Union[discord.TextChannel, None]:
        """This is the bot utils Channel Parse Function\n
        It handles finding the specificed Discord `<channel>` in multiple different formats, either numeric or alphanumeric.\n
        returns `<channel>` object if True, else returns `None`
        **Note** Use context.guild.id"""
        self.logger.dev('Channel Parse Called...')   
        
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
            category_clear = parameter.find('->')
            if category_clear != -1:
                parameter = parameter[(category_clear + 2):].strip()

            for channel in channel_list:
                if channel.name == parameter:
                    self.logger.debug(f'Found the Discord Channel {channel}')
                    return channel
            else:
                self.logger.error('Unable to Find the Discord Channel')
                #await context.reply(f'Unable to find the Discord Channel: {parameter}')
                return None
    
    def userparse(self, parameter:str, context:commands.Context=None, guild_id:int=None) -> Union[discord.Member, None]:
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
            
    def serverparse(self, instanceID= str, context:commands.Context=None, guild_id:int=None) -> Union[AMP.AMPInstance, None]:
        """This is the botUtils Server Parse function.
        **Note** Use context.guild.id \n
        Returns `AMPInstance[server] <object>`"""
        self.logger.dev('Bot Utility Server Parse')
        cur_server = None
        for key, value in self.AMPHandler.AMP_Instances.items():
            if key == instanceID:
                cur_server = value
                self.logger.dev(f'Selected Server is {value} - InstanceID: {key}')
                break

        return cur_server #AMP instance object 

    def sub_command_handler(self, command:str, sub_command):
        """This will get the `Parent` command and then add a `Sub` command to said `Parent` command."""
        parent_command = self._client.get_command(command)
        self.logger.dev(f'Loading Parent Command: {parent_command}')
        parent_command.add_command(sub_command)
    
    async def _serverCheck(self, context:commands.Context, server, online_only:bool=True) -> Union[AMP.AMPInstance,bool]:
        """Verifies if the AMP Server exists and if its Instance is running and its ADS is Running"""
        amp_server = self.serverparse(server, context, context.guild.id)
        
        if online_only == False:
            return amp_server

        if amp_server.Running and amp_server._ADScheck():
            return amp_server
        
        await context.send(f'Well this is awkward, it appears the **{amp_server.FriendlyName if amp_server.FriendlyName != None else amp_server.InstanceName}** is `Offline`.', ephemeral=True, delete_after= self._client.Message_Timeout)
        return False
                    
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

                    if role['discord_role_id'] == 'None':
                        continue

                    #Verifies each role has a numeric discord_role_id or is equal to none.
                    if type(role['discord_role_id']) != str:
                        self.logger.critical(f'Your Discord Role ID for {role["name"]} does not appear to be string. Please check your bot_perms.json.')
                        sys.exit(0) 

                    elif not role['discord_role_id'].isnumeric():
                        self.logger.critical(f'Your Discord Role ID for {role["name"]} does not appear to be all numbers. Please check your bot_perms.json.')
                        sys.exit(0) 

            except json.JSONDecodeError:
                self.permissions = None
                self.logger.critical('Unable to load your permissions file. Please check your formatting.')

    def perm_node_check(self, command_perm_node:str, context:commands.Context) -> bool:
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
                if command_super_node in role['permissions']:
                    command_perm_node_false_check = '-' + command_perm_node
                    if command_perm_node_false_check in role['permissions']:
                        if command_perm_node_false_check[1:] == command_perm_node:
                            self.logger.dev('This perm node has been denied even though you have global permissions.',command_perm_node_false_check,command_perm_node)
                            return False

                if command_perm_node in role['permissions']:
                    self.logger.dev('Found command perm node in Roles Permissions list.',command_perm_node)
                    return True
    
    def get_roles(self) -> list[str]:
        """Pre build my Permissions Role Name List"""
        self.permission_roles = []
        for role in self.permissions['Roles']:
            self.permission_roles.append(role['name'])
        return self.permission_roles

    async def get_role_prefix(self, user_id:str=None, context:commands.Context=None) -> Union[str, None]:
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