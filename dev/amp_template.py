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

    def console_events(self, message):
        """This will handle all player join/leave/disconnects and other achievements. THIS SHOULD ALWAYS RETURN FALSE!
        ALL events go to `self.console_event_messages` """
        #Any specific events that need to be caught, like achievements, player deaths.
        #Anything that is deemed an "event" worth monitoring and displaying to a different discord channel.
        #Example:
        # if message['Contents'].endswith('has joined the game'):
        #     self.console_event_message_lock.acquire()
        #     self.console_event_messages.append(message['Contents'])
        #     self.console_event_message_lock.release()
        #     return False
        return False
    
    def console_filter(self, message):
        """Controls what will be sent to the Discord Console Channel via AMP Console."""
        #You can remove specific console messages that get output to the Discord Console Channel.
        #Return TRUE if you want to PREVENT the message from being displayed. 
        #Usually you return True by default and use this as a whitelist.
        #Example:
        #This list will be used to capture output that I want. These are best for partial finds.
        # message_finder_list = ['Unkown command.', 'players online:','Staff','?','Help', 'left the game', 'joined the game', 'lost connection:']
        # for entry in message_finder_list:
        #     if message['Contents'].find(entry) != -1:
        #         return False

        if not self.AMPInstance.Console_Filtered:
            return False
        return True


    