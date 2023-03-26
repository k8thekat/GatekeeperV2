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
import sys
import subprocess
import argparse
import pip
import threading
from threading import current_thread
import time
import logging

import logger
from amp_handler import AMPHandler
from db import DBHandler

import Gatekeeper
from dotenv.main import load_dotenv
import os


class Setup:
    load_dotenv()
    TOKEN: str = os.environ["TOKEN"].strip()

    def __init__(self):
        # Use action="store_true", then check the arg via "args.name" eg. "args.dev"
        # By default argparase has -h/--h.
        parser = argparse.ArgumentParser(description='Gatekeeper - AMP Discord Bot')
        parser.add_argument("-super", help='This leaves AMP Super Admin role intact *Warning* Potential security risk', required=False, action="store_true")
        # All the args below are used for development purpose.
        parser.add_argument("-dev", help='Enable development logger statments.', required=False, action="store_true")
        parser.add_argument("-debug", help='Enables DEBUGGING level for logging', required=False, action="store_true")
        parser.add_argument("arg1", action="store_true")
        self.args = parser.parse_args()

        self._pip_setup()
        self._python_ver_check()

        # Renaming Main Thread to "Gatekeeper"
        bot_thread = current_thread()
        bot_thread.name = "Gatekeeper"

        # Setup Logger functionality.
        logger.init(self.args)
        self._logger = logging.getLogger()
        self._logger.info(f'Current Startup Args:{self.args}')  # type:ignore

        # This sets up our SQLite Database!
        self._DBHandler = DBHandler()
        self._DB = self._DBHandler.DB
        self._DB_Config = self._DB.DBConfig
        self._logger.info(f'SQL Database Version: {self._DBHandler.DB_Version} // SQL Database: {self._DBHandler.SuccessfulDatabase}')

        self.AMP_Thread = threading.Thread(target=AMPHandler, name='AMPHandler', args=[self.args, ])
        self.AMP_Thread.start()
        while (AMPHandler.AMP_SETUP == False):
            time.sleep(.5)

        Gatekeeper.client_run(self.TOKEN)

    def _python_ver_check(self):
        if not sys.version_info.major >= 3 and not sys.version_info.minor >= 8:
            self._logger.critical(f'Unable to Start Gatekeeper, Python Version is {str(sys.version_info.major) + "." + str(sys.version_info.minor)} we require Python Version >= 3.8')
            sys.exit(1)

    def _pip_setup(self):
        """Validated the version of PIP installed due to certain versions of packages requiring certain versions of PIP. Then installs the required packages."""
        pip_version: list[str] = pip.__version__.split('.')
        pip_v_major: int = int(pip_version[0])
        pip_v_minor: int = int(pip_version[1])

        if pip_v_major > 22 or (pip_v_major == 22 and pip_v_minor >= 1):
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        else:
            self._logger.critical(f'Unable to Start Gatekeeper, PIP Version is {pip.__version__}, we require PIP Version >= 22.1')


Start = Setup()
