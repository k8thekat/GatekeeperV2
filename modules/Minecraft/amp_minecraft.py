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

from DB import DBUser


DisplayImageSources = ["internal:MinecraftJava"]
class AMPMinecraft(AMP.AMPInstance):
    """This is Minecraft Specific API calls for AMP"""
    def __init__(self, instanceID:int= 0, serverdata:dict= {}, default_console:bool= False, Handler=None, TargetName:str = None):
        self.perms = ['Minecraft.*','Minecraft.InGameActions.*','-Minecraft.PluginManagement.*']
        self.APIModule = 'MinecraftModule' #This is what AMP API calls the Module in the Web GUI API Documentation Browser

        
        super().__init__(instanceID, serverdata, Handler= Handler, TargetName=TargetName)
        self.Console = AMPMinecraftConsole(self)
        
        self.default_background_banner_path = 'resources/banners/Minecraft_banner.png'
        
        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/k8thekat/GatekeeperV2/blob/main/resources/avatars/mc_avatar.jpg?raw=true'
         
    def setup_Gatekeeper_Permissions(self):
        """Sets the Permissions for Minecraft Modules"""
        self.logger.warning(f'Setting up {self.FriendlyName} Minecraft Module permissions...')
        for perm in self.perms:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]

            if self.setAMPRolePermissions(self.AMP_BotRoleID, perm, enabled):
                self.logger.dev(f'Set {perm} for {self.AMP_BotRoleID} to {enabled}')

    def name_Conversion(self, name): 
        self.logger.dev(f'Converting IGN to UUID: {name}')
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

    def addWhitelist(self, db_user: DBUser):
        """Adds a User to the Whitelist File *Supports IGN*"""
        self.Login()
        self.ConsoleMessage(f'whitelist add {db_user.MC_IngameName}')

    def getWhitelist(self):
        """Returns a List of Dictionary Entries of all Whitelisted Users `{'name': 'IGN', 'uuid': '781a2971-c14b-42c2-8742-d1e2b029d00a'}`"""
        self.Login()
        parameters = {}
        result = self.CallAPI(f'{self.APIModule}/GetWhitelist',parameters)
        return result['result']

    def removeWhitelist(self, name:str):
        """Removes a User from the Whitelist File *Supports IGN*"""
        self.Login()
        self.ConsoleMessage(f'whitelist remove {name}')
        
    def check_Whitelist(self, db_user: DBUser, in_gamename: str= None):
        self.logger.dev(f'Checking if {db_user.DiscordName} is whitelisted on {self.FriendlyName}...')
        """Checks if the User is already in the whitelist file. Supports DB User and MC In game Name.\n
        Returns `None` if the UUID is whitelisted \n
        Returns `False` if no UUID exists \n
        Returns `True` if not in Whitelisted"""
        #No IGN or UUID and they didnt provide one. Return False
        if db_user.MC_IngameName == None and in_gamename == None:
            return False
        
        if db_user.MC_IngameName == None and in_gamename != None:
            uuid = self.name_Conversion(in_gamename)
            if uuid == None:
                return False
            
            db_user.MC_IngameName = in_gamename
            db_user.MC_UUID = uuid
        
        if db_user.MC_UUID == None:
            uuid = self.name_Conversion(db_user.MC_IngameName)
            if uuid == None:
                return False
            
            db_user.MC_UUID = uuid

        self.Login()
        server_whitelist = self.getWhitelist()
        for entry in server_whitelist:
            if db_user.MC_UUID == entry['uuid'].replace('-',''):
                return None

        return True

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
