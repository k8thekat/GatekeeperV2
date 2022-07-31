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

class Parser():
    def __init__(self):
        import logging
        self.logger = logging.getLogger()
        self.logger.info('Setting Up the Parser')

        #We can swap these out to allow people to set them via the DB for more in-depth filtering
        #self.symbol_reg = "[,./':;&\.\-\?()]"
        self.symbol_reg = "[,/':;&\-\?()]"
        self.server_reg = "(server|pack)"

        self.ign_reg = r"(\bign|\bing|ingamename|in-game-name|in-gamename|in.game.name|name.)" 
        self.steam_reg = r"\b(steamid|\bid|steam.id|steam.name|steamname)"

        self.str_filter_exact = r"\b(for|the|and|on|in|to|and|is|server|ign|so|may|be|multiple|thanks)"
        self.whitelist_reg = r"(whitelist|\bwl)"
        #self.str_filter_loose = "(for|the|and|on|in|to|and|is|server|ign|so|may|be)"

        self.uBot = utils.botUtils()

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB

        self.isSteam = False

    def ParseIGNServer(self,messages):
        msg_split = messages.split(' ')
        self.logger.debug(msg_split)
        servers = []
        name = None
        pos = -1
        for entry in msg_split:
            #print('msg entry',entry)
            pos += 1
            flag_server = re.search(self.server_reg, entry.lower())
            flag_ign = re.search(self.ign_reg,entry.lower())
            flag_steam = re.search(self.steam_reg,entry.lower())
            flag_whitelist = re.search("(whitelist)",entry.lower())
            if flag_server != None:
            
                if len(msg_split) > pos+1:

                    #This catch's servers if they are attached to the server (eg:server:TNP5)
                    start,end = flag_server.span()
                    if end < len(msg_split[pos])-1: 
                        possible_server = msg_split[pos][end:len(msg_split[pos])]
                        possible_server = re.sub(self.symbol_reg, "",possible_server)
                
                        if len(possible_server) >= 2:
                            self.logger.debug(f'possible server attached to server: {possible_server}')
                            servers.append(possible_server)
                        
                    flag_str_filter = re.search(self.str_filter_exact, msg_split[pos+1])
                    if flag_str_filter != None and len(msg_split) > pos+2:
                        possible_server = msg_split[pos+2][0:len(msg_split[pos+2])]
                        possible_server = re.sub(self.symbol_reg,"",possible_server)

                        if flag_str_filter == None:
                            self.logger.debug(f'possible server after filter: {possible_server}')
                            servers.append(possible_server)
                
                    else:
                        possible_server = msg_split[pos+1][0:len(msg_split[pos+1])]
                        possible_server = re.sub(self.symbol_reg,"",possible_server)
                        self.logger.debug(f'possible server: {possible_server}') 

                        server = self.uBot.serverparse(possible_server) #We will attempt to look up the server here.
                        if server != None:
                            servers.append(possible_server)

                        #This would be checked using utils server parse and if it fails then maybe we have an IGN? 
                        # Could also check the discord user if they have an ign already.
                        if server == None: 
                            possible_name = msg_split[pos+1][0:len(msg_split[pos+1])]
                            possible_name = re.sub(self.symbol_reg,"",possible_name)
                            self.logger.debug(f'possible name after server: {possible_name}')
                            name = possible_name
                            
                        
                if len(msg_split) > pos+3:
                    flag_symbols = re.search(self.symbol_reg, msg_split[pos+2])
                    if flag_symbols == None:
                        next_possible_server = msg_split[pos+2][0:len(msg_split[pos+2])]
                        flag_str_filter = re.search(self.str_filter_exact, next_possible_server)
                        if flag_str_filter == None:
                            self.logger.debug(f'next_possible_server: {next_possible_server}') #We will attempt to look this server up too!
                            servers.append(next_possible_server)

            if flag_ign != None or flag_steam != None:
                name_found = False

                self.isSteam = False
                if flag_steam != None:
                    self.isSteam = True
    
                #Need to find ign and see if the name is attached to the same entry.
                if len(msg_split) > pos+1:
                    start,end = flag_ign.span()
            
                    if end < len(msg_split[pos])-1: #This catch's IGNs if they are attached to the IGN (eg:IGN:k8thekat)
                        possible_name = msg_split[pos][end:len(msg_split[pos])]
                        possible_name = re.sub(self.symbol_reg, "",possible_name)
                        name_found = True
                        self.logger.debug(f'possible name attached to IGN: {possible_name}')
                        name = possible_name
                        

                    flag_str_filter = re.search(self.str_filter_exact,msg_split[pos+1].lower()) #Need to make it so that str has to be "alone" not inside of a name/server etc..
                    if flag_str_filter != None and len(msg_split) > pos+2:
                        possible_name = msg_split[pos+2][0:len(msg_split[pos+2])]
                        possible_name = re.sub(self.symbol_reg,"",possible_name)
                        self.logger.debug(f'possible name after str filter: {possible_name}') 
                        name = possible_name

                    else:
                        if name_found:
                            possible_server = msg_split[pos+1][0:len(msg_split[pos+1])]
                            possible_server = re.sub(self.symbol_reg,"",msg_split[pos+1])
                            self.logger.debug(f'possible server after name found: {possible_server}')
                            servers.append(possible_server)

                        else:
                            possible_name = msg_split[pos+1][0:len(msg_split[pos+1])]
                            possible_name = re.sub(self.symbol_reg,"",msg_split[pos+1])
                            self.logger.debug(f'possible name: {possible_name}') 
                            name = possible_name

                if len(msg_split) > pos+2:
                    flag_search = re.search(f"{self.server_reg}|{self.ign_reg}",msg_split[pos+2].lower())
                    if flag_search == None and len(msg_split[pos+2]) > 1:

                        #This makes sure the next entry ISNT the same as the IGN
                        if possible_name != msg_split[pos+2]: 
                            possible_server_afterIGN = msg_split[pos+2][0:len(msg_split[pos+2])]
                            possible_server_afterIGN = re.sub(self.symbol_reg,"",possible_server_afterIGN)
                            self.logger.debug(f'possible server after IGN: {possible_server_afterIGN}')
                            servers.append(possible_server_afterIGN)


            if flag_whitelist != None:
                if len(msg_split) > pos+1:

                    #Check next entry if its apart of the str_filter if not then use it; else go one entry further.
                    flag_str_filter = re.search(self.str_filter_exact,msg_split[pos+1])
                    if flag_str_filter != None and len(msg_split) > pos+2:
                        possible_server_afterwhitelist = msg_split[pos+2][0:len(msg_split[pos+2])]
                        possible_server_afterwhitelist = re.sub(self.symbol_reg,"",possible_server_afterwhitelist)

                        flag_str_filter = re.search(self.str_filter_exact,msg_split[pos+2])
                        if flag_str_filter == None:
                            self.logger.debug(f'possible server after whitelist: {possible_server_afterwhitelist}')
                            servers.append(possible_server_afterwhitelist)

        #This handles really short whitelist requests. Usually without IGN or Server in the message.
        if len(msg_split) < 4:
            flag_server = re.search(self.server_reg, messages.lower())
            flag_ign = re.search(self.ign_reg, messages.lower())
            flag_whitelist = re.search(self.whitelist_reg, messages.lower())
            if flag_ign== None and flag_server== None and flag_whitelist== None:

                msg_split = messages.split(' ')
    
                self.logger.debug(f'short whitelist request: {msg_split}')

                #These CAN and WILL MOST LIKELY FAIL. Very unreliable ways to handling whitelist requests without formatting.
                self.logger.debug(f'short possible name: {msg_split[0]}') 
                self.logger.debug(f'short possible server: {msg_split[1]}') 
                name = msg_split[0]
                servers.append(msg_split[1])
    
        return name,servers

