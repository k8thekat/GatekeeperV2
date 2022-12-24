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
import pathlib

#Resources
#https://wiki.factorio.com/Console

DisplayImageSources = ['steam:427520']
class AMPFactorio(AMP.AMPInstance):
    def __init__(self, instanceID:int= 0, serverdata:dict= {}, default_console:bool= False, Handler=None, TargetName:str = None):
        self.APIModule = 'Factorio'
        
        super().__init__(instanceID,serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPFactorioConsole(AMPInstance = self)

        self.default_background_banner_path = 'resources/banners/Factorio_Banner.jpg'
        
        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/k8thekat/GatekeeperV2/blob/main/resources/avatars/factorio_avatar.png?raw=true'
            
    def setup_Gatekeeper_Permissions(self):
        """Sets the Permissions for Factorio Modules"""
        self.logger.warning(f'Setting up {self.FriendlyName} Factorio Module permissions...')
        for perm in self.perms:
            enabled = True
            if perm.startswith('-'):
                enabled = False
                perm = perm[1:]
     
            if self.setAMPRolePermissions(self.AMP_BotRoleID, perm, enabled):
                self.logger.dev(f'Set {perm} for {self.AMP_BotRoleID} to {enabled}')

    def Chat_Message(self, message:str, author:str=None, prefix:str=None):
        #See https://wiki.factorio.com/Rich_text
        self.ConsoleMessage(f'[color=blue]"[Discord]"[/color] [color=default]<{author}>: {message}[/color]')

class AMPFactorioConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPFactorio):
        super().__init__(AMPInstance)