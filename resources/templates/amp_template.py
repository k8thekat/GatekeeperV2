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

#The DisplayImageSource is used to Uniquely indentify an Instance; as most instances use a `Generic` Template from AMP
#If you enable `-dev` when running Gatekeeper you can see the `DisplayImageSource` during startup when it is connecting/creating your AMP Instance Objects.
#Most will show something like `Steam:#####` which points to the SteamAPP library location of the game. 
#Yes this is just an image; but as it stands its the only unique peice of information a Generic Template has at this time.
#eg. `Instance Name: ComfyCraftServer101 // InstanceID: abd7b27d-9f4a-4bda-afff-7287dc061b53 // Module: Minecraft // Port: 8087 // DisplayImageSource: internal:MinecraftJava`
DisplayImageSources = ['Template']
class AMPTemplate(AMP.AMPInstance):
    def __init__(self, instanceID:int= 0, serverdata:dict= {}, default_console:bool= False, Handler=None, TargetName:str = None):
        #This list will house any special permissions you need to be able to make API calls (If the Module supports it)
        #eg `['Minecraft.*','Minecraft.InGameActions.*','-Minecraft.PluginManagement.*']`
        #Any perm node with a `-` in front of it tells the permissions check to NOT GRANT THAT PERMISSION TO GATEKEEPER
        #Each of those perm nodes are required to use specific API calls that can be seen by logging into that specific Instance with `/API` at the end of the URL. See below...
        self.perms = []

        #The APIModule must line up with the API calls that AMP makes for a particular instance.
        #Most cases this should be changed to `Generic` and left alone; unless the Server Type is a unique module that AMP(Cubecoders) has created.
        #As seen above, the parameter `Module:` repsents what type of Template the Server is using. 
        #!!!IF it says `GenericModule` then this MUST BE SET TO `GENERIC`!!!
        #Otherwise you can validate the Module by logging into that specific Instance(eg. www.youramppanelurlhere.com/AMPPort/API)
        #You can get the `AMPPort` from the `-dev` print as seen in the above comments under `Port: XXXX`.
        self.APIModule = 'Template'
        
        super().__init__(instanceID, serverdata, Handler= Handler, TargetName= TargetName)
        self.Console = AMPTemplateConsole(AMPInstance = self)

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://drive.google.com/uc?export=download&id=12XKmQwng3lNSDKxmvImyHIMQ1Ykg6XcQ'
        
    def setup_AMPpermissions(self):
        #This is used for any special permissions the AMP Module will need. You simply add them to `self.perms`
        #!!DO NOT CHANGE HOW THIS METHOD FUNCTIONS OR YOU WILL BREAK STARTUP!!
        """Sets the Permissions for Template Modules"""
        self.logger.warning(f'Setting up {self.FriendlyName} {self.APIModule} Module permissions...')
        for perm in self.perms:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]

            if self.setAMPRolePermissions(self.AMP_BotRoleID, perm, enabled):
                self.logger.dev(f'Set {perm} for {self.AMP_BotRoleID} to {enabled}')

    def Chat_Message(self, message:str, author:str=None, author_prefix:str=None, server_prefix:str=None):
        """Sends a message in a way to mimic that of in-game Chat Messages."""
        #!!DO NOT CHANGE THE PARAMETERS!! You will break functionality.
        #This is where you place your code for sending messages in a format/way that mimics that of in game chat messages.
        #Some servers have build in commands via console commands; others may require more work.
        #Always make sure to login if it requires an AMP API call.
        #
        #Example is Minecraft requires you to use `/say` inside the console to mimic a Chat message.
        self.Login()

    #All of the below methods are apart of the core functionality of each AMP Module; some Instances will never need these and some will need them configured for a specific server type.
    #Feel free to change the logic inside the methods; but remember to keep any parameters intact.

    def Broadcast_Message(self, message, prefix:str=None):
        """Base Function for Broadcast Messages to AMP ADS"""
        return

    def addWhitelist(self, db_user, in_gamename: str= None):
        """Base Function for AMP.addWhitelist"""
        #Use the DB_User object and get the required IGN depending on the server type.
        return False

    def getWhitelist(self) -> dict[str, str]:
        """Base Function for AMP.getWhitelist"""
        return

    def removeWhitelist(self, db_user, in_gamename: str= None):
        """Base Function for AMP.removeWhitelist"""
        return False

    def check_Whitelist(self, db_user=None, in_gamename:str= None):
        self.logger.dev(f'Checking if {in_gamename if db_user == None else db_user.DiscordName} is whitelisted on {self.FriendlyName}...')
        """Returns `None` if the ign is whitelisted \n
        Returns `False` if no UUID exists \n
        Returns `True` if not in Whitelisted"""
        return None
 
    #Any custom Methods or Functionality you need can be added below here. -------------------------------------------------------------------------

class AMPTemplateConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPTemplate):
        super().__init__(AMPInstance)