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
from amp_instance import AMPInstance
import amp_console


DisplayImageSources = ['steam:730']


class AMPCsgo(AMPInstance):
    def __init__(self, instanceID: int = 0, serverdata: dict = {}, default_console: bool = False, Handler=None, _TargetName: str = None):
        self.perms = []
        self.APIModule = 'Counterstrike_GO'

        super().__init__(instanceID, serverdata, Handler=Handler, _TargetName=_TargetName)
        self.Console = AMPCsgoConsole(AMPInstance=self)

        self.default_background_banner_path = 'resources/banners/CS_Go_Banner_3.png'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://github.com/k8thekat/GatekeeperV2/blob/main/resources/avatars/csgo_avatar.png?raw=true'


class AMPCsgoConsole(amp_console.AMPConsole):
    def __init__(self, AMPInstance=AMPCsgo):
        super().__init__(AMPInstance)
