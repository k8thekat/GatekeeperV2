from http import server
import os
import logging
import re

import discord
from discord.ext import commands

import utils
import AMP 
import DB


class DB_Module(commands.Cog):
    def __init__ (self,client:commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger(__name__) #Point all print/logging statments here!

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP#Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances #Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB #Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)

        self.uBot.sub_command_handler('bot',self.db_bot_whitelist)
        self.uBot.sub_command_handler('bot',self.db_bot_settings)

        self.whitelist_emoji_message = '' 
        self.whitelist_emoji_pending = False
        self.whitelist_emoji_done = False
        self.logger.info(f'**SUCESS** Initializing **{self.name.replace("db","DB")}**')
     

    @commands.Cog.listener('on_message')
    async def on_message(self,message:discord.Message):
        if message.webhook_id != None:
            return message
        if message.content.startswith(self._client.command_prefix):
            return message

        #This is purely for testing!
        if message.content.startswith('test_emoji') and message.author.id == 144462063920611328: #This is my Discord ID
            if self.DBConfig.Whitelist_emoji_pending != None:
                emoji = self._client.get_emoji(int(self.DBConfig.Whitelist_emoji_pending))
                await message.add_reaction(emoji)

        if message.author != self._client.user:
            self.logger.info(f'On Message Event for {self.name}')
            return message

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self,user_before:discord.User,user_after:discord.User):
        #Lets see if the name is different from before.
        if user_before.name != user_after.name:
            #Lets look up the previous ID to gaurentee a proper search, could use the newer user ID; both in theory should be the same.
            db_user = self.DB.GetUser(user_before.id)
            #If we found the DB User
            if db_user != None:
                db_user.DiscordName = user_after.name
            else: #Lets Add them with the info we have!
                self.DB.AddUser(DiscordID= user_before.id, DiscordName= user_after.name)

            self.logger.info(f'User Update {self.name}: {user_before.name} into {user_after.name}')
            return user_after

    #This is called when a message in any channel of the guild is edited. Returns <message> object.
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self,message_before:discord.Message,message_after:discord.Message):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            self.logger.info(f'Edited Message Event for {self.name}')
            return message_before,message_after
    
    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member:discord.Member):
        print(f'Member has left the server {member.name}')
        return member

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self,reaction:discord.Reaction,user:discord.User):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self.logger.info(f'Reaction Add {self.name}: {user} Reaction: {reaction}')

        #This is for setting the Whitelist_Emoji_pending after using the command!
        if reaction.message.id == self.whitelist_emoji_message:
            #This is for pending whitelist requests
            if self.whitelist_emoji_pending:
                self.DBConfig.Whitelist_emoji_pending = reaction.emoji.id
                self.whitelist_emoji_pending = False
            #This is for completed whitelist requests
            if self.whitelist_emoji_done:
                self.DBConfig.Whitelist_emoji_done = reaction.emoji.id
                self.whitelist_emoji_done = False

        return reaction,user

    @utils.role_check()
    @commands.hybrid_group()
    async def user(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...')

    @user.command(name='info')
    @utils.role_check()
    async def user_info(self,context:commands.Context,user:str=None):
        """Displays the Discord Users Database information"""
        #Call on DB User specific Info from here
        self.logger.info('User Information')
        discord_user = self.uBot.userparse(user,context,context.guild.id)
        if discord_user != None:
            db_user = self.DB.GetUser(str(discord_user.id))
            if db_user != None:
                print(db_user.DiscordID,db_user.DiscordName,db_user.MC_IngameName,db_user.MC_UUID,db_user.SteamID,db_user.Donator)

    @user.command(name='add')
    @utils.role_check()
    async def user_add(self,context:commands.Context,discord_name:str,discord_id:str=None,mc_ign:str=None,mc_uuid:str=None,steamid:str=None,donator:bool=False):
        """Adds the Discord Users information to the Database"""
        self.logger.info('User Add Function')
        if mc_ign != None:
            mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)

        if discord_id == None:
            discord_user = self.uBot.userparse(discord_name,context,context.guild.id)
            if discord_user != None:
                self.DB.AddUser(DiscordID=discord_user.id,DiscordName=discord_user.name,MC_IngameName=mc_ign,MC_UUID=mc_uuid,SteamID=steamid,Donator=donator)
        else:
            self.DB.AddUser(DiscordID=discord_id,DiscordName=discord_name,MC_IngameName=mc_ign,MC_UUID=mc_uuid,SteamID=steamid,Donator=donator)
        await context.send(f'Added {discord_user.name} to the Database!')
            

    @user.command(name='update')
    @utils.role_check()
    async def user_update(self,context:commands.Context,discord_name:str,discord_id:str=None,mc_ign:str=None,mc_uuid:str=None,steamid:str=None,donator:bool=False):
        """Updated a Discord Users information in the Database"""
        self.logger.info('User Update Function')
        discord_user = None
        db_user = None
        print(discord_name,discord_id,mc_ign,mc_uuid,steamid,donator)

        if mc_ign != None:
            mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)
            print(mc_uuid)

        if discord_id == None:
            discord_user = self.uBot.userparse(discord_name,context,context.guild.id)
            print(discord_user)
        else:
            discord_user = self._client.get_user(int(discord_id))

        if discord_user != None:
            db_user = self.DB.GetUser(discord_user.id)
            print(db_user)
            if db_user != None:
                db_user.DiscordName = discord_user.name
                db_user.MC_IngameName = mc_ign
                db_user.MC_UUID = mc_uuid
                db_user.SteamID = steamid
                db_user.Donator = donator
                await context.send(f'We Updated the user {db_user.DiscordName}')
            else:
                await context.send(f'Looks like this user is not in the Database, please use `/user add`')
        else:
            await context.send(f'Hey I was unable to find the User: {discord_name}')
        

    @user.command(name='uuid')
    @utils.role_check()
    async def user_uuid(self,context:commands.Context,mc_ign:str):
        """This will convert a Minecraft IGN to a UUID if it exists"""
        self.logger.info('User UUID Function')
        await context.send(f'The UUID of {mc_ign} is: {self.uBot.name_to_uuid_MC(mc_ign)}')

    @user.command(name='test')
    @utils.role_check()
    async def user_test(self,context:commands.Context,user:str=None):
        """DB User Test Function"""
        #print(dir(context))
        cur_user = self.uBot.userparse(context = context,guild_id=context.guild.id,parameter = user)
        self.logger.info('User Test Function')
        await context.send(cur_user)

    #All DBConfig Whitelist Specific function settings --------------------------------------------------------------
    @commands.hybrid_group(name='whitelist')
    @utils.role_check()
    async def db_bot_whitelist(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_bot_whitelist.command(name='channel')
    @utils.role_check()
    async def db_bot_whitelist_channel_set(self,context:commands.Context,id:str):
        """Sets the Whitelist Channel for the Bot to monitor"""
        self.logger.info('Bot Whitelist Channel Set...')

        channel = self.uBot.channelparse(id,context,context.guild.id)
        if channel == None:
            return await context.reply(f'Unable to find the Discord Channel: {id}')
        else:
            self.DBConfig.SetSetting('Whitelist_channel',channel.id)
            await context.send(f'Set Bot Channel Whitelist to {channel.name}')
    
    @db_bot_whitelist.command(name='waittime')
    @utils.role_check()
    async def db_bot_whitelist_wait_time_set(self,context:commands.Context,time:str):
        """Set the Bots Whitelist wait time , this value is in minutes!"""
        self.logger.info('Bot Whitelist wait time Set...')
        if time.isalnum():
            self.DBConfig.Whitelist_wait_time = time
            await context.send(f'Whitelist wait time has been set to {time} minutes.')
        else:
            await context.send(f'Please use only numbers when setting the wait time. All values are in minutes!')

    @db_bot_whitelist.command(name='auto')
    @utils.role_check()
    async def db_bot_whitelist_auto_whitelist(self,context:commands.Context,flag:str):
        """This turns on or off Auto-Whitelisting"""
        self.logger.info('Bot Whitelist Auto Whitelist...')
        flag_reg = re.search("(true|false)",flag.lower())
        if flag_reg == None:
            return await context.send(f'Please use `true` or `false` for your flag.')
        if flag_reg.group() == 'true':
            self.DBConfig.Auto_whitelist = True
            return await context.send(f'Enabling Auto-Whitelist.')
        if flag_reg.group() == 'false':
            self.DBConfig.Auto_whitelist = False
            return await context.send(f'Disabling Auto-Whitelist')
        
    @db_bot_whitelist.command(name='pending_emoji')
    @utils.role_check()
    async def db_bot_whitelist_pending_emjoi_set(self,context:commands.Context):
        """This sets the Whitelist pending emoji, you MUST ONLY use your Servers Emojis'"""
        flag = 'pending Whitelist requests!'
        await context.send(f'Please react to this message with the emoji you want for pending Whitelist requests!')
        channel = self._client.get_channel(context.channel.id)
        messages = [message async for message in channel.history(limit=5)]
        for message in messages:
            if flag in message.content:
                self.whitelist_emoji_message = messages[0].id

        self.whitelist_emoji_pending = True

    @db_bot_whitelist.command(name='done_emoji')
    @utils.role_check()
    async def db_bot_whitelist_done_emjoi_set(self,context:commands.Context):
        """This sets the Whitelist completed emoji, you MUST ONLY use your Servers Emojis'"""
        flag = 'completed Whitelist requests!'
        await context.send(f'Please react to this message with the emoji you want for completed Whitelist requests!')
        channel = self._client.get_channel(context.channel.id)
        messages = [message async for message in channel.history(limit=5)]
        for message in messages:
            if flag in message.content:
                self.whitelist_emoji_message = messages[0].id

        self.whitelist_emoji_done = True

    @commands.hybrid_command(name='settings')
    @utils.role_check()
    async def db_bot_settings(self,context:commands.Context):
        """Displays currently set Bot settings"""
        dbsettings_list = self.DBConfig.GetSettingList()
        settings_list = []
        for setting in dbsettings_list:
            config = self.DBConfig.GetSetting(setting)
            settings_list.append({f'{setting.capitalize()}': f'{str(config)}'})
        await context.send(embed= self.uBot.bot_settings_embed(context,settings_list))
        
    @commands.hybrid_group(name='dbserver')
    @utils.role_check()
    async def db_server(self,context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_server.command(name='cleanup')
    @utils.role_check()
    async def db_server_cleanup(self,context:commands.Context):
        """This is used to remove un-used DBServer entries and update names of existing servers."""
        self.logger.info('Database Clean-Up in progress...')

        db_server_list = self.DB.GetAllServers() 

        for server in db_server_list:
            if server.InstanceID not in self.AMPInstances:
                db_server = self.DB.GetServer(InstanceID = server.InstanceID)
                db_server.delServer()
            if server.InstanceID in self.AMPInstances:
                for instance in self.AMPInstances:
                    if self.AMPInstances[instance].InstanceID == server.InstanceID:
                            server.FriendlyName = self.AMPInstances[instance].FriendlyName

    #!TODO! This Function needs to be laid out and tested.
    @db_server.command(name='swap')
    @utils.role_check()
    async def db_server_instance_swap(self,context,old_server,new_server):
        """This will be used to swap Instance ID's with an existing AMP Instance"""
        self.logger.info()
        old_server = self.uBot.serverparse(context,context.guild.id)

async def setup(client):
    await client.add_cog(DB_Module(client))