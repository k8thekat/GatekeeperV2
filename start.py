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
import pathlib

class Setup:
    def __init__(self):
        #Use action="store_true", then check the arg via "args.name" eg. "args.dev"
        parser = argparse.ArgumentParser(description='AMP Discord Bot')
        parser.add_argument('-token', help='Bypasse tokens validation check.',required= False, action="store_true")
        parser.add_argument('-super', help='This leaves AMP Super Admin role intact, use at your own risk.', required= False, action="store_true")

        # All the args below are used for development purpose.
        parser.add_argument('-dev', help='Enable development print statments.',required= False, action="store_true")
        parser.add_argument('-command', help='Enable command usage print statements.', required= False, action="store_true")
        parser.add_argument('-discord', help='Disables Discord Intigration (used for testing)',required= False, action="store_false")
        parser.add_argument('-debug', help='Enables DEBUGGING level for logging', required= False, action="store_true")
        self.args = parser.parse_args()

        self.pip_install()

        #Renaming Main Thread to "Gatekeeper"
        Gatekeeper = current_thread()
        Gatekeeper.name = 'Gatekeeper'

        #Custom Logger functionality.
        import logging 
        import logger
        logger.init(self.args)
        self.logger = logging.getLogger()

        self.logger.dev(f'Current Startup Args:{self.args}')

        self.logger.dev("**ATTENTION** YOU ARE IN DEVELOPMENT MODE** All features are not present and stability is not guaranteed!")

        if not self.args.discord:
            self.logger.critical("***ATTENTION*** Discord Intergration has been DISABLED!")

        #This sets up our SQLite Database!
        import DB
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DB_Config = self.DB.DBConfig
        self.logger.info(f'SQL Database Version: {self.DB.DBHandler.DB_Version} // SQL Database: {self.DB.DBHandler.SuccessfulDatabase}')

        #This connects and creates all our AMP related parts
        import AMP
        self.AMP_Thread = threading.Thread(target= AMP.AMP_init, name= 'AMP', args= [self.args,])
        self.AMP_Thread.start()

        if self.args.discord:
            while(AMP.AMP_setup == False):
                time.sleep(.5)

            if self.args.dev and pathlib.Path('tokens_dev.py').exists():
                import tokens_dev as tokens

            else:
                import tokens
                
            import discordBot
            discordBot.client_run(tokens)
      
    def python_ver_check(self):
        if not sys.version_info.major >= 3 and not sys.version_info.minor >= 10:
            self.logger.critical(f'Unable to Start Gatekeeper, Python Version is {sys.version_info.major + "." + sys.version_info.minor} we require Python Version >= 3.10')
            sys.exit(1)

    def pip_install(self):
        pip_version = pip.__version__.split('.')
        pip_v_major = int(pip_version[0])
        pip_v_minor = int(pip_version[1])

        if pip_v_major > 22 or (pip_v_major == 22 and pip_v_minor >= 1):
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r','requirements.txt'])
        else:
            self.logger.critical(f'Unable to Start Gatekeeper, PIP Version is {pip.__version__}, we require PIP Version >= 22.1')

Start = Setup()

    
