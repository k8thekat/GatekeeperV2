from typing import Union
import json
import re
from re import Match
import logging
import requests
from requests import Response


def name_to_uuid_MC(name: str) -> Union[None, str]:
    """Converts an IGN to a UUID/Name Table \n
    `returns 'uuid'` else returns `None`, multiple results return `None`"""
    url = 'https://api.mojang.com/profiles/minecraft'
    header = {'Content-Type': 'application/json'}
    jsonhandler = json.dumps(name)
    post_req = requests.post(url, headers=header, data=jsonhandler)
    minecraft_user = post_req.json()

    if len(minecraft_user) == 0:
        return None

    if len(minecraft_user) > 1:
        return None

    else:
        return minecraft_user[0]['id']  # returns [{'id': 'uuid', 'name': 'name'}]


def name_to_steam_id(steamname: str) -> Union[None, str]:
    """Converts a Steam Name to a Steam ID returns `STEAM_0:0:2806383`
    """
    # Really basic HTML text scan to find the Title; which has the steam ID in it. Thank you STEAMIDFINDER! <3
    # <title> Steam ID STEAM_0:0:2806383 via Steam ID Finder</title>
    # FIXME -- This still needs to be tested and properly setup using re
    _logger = logging.getLogger("")
    r: Response = requests.get(f'https://www.steamidfinder.com/lookup/{steamname}')
    _logger.dev('Status Code', r.status_code)  # type:ignore
    if r.status_code == 404:
        return None
    title_start: int = 0
    title_end: int = 0
    title: Match[str] | None = re.search('(<title>)', r.text)
    if isinstance(title, Match):
        start, title_start = title.span()

    title = re.search('(</title>)', r.text)
    if isinstance(title, Match):
        title_end, end = title.span()
    # turns into  " STEAM_0:0:2806383 "
    # This should work regardless of the Steam ID length; since we came from the end of the second title backwards.
    if title_start and title_end:
        steam_id: str = r.text[title_start + 9:title_end - 20].strip()
        _logger.dev(f'Found Steam ID {steam_id}')  # type:ignore
        return steam_id
    else:
        return None
