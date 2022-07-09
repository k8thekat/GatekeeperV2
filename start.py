import DB
import AMP
import logger as bot_logger
import time



class Setup:
    def __init__(self):
        bot_logger.init()
        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB
        self.DB_Config = self.DB.GetConfig()

        self.AMPHandler = AMP.getAMPHandler()
        self.AMPHandler.setup_AMPInstances() 
        #print("Setup init:", self.AMPHandler.AMP_Instances)
        self.AMP = self.AMPHandler.AMP
        
        #self.pip_install()

    def pip_install(self):
        import sys
        import subprocess
        # implement pip as a subprocess:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install' '-r','requirements.txt'])

Start = Setup()
#import discordBot
#discordBot.client_run()
