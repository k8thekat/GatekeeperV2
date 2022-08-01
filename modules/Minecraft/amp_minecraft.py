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


DisplayImageSources = ["internal:MinecraftJava"]

class AMPMinecraft(AMP.AMPInstance):
    """This is Minecraft Specific API calls for AMP"""
    def __init__(self, instanceID = 0, serverdata = {},Index = 0, Handler=None):
        self.perms = [f'Minecraft.*',f'Minecraft.InGameActions.*',f'-Minecraft.PluginManagement.*']
        self.APIModule = 'MinecraftModule' #This is what AMP API calls the Module in the Web GUI API Documentation Browser
        
        super().__init__(instanceID, serverdata, Index,Handler= Handler)
        self.Console = AMPMinecraftConsole(self)
         
    def setup_AMPpermissions(self):
        """Sets the Permissions for Minecraft Modules"""
        self.logger.info(f'Setting up {self.FriendlyName} Minecraft Module permissions.')
        for perm in self.perms:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]
            #print(self.AMP_BotRoleID)
            self.setAMPRolePermissions(self.AMP_BotRoleID,perm,enabled)
            self.logger.info(f'Set {perm} for {self.AMP_BotRoleID} to {enabled}')
        return True

    def name_Conversion(self,name): 
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

    def name_History(self,mc_user_uuid):
        """Requires `user_UUID` WTF Does this even return? Possible a Dictionary List?"""
        url = f'https://api.mojang.com/user/profiles/{mc_user_uuid}/names'
        post_req = requests.get(url)
        return post_req.json()[-1]

   
    def addWhitelist(self,User:str):
        """Adds a User to the Whitelist File *Supports UUID or IGN*"""
        self.Login()
        #print(User)
        parameters = {'UserOrUUID': User}
        result = self.CallAPI(f'{self.APIModule}/AddToWhitelist', parameters)
        #print(result)
        return result

    def getWhitelist(self):
        """Returns a List of Dictionary Entries of all Whitelisted Users `{'name': 'IGN', 'uuid': '781a2971-c14b-42c2-8742-d1e2b029d00a'}`"""
        self.Login()
        parameters = {}
        result = self.CallAPI(f'{self.APIModule}/GetWhitelist',parameters)
        #print(result)
        return result['result']

    def removeWhitelist(self,User:str):
        """Removes a User from the Whitelist File *Supports UUID or IGN*"""
        self.Login()
        parameters = {'UserOrUUID': User}
        result = self.CallAPI(f'{self.APIModule}/RemoveWhitelistEntry',parameters)
        return result

    def check_Whitelist(self,user_UUID):
        """Checks if the User is already in the whitelist file.
        Returns `True` if the UUID is found."""
        self.Login()
        server_whitelist = self.getWhitelist()
        for entry in server_whitelist:
            if user_UUID == entry['uuid']:
                return True

    def getHeadbyUUID(self,UUID:str):
        """Gets a Users Player Head via UUID"""
        #DOESNT WORK FOR AVATAR ICONS.. DONT USE IT!
        MChead = 'https://mc-heads.net/head/' + UUID
        return MChead

    def banUserID(self,ID:str):
        """Bans a User from the Server"""
        self.Login()
        parameters = {'id': ID}
        result = self.CallAPI(f'{self.APIModule}/BanUserByID', parameters)
        return result
    
    def send_message(self, message:discord.Message):
        """Sends a customized message via tellraw through the console."""
        self.Login()
        self.ConsoleMessage(f'tellraw @a [{{"text":"[Discord]","color":"purple"}},{{"text":"<{message.author.name}>: {message.content}","color":"white"}}]')

    def discord_message(self,user):
        """Handles returning customized discord message data for Minecraft Servers only."""
        if user.MC_IngameName != None and user.MC_UUID != None:
            return user.MC_IngameName, self.getHeadbyUUID(user.MC_UUID)


class AMPMinecraftConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPMinecraft):
        super().__init__(AMPInstance)


    def console_filter(self, message):
        """This is what SHOULD be displayed if we filter the console!"""
        #Example Console Entry: {'Timestamp': '/Date(1658685241525)/', 'Source': 'Server thread/INFO', 'Type': 'Console', 'Contents': 'k8_thekat issued server command: /gamemode survival'}
        #Return TRUE to Exclude message
        if not self.AMPInstance.Console_Filtered:
            return False
        else:
            if message['Type'] == 'Chat':
                return False
            #This list will be used to capture output that I want. These are best for partial finds.
            message_finder_list = ['Unkown command.', 'players online.','Staff','?','Help']
            for entry in message_finder_list:
                if message['Contents'].find(entry) != -1:
                    print(f"Found {entry} in {message['Contents']}")
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
                return True
    


    def console_events(self, message):
        """ALWAYS RETURN FALSE!"""
        if message['Contents'].endswith('has joined the game!'):
            return message
        if message['Contents'].endswith('has left the game!'):
            return message
        else:
            return False
