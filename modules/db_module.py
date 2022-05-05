from sqlite3 import dbapi2
import discord
from discord.ext import commands
import utils
import database


class Cog_Template(commands.Cog):
    def __init__ (self,client):
        self._client = client
        self.db = database.getDatabase()
        self.ubot = utils.botUtils
        print('Cog Template Loaded')
        self.ubot.sub_command_handler(self,'user',self.userdb_info)
     

    @commands.Cog.listener('on_message')
    async def on_message(self,message):
        if message.content.startswith(self._client.command_prefix):
            return message
        if message.author != self._client.user:
            print(f'On Message {self.name}: {message}')
            return message

    @commands.Cog.listener('on_member_update')
    async def on_member_update(user_before,user_after):
        if user_before.nick != user_after.nick:
            print(f'Edited User: {user_before} into {user_after}')
            return user_before,user_after

    #This is called when a message in any channel of the guild is edited. Returns <message> object.
    @commands.Cog.listener('on_message_edit')
    async def on_message_edit(self,message_before,message_after):
        """Called when a Message receives an update event. If the message is not found in the internal message cache, then these events will not be called. Messages might not be in cache if the message is too old or the client is participating in high traffic guilds."""
        if message_before.author != self._client.user:
            self.logger.info(f'Edited Message {self.name}: {message_before} into {message_after}')
            return message_before,message_after

    @commands.Cog.listener('on_reaction_add')
    async def on_reaction_add(self,reaction,user):
        """Called when a message has a reaction added to it. Similar to on_message_edit(), if the message is not found in the internal message cache, then this event will not be called. Consider using on_raw_reaction_add() instead."""
        print(f'{user} Added the Reaction: {reaction}')
        return reaction,user

    @commands.Cog.listener('on_reaction_remove')
    async def on_reaction_remove(self,reaction,user):
        """Called when a message has a reaction removed from it. Similar to on_message_edit, if the message is not found in the internal message cache, then this event will not be called."""
        print(f'{user} Removed the Reaction: {reaction}')
        return reaction,user

    #This is called when a User/Member leaves a Discord Guild. Returns a <member> object.
    @commands.Cog.listener('on_member_remove')
    async def on_member_remove(self,member):
        print(f'Member has left the server {member}')
        return member

  

    #Any COMMAND needs a ROLE CHECK prior
    @commands.command(name='info',description = 'cog template command')
    @utils.role_check()
    async def userdb_info(self,context,*param):
        print('user info')
        
        

def setup(client):
    client.add_cog(Cog_Template(client))