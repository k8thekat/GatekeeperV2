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
import amp
import amp_console


DisplayImageSources = ['steam:108600']


class AMPProjectzomboid(amp.AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, _TargetName: str = None):
        self.perms = []
        self.APIModule = 'Project Zomboid'

        super().__init__(instanceID, serverdata, Handler=Handler, _TargetName=_TargetName)
        self.Console = AMPProjectzomboidConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/Project_Zomboid_banner_1.jpg'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/k8thekat/GatekeeperV2/blob/main/resources/avatars/project_zomboid_avatar.png?raw=true'

    # This isn't the best implementation...
    # Project Zomboid has one-way chat from game to Discord. You need to enable that.
    # This method will allow messages from Discord to be posted in-game.
    # However, they are server broadcasts and will be posted in the middle of the screen.
    def Chat_Message(self, message: str, author: str = None, author_prefix: str = None, server_prefix: str = None):
        """Sends a customized message via servermsg through the console."""
        self.Login()
        content = 'servermsg "[Discord]'
        if server_prefix != None:
            content += f'({server_prefix}) '

        if author_prefix != None:
            content += f'({author_prefix}) '

        content += f'[{author}]: {message}"'
        self.ConsoleMessage(content)

    def Broadcast_Message(self, message, prefix: str = None):
        """Used to Send a Broadcast Message to the Server"""
        self.Login()
        content = 'servermsg "'
        if prefix != None:
            content += f'<{prefix}> '

        content += f'{message}"'
        self.ConsoleMessage(content)


class AMPProjectzomboidConsole(amp_console.AMPConsole):
    def __init__(self, AMPInstance=AMPProjectzomboid):
        super().__init__(AMPInstance)
