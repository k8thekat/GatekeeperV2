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

test = [ 'Can i get re-whitelisted for TNP 5?  ign: rahz_vael',
    'server: Tnp5 Name: Speamy3',
    'Not sure if I need to resubmit a request or not  IGN: Codemeister101 TNP5',
    'Can I be whitelisted for E6 please ign aimhreidh1 ',
    'an i get a whitelist on E6 Normal    ing Solclaim',
    'server(s): TNP5, E6 ign: Clinomanic_Sloth',
    'IGN: Warteks; Server: DW20',
    'IGN: Kalvsund Server; Dw20',
    'I assume were allowed to be whitelisted in multiple servers, so may i ask to be whitelisted in tnp5?',
    'Can i please get whitelisted to e6',
    'IGN: Rat_And_the_Gat Server: e6',
    'Ign spontaneo server SB2',
    'Can I be whitelisted for sky bees please IGN is aimhreidh1 thanks.',
    'SoulessJoke SB2',
    'MarceloFelix enigmatic 6',
    'IGN Cyantrent Server SkyBee 2',
    'TheGamingPigeon Sky Bees 2',
    'Hello, ign:k8thekat E6']


import re

class Parser():
    def __init__(self):
        #We can swap these out to allow people to set them via the DB for more in-depth filtering
        self.symbol_reg = "[,./':;&\.\-\?]"
        self.server_reg = "(server)"
        self.ign_reg = "(ign|ingamename|in-game-name|in-gamename)" 
        self.str_filter = "\b(for|the|and|on|in|to|and|is|server|ign)"

    def ParseIGNServer(self,messages):
        for msg in messages:
            msg_split = msg.split(' ')
            print(msg_split)
            pos = -1
            for entry in msg_split:
                #print('msg entry',entry)
                pos += 1
                flag_server = re.search(self.server_reg, entry.lower())
                if flag_server != None:
                    #print('pos',pos)
                    #print('len of msg_split',len(msg_split),'msg_split pos',pos+1)
                    if len(msg_split) > pos+1:
                        possible_server = msg_split[pos+1][0:len(msg_split[pos+1])]
                        possible_server = re.sub(self.symbol_reg,"",possible_server)
                        print('possible server:',possible_server) #We will attempt to look up the server here.
                    

                    if len(msg_split) > pos+3:
                        #print(msg_split[pos+2])
                        #print(entry)
                        flag_symbols = re.search(self.symbol_reg, msg_split[pos+2])
                        if flag_symbols == None:
                            next_possible_server = msg_split[pos+2][0:len(msg_split[pos+2])]
                            print('next_possible_server:',next_possible_server) #We will attempt to look this server up too!

                flag_ign = re.search("(ign|ingamename|in-game-name|in-gamename)|in.game.name|(name.)",entry.lower())
                if flag_ign != None:
                    #print(entry)
                    #Need to find ign and see if the name is attached to the same entry.
                    if len(msg_split) > pos+1:
                        possible_name = msg_split[pos+1][0:len(msg_split[pos+1])]
                        possible_name = re.sub(self.symbol_reg,"",possible_name)
                        flag_str_filter = re.search(self.str_filter,possible_name) #Need to make it so that str has to be "alone" not inside of a name/server etc..
                        if flag_str_filter != None and len(msg_split) > pos+2:
                            possible_name = msg_split[pos+2][0:len(msg_split[pos+2])]
                            print('possible name with str filter:',possible_name) #We look this up in the DB if not there, we add it. Add all there Discord details too!
                        else:
                            print('possible name:',possible_name) #We look this up in the DB if not there, we add it. Add all there Discord details too!

                    if len(msg_split) > pos+2:
                        flag_search = re.search(f"{self.server_reg}|{self.ign_reg}",msg_split[pos+2].lower())
                        if flag_search == None and len(msg_split[pos+2]) > 1:
                            #print(msg_split[pos+2][0:len(msg_split[pos+2])])
                            possible_server_afterIGN = msg_split[pos+2][0:len(msg_split[pos+2])]
                            
                            possible_server_afterIGN = re.sub(self.symbol_reg,"",possible_server_afterIGN)
                            print('possible server after IGN:',possible_server_afterIGN) #We look this up in the DB if not there, we add it. Add all there Discord details too!


                flag_whitelist = re.search("(whitelist)",entry.lower())
                if flag_whitelist != None:
                    if len(msg_split) > pos+1:
                        #Check next entry if its apart of the str_filter if not then use it; else go one entry further.
                        flag_str_filter = re.search(self.str_filter,msg_split[pos+1])
                        if flag_str_filter != None and len(msg_split) > pos+2:
                            possible_server_afterwhitelist = msg_split[pos+2][0:len(msg_split[pos+2])]
                            possible_server_afterwhitelist = re.sub(self.symbol_reg,"",possible_server_afterwhitelist)
                            print('possible server after whitelist:',possible_server_afterwhitelist)

a = Parser()
a.ParseIGNServer(test)

