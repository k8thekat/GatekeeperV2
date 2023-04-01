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
import datetime
import sys
import logging
from haggis import logs
from logging.handlers import TimedRotatingFileHandler
import pathlib


def init(args) -> None:
    logginglevel = logging.INFO

    # To Enable debug logging level (ewwwwww.....)
    if args.debug:
        logginglevel = logging.DEBUG

    dircheck = pathlib.Path.exists(pathlib.Path.cwd().joinpath('logs'))
    if dircheck != True:
        print('Making Log Directory...')
        pathlib.Path.mkdir(pathlib.Path.cwd().joinpath('logs'))

    # This level is for development purpose; a little more information in key spots without the debug annoyance.
    dev_level = 15
    dev_label = 'DEV'
    logs.add_logging_level(dev_label, dev_level)
    if args.dev:
        logginglevel = logging.DEV  # type:ignore

    # # This is for displaying slash commands information for tracing info!
    # command_level = 19
    # command_label = 'COMMAND'

    # logs.add_logging_level(command_label, command_level)
    # if args.command:
    #     logginglevel = logging.COMMAND  # type:ignore

    logging.basicConfig(level=logginglevel, format='%(asctime)s [%(threadName)s] [%(levelname)s]  %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.StreamHandler(sys.stdout),
                                  TimedRotatingFileHandler(pathlib.Path.as_posix(pathlib.Path.cwd().joinpath('logs')) + '/log', 'midnight', atTime=datetime.datetime.min.time(), backupCount=4, encoding='utf-8', utc=True)])
