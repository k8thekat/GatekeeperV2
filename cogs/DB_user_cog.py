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

import discord
from discord.ext import commands
from discord import app_commands

import utils
import AMP 
import DB

class DB_User(commands.Cog):
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
        self.pBot = utils.botPerms()

        self.uBot.sub_command_handler('bot',self.db_bot_settings)
        self.uBot.sub_command_handler('bot',self.db_bot_donator)

        self.logger.info(f'**SUCCESS** Initializing {self.name.replace("db","DB")}')

    @commands.Cog.listener('on_message')
    async def on_message(self, message:discord.Message):
        if message.webhook_id != None:
            return message
        
        if message.author != self._client.user:
            self.logger.dev(f'On Message Event for {self.name}')

            #Testing out DM Functionality, Possible for allowing users to Update Information.
            if not message.guild:
                try:
                    await message.channel.send("This is a DM.")
                except discord.errors.Forbidden:
                    pass
            return message

        if message.content.startswith(self._client.command_prefix):
            return message

    @commands.Cog.listener('on_member_update')
    async def on_member_update(self, user_before:discord.User, user_after:discord.User):
        #Lets see if the name is different from before.
        if user_before.name != user_after.name:
            #Lets look up the previous ID to gaurentee a proper search, could use the newer user ID; both in theory should be the same.
            db_user = self.DB.GetUser(user_before.id)
            #If we found the DB User
            if db_user != None:
                db_user.DiscordName = user_after.name
            else:  # Lets Add them with the info we have!
                self.DB.AddUser(DiscordID=user_before.id, DiscordName=user_after.name)

            self.logger.dev(f'User Update {self.name}: {user_before.name} into {user_after.name}')
            return user_after

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self, member:discord.Member):
        self.logger.dev(f'Member has left the server {member.name}')
        return member

    @utils.role_check()
    @commands.hybrid_group(name='user')
    async def user(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Please try your command again...')

    @user.command(name='info')
    @utils.role_check()
    async def user_info(self, context:commands.Context, user:str):
        """Displays the Discord Users Database information"""
        self.logger.command(f'{context.author.name} used User Information')
        
        discord_user = self.uBot.userparse(user,context,context.guild.id)
        if discord_user != None:
            db_user = self.DB.GetUser(str(discord_user.id))
            if db_user != None:
                await context.send(embed= self.uBot.user_info_embed(context,db_user,discord_user))
            else:
                await context.send(f'Unable to find the user {discord_user} in the Database, please add them.')
               
    @user.command(name='add')
    @utils.role_check()
    async def user_add(self, context:commands.Context, discord_name:str, mc_ign:str=None, mc_uuid:str=None, steamid:str=None):
        """Adds the Discord Users information to the Database"""
        self.logger.command(f'{context.author.name} used User Add Function')
       
        if mc_ign != None:
            mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)

        discord_user = self.uBot.userparse(discord_name,context,context.guild.id)
        if discord_user != None:
            self.DB.AddUser(DiscordID=discord_user.id, DiscordName=discord_user.name, MC_IngameName=mc_ign, MC_UUID=mc_uuid, SteamID=steamid)
            await context.send(f'Added {discord_user.name} to the Database!')
        else:
            await context.send(f'Unable to find the {discord_name} you provided, please try again.')
            
    @user.command(name='update')
    @utils.role_check()
    async def user_update(self, context:commands.Context, discord_name:str, mc_ign:str=None, mc_uuid:str=None, steamid:str=None):
        """Updated a Discord Users information in the Database"""
        self.logger.command(f'{context.author.name} used User Update Function')
       
        discord_user = None
        db_user = None
        params = locals()
        db_params = {'discord_name': 'DiscordName',
                    'mc_ign' : 'MC_IngameName',
                    'mc_uuid' : 'MC_UUID',
                    'steamid' : 'SteamID'
                    }

        if mc_ign != None:
            mc_uuid = self.uBot.name_to_uuid_MC(mc_ign)
            params['mc_uuid'] = mc_uuid

        discord_user = self.uBot.userparse(discord_name,context,context.guild.id)
        if discord_user != None:
            db_user = self.DB.GetUser(discord_user.id)
            if db_user != None:
                for entry in db_params:
                    if params[entry] != None:
                        setattr(db_user,db_params[entry],params[entry])

                await context.send(f'We Updated the user {db_user.DiscordName}')
            else:
                await context.send('Looks like this user is not in the Database, please use `/user add`')
        else:
            await context.send(f'Hey I was unable to find the User: {discord_name}')

    @user.command(name='uuid')
    @utils.role_check()
    async def user_uuid(self, context:commands.Context, mc_ign:str):
        """This will convert a Minecraft IGN to a UUID if it exists"""
        self.logger.command(f'{context.author.name} used User UUID Function')

        await context.send(f'The UUID of {mc_ign} is: {self.uBot.name_to_uuid_MC(mc_ign)}')

    @user.command(name='steamid')
    @utils.role_check()
    async def user_steamid(self, context:commands.Context, steam_name:str):
        """This will convert a Steam Display Name to a SteamID if it exists"""
        self.logger.command(f'{context.author.name} used User SteamID Function')

        await context.send(f'The SteamID of {steam_name} is: {self.uBot.name_to_steam_id(steam_name)}')
    
    @user.command(name='role')
    @utils.role_check()
    @app_commands.autocomplete(role= utils.autocomplete_permission_roles)
    async def user_role(self, context:commands.Context, user:str, role:str):
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
    async def user_test(self, context:commands.Context, user:str):
        """DB User Test Function"""
        self.logger.command(f'{context.author.name} used User Test Function')
        cur_user = self.uBot.userparse(context = context,guild_id=context.guild.id,parameter = user)
        DB_user = self.DB.GetUser(cur_user.id)
        print('DB User Role', DB_user.Role)
        await context.send(cur_user)

    @commands.hybrid_command(name='settings')
    @utils.role_check()
    async def db_bot_settings(self, context:commands.Context):
        """Displays currently set Bot settings"""
        self.logger.command(f'{context.author.name} used Bot Settings...')
    
        self.DBConfig = self.DB.GetConfig()
        dbsettings_list = self.DBConfig.GetSettingList()
        settings_list = []
        for setting in dbsettings_list:
            config = self.DBConfig.GetSetting(setting)
            settings_list.append({f'{setting.capitalize()}': f'{str(config)}'})
        await context.send(embed=self.uBot.bot_settings_embed(context, settings_list))

    @commands.hybrid_command(name='donator')
    @utils.role_check()
    @app_commands.autocomplete(role= utils.autocomplete_discord_roles)
    async def db_bot_donator(self, context:commands.Context, role:str):
        """Sets the Donator Role for Donator Only AMP Server access."""
        self.logger.command(f'{context.author.name} used Bot Donator Role...')
        self.DBConfig = self.DB.GetConfig()
        discord_role = self.uBot.roleparse(role,context,context.guild.id)
        if discord_role != None:
            self.DBConfig.SetSetting('Donator_role_id',str(discord_role.id))
            await context.send(f'You are all set! Donator Role is now set to {discord_role.name}')
        else:
            await context.send(f'Hey! I was unable to find the role {role}, Please try again.')
    
    @commands.hybrid_group(name='display')
    @utils.role_check()
    async def db_bot_display(self, context:commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    #!TODO! Allow DMs to update a Users information
    # @commands.command()
    # @commands.dm_only()
    # async def com(self, ctx):
    #     await ctx.send("You used the command. Say something.")
    #     def check(m):
    #         return True
    #     try:
    #         msg = await self.bot.wait_for('message', check = check, timeout = 10.0) # waits for 10 seconds 
    #     except asyncio.TimeoutError:
    #         await ctx.send("You took too long...")
    #     else:
    #         await ctx.send(f"You said `{msg.content}`")

async def setup(client):
    await client.add_cog(DB_User(client))