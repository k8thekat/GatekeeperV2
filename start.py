import discordBot
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

Start = Setup()
#discordBot.client_run()
