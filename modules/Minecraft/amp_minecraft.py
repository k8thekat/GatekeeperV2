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
import AMP
import requests
import json
import discord
import os
import pathlib

from DB import DBUser


DisplayImageSources = ["internal:MinecraftJava"]
class AMPMinecraft(AMP.AMPInstance):
    """This is Minecraft Specific API calls for AMP"""
    def __init__(self, instanceID = 0, serverdata = {}, Handler=None):
        self.perms = ['Minecraft.*','Minecraft.InGameActions.*','-Minecraft.PluginManagement.*']
        self.APIModule = 'MinecraftModule' #This is what AMP API calls the Module in the Web GUI API Documentation Browser

        
        super().__init__(instanceID, serverdata,Handler= Handler)
        self.Console = AMPMinecraftConsole(self)
        
        self.default_background_banner_path = 'resources/banners/Minecraft_banner.png'
        
        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/k8thekat/GatekeeperV2/blob/main/resources/avatars/mc_avatar.jpg?raw=true'
         
    def setup_AMPpermissions(self):
        """Sets the Permissions for Minecraft Modules"""
        self.logger.warning(f'Setting up {self.FriendlyName} Minecraft Module permissions...')
        for perm in self.perms:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]
            #print(self.AMP_BotRoleID)
            self.setAMPRolePermissions(self.AMP_BotRoleID,perm,enabled)
            self.logger.dev(f'Set {perm} for {self.AMP_BotRoleID} to {enabled}')
        return True

    def name_Conversion(self, name): 
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

    def name_History(self, mc_user_uuid):
        """Requires `user_UUID` WTF Does this even return? Possible a Dictionary List?"""
        url = f'https://api.mojang.com/user/profiles/{mc_user_uuid}/names'
        post_req = requests.get(url)
        return post_req.json()[-1]

    def addWhitelist(self, name:str= None, discord_user:discord.Member= None):
        """Adds a User to the Whitelist File *Supports IGN*"""
        self.Login()
        check = False
        if discord_user != None:
            check = self.check_Whitelist(discord_user= discord_user)
            db_user = self.DB.GetUser(discord_user.name)
            if db_user.MC_IngameName == None:
                name = db_user.MC_IngameName
        else:
            check = self.check_Whitelist(in_gamename= name)
        
        if check:
            self.ConsoleMessage(f'whitelist add {name}')
            return check
        else:
            return check
        
    def getWhitelist(self):
        """Returns a List of Dictionary Entries of all Whitelisted Users `{'name': 'IGN', 'uuid': '781a2971-c14b-42c2-8742-d1e2b029d00a'}`"""
        self.Login()
        parameters = {}
        result = self.CallAPI(f'{self.APIModule}/GetWhitelist',parameters)
        return result['result']

    def removeWhitelist(self, name:str= None, discord_user:discord.Member= None):
        """Removes a User from the Whitelist File *Supports IGN*"""
        self.Login()
        check = False
        if discord_user != None:
            check = self.check_Whitelist(discord_user= discord_user)
            db_user = self.DB.GetUser(discord_user.name)
            if db_user.MC_IngameName == None:
                name = db_user.MC_IngameName
        else:
            check = self.check_Whitelist(in_gamename= name)
            
        #If Check is None, means we found a Match! Remove them.
        if check == None:
            self.ConsoleMessage(f'whitelist remove {name}')
            return check
        else:
            return check
        
    def check_Whitelist(self, discord_user:discord.Member= None, in_gamename:str= None):
        """Checks if the User is already in the whitelist file. Supports DB User and MC In game Name.\n
        Returns `None` if the UUID is whitelisted \n
        Returns `False` if no UUID exists \n
        Returns `True` if not in Whitelisted"""
        user_uuid = None
        if discord_user != None:
            db_user = self.DB.GetUser(discord_user.name)
            if db_user.MC_UUID == None:
                return False
            user_uuid = db_user.MC_UUID

        if in_gamename != None:
            uuid = self.name_Conversion(in_gamename)
            if uuid == None:
                return False
            user_uuid = uuid 

        self.Login()
        server_whitelist = self.getWhitelist()
        for entry in server_whitelist:
            if user_uuid == entry['uuid'].replace('-',''):
                return None

        return True

    def whitelist_intake(self, discord_user:discord.Member, user_name:str):
        """Handles checking the User is in the Database, and if not, adding them to the Database.
        Returns False if UUID/IGN not found, <db_user> if found."""
        #Try to find the DB user first.
        db_user = self.DB.GetUser(discord_user.name)
        user_uuid = self.name_Conversion(user_name)
        if db_user != None:    
            #Check if the UUID and IGN are in the DB.
            if db_user.MC_UUID == None and db_user.MC_IngameName == None:
                #Updates User info in the Database with all the required information.
                if user_uuid != None:
                    db_user.MC_UUID = user_uuid
                    db_user.MC_IngameName = user_name
                    return True
                else:
                    return False
            else:
                #This assumes the UUID and IGN are set in the DB
                return True
        else:
            #Somehow the user isnt in the DB.
            return False

    def getHeadbyUUID(self, UUID:str):
        """Gets a Users Player Head via UUID"""
        #DOESNT WORK FOR AVATAR ICONS.. DONT USE IT!
        MChead = 'https://mc-heads.net/head/' + UUID
        return MChead

    def banUserID(self, ID:str):
        """Bans a User from the Server"""
        self.Login()
        parameters = {'id': ID}
        result = self.CallAPI(f'{self.APIModule}/BanUserByID', parameters)
        return result
    
    def Chat_Message(self, message:str, author:str=None, author_prefix:str=None, server_prefix:str=None):
        """Sends a customized message via tellraw through the console."""
        self.Login()
        # Colors:
        # To write colors, you have to use the "color" variable. To write the command, use /tellraw (text){"color":(insert color)}Ex: /tellraw @p {"text":"hi","color":"red"}
        # Here's a list of colors:Red, Green, Blue, White, Yellow, Dark_Red, Dark_Green, Dark_Blue, and Gold.
        # Fancy Font:
        # Writing font is fairly simple. Use the basic /tellraw command, and write {"(insert font)":true}. The fonts you can use are:italic, underlined, and bold.
        # How To Use Both:
        # To use both font and color, write a comma between the variables. Ex: /tellraw {"color":"green","bold":"true"}
        content = 'tellraw @a [{"text":"[Discord]","color":"blue"},'
        if server_prefix != None:
            content += f'{{"text":"({server_prefix})","color":"gold"}},'

        if author_prefix != None:
            content += f'{{"text":"({author_prefix})","color":"yellow"}},'
            
        content += f'{{"text":"<{author}>: {message}","color":"white"}}]'
        self.ConsoleMessage(content)

    def Chat_Message_Formatter(self, message:str):
        """Formats the message for Discord \n"""
        return message

    def get_IGN_Avatar(self, db_user:DBUser=None, user:str=None):
        """Handles returning customized discord message data for Minecraft Servers only."""

        if db_user != None and db_user.MC_IngameName != None and db_user.MC_UUID != None:
            return db_user.MC_IngameName, self.getHeadbyUUID(db_user.MC_UUID)

        if user != None:
            user_uuid = self.name_Conversion(user)
            if user_uuid == None:
                return False
            return user, self.getHeadbyUUID(user_uuid)

        else:
            self.logger.error('We failed to format the Chat Message.')
            return False

    def Broadcast_Message(self, message, prefix: str = None):
        """Used to Send a Broadcast Message to the Server"""
        self.Login()
        self.ConsoleMessage(f'say <{prefix}> :{message}')

class AMPMinecraftConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPMinecraft):
        super().__init__(AMPInstance)

    def console_filter(self, message):
        """This is what SHOULD be displayed if we filter the console!
        By Default everything is excluded, so we need to include what we want to see."""
        #Example Console Entry: {'Timestamp': '/Date(1658685241525)/', 'Source': 'Server thread/INFO', 'Type': 'Console', 'Contents': 'k8_thekat issued server command: /gamemode survival'}
        #Return TRUE to Exclude message
        if not self.AMPInstance.Console_Filtered:
            return False
        else:
            if message['Type'] == 'Chat':
                return False
            #This list will be used to capture output that I want. These are best for partial finds.
            message_finder_list = [
                'Unkown command.', 
                'players online:',
                'Staff',
                '?',
                'Help', 
                'left the game', 
                'joined the game', 
                'lost connection:',
                'whitelisted players:',
                'was slain by',
                'game mode to']
            for entry in message_finder_list:
                if message['Contents'].find(entry) != -1:
                    #print(f"Found {entry} in {message['Contents']}")
                    return False
            if message['Contents'].startswith('/'):
                return False
            if message['Contents'].startswith('Player Console banned') and message['Contents'].endswith('You have been banned:'):
                return False
            if message['Contents'].startswith('Player Console unbanned'):
                return False
            if message['Contents'].startswith('Added') and message['Contents'].endswith('to the whitelist'):
                return False
            if message['Contents'].startswith('Removed') and message['Contents'].endswith('from the whitelist'):
                return False
            else:
                self.logger.dev(f'Filtered Message {message}')
                return True
    
    def console_events(self, message):
        """ALWAYS RETURN FALSE! ALL events go to `.console_event_messages`"""
        event_list = ['left the game', 'joined the game', 'tried to swim','completed the challenge','made the advancement', 'was slain by', 'fell off', 'was shot by']
        #Event List Interations
        for event in event_list:
            if message['Contents'].find(event) != -1:
                self.logger.dev(f'**{self.AMPInstance.APIModule} Event Message Found {event}**')
                self.console_event_message_lock.acquire()
                self.console_event_messages.append(message['Contents'])
                self.console_event_message_lock.release()
                return False

        else:
            return False
