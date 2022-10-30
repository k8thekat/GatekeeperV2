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
#Resources - https://www.dexerto.com/gaming/terraria-console-commands-explained-a-simple-controls-guide-1663852/
DisplayImageSources = ['steam:105600']
class AMPTerraria(AMP.AMPInstance):
    def __init__(self, instanceID = 0, serverdata = {},Index = 0,Handler=None):
        self.perms = []
        self.APIModule = 'Terraria'
        
        super().__init__(instanceID,serverdata,Index,Handler=Handler)
        self.Console = AMPTerrariaConsole(AMPInstance = self)

        self.default_background_banner_path = 'resources/banners/Terraria_Banner.png'

        if self.Avatar_url == None:
            self.DB_Server.Avatar_url = 'https://drive.google.com/uc?export=download&id=12SJ2Z9BBuOKiTkdKSMgtRrsmOgWWZIz3'

class AMPTerrariaConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPTerraria):
        super().__init__(AMPInstance)