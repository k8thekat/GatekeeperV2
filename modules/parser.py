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
import re
import utils
import DB
from discord.ext import commands

class Parser():
    def __init__(self, client: commands.Bot=None):
        import logging
        self.logger = logging.getLogger()
        self._client = client
       
        self.symbol_reg = "[,/':;&\-\?()]"
        self.server_reg = "(server|pack)"

        self.ign_reg = r"(\bign|ingamename|in-game-name|in-gamename|in.game.name|name.)" 
        self.steam_reg = r"\b(steamid|\bid|steam.id|steam.name|steamname)"

        self.str_filter_exact = r"\b(for|the|and|on|in|to|and|is|server|so|may|be|multiple|thanks|please|pls|plz)"
        self.whitelist_reg = r"(whitelist|\bwl)"
  
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        #self.uBot = utils.botUtils(self._client)

        self.isSteam = False
        self.logger.dev('Setting Up the Parser...')

    def ParseIGNServer(self, messages:str):
        msg_split = messages.split()
        servers = []
        name = None
        pos = -1

        for entry in msg_split: 
            pos += 1
            flag_server = re.search(self.server_reg, entry.lower())
            flag_ign = re.search(self.ign_reg, entry.lower())
            flag_steam = re.search(self.steam_reg, entry.lower())
            flag_whitelist = re.search(self.whitelist_reg, entry.lower())
            if flag_server != None:
            
                if len(msg_split) > pos+1:

                    #This catch's servers if they are attached to the server (eg:server:TNP5)
                    start,end = flag_server.span()
                    if end < len(msg_split[pos])-1: 
                        possible_server = msg_split[pos][end:len(msg_split[pos])]
                        possible_server = re.sub(self.symbol_reg, "",possible_server)
                
                        if len(possible_server) >= 2:
                            self.logger.dev(f'possible server attached to server: {possible_server}')
                            servers.append(possible_server.lower())
                        
                    flag_str_filter = re.search(self.str_filter_exact, msg_split[pos+1])
                    if flag_str_filter != None and len(msg_split) > pos+2:
                        possible_server = msg_split[pos+2][0:len(msg_split[pos+2])]
                        possible_server = re.sub(self.symbol_reg,"",possible_server)

                        if flag_str_filter == None:
                            self.logger.dev(f'possible server after filter: {possible_server}')
                            servers.append(possible_server.lower())
                
                    else:
                        possible_server = msg_split[pos+1][0:len(msg_split[pos+1])]
                        possible_server = re.sub(self.symbol_reg,"",possible_server)
                        self.logger.dev(f'possible server: {possible_server}') 
                        servers.append(possible_server.lower())
                        
                if len(msg_split) > pos+3:
                    flag_symbols = re.search(self.symbol_reg, msg_split[pos+2])
                    if flag_symbols == None:
                        next_possible_server = msg_split[pos+2][0:len(msg_split[pos+2])]
                        flag_str_filter = re.search(self.str_filter_exact, next_possible_server)
                        if flag_str_filter == None:
                            self.logger.dev(f'next_possible_server: {next_possible_server}') #We will attempt to look this server up too!
                            servers.append(next_possible_server.lower())

            if flag_ign != None or flag_steam != None:
                name_found = False

                self.isSteam = False
                if flag_steam != None:
                    self.isSteam = True
    
                #Need to find ign and see if the name is attached to the same entry.
                if len(msg_split) > pos+1:
                    start,end = flag_ign.span()

                    #This catch's IGNs if they are attached to the IGN (eg:IGN:k8thekat)
                    if end < len(msg_split[pos])-1: 
                        possible_name = msg_split[pos][end:len(msg_split[pos])]
                        possible_name = re.sub(self.symbol_reg, "",possible_name)
                        name_found = True
                        self.logger.dev(f'possible name attached to IGN: {possible_name}')
                        name = possible_name
                        
                    #Need to make it so that str has to be "alone" not inside of a name/server etc..
                    flag_str_filter = re.search(self.str_filter_exact,msg_split[pos+1].lower()) 
                    if flag_str_filter != None and len(msg_split) > pos+2:
                        possible_name = msg_split[pos+2][0:len(msg_split[pos+2])]
                        possible_name = re.sub(self.symbol_reg,"",possible_name)
                        self.logger.dev(f'possible name after str filter: {possible_name}') 
                        name = possible_name

                    else:
                        if name_found:
                            possible_server = msg_split[pos+1][0:len(msg_split[pos+1])]
                            possible_server = re.sub(self.symbol_reg,"",msg_split[pos+1])
                            self.logger.dev(f'possible server after name found: {possible_server}')
                            servers.append(possible_server.lower())

                        else:
                            possible_name = msg_split[pos+1][0:len(msg_split[pos+1])]
                            possible_name = re.sub(self.symbol_reg,"",msg_split[pos+1])
                            self.logger.dev(f'possible name: {possible_name}') 
                            name = possible_name

                if len(msg_split) > pos+2:
                    flag_search = re.search(f"{self.server_reg}|{self.ign_reg}",msg_split[pos+2].lower())
                    if flag_search == None and len(msg_split[pos+2]) > 1:

                        #This makes sure the next entry ISNT the same as the IGN
                        if possible_name != msg_split[pos+2]: 
                            possible_server_afterIGN = msg_split[pos+2][0:len(msg_split[pos+2])]
                            possible_server_afterIGN = re.sub(self.symbol_reg,"",possible_server_afterIGN)

                            #Check the next entry to see if ts a filtered string, if so lets keep going.
                            if re.search(self.str_filter_exact,possible_server_afterIGN) != None:
                                for message in msg_split[pos+3:]:
                                    if re.search(self.str_filter_exact, message) == None:
                                        possible_server_afterIGN = message
                                        self.logger.dev(f'possible server after IGN loop: {possible_server_afterIGN}')
                                        servers.append(possible_server_afterIGN.lower())  
                            else:
                                self.logger.dev(f'possible server after IGN: {possible_server_afterIGN}')
                                servers.append(possible_server_afterIGN.lower())
                               


            if flag_whitelist != None:
                if len(msg_split) > pos+1:

                    #Check next entry if its apart of the str_filter if not then use it; else go one entry further.
                    flag_str_filter = re.search(self.str_filter_exact,msg_split[pos+1])
                    if flag_str_filter != None and len(msg_split) > pos+2:
                        possible_server_afterwhitelist = msg_split[pos+2][0:len(msg_split[pos+2])]
                        possible_server_afterwhitelist = re.sub(self.symbol_reg,"",possible_server_afterwhitelist)

                        flag_str_filter = re.search(self.str_filter_exact,msg_split[pos+2])
                        if flag_str_filter == None:
                            self.logger.dev(f'possible server after whitelist: {possible_server_afterwhitelist}')
                            servers.append(possible_server_afterwhitelist.lower())

        return name,servers
     
    def serverName_match(self, server_list:list):
        """Attempts to match user server requests to possible server names/nicknames when a nickname has a space."""
        db_servers = self.DB.GetAllServers()
        list_of_server_names = []
        for server in db_servers:
            dbserver = self.DB.GetServer(Name = server)
            list_of_server_names.append(server.replace('_',' ').lower())
            for nickname in dbserver.Nicknames:
                list_of_server_names.append(nickname.lower())
                
        list_of_server_names.sort(reverse=True)
        for i in range(0, len(list_of_server_names)):
            list_of_server_names[i] = list_of_server_names[i].split()

        self.logger.dev(list_of_server_names)
        #use the length of the list entry inside of the server names/nicknames list eg mylist[1,2] to entry[0:len(mylist)].
        index = 0
        possible_servers = []
        while index < len(server_list):
            found_server = None
            for curserver in list_of_server_names:
                self.logger.dev('server entry', server_list[index:index+len(curserver)], 'server name entry', curserver)
                if server_list[index:index+len(curserver)] == curserver:
                    found_server = curserver
                    break
            if found_server != None:
                index += len(found_server)
                possible_servers.append(" ".join(found_server))
            else:
                index += 1
        return possible_servers