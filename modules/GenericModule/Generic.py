import discord
from discord.ext import commands
import os
import logging
from modules.Minecraft.minecraft import Minecraft

import utils
import modules.AMP as AMP
import modules.database as DB


class Generic(commands.Cog):
    def __init__ (self,client):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger(__name__) #Point all print/logging statments here!
        self.logger.info(f'{self.name} Module Loaded')

        self.AMP = AMP.getAMP() #Main AMP object
        self.DB = DB.getDatabase() #Main Database object

        self.uBot = utils.botUtils(client)
        self.dBot = utils.discordBot(client)
        self.uBot.sub_command_handler('server',self.server_whitelist) 
        #self.uBot.sub_command_handler(self,'user',self.info)

    @commands.Cog.listener('on_message')
    async def on_message(self,message):
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            self.logger.info(f'On Message Event for {self.name}')
            return message

    @commands.Cog.listener('on_user_update')
    async def on_user_update(self,user_before,user_after):
        """Called when a User updates any part of their Discord Profile; this provides access to the `user_before` and `user_after` <discord.Member> objects."""
        self.logger.info(f'User Update {self.name}: {user_before} into {user_after}')
        return user_before,user_after

    #This is called when a message in any channel of the guild is edited. Returns <message> object.
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self,message_before,message_after):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            self.logger.info(f'Edited Message Event for {self.name}')
            return message_before,message_after

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self,reaction,user):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        self.logger.info(f'Reaction Add {self.name}: {user} Reaction: {reaction}')
        return reaction,user

    @commands.Cog.listener('on_reaction_remove')
    async def on_reaction_remove(self,reaction,user):
        """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
        self.logger.info(f'Reaction Remove {self.name}: {user} Reaction: {reaction}')
        return reaction,user

    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member):
        """Called when a member is kicked or leaves the Server/Guild. Returns a <discord.Member> object."""
        self.logger.info(f'Member Leave {self.name}: {member.name} {member}')
        return member

    @commands.hybrid_group(name='whitelist')
    @utils.role_check()
    async def server_whitelist(self,context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...')

    @server_whitelist.command(name='true')
    @utils.role_check()
    async def server_whitelist_true(self,context,server):
        """Set Servers Whitelist Allowed to True"""
        server = await self.uBot.serverparse(context,context.guild.id,server)
        self.DB.getServer(server.FriendlyName).Whitelist = True
        await context.send(f"Server: {server.FriendlyName}, Whitelist set to : `True`")

    @server_whitelist.command(name='false')
    @utils.role_check()
    async def server_whitelist_false(self,context,server):
        """Set Servers Whitelist Allowed to False"""
        server = await self.uBot.serverparse(context,context.guild.id,server)
        self.DB.getServer(server.FriendlyName).Whitelist = False
        await context.send(f"Server: {server.FriendlyName}, Whitelist set to : `False`")

    @server_whitelist.command(name='test')
    @utils.role_check()
    async def server_whitelist_test(self,context,server=None,user=None):
        """Server Whitelist Test function."""
        server = await self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            #user = await self.uBot.name_to_UUID(context,user)
            server_whitelist = server.getWhitelist()
            print(server_whitelist)
            #await context.send(f'Test Function for Server Whitelist {server}{user[0]["name"]}')

    @server_whitelist.command(name='add')
    @utils.role_check()
    async def server_whitelist_add(self,context,server,user):
        """Adds User to Servers Whitelist"""
        server = await self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            user = await self.uBot.name_to_UUID(context,user)
            if user != None:
                server.addWhitelist(user[0]['name'])
                await context.send(f'User: {user[0]["name"]} was whitelisted on Server: {server.FriendlyName}')

    @server_whitelist.command(name='remove')
    @utils.role_check()
    async def server_whitelist_remove(self,context,server,user):
        """Remove a User from the Servers Whitelist"""
        server = await self.uBot.serverparse(context,context.guild.id,server)
        if server != None:
            user = await self.uBot.name_to_UUID(context,user)
            if user != None:
                server.removeWhitelist(user[0]['name'])
                await context.send(f'User: {user[0]["name"]} was removed from the Whitelist on Server: {server.FriendlyName}')
        
async def setup(client):
    await client.add_cog(Generic(client))