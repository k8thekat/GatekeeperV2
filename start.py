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
import re
import argparse


class Setup:
    def __init__(self):
        # Use action="store_true", then check the arg via "args.name" eg. "args.dev"
        parser = argparse.ArgumentParser(description='AMP Discord Bot')
        parser.add_argument('-token', help='Bypasse tokens validation check.', required=False, action="store_true")
        parser.add_argument('-super', help='This leaves AMP Super Admin role intact, use at your own risk.', required=False, action="store_true")
        #parser.add_argument('guildID', help='Set to your Discord Server ID for local Sync', nargs='?', default=None)

        # All the args below are used for development purpose.
        parser.add_argument('-dev', help='Enable development print statments.', required=False, action="store_true")
        parser.add_argument('-command', help='Enable command usage print statements.', required=False, action="store_true")
        parser.add_argument('-discord', help='Disables Discord Intigration (used for testing)', required=False, action="store_false")
        parser.add_argument('-debug', help='Enables DEBUGGING level for logging', required=False, action="store_true")
        #parser.add_argument('-setup', help='***NOT IN USE*** First time setup of AMP and DB', required= False, action="store_false")
        self.args = parser.parse_args()
        import logging
        self.logger = logging.getLogger()

        self.pip_install()

        # Custom Logger functionality.
        import logger
        logger.init(self.args)
        self.logger = logging.getLogger()

        self.logger.dev(f'Current Startup Args:{self.args}')

        self.logger.dev("**ATTENTION** YOU ARE IN DEVELOPMENT MODE** All features are not present and stability is not guaranteed!")

        if not self.args.discord:
            self.logger.critical("***ATTENTION*** Discord Intergration has been DISABLED!")

        # This sets up our SQLite Database!
        import DB
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DB_Config = self.DB.GetConfig()

        # This connects and creates all our AMP related parts
        import AMP
        self.AMPHandler = AMP.getAMPHandler(args=self.args)
        self.AMPHandler.setup_AMPInstances()
        self.AMP = self.AMPHandler.AMP

    def pip_install(self):
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        try:
            import discord
            ver = discord.__version__
            flag = re.search("(2.0)", ver.lower())
            if flag is None:
                self.logger.error('Please visit: https://github.com/Rapptz/discord.py to install discord.py development version!')
                sys.exit(1)

        except Exception:
            self.logger.error('Please visit: https://github.com/Rapptz/discord.py to install discord.py development version!')
            sys.exit(1)


Start = Setup()

# This has to be called outside of the init; its blocking and will cause issues inside of the Setup.init()
if Start.args.discord:
    import discordBot
    discordBot.client_run()
