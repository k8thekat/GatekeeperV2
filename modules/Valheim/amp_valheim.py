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

DisplayImageSources = ['steam:892970']
class AMPValheim(AMP.AMPInstance):
    def __init__(self, instanceID = 0, serverdata = {},Index = 0,Handler=None):
        self.perms = []
        self.APIModule = 'Valheim'
        
        super().__init__(instanceID,serverdata,Index,Handler=Handler)
        self.Console = AMPValheimConsole(AMPInstance = self)


class AMPValheimConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPValheim):
        super().__init__(AMPInstance)