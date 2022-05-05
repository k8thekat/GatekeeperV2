from datetime import datetime
import logging

import discord
from discord.ext import commands,tasks
from discord.ui import Button,View
import asyncio

import bot_config
import modules.database as DB
import modules.AMP as AMP

async def async_rolecheck(context):
    logger = logging.getLogger(__name__)
    staff_role,author_top_role = 0,0
    guild_roles = context.guild.roles
    
    if type(context) == discord.member.Member:
        top_role_id = context.top_role.id
        author = context.name
    else:
        top_role_id = context.message.author.top_role.id
        author = context.message.author
    for i in range(0,len(guild_roles)):
        if guild_roles[i].id == top_role_id:
            author_top_role = i

        if guild_roles[i].id == bot_config.Staff_Role:
            staff_role = i
            
    if author_top_role > staff_role:
        logger.info(f'Permission Check Okay on {author}')
        return True
        
    else:
        logger.info(f'Permission Check Failed on {author}')
        await context.send('You do not have permission to use that command...')
        return False

def role_check():
    """Use this before any Commands that require a Staff/Mod level permission Role"""
    return commands.check(async_rolecheck)

class CustomButton(Button):
    def __init__(self,server,view,function,label:str,callback_label:str,callback_disabled:bool,style=discord.ButtonStyle.green,context=None):
        super().__init__(label=label, style=style, custom_id=label)
        self.server = server
        self.context = context
        self._label = label

        self.callback_label = callback_label
        self.callback_disabled = callback_disabled

        self._function = function
        self._view = view
        view.add_item(self)

    async def callback(self,interaction):
        """This is called when a button is interacted with."""
        if not await async_rolecheck(interaction.user):
            return
        self._interaction = interaction
        self.label = self.callback_label
        self.disabled = self.callback_disabled
        await interaction.response.edit_message(view=self._view)
        print('Run my Command')
        #self._function()
        await asyncio.sleep(30)
        await self.reset()

    #@tasks.loop(seconds=30.0)
    async def reset(self):
        #print(dir(self._interaction))
        print('Resetting Buttons...')
        self.label = self._label
        self.disabled = False
        await self._interaction.followup.edit_message(message_id=self._interaction.message.id,view=self._view)



class StopButton(CustomButton):
    def __init__(self,server,view,function):
        super().__init__(server=server,view=view,function=function,label='Stop', callback_label='Stopping...',callback_disabled=True,style=discord.ButtonStyle.red)

class RestartButton(CustomButton):
    def __init__(self,server,view,function):
        super().__init__(server=server,view=view,function=function,label='Restart', callback_label='Restarting...',callback_disabled=True,style=discord.ButtonStyle.blurple)

class KillButton(CustomButton):
    def __init__(self,server,view,function):
        super().__init__(server=server,view=view,function=function,label='Kill', callback_label='Killed...', callback_disabled=True,style=discord.ButtonStyle.danger)
    
class StatusView(View):
    def __init__(self,timeout=180):
        super().__init__(timeout=timeout)

    async def on_timeout(self):
        """This Removes all the Buttons after timeout has expired"""
        #!TODO! Find an alternative to stop.
        self.stop()

