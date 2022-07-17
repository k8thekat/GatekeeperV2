import sys
import subprocess
import re

class Setup:
    def __init__(self):
        import logger
        logger.init()
        import logging 
        self.logger = logging.getLogger()

        self.args = sys.argv
        #print(self.args)
        self.pip_install()

        import DB
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DB_Config = self.DB.GetConfig()

        import AMP
        self.AMPHandler = AMP.getAMPHandler(args=self.args)
        self.AMPHandler.setup_AMPInstances() 
        #print("Setup init:", self.AMPHandler.AMP_Instances)
        self.AMP = self.AMPHandler.AMP


    def pip_install(self):
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r','requirements.txt'])
        try:
            import discord
            ver = discord.__version__
            flag = re.search("(2.0)",ver.lower())
            if flag == None:
                self.logger.error('Please visit: https://github.com/Rapptz/discord.py to install discord.py development version!')
                sys.exit(1)

        except:
            
            self.logger.error('Please visit: https://github.com/Rapptz/discord.py to install discord.py development version!')
            sys.exit(1)

Start = Setup()

# for instance in Start.AMPHandler.AMP_Instances:
#     #if Start.AMPHandler.AMP_Instances[instance].Running:
#     Start.AMPHandler.AMP_Instances[instance].getAPItest()
import discordBot 
discordBot.client_run()