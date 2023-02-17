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
import AMP_Console


DisplayImageSources = ['steam:251570']
class AMPSevendays(AMP.AMPInstance):
    def __init__(self, instanceID:int= 0, serverdata:dict= {}, default_console:bool= False, Handler=None, TargetName:str = None):
        self.perms = []
        self.APIModule = 'Seven Days To Die'
        
        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPSevendaysConsole(AMPInstance = self)

        self.default_background_banner_path = 'resources/banners/7Days_Banner_2.jpg'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/k8thekat/GatekeeperV2/blob/main/resources/avatars/7days_avatar.png?raw=true'

    def Chat_Message(self, message:str, author:str=None, author_prefix:str=None, server_prefix:str=None):
            """Sends a customized message via say through the console."""
            self.Login()
            content = 'say "[Discord] '
            if server_prefix != None:
                content += f'({server_prefix}) '

            if author_prefix != None:
                content += f'({author_prefix}) '
                
            content += f'<{author}> {message}"'
            self.ConsoleMessage(content)

    def Broadcast_Message(self, message, prefix: str = None):
        """Used to Send a Broadcast Message to the Server"""
        self.Login()
        content = 'say "'
        if prefix != None:
            content += f'<{prefix}> '
        
        content += f'{message}"'
        self.ConsoleMessage(content)


class AMPSevendaysConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance = AMPSevendays):
        super().__init__(AMPInstance)