class discordBot():
    def __init__(self,client):
        self.botLogger = logging.getLogger(__name__)
        self._client = client
        self.botLogger.info(f'Bot Init')
    
    async def userAddRole(self, user: discord.user, role: discord.role, reason:str=None):
        """Adds a Role to a User.\n
        Requires a `<user`> and `<role>` discord object.\n
        Supports `reason`(Optional)"""
        
        self.botLogger.info('Add Users Discord Role Called...')
        await user.add_roles(role,reason)

    async def userRemoveRole(self, user: discord.user, role: discord.role, reason:str=None):
        """Removes a Role from the User.\n
        Requires a `<user>` and `<role>` discord object.\n
        Supports `reason`(Optional)"""

        self.botLogger.info('Remove Users Discord Role Called...')
        print(type(user),type(role))
        await user.remove_roles(role,reason)

    async def delMessage(self,message: discord.message, delay: float=None):
        """Deletes the message.\n
        Your own messages could be deleted without any proper permissions. However to delete other people's messages, you need the `manage_messages` permission.\n
        Supports `delay[float]`(Optional)"""

        self.botLogger.info('Delete Discord Message Called...')
        await message.delete(delay=delay)

    async def channelHistory(self,channel:discord.TextChannel,limit:int=10,before:datetime=None,after:datetime=None,around:datetime=None,oldest_first:bool=False):
        if limit > 100:
            limit = 100
        messages = await channel.history(limit,before,after,around,oldest_first).flatten()
        return messages

    async def editMessage(self,message: discord.message ,content: str=None, delete_after:float=None):
        """Edits the message.\n
        The content must be able to be transformed into a string via `str(content)`.\n
        Supports `delete_after[float]`(Optional)"""

        self.botLogger.info('Edit Discord Message Called...')
        await message.edit(content,delete_after)

    async def sendMessage(self, parameter:object, content:str,*, tts:bool=False,embed=None, file:discord.file=None, files:list=None, delete_after:float=None, nonce= None, allowed_mentions=None, reference:object=None):
        #content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, allowed_mentions=None, reference=None, mention_author=None
        """Sends a message to the destination with the content given.\n
        The content must be a type that can convert to a string through `str(content)`. If the content is set to `None` (the default), then the embed parameter must be provided.\n
        To upload a single file, the `file` parameter should be used with a single File object. To upload multiple files, the `files` parameter should be used with a `list` of `File` objects. Specifying both parameters will lead to an exception.\n
        `NOTE:` Using `file` - await channel.send(file=discord.File('my_file.png')) or 
            with open('my_file.png', 'rb') as fp:
                await channel.send(file=discord.File(fp, 'new_filename.png')) 
        `NOTE:` Using `files` - my_files = [discord.File('result.zip'), discord.File('teaser_graph.png')] await channel.send(files=my_files)"""

        self.botLogger.info('Member Send Message Called...')
        await parameter.send(content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after, nonce=nonce, allowed_mentions=allowed_mentions, reference=reference)

    async def messageAddReaction(self,message: discord.message, reaction_id:str):
        """The name and ID of a custom emoji can be found with the client by prefixing ':custom_emoji:' with a backslash. \n
            For example, sending the message '\:python3:' with the client will result in '<:python3:232720527448342530>'.
            `NOTE` Can only use Emoji's the bot has access too"""

        self.botLogger.info('Message Add Reaction Called...')
        if reaction_id.isnumeric():
            emoji = self._client.get_emoji(int(reaction_id))

        if not reaction_id.startswith('<') and not reaction_id.endswith('>'):
            emoji = discord.utils.get(self._client.emojis, name= reaction_id)

        else:
            emoji = reaction_id

        await message.add_reaction(emoji)

    async def cog_load(self,context,cog:str):
        try:
            self._client.load_extension(name= cog)
        except Exception as e:
            await context.send(f'**ERROR** Loading Extension {cog} - {e}')
        else:
            await context.send(f'**SUCCESS** Loading Extension {cog}')
        
    async def cog_unload(self,context,cog:str):
        try:
            self._client.unload_extension(name= cog)
        except Exception as e:
            await context.send(f'**ERROR** Un-Loading Extension {cog} - {e}')
        else:
            await context.send(f'**SUCCESS** Un-Loading Extension {cog}')

class botUtils():
        def __init__ (self,client):
            self._client = client
            self.logger = logging.getLogger(__name__)
            self.logger.info('Bot Utilities Loaded')
            self.DB = DB.getDatabase()
            self.AMPInstances = AMP.AMP_Instances

        async def roleparse(self,context,guild_id:int,parameter:str): 
            """This is the bot utils Role Parse Function\n
            It handles finding the specificed Discord `<role>` in multiple different formats.\n
            They can contain single quotes, double quotes and underscores. (" ",' ',_)\n
            returns `<role>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.info('Role Parse Called...')
            #print(dir(self._client),self._client.get_guild(guild_id),guild_id)
            guild = self._client.get_guild(guild_id)
            role_list = guild.roles
            
            #Role ID catch
            if parameter.isnumeric():
                role = guild.get_role(int(parameter))
                self.logger.debug('Found the Discord Role {role}')
                return role
            else:
                #This allows a user to pass in a role in quotes double or single
                if parameter.find("'") != -1 or parameter.find('"'):
                    parameter = parameter.replace('"','')
                    parameter = parameter.replace("'",'')

                #If a user provides a role name; this will check if it exists and return the ID
                for role in role_list:
                    if role.name.lower() == parameter.lower():
                        self.logger.debug('Found the Discord Role {role}')
                        return role

                    #This is to handle roles with spaces
                    parameter.replace('_',' ')
                    if role.name.lower() == parameter.lower():
                        self.logger.debug('Found the Discord Role {role}')
                        return role
                await context.send(f'Unable to find the Discord Role: {parameter}')
                return None

        async def channelparse(self,context,guild_id:int,parameter:str):
            """This is the bot utils Channel Parse Function\n
            It handles finding the specificed Discord `<channel>` in multiple different formats, either numeric or alphanumeric.\n
            returns `<channel>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.info('Channel Parse Called...')
            guild = self._client.get_guild(guild_id)

            channel_list = guild.channels
            if parameter.isnumeric():
                channel = guild.get_channel(int(parameter))
                self.logger.debug('Found the Discord Channel {channel}')
                return channel
            else:
                for channel in channel_list:
                    if channel.name == parameter:
                        self.logger.debug('Found the Discord Channel {channel}')
                        return channel
                else:
                    self.logger.error('Unable to Find the Discord Channel')
                    await context.send(f'Unable to find the Discord Channel: {parameter}')
                    return None
        
        async def userparse(self,context,guild_id:int,parameter: str):
            """This is the bot utils User Parse Function\n
            It handles finding the specificed Discord `<user>` in multiple different formats, either numeric or alphanumeric.\n
            It also supports '@', '#0000' and partial display name searching for user indentification (eg. k8thekat#1357)\n
            returns `<user>` object if True, else returns `None`
            **Note** Use context.guild.id"""
            self.logger.info('User Parse Called...')
            guild = self._client.get_guild(guild_id)
            #Discord ID catch
            if parameter.isnumeric():
                cur_member = guild.get_member(int(parameter))
                self.logger.debug('Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Profile Name Catch
            if parameter.find('#') != -1:
                cur_member = guild.get_member_named(parameter)
                self.logger.debug('Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Using @ at user and stripping
            if parameter.startswith('<@!') and parameter.endswith('>'):
                user_discordid = parameter[3:-1]
                cur_member = guild.get_member(int(user_discordid))
                self.logger.debug('Found the Discord Member {cur_member.display_name}')
                return cur_member

            #DiscordName/IGN Catch(DB Get user can look this up)
            cur_member = guild.get_member_named(parameter)
            if cur_member != None:
                self.logger.debug('Found the Discord Member {cur_member.display_name}')
                return cur_member

            #Display Name Lookup
            else:
                cur_member = None
                for member in guild.members:
                    if member.display_name.lower().startswith(parameter.lower()) or (member.display_name.lower().find(parameter.lower()) != -1):
                        if cur_member != None:
                            self.logger.error('Found multiple Discord Members: {parameter}, Returning None')
                            await context.send('Found multiple Discord Members matching that name, please be more specific.')
                            return None

                        self.logger.debug('Found the Discord Member {member.display_name}')
                        cur_member = member
                return cur_member
                
        async def serverparse(self,context,guild_id:int,parameter):
            """This is the botUtils Server Parse function.
            **Note** Use context.guild.id \n
            Returns `AMPInstance[server] <object>`"""
            self.logger.info('Bot Utility Server Parse')
            cur_server = None
            print(parameter)
            if type(parameter) == tuple:
                parameter = ' '.join(parameter)
            parameter = parameter.replace(' ','_').replace("'",'').replace('"','')
            print(parameter)
            for server in self.AMPInstances:
                var = self.AMPInstances[server].FriendlyName.lower().find(parameter.lower())

                if var != -1:
                    if cur_server != None:
                        self.logger.error('Found multiple AMP Servers matching the provided name: {parameter}. Returning None')
                        await context.send('Found multiple AMP Servers matching the provided name, please be more specific.')
                        return None

                    self.logger.debug(f'Found the AMP Server {self.AMPInstances[server].FriendlyName}')
                    cur_server = self.AMPInstances[server]

            return cur_server #AMP instance object 

        def sub_command_handler(self,command:str,sub_command):
            """This will get the `Parent` command and then add a `Sub` command to said `Parent` command."""
            parent_command = self._client.get_command(command)
            self.logger.info(f'Loading Parent Command: {parent_command}')
            parent_command.add_command(sub_command)
        
        def default_embedmsg(self,context,title,description=None,field=None,field_value=None):
            embed=discord.Embed(title=title, description=description, color=0x808000)
            embed.set_author(name=context.author.display_name, icon_url=context.author.avatar)
            embed.add_field(name=field, value=field_value, inline=False)
            return embed
           
        def server_status_embed(self,context,server,TPS,Users,CPU,Memory,Uptime,Users_Online):
            embed=discord.Embed(title=f'{server.FriendlyName}', description='Server Stats', color=0x00ff40)
            embed.set_thumbnail(url=context.guild.icon)
            embed.add_field(name='TPS', value=TPS, inline=True)
            embed.add_field(name='Player Count', value=f'{Users[0]}/{Users[1]}', inline=True)
            embed.add_field(name='Memory Usage', value=f'{Memory[0]}/{Memory[1]}', inline=False)
            embed.add_field(name='CPU Usage', value=f'{CPU}/100%', inline=True)
            embed.add_field(name='Uptime', value=Uptime, inline=True)
            embed.add_field(name='Players Online', value=Users_Online, inline=False)
            return embed

