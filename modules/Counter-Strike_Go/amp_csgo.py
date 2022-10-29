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
import pathlib

DisplayImageSources = ['steam:730']
class AMPCsgo(AMP.AMPInstance):
    def __init__(self, instanceID = 0, serverdata = {},Index = 0,Handler=None):
        self.perms = []
        self.APIModule = 'Counterstrike_GO'
        
        super().__init__(instanceID,serverdata,Index,Handler=Handler)
        self.Console = AMPCsgoConsole(AMPInstance = self)

        self.background_banner_path = 'resources/banners/CS_Go_Banner_3.png'
        self.Banner = self.DB_Server.getBanner(self.background_banner_path)

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://drive.google.com/uc?export=download&id=12QI1dnEN4fFbspNLCHELcJIy6ar2cQUa'

class AMPCsgoConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPCsgo):
        super().__init__(AMPInstance)

    
    def console_filter(self, message):
        print()

    def console_events(self, message):
        print()