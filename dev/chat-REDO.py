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
#Gatekeeper - Minecraft Chat
from AMP_API import AMPAPI
import asyncio
import database
import UUIDhandler
import chatfilter
import time
import logging
import pprint

#database setup
db = database.Database()

#AMP API setup
AMP = AMPAPI()
AMPservers = AMP.getInstances() # creates objects for server console/chat updates

#Discord Hook
SERVERCHAT = {}

def init(client):
    while(client.is_ready() == False): #Lets wait to start this until the bot has fully setup.
        time.sleep(1)
    global SERVERCHAT, AMPservers
    #Lets generate our list of servers via Chat channels for easier lookup.
    for server in AMPservers:
        channel = db.GetServer(server).DiscordChatChannel #Needs to be an int() because of discord message.channel.id type is int()
        if channel != None:
            time.sleep(0.1)
            SERVERCHAT.update({int(channel): {'AMPserver' : AMPservers[server], 'status' : AMPservers[server].Running}})
    pprint.pprint(SERVERCHAT)

#@client.event()
#This handles scanning discord chat messages to send it to the correct minecraft server
def on_message(message,client):
    if SERVERCHAT[message.channel.id]['status']:
        message.content = message.content.replace('\n',' ')
        message.content = chatfilter.scan(message.content,client) #Removes characters that MC cannot display properly (emojis,ascii,etc)
        if message.content == True:
            return True
        else:
            SERVERCHAT[message.channel.id]['AMPserver'].ConsoleMessage(f'tellraw @a [{{"text":"(Discord)","color":"blue"}},{{"text":"<{message.author.name}>: {message.content}","color":"white"}}]')
            return True
    return False

#This fetches MC avatars heads and uses them for Discord Profile Pics and changes the message name to the IGN from minecraft
async def MCchatsend(channel, user, message):
    if user != None:
        print(user)
        MChead = 'https://mc-heads.net/head/' + str(user[1][0]['id'])
        webhook = await channel.create_webhook(name= user[1][0]['name'])
        await webhook.send(message, username= user[1][0]['name'], avatar_url= MChead)
    
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        try:
            await webhook.delete()
        except Exception as e:
            logging.error(e)
            print(e)

#Console messages are checked by 'Source' and by 'Type' to be sent to a designated discord channel.
def MCchattoDiscord(amp_server,async_loop,client,chat):
    user = None
    channel = db.GetServer(amp_server.InstanceID).DiscordChatChannel
    #print(channel,type(channel))
    # No point in sending a message if the channel is None.
    if channel == None:
        return
    disc_channel = client.get_channel(int(channel))

    chatmsg = []
    if chat['Source'].startswith('Async Chat Thread'):
        chatmsg.append(chat['Contents'])

    #This is an attempt to handle OP'd users when the 'Type' Changes from 'Chat' to 'Console'. Not sure why...
    #This may cause problems in the future if anything uses '<' or '>'
    #03/22/2022 04:37:26 PM [Thread-15 (serverconsole)] [INFO]  PO3 {'Timestamp': '/Date(1647992246393)/', 'Source': 'Server thread/INFO', 'Type': 'Console', 'Contents': '<[staff]: k8_thekat> Help'}
    if chat['Type'] == 'Console':
        indexleft = chat['Contents'].find('<')
        indexright = chat['Contents'].find('>')
        if (indexleft != -1) and (indexright != -1):
            indexcolon = chat['Contents'].find(':')
            if indexcolon != -1:
                chatmsg.append(chat['Contents'])
                user = UUIDhandler.uuidcheck(chat['Contents'][indexcolon+1:-1].strip())

            else:
                print('This console entry or message triggered OP user messages',chat['Contents'])

    elif chat['Type'] == 'Chat':
        user = UUIDhandler.uuidcheck(chat['Source'])
        chatmsg.append(chat['Contents'])
    else:
        return
    
    if len(chatmsg) > 0:
        bulkentry = ''
        for entry in chatmsg:
            if len(bulkentry+entry) < 1500:
                bulkentry = bulkentry + entry + '\n' 
            else:
                if chat['Type'] == 'Chat':
                    ret = asyncio.run_coroutine_threadsafe(MCchatsend(disc_channel, user, bulkentry[:-1]), async_loop)
                    ret.result()
                bulkentry = entry + '\n'
        if len(bulkentry):
            ret = asyncio.run_coroutine_threadsafe(MCchatsend(disc_channel, user, bulkentry[:-1]), async_loop)
            ret.result()
