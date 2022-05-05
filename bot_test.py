#from main import discordBot,botutils
#import main
import asyncio
import sys
import time
import utils as botclass
import modules.AMP as AMP
import os

#loop = asyncio.get_event_loop()
#asyncio.set_event_loop(loop)

CWD = os.getcwd()
dBot = None
uBot = None
loop = None
discord_user = None
discord_role = None

#dBot = main.initbot()
#main.bot_start()
class TestingBot():
    def __init__(self,client):#,async_loop_main):
        global dBot,uBot#,loop
        self._client = client
        dBot = botclass.discordBot(client)
        uBot = botclass.botUtils(client)
        #loop = async_loop_main
        #uBot = main.botutils()
        #asyncio.run_coroutine_threadsafe(test(),loop)
        #asyncio.run_coroutine_threadsafe(test5(),loop)

    async def test(self):
        # while dBot._client.is_ready() == False: #Lets wait to start this until the bot has fully setup.
        #     await asyncio.sleep(1)
        uBot = botclass.botUtils(self._client)
        client_guild = 602285328320954378
        discord_role = uBot.roleparse(client_guild,'Test')
        discord_user = uBot.userparse(client_guild,'k8thekat#1357')
        print(type(discord_role),type(discord_user))
        await discord_user.add_roles(discord_role,reason='Testing User Add Role..')
        #await dBot.userAddRole(discord_user,discord_role,reason= 'Testing User Add Role..')


    async def test2(self):
        # while dBot._client.is_ready() == False: #Lets wait to start this until the bot has fully setup.
        #     await asyncio.sleep(1)
        client_guild = 602285328320954378 #602285328320954378
        discord_role = uBot.roleparse(client_guild,'Test')
        discord_user = uBot.userparse(client_guild,'k8thekat#1357')
        print(type(discord_role),discord_role.name,discord_role.id)
        await dBot.userRemoveRole(discord_user,discord_role,reason= 'Testing User Remove Role...')

    async def test3(self):
        # while dBot._client.is_ready() == False: #Lets wait to start this until the bot has fully setup.
        #     await asyncio.sleep(1)
        client_guild = 602285328320954378 #602285328320954378
        discord_channel = uBot.channelparse(client_guild,'botchannel')
        print(type(discord_channel),discord_channel.name,discord_channel.id)
        await dBot.sendMessage(discord_channel,content = 'This is a Test Message')

    async def test4(self):
        # while dBot._client.is_ready() == False: #Lets wait to start this until the bot has fully setup.
        #     await asyncio.sleep(1)
        client_guild = 602285328320954378 #602285328320954378
        discord_channel = uBot.channelparse(client_guild,'botchannel')
        message_id = '' 
        last_message = await discord_channel.fetch_message(message_id)
        print(last_message)
        await dBot.sendMessage(discord_channel,content = 'This Message will be deleted in 3 seconds...')
        await dBot.delMessage(last_message,3)

    async def test5(self): #Add Reaction Test
        # while dBot._client.is_ready() == False: #Lets wait to start this until the bot has fully setup.
        #     await asyncio.sleep(1)
        client_guild = 602285328320954378 #602285328320954378
        message_id = 963928591027036230
        discord_channel = uBot.channelparse(client_guild,'botchannel')
        message = await discord_channel.fetch_message(message_id)
        emoji = '<:love:873700764927811605>'
        #print(message)
        await dBot.messageAddReaction(message,emoji)

def AMPtest():
    main_AMP = AMP.getAMP()
    AMPInstances = main_AMP.getInstances()
    # test_server = AMPInstances['38407aa5-7b3e-4cc6-97b7-569ad1d0ff32']
    # #print(AMPInstances)
    # print(dir(test_server))
    # print(test_server.Module)
    for instance in AMPInstances:
        module = AMPInstances[instance].Module
        print(module)
        path = f'modules.{module}' #This gets us to the folder for the module specific scripts to load via the cog.
        try:
            module_file_list = os.listdir(CWD + '\\' + path.replace('.','\\')) #This gets me the list of files in the directory
            print(module_file_list)
            for script in module_file_list:
                print(script[:-3])
                if script.endswith('.py'):
                    print('Found a Script')
                    cog = f'{path}.script'
                    #TODO -- This needs testing.
                    #self._client.load_extension(cog) #We will load the scripts like a cog to access the commands and functions.

        except FileNotFoundError:
            print(f'Module Failed to Load - {module}')
      

AMPtest()



# while dBot._client.is_ready() == False: #Lets wait to start this until the bot has fully setup.
#     time.sleep(1)
# asyncio.ensure_future(test(discord_user,discord_role))
#main.async_loop.close()
