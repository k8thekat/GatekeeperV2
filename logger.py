import datetime
import platform
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

import bot_config

CURTIME = datetime.datetime.now()
DATE = CURTIME.strftime('%Y-%m-%d-')
OSPLAT = platform.system()
BOTDIR = os.getcwd()
DIR = '\\logs\\'


def init():
    global DIR
    if OSPLAT.lower() == 'linux': #Flip the slash to accomadate Linux users <3
        DIR.replace('\\','//')
    
    dircheck = os.path.isdir(BOTDIR + DIR)
    if dircheck != True:
        print('Making Log Directory...')
        os.makedirs(BOTDIR + DIR)
        
    log_file_name = BOTDIR + DIR + 'log'
    logging.basicConfig(level=bot_config.logginglevel, format='%(asctime)s [%(threadName)s] [%(levelname)s]  %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers = [logging.StreamHandler(sys.stdout),
                        TimedRotatingFileHandler(log_file_name,'midnight',atTime=datetime.datetime.min.time(),backupCount= 4,encoding='utf-8',utc=True)])
    return
