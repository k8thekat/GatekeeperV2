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
import AMP as AMP
import discord
from DB import DBUser

DisplayImageSources = ['Template']
class AMPTemplate(AMP.AMPInstance):
    def __init__(self, instanceID = 0, serverdata = {},Index = 0,Handler=None):
        self.perms = []
        self.APIModule = 'Template'
        
        super().__init__(instanceID,serverdata,Index,Handler=Handler)
        self.Console = AMPTemplateConsole(AMPInstance = self)

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://drive.google.com/uc?export=download&id=12XKmQwng3lNSDKxmvImyHIMQ1Ykg6XcQ'
        
    def setup_AMPpermissions(self):
        """Sets the Permissions for Template Modules"""
        self.logger.warning(f'Setting up {self.FriendlyName} Template Module permissions...')
        for perm in self.perms:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]
            self.setAMPRolePermissions(self.AMP_BotRoleID,perm,enabled)
            self.logger.dev(f'Set {perm} for {self.AMP_BotRoleID} to {enabled}')
        return True

    def Chat_Message(self, message:str, author:str=None, prefix:str=None):
        """Sends a message in a way to mimic that of in-game Chat Messages."""
        #This is where you place your code for sending messages in a format/way that mimics that of in game chat messages.
        #Some servers have build in commands via console commands; others may require more work.
        #Always make sure to login if it requires an AMP API call.
        self.Login()
    
    def Chat_Message_Formatter(self, message:str):
        """Any Special formatting for Messages to be sent to the Servers Chat"""
        return message

    def get_IGN_Avatar(self, db_user:DBUser=None, user:str=None):
        """Handles converting discord information into something unique for the server if needed."""
        #Anything like formatting or replacing a users display name to be attached to the Chat_message().
        return False

    def whitelist_intake(self, discord_user:discord.Member, user_name:str):
        """Customized Setup for handling Whitelist requests depending on the server Type. AMP has a built in Generic handler. 
        Override this method for more customization."""
        #Example:
        #Try to find the DB user first.
        # db_user = self.DB.GetUser(discord_user.name)
        # if db_user == None:
        #     #Basic Add of user to DB.
        #     self.DB.AddUser(DiscordID=discord_user.id, DiscordName=discord_user.name) 
        # else:
        #     return True

class AMPTemplateConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPTemplate):
        super().__init__(AMPInstance)


    