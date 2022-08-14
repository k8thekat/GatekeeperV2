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
# Gatekeeper Bot - Chat filter
from datetime import datetime
import logging


def scan(content, client):
    content = unicode(content)
    while(1):
        userstatus = user(content, client)
        emojistatus = emoji(content)
        channelstatus = channel(content, client)
        if userstatus != False:
            content = userstatus
        elif emojistatus != False:
            content = emojistatus
        elif channelstatus != False:
            content = channelstatus
        else:
            if userstatus == False and emojistatus == False and channelstatus == False:
                content = content.strip()
                if len(content) == 0:
                    return True
                else:
                    return content

# Strips Unicode out of the message


def unicode(content):
    content = content.encode("ascii", "ignore")
    content = content.decode()
    return content

# Replaces @User calls in Discord with just the Name


def user(content, client):
    user_find_start = content.find('<@!')
    user_find_end = content.find('>', user_find_start)
    if user_find_start != -1 and user_find_end != -1:
        userid = content[user_find_start+3:user_find_end]
        user = client.get_user(id=int(userid))
        content = content[0:user_find_start] + user.name + content[user_find_end+1:]
        return content
    else:
        return False


def channel(content, client):
    channel_find_start = content.find('<#')
    channel_find_end = content.find('>', channel_find_start)
    if channel_find_start != -1 and channel_find_end != -1:
        channelid = content[channel_find_start+2:channel_find_end]
        channel = client.get_channel(id=int(channelid))
        content = content[0:channel_find_start] + channel.name + content[channel_find_end+1:]
        return content
    else:
        return False

# Attempts to find discord emoji's and remove them


def emoji(content):
    start_bracket = content.find('<:')
    end_bracket = content.find('>', start_bracket)
    if start_bracket != -1 and end_bracket != -1:
        msgpart = content[0:start_bracket]
        msgpart += content[end_bracket+1:]
        content = msgpart
        return content
    else:
        return False


# Attempts to flag Scam Spam bots/Compromised accounts or anyone being annoying...
MSGLOG = {}


def spamFilter(message):
    global MSGLOG
    storeflag = False
    # print(message.author.name,message.content,message.mention_everyone)
    flags = ['https://', '.gift', 'nitro']
    data = {'Count': 1, 'First Seen': datetime.now()}

    for flag in flags:
        if flag in message.content:
            print(f'Message contains a flagged word...{message.author.name}: {message.content}')
            storeflag = True

    if message.mention_everyone:  # If someone is repeatidly using @everyone; I want them to be caught and punished
        storeflag = True

    if storeflag:
        if message.author.name in MSGLOG:
            if message.content in MSGLOG[message.author.name]:
                if MSGLOG[message.author.name][message.content]['Count'] >= 3:  # Once a user has said the same 3 things; lets check the time between them.
                    # If the time between the first message and the curtime is less than or equal to 1 minute.
                    if ((datetime.now() - MSGLOG[message.author.name][message.content]['First Seen'])/60) <= 1:
                        return True
                    else:  # lets reset the info and wait again..
                        MSGLOG[message.author.name][message.content]['First Seen'] = datetime.now()  # Lets reset the time between their messages to now
                        MSGLOG[message.author.name][message.content]['Count'] = 1  # Lets reset the count too
                else:
                    MSGLOG[message.author.name][message.content]['Count'] += 1
            else:
                MSGLOG[message.author.name][message.content] = data
        else:
            MSGLOG[message.author.name] = {message.content: data}
    return False

# Checks the log file for entries older than 5 minutes and removed them.


def logCleaner():
    logging.info('Cleaning up the Chat Spam Log...')
    global MSGLOG
    authorkeys = list(MSGLOG.keys())
    for author in authorkeys:
        contentkeys = list(MSGLOG[author].keys())
        for content in contentkeys:
            if datetime.now() - MSGLOG[author][content]['First Seen'] > 5:
                MSGLOG[author].pop(content)
        if len(MSGLOG[author].keys()) == 0:
            MSGLOG.pop(author)
    return
