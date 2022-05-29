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
#Gatekeeper Bot - Console Scanning
import config
import plugin_commands
from datetime import datetime, timedelta
import traceback
import database
import logging
import logger
import whitelist
import rank

#Database
db = database.Database()

#Handles each entry of the console to update DB or filter messages/etc.
def scan(amp_server,entry):
    curtime = datetime.now()
    curserver = db.GetServer(amp_server.InstanceID)
    #
    rank.timeUpdate(entry)
    #Finding in game issued server commands
    if entry['Contents'].find('issued server command:') != -1:
        logger.commandLog(None,curserver,entry,'console')
        entry_split = entry['Contents'].split(' ')
        command_user = entry_split[0]
        command = entry_split[4]
        #Catchs manual ban and pardon commands, updates db
        if command == '/ban' or command == '/pardon':
            target_user = entry_split[-1]
            curserveruser = curserver.GetUser(target_user)
            if curserveruser != None:
                if command == '/ban':
                    curserveruser.SuspensionExpiration = curtime + timedelta(days=9999)
                    curserveruser.Whitelisted = False
                else:
                    curserveruser.SuspensionExpiration = None
        #catchs manual whitelist command, updates db   
        if command == '/whitelist':
            target_user = entry_split[-1]
            curserveruser = curserver.GetUser(target_user)
            if len(entry_split) == 5:
                command_func = entry_split[5]
            if curserveruser != None:
                if command_func == 'remove':
                    curserveruser.Whitelisted = False
                else:
                    curserveruser.Whitelisted = True
        #below here will be a script to handle common plugin commands (eg. /tempban) See config.py and plugin_commands.py
        if config.Plugins:
            if config.Essentials:
                time_out,IGN = plugin_commands.Essentials(entry)
                curserveruser = curserver.GetUser(IGN)
                curserveruser.SuspensionExpiration = curtime + time_out
    #Player�c Console �6banned�c k8_thekat �6for: �c�cYou have been banned:
    if entry['Contents'].startswith('Player Console banned') and entry['Contents'].endswith('You have been banned:'):
        logging.info('User has been banned via console...')
        logger.commandLog(None,curserver,entry,'console')
        entry_split = entry['Contents'].split(' ')
        try:
            curserver.GetUser(entry_split[3]).SuspensionExpiration = curtime + timedelta(days=9999)
            curserver.GetUser(entry_split[3]).Whitelisted = False
        except Exception as e:
            logging.exception(e)
            logging.error(traceback.print_exc())
            return True, f'**Unable to update User**: {entry_split[3]} banned status in the database!'
    #�6Player�c Console �6unbanned�c k8_thekat
    if entry['Contents'].startswith('Player Console unbanned'):
        logging.info('User has been unbanned via console...')
        logger.commandLog(None,curserver,entry,'console')
        entry_split = entry['Contents'].split(' ')
        try:
            curserver.GetUser(entry_split[3]).SuspensionExpiration = None
            #curserver.GetUser(entry_split[3]).Whitelisted = True
            #AMPservers[curserver.InstanceID].ConsoleMessage(f'whitelist add {entry_split[3]}')
        except Exception as e:
            logging.exception(e)
            logging.error(traceback.print_exc())
            return True, f'**Unable to update User**: {entry_split[3]} banned status in the database!'

    #Added k8_thekat to the whitelist
    if entry['Contents'].startswith('Added') and entry['Contents'].endswith('to the whitelist'):
        logging.info('User added to Whitelist via console..')
        logger.commandLog(None,curserver,entry,'console')
        entry_split = entry['Contents'].split(' ')
        db_user = db.GetUser(entry_split[1])
        found = False
        #{'User': user, 'IGN': user.IngameName, 'timestamp' : curtime, 'server' : curserver, 'Context': message})

        for index in range(0,len(whitelist.WhitelistWaitList)):
            user = whitelist.WhitelistWaitList[index]
            
            #Lets first try to compare via db_user; this can fail if they are not in the database.. somehow..
            if db_user != None:
                print('Whitelist db_user lookup',db_user,user)
                if db_user == user['User']:
                    found = True
                    curserver.GetUser(db_user).Whitelisted = True
                    whitelist.WhitelistWaitList.remove(user)
                    return True,f'**Removed User*: {db_user.IngameName} from Whitelist wait list and updated their Whitelisted Status to `True` on {curserver.FriendlyName}.'  

            #Lets now try via the whitelisted ign and see if we can find a match.
            print('Whitelist IGN Lookup',entry_split[1],user['IGN'])
            if entry_split[1] == user['IGN']:
                found = True
                whitelist.WhitelistWaitList.remove(user)
                return True,f'**Removed User**: {entry_split[1]} from Whitelist wait list, unable to update Whitelisted status in the Database!'  

        if found == False:
            return True, f'**Unable to update User**: {entry_split[1]} whitelisted status in the database!'
        
    #Removed k8_thekat from the whitelist
    if entry['Contents'].startswith('Removed') and entry['Contents'].endswith('from the whitelist'):
        logging.info('User removed from Whitelist via console..')
        logger.commandLog(None,curserver,entry,'console')
        entry_split = entry['Contents'].split(' ')
        try:
            curserver.GetUser(entry_split[1]).Whitelisted = False
        except Exception as e:
            logging.exception(e)
            logging.error(traceback.print_exc())
            return True, f'**Unable to update User**: {entry_split[1]} whitelisted status in the database!'
    #User Lastlogin Stuff
    if entry['Source'].startswith('User Authenticator'):
            #if entry['Source'].startswith('Server thread/INFO') and entry[''].startswith()
        curtime = datetime.now()
        psplit = entry['Contents'].split(' ')
        user = db.GetUser(psplit[3])
        if user != None:
            logging.info(f'**Updating {user.IngameName} Last Login to {curtime}...**')
            serveruser = curserver.GetUser(user)
            if serveruser == None:
                curserver.AddUser(user)
                serveruser = curserver.GetUser(user)
                serveruser.LastLogin = curtime
                return True, f'**Adding user to Server**: {curserver.FriendlyName} User: {user.DiscordName} IGN: {user.IngameName}'
            else:
                serveruser = curserver.GetUser(user)
                serveruser.LastLogin = curtime
                return True, f'**Updating User Last Login on Server**: {curserver.FriendlyName} User: {user.DiscordName} IGN: {user.IngameName}'
        else:
            return True, f'**Failed to set Last Login for Server**: {curserver.FriendlyName} User: {psplit[3]}. Please add the user to the database and set the users IGN via //user DiscordID ign {psplit[3]}'
    
    #User Played Time
    # if entry['Source'].lower() == 'server thread/info' and entry['Contents'].find('left the game') !=-1:
    #     logout_time = datetime.fromtimestamp(float(entry['Timestamp'][6:-2])/1000)
    #     entry = entry['Contents'].split(' ') #Prep to help me get the user out of the 'Contents'
    #     db_user = db.GetUser(entry[0])
    #     if db_user == None:
    #         return True, f'**Failed to Update Time Played**: User: {entry[0]}; Please add the user to the database and set the users IGN via //user DiscordID ign {entry[0]}.'
    
    #     logging.info(f'**Updating {db_user.IngameName} played time on {curserver.FriendlyName}**')
    #     lastlogin = curserver.GetUser(db_user).LastLogin #Gets the datetime object of the ServerUser last login
    #     print('Last Login',lastlogin)
    #     if lastlogin == None:
    #         lastlogin = logout_time
    #     total_timeplayed = curserver.GetUser(db_user).TimePlayed #Gets the time played of the ServerUser - Should be in minutes
    #     print('Total',total_timeplayed)
    #     if total_timeplayed == None:
    #         total_timeplayed = 0
    #     time_played = (logout_time - lastlogin) #The datetime of how long they played.
    #     print('Time played',time_played)
    #     total_timeplayed += (time_played.seconds/60) #Add's the play time to their current accured amount of play time..
    #     return True, f'**Updated User**: {entry[0]} played time increased by {time_played} Minutes. Total: {total_timeplayed} Minutes.'
    return False, entry