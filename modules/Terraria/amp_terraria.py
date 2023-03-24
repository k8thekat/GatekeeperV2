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
from __future__ import annotations
import AMP_Console
import AMP

# Resources - https://www.dexerto.com/gaming/terraria-console-commands-explained-a-simple-controls-guide-1663852/
DisplayImageSources = ['steam:105600']


class AMPTerraria(AMP.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, TargetName: str = None):
        self.perms = []
        self.APIModule = 'Terraria'

        super().__init__(instanceID, serverdata, Handler=Handler, TargetName=TargetName)
        self.Console = AMPTerrariaConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Terraria_Banner.png'
        self.SenderFilterList.append('Server')

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/k8thekat/GatekeeperV2/blob/main/resources/avatars/terraria_avatar.jpg?raw=true'

    def Chat_Message(self, message: str, author: str = None, author_prefix: str = None, server_prefix: str = None):
        """Sends a customized message via say through the console."""
        self.Login()
        # Colors:
        # To write colors, you have to use the "color" variable. To write the command, use 'say [c/(insert color):text]' Ex: /say [c/ff0000:Hi!]
        # Colors must be entered as hex codes
        content = 'say [c/0000ff:[Discord][c/0000ff:]] '
        if server_prefix != None:
            content += f'[c/ffd700:({server_prefix})]'

        if author_prefix != None:
            content += f'[c/ffff00:({author_prefix})]'

        content += f'[c/ffffff:<{author}> {message}]'
        self.ConsoleMessage(content)

    def Broadcast_Message(self, message, prefix: str = None):
        """Used to Send a Broadcast Message to the Server"""
        self.Login()
        content = 'say '
        if prefix != None:
            content += f'<{prefix}> '

        content += f'{message}'
        self.ConsoleMessage(content)


class AMPTerrariaConsole(AMP_Console.AMPConsole):
    def __init__(self, AMPInstance=AMPTerraria):
        super().__init__(AMPInstance)
