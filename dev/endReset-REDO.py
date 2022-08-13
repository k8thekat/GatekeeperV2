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
# Gatekeeper - The Level.dat End Reset Script
import nbtlib
import bot_config
import io
import base64
import gzip
import platform
import logging

FILENAME = ''
OSPLAT = ''


def init(AMPservers, curserver):
    global FILENAME, OSPLAT
    OSPLAT = platform.system()
    if OSPLAT.lower() == 'windows':
        FILENAME = f'world\level.dat'
    if OSPLAT.lower() == 'linux':  # Flip the slash to accomadate Linux users <3
        FILENAME = f'world/level.dat'
    leveldat = AMPservers[curserver].getFileChunk(FILENAME, 0, 33554432)
    newlevel = dragonReset(base64.b64decode(leveldat['result']['Base64Data']))
    newdata = base64.b64encode(newlevel).decode('utf-8')
    AMPservers[curserver].writeFileChunk(FILENAME, 0, newdata)
    worldremove(AMPservers, curserver)
    return True


def dragonReset(leveldat):
    logging.info('Attempting to reset the Dragon Fight in level.dat...')
    fakefile = io.BytesIO()
    fakefile.write(leveldat)
    fakefile.seek(0)
    if leveldat[0:2] == b"\x1f\x8b":
        fakefile = gzip.GzipFile(fileobj=fakefile)
    nbtdata = nbtlib.File.from_fileobj(fakefile, "big")
    dragon_path = nbtdata['']['Data']['DragonFight']
    del_list = []
    for entry in dragon_path:
        del_list.append(entry)
    for entry in del_list:
        logging.warning(f'Removing {entry}')
        del dragon_path[entry]
    fakefile = io.BytesIO()
    nbtdata.write(fakefile)
    fakefile.seek(0)
    newdata = fakefile.read()
    return newdata


def worldremove(AMPservers, curserver):
    logging.info('Removing the End World file...')
    global OSPLAT
    if bot_config.Multiverse_Core:
        worlddir = AMPservers[curserver].TrashDirectory('world_the_end')
        # print(worlddir)
    else:
        if OSPLAT.lower() == 'windows':
            trashdir = f'world\DIM1'
        if OSPLAT.lower() == 'linux':  # Flip the slash to accomadate Linux users <3
            trashdir = f'world/DIM1'
        worlddir = AMPservers[curserver].TrashDirectory(trashdir)
        # print(worlddir)
    return
