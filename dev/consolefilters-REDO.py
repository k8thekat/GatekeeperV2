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
# Gatekeeper Bot - consolefilters
import config
import logging


def filters(entry):
    if type(entry) == dict:
        if config.CommandBlocks:
            if entry['Contents'].startswith('CommandBlock at'):
                return True

        if config.WorldEdit:
            if entry['Contents'].find('issued server command: //') != -1:
                return True
        if config.Modpack:
            if entry['Contents'].lower().startswith('OpenComputers-Computer-1'):
                return True
            if entry['Source'].lower() != 'server thread/info':
                return True
        if config.Default:
            filter_source_table = {'installer', 'server thread/warn', 'server thread/error', 'server thread/fatal', 'main/error', 'main/info', 'main/warn'}
            if entry['Contents'].startswith('Current Memory Usage:') and entry['Contents'].endswith('mb)'):
                return True
            if entry['Source'].lower() in filter_source_table:
                return True
            if entry['Type'].lower() == 'action':  # Filters enchantment Actions afaik
                return True
            if entry['Source'].lower().startswith('netty server io'):
                return True
        if config.DiscordBot:
            # This may be specific to a MC chat bot; but it causes errors.
            if entry['Source'].lower().startswith('ml'):
                return True
            if entry['Source'].lower().startswith('d4j'):
                return True
        if config.Debugging:
            # if entry['Source'].lower() == 'server thread/info':
            # return True
            # TODO - Needs to be Adressed; find out console filter solutions for mod loading.
            filtertable = ['\tat', 'java.lang', 'java.io', 'com.google']
            for filter in filtertable:
                if entry['Contents'].lower().startswith(filter):
                    return True
        return entry
    else:
        return entry

# Removed the odd character for color idicators on text


def colorstrip(entry):
    char = '�'
    if entry['Contents'].find(char) != -1:
        logging.info('Color strip triggered...')
        index = 0
        while 1:
            index = entry['Contents'].find(char, index)
            if index == -1:
                break
            newchar = entry['Contents'][index:index+2]
            entry['Contents'] = entry['Contents'].replace(newchar, '')
        return entry
    return entry
