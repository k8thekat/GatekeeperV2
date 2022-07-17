#<title> Steam ID STEAM_0:0:2806383 via Steam ID Finder</title>
import requests
import re
import logging

#Really basic HTML text scan to find the Title; which has the steam ID in it. Thank you STEAMIDFINDER! <3

#steamname = 'k8thekat'
def steam_id(steamname):
    logger = logging.getLogger()
    r = requests.get(f'https://www.steamidfinder.com/lookup/{steamname}')
    logger.deubg('Status Code',r.status_code)
    if r.status_code == 404:
        return None

    title = re.search('(<title>)',r.text)
    start,title_start = title.span()
    title = re.search('(</title>)',r.text)
    title_end,end = title.span()
    #turns into  " STEAM_0:0:2806383 "
    #This should work regardless of the Steam ID length; since we came from the end of the second title backwards.
    steam_id = r.text[title_start+9:title_end-20].strip() 
    logger.debug(f'Found Steam ID {steam_id}')
    return steam_id

