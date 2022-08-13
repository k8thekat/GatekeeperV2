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
import os
import logging
import re

import discord
from discord.ext import commands
from discord import app_commands

import utils
import AMP
import DB


class DB_Module(commands.Cog):
    def __init__(self, client: commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)

        self.logger = logging.getLogger(__name__)  # Point all print/logging statments here!

        self.AMPHandler = AMP.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        self.pBot = utils.botPerms()

        self.uBot.sub_command_handler('bot', self.db_bot_whitelist)
        self.uBot.sub_command_handler('bot', self.db_bot_settings)

        self.whitelist_emoji_message = ''
        self.whitelist_emoji_pending = False
        self.whitelist_emoji_done = False
        self.logger.info(f'**SUCCESS** Initializing {self.name.replace("db","DB")}')
     

    @commands.Cog.listener('on_message')
    async def on_message(self, message: discord.Message):
        if message.webhook_id is not None:
            return message
        if message.content.startswith(self._client.command_prefix):
            return message

        # This is purely for testing!
        if message.content.startswith('test_emoji') and message.author.id == 144462063920611328:  # This is my Discord ID
            if self.DBConfig.Whitelist_emoji_pending is not None:
                emoji = self._client.get_emoji(int(self.DBConfig.Whitelist_emoji_pending))
                await message.add_reaction(emoji)

        if message.author != self._client.user:
            self.logger.dev(f'On Message Event for {self.name}')
            return message

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self, user_before: discord.User, user_after: discord.User):
        # Lets see if the name is different from before.
        if user_before.name != user_after.name:
            # Lets look up the previous ID to gaurentee a proper search, could use the newer user ID; both in theory should be the same.
            db_user = self.DB.GetUser(user_before.id)
            # If we found the DB User
            if db_user is not None:
                db_user.DiscordName = user_after.name
            else:  # Lets Add them with the info we have!
                self.DB.AddUser(DiscordID=user_before.id, DiscordName=user_after.name)

            self.logger.dev(f'User Update {self.name}: {user_before.name} into {user_after.name}')
            return user_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member: discord.Member):
        self.logger.dev(f'Member has left the server {member.name}')
        return member

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self.logger.dev(f'Reaction Add {self.name}: {user} Reaction: {reaction}')

        # This is for setting the Whitelist_Emoji_pending after using the command!
        if reaction.message.id == self.whitelist_emoji_message:
            # This is for pending whitelist requests
            if self.whitelist_emoji_pending:
                self.DBConfig.Whitelist_emoji_pending = reaction.emoji.id
                self.whitelist_emoji_pending = False
            # This is for completed whitelist requests
            if self.whitelist_emoji_done:
                self.DBConfig.Whitelist_emoji_done = reaction.emoji.id
                self.whitelist_emoji_done = False

        return reaction, user

    @utils.role_check()
    @commands.hybrid_group()
    async def user(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...')

    @user.command(name='info')
    @utils.role_check()
    async def user_info(self, context: commands.Context, user: str):
        """Displays the Discord Users Database information"""
        self.logger.command(f'{context.author.name} used User Information')
     
        
        discord_user = self.uBot.userparse(user,context,context.guild.id)
        if discord_user != None:
            db_user = self.DB.GetUser(str(discord_user.id))
            if db_user is not None:
                await context.send(embed=self.uBot.user_info_embed(context, db_user, discord_user))

    @user.command(name='add')
    @utils.role_check()
    async def user_add(self,context:commands.Context,discord_name:str,mc_ign:str=None,mc_uuid:str=None,steamid:str=None,donator:bool=False):
        """Adds the Discord Users information to the Database"""
        self.logger.command(f'{context.author.name} used User Add Function')
       

        if mc_ign != None:
            mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)

        discord_user = self.uBot.userparse(discord_name,context,context.guild.id)
        if discord_user != None:
            self.DB.AddUser(DiscordID=discord_user.id,DiscordName=discord_user.name,MC_IngameName=mc_ign,MC_UUID=mc_uuid,SteamID=steamid,Donator=donator)
            await context.send(f'Added {discord_user.name} to the Database!')
        else:
            await context.send(f'Unable to find the {discord_name} you provided, please try again.')
            

    @user.command(name='update')
    @utils.role_check()
    async def user_update(self,context:commands.Context,discord_name:str,mc_ign:str=None,mc_uuid:str=None,steamid:str=None,donator:bool=None):
        """Updated a Discord Users information in the Database"""
        self.logger.command(f'{context.author.name} used User Update Function')
       

        discord_user = None
        db_user = None
        params = locals()
        db_params = {'discord_name': 'DiscordName',
                    'mc_ign' : 'MC_IngameName',
                    'mc_uuid' : 'MC_UUID',
                    'steamid' : 'SteamID',
                    'donator' : 'Donator'}

        if mc_ign is not None:
            mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)
            params['mc_uuid'] = mc_uuid


        discord_user = self.uBot.userparse(discord_name,context,context.guild.id)

        if discord_user is not None:
            db_user = self.DB.GetUser(discord_user.id)
            if db_user is not None:
                for entry in db_params:
                    if params[entry] is not None:
                        setattr(db_user, db_params[entry], params[entry])

                await context.send(f'We Updated the user {db_user.DiscordName}')
            else:
                await context.send('Looks like this user is not in the Database, please use `/user add`')
        else:
            await context.send(f'Hey I was unable to find the User: {discord_name}')

    @user.command(name='uuid')
    @utils.role_check()
    async def user_uuid(self, context: commands.Context, mc_ign: str):
        """This will convert a Minecraft IGN to a UUID if it exists"""
        self.logger.command(f'{context.author.name} used User UUID Function')

        await context.send(f'The UUID of {mc_ign} is: {self.uBot.name_to_uuid_MC(mc_ign)}')


    @user.command(name='role')
    @utils.role_check()
    @app_commands.autocomplete(role=utils.autocomplete_permission_roles)
    async def user_role(self,context:commands.Context,user:str,role:str):
        """Set a users Permission Role for commands."""
        self.logger.command(f'{context.author.name} used User Role Function')

        discord_user = self.uBot.userparse(user,context,context.guild.id)
        if discord_user == None:
            await context.send(f'We failed to find the User: {user}, please make sure they are apart of the server..')
            return

        db_user = self.DB.GetUser(discord_user.id)
        if db_user != None:
            db_user.Role = role
            await context.send(f"We set the User: {user} permission's role to {role}.")
        else:
            await context.send(f'We failed to find the User: {user}, please make sure they are in the DB.')

    @user.command(name='test')
    @utils.role_check()
    async def user_test(self,context:commands.Context,user:str):
        """DB User Test Function"""
        cur_user = self.uBot.userparse(context = context,guild_id=context.guild.id,parameter = user)
        DB_user = self.DB.GetUser(cur_user.id)
        print('DB User Role', DB_user.Role)
        self.logger.command(f'{context.author.name} used User Test Function')
        await context.send(cur_user)

    # All DBConfig Whitelist Specific function settings --------------------------------------------------------------
    @commands.hybrid_group(name='whitelist')
    @utils.role_check()
    async def db_bot_whitelist(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_bot_whitelist.command(name='channel')
    @utils.role_check()
    async def db_bot_whitelist_channel_set(self, context: commands.Context, id: str):
        """Sets the Whitelist Channel for the Bot to monitor"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Channel Set...')
      

        channel = self.uBot.channelparse(id, context, context.guild.id)
        if channel is None:
            return await context.reply(f'Unable to find the Discord Channel: {id}')
        else:
            self.DBConfig.SetSetting('Whitelist_channel', channel.id)
            await context.send(f'Set Bot Channel Whitelist to {channel.name}')

    @db_bot_whitelist.command(name='waittime')
    @utils.role_check()
    async def db_bot_whitelist_wait_time_set(self, context: commands.Context, time: str):
        """Set the Bots Whitelist wait time , this value is in minutes!"""
        self.logger.command(f'{context.author.name} used Bot Whitelist wait time Set...')
        

        if time.isalnum():
            self.DBConfig.Whitelist_wait_time = time
            await context.send(f'Whitelist wait time has been set to {time} minutes.')
        else:
            await context.send('Please use only numbers when setting the wait time. All values are in minutes!')

    @db_bot_whitelist.command(name='auto')
    @utils.role_check()
    async def db_bot_whitelist_auto_whitelist(self, context: commands.Context, flag: str):
        """This turns on or off Auto-Whitelisting"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Auto Whitelist...')
    

        flag_reg = re.search("(true|false)", flag.lower())
        if flag_reg is None:
            return await context.send('Please use `true` or `false` for your flag.')
        if flag_reg.group() == 'true':
            self.DBConfig.Auto_whitelist = True
            return await context.send('Enabling Auto-Whitelist.')
        if flag_reg.group() == 'false':
            self.DBConfig.Auto_whitelist = False
            return await context.send('Disabling Auto-Whitelist')

    @db_bot_whitelist.command(name='pending_emoji')
    @utils.role_check()
    async def db_bot_whitelist_pending_emjoi_set(self, context: commands.Context):
        """This sets the Whitelist pending emoji, you MUST ONLY use your Servers Emojis'"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Pending Emoji...')
      

        flag = 'pending Whitelist requests!'
        await context.send('Please react to this message with the emoji you want for pending Whitelist requests!\n Only use Emojis from this Discord Server!')
        channel = self._client.get_channel(context.channel.id)
        messages = [message async for message in channel.history(limit=5)]
        for message in messages:
            if flag in message.content:
                self.whitelist_emoji_message = messages[0].id

        self.whitelist_emoji_pending = True

    @db_bot_whitelist.command(name='done_emoji')
    @utils.role_check()
    async def db_bot_whitelist_done_emjoi_set(self, context: commands.Context):
        """This sets the Whitelist completed emoji, you MUST ONLY use your Servers Emojis'"""
        self.logger.command(f'{context.author.name} used Bot Whitelist Done Emoji...')
    

        flag = 'completed Whitelist requests!'
        await context.send('Please react to this message with the emoji you want for completed Whitelist requests!\n Only use Emojis from this Discord Server!')
        channel = self._client.get_channel(context.channel.id)
        messages = [message async for message in channel.history(limit=5)]
        for message in messages:
            if flag in message.content:
                self.whitelist_emoji_message = messages[0].id

        self.whitelist_emoji_done = True

    @commands.hybrid_command(name='settings')
    @utils.role_check()
    async def db_bot_settings(self, context: commands.Context):
        """Displays currently set Bot settings"""
        self.logger.command(f'{context.author.name} used Bot Settings...')
      

        self.DBConfig = self.DB.GetConfig()
        dbsettings_list = self.DBConfig.GetSettingList()
        settings_list = []
        for setting in dbsettings_list:
            config = self.DBConfig.GetSetting(setting)
            settings_list.append({f'{setting.capitalize()}': f'{str(config)}'})
        await context.send(embed=self.uBot.bot_settings_embed(context, settings_list))

    @commands.hybrid_group(name='dbserver')
    @utils.role_check()
    async def db_server(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @db_server.command(name='cleanup')
    @utils.role_check()
    async def db_server_cleanup(self, context: commands.Context):
        """This is used to remove un-used DBServer entries and update names of existing servers."""
        self.logger.command(f'{context.author.name} used Database Clean-Up in progress...')
    

        db_server_list = self.DB.GetAllServers()

        for server in db_server_list:
            if server.InstanceID not in self.AMPInstances:
                db_server = self.DB.GetServer(InstanceID=server.InstanceID)
                db_server.delServer()
            if server.InstanceID in self.AMPInstances:
                for instance in self.AMPInstances:
                    if self.AMPInstances[instance].InstanceID == server.InstanceID:
                        server.FriendlyName = self.AMPInstances[instance].FriendlyName

    #!TODO! This Function needs to be laid out and tested.
    @db_server.command(name='swap')
    @utils.role_check()
    async def db_server_instance_swap(self, context, old_server, new_server):
        """This will be used to swap Instance ID's with an existing AMP Instance"""
        self.logger.command(f'{context.author.name} used Database Instance swap...')
        

        old_server = self.uBot.serverparse(context,context.guild.id)

async def setup(client):
    await client.add_cog(DB_Module(client))
