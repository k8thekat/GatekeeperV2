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
import requests
import re
import logging

# Really basic HTML text scan to find the Title; which has the steam ID in it. Thank you STEAMIDFINDER! <3
# <title> Steam ID STEAM_0:0:2806383 via Steam ID Finder</title>

#steamname = 'k8thekat'


def steam_id(steamname):
    logger = logging.getLogger()
    r = requests.get(f'https://www.steamidfinder.com/lookup/{steamname}')
    logger.dev('Status Code', r.status_code)
    if r.status_code == 404:
        return None

    title = re.search('(<title>)', r.text)
    start, title_start = title.span()
    title = re.search('(</title>)', r.text)
    title_end, end = title.span()
    # turns into  " STEAM_0:0:2806383 "
    # This should work regardless of the Steam ID length; since we came from the end of the second title backwards.
    steam_id = r.text[title_start+9:title_end-20].strip()
    logger.dev(f'Found Steam ID {steam_id}')
    return steam_id
