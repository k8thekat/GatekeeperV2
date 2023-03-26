from __future__ import annotations
from amp import AMPInstance
from utils.check import validate_avatar

from discord.ext import commands
from discord import Embed, Role
from db import DBHandler, DBServer

from typing import Union

# FIXME -- Possible query the API Inside this embed instead of passing in the vars. Oof...


async def server_status_embed(context: commands.Context, server: AMPInstance) -> Union[Embed, None]:
    """This is the Server Status Embed Message"""
    _db_handler: DBHandler = DBHandler()
    db_server: DBServer | None = None
    TPS, USERS, CPU, MEMORY, UPTIME = server.getMetrics()
    Users_online = ', '.join(server.getUserList())

    if len(Users_online) == 0:
        Users_online = 'None'

    if type(server.InstanceID) == str:
        db_server = _db_handler.DB.GetServer(InstanceID=server.InstanceID)

    if not isinstance(db_server, DBServer):
        return None

    if server.Running:
        instance_status: str = 'Online'
    else:
        instance_status: str = 'Offline'

    if server._App_Running:
        server_status: str = 'Online'
    else:
        server_status: str = 'Offline'

    embed_color = 0x71368a
    if db_server.Discord_Role != None:  # FIXME Need to add an `attr` to DBServer called `Discord_Role` This should also fix line 37.
        db_server_role: Role | None = context.guild.get_role(int(db_server.Discord_Role))
        if db_server_role != None:
            embed_color = db_server_role.color

    server_name: None = server.FriendlyName
    if server.DisplayName != None:
        server_name = db_server.DisplayName  # FIXME Need to add an `attr` to DBServer called `DisplayName`

    embed: Embed = Embed(title=f"{server_name} - [{server._TargetName}]", description=f'Instance Server Status: **{instance_status}**', color=embed_color)

    avatar: str | None = await validate_avatar(db_server)
    if avatar != None:
        embed.set_thumbnail(url=avatar)

    embed.add_field(name='**Dedicated Server Status**:', value=server_status, inline=True)

    if db_server.Host != None:  # FIXME Need to add an `attr` to DBServer called `Host` Same for line 54
        embed.add_field(name=f'Host: ', value=db_server.Host, inline=True)

    # embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False)
    embed.add_field(name='Donator Only:', value=str(bool(db_server.Donator)), inline=True)
    embed.add_field(name='Whitelist Open:', value=str(bool(db_server.Whitelist)), inline=True)
    # embed.add_field(name='\u1CBC\u1CBC',value='\u1CBC\u1CBC',inline=False) #This Generates a BLANK Field entirely.

    if server._App_Running:
        embed.add_field(name='TPS', value=TPS, inline=True)
        embed.add_field(name='Player Count', value=f'{USERS[0]}/{USERS[1]}', inline=True)
        embed.add_field(name='Memory Usage', value=f'{MEMORY[0]}/{MEMORY[1]}', inline=True)
        embed.add_field(name='CPU Usage', value=f'{CPU}/100%', inline=True)
        # FIXME Uptime is disabled until AMP Impliments the feature. Possible add my own Uptime value and compare time.. etc..
        #embed.add_field(name='Uptime', value=Uptime, inline=True)
        embed.add_field(name='Players Online', value=Users_online, inline=True)
    embed.set_footer(text=f'InstanceID: {server.InstanceID}')
    return embed


async def server_info_embed(server: AMP_Handler.AMP.AMPInstance, context: commands.Context) -> discord.Embed:
    """For Individual Server info embed replies"""
    db_server = self.DB.GetServer(InstanceID=server.InstanceID)
    server_name = db_server.InstanceName
    if db_server.DisplayName != None:
        server_name = db_server.DisplayName

    embed = discord.Embed(title=f'__**{server_name}**__ - {[server._TargetName]}', color=0x00ff00, description=server.Description)

    discord_role = db_server.Discord_Role
    if discord_role != None:
        discord_role = context.guild.get_role(int(db_server.Discord_Role)).name

    avatar = await validate_avatar(db_server)
    if avatar != None:
        embed.set_thumbnail(url=avatar)

    embed.add_field(name=f'Host:', value=str(db_server.Host), inline=False)
    embed.add_field(name='Donator Only:', value=str(bool(db_server.Donator)), inline=True)
    embed.add_field(name='Whitelist Open:', value=str(bool(db_server.Whitelist)), inline=True)
    embed.add_field(name='Role:', value=str(discord_role), inline=False)
    embed.add_field(name='Hidden', value=bool(db_server.Hidden), inline=True)
    embed.add_field(name='Whitelist Hidden', value=bool(db_server.Whitelist_disabled), inline=True)

    embed.add_field(name='Filtered Console:', value=str(bool(db_server.Whitelist)), inline=False)
    embed.add_field(name='Console Filter Type:', value=bool(db_server.Console_Filtered_Type), inline=True)
    if db_server.Discord_Console_Channel != None:
        discord_channel = context.guild.get_channel(db_server.Discord_Console_Channel)
        embed.add_field(name='Console Channel:', value=discord_channel.name, inline=False)
    else:
        embed.add_field(name='Console Channel:', value=db_server.Discord_Console_Channel, inline=False)

    embed.add_field(name='Discord Chat Prefix:', value=str(db_server.Discord_Chat_Prefix), inline=False)
    if db_server.Discord_Chat_Channel != None:
        discord_channel = context.guild.get_channel(db_server.Discord_Chat_Channel)
        embed.add_field(name='Chat Channel:', value=discord_channel.name, inline=True)
    else:
        embed.add_field(name='Chat Channel:', value=db_server.Discord_Chat_Channel, inline=True)

    if db_server.Discord_Event_Channel != None:
        discord_channel = context.guild.get_channel(db_server.Discord_Event_Channel)
        embed.add_field(name='Event Channel:', value=discord_channel.name, inline=True)
    else:
        embed.add_field(name='Event Channel:', value=db_server.Discord_Event_Channel, inline=True)
    embed.set_footer(text=f'InstanceID: {server.InstanceID}')
    return embed


async def server_display_embed(server_list: list[DB.DBServer], guild: discord.Guild = None) -> list[discord.Embed]:
    """Used for Banner Groups and Display"""
    embed_list = []
    for db_server in server_list:
        server = self.AMPInstances[db_server.InstanceID]

        # If no DB Server or the Server is Hidden; skip.
        if db_server == None or db_server.Hidden == 1:
            continue

        instance_status = '\U0000274c Offline'
        dedicated_status = 'Offline'
        Users = None
        User_list = None
        # This is for the Instance
        if server.Running:
            instance_status = 'Online'
            # ADS AKA Application status
            if server._ADScheck() and server._App_Running:
                dedicated_status = 'Online'
                Users = server.getUsersOnline()
                if len(server.getUserList()) >= 1:
                    User_list = (', ').join(server.getUserList())

        embed_color = 0x71368a
        if guild != None and db_server.Discord_Role != None:
            db_server_role = guild.get_role(int(db_server.Discord_Role))
            if db_server_role != None:
                embed_color = db_server_role.color

        server_name = server.FriendlyName
        if server.DisplayName != None:
            server_name = db_server.DisplayName

        embed = discord.Embed(title=f'**=======  {server_name}  =======**', description=server.Description, color=embed_color)
        # This is for future custom avatar support.
        avatar = await validate_avatar(db_server)
        if avatar != None:
            embed.set_thumbnail(url=avatar)
        embed.add_field(name='**Instance Status**:', value=instance_status, inline=False)
        embed.add_field(name='**Dedicated Server Status**:', value=dedicated_status, inline=False)
        embed.add_field(name='**Host**:', value=str(db_server.Host), inline=True)
        embed.add_field(name='**Donator Only**:', value=str(bool(db_server.Donator)), inline=True)
        embed.add_field(name='**Whitelist Open**:', value=str(bool(db_server.Whitelist)), inline=True)
        if Users != None:
            embed.add_field(name=f'**Players**:', value=f'{Users[0]}/{Users[1]}', inline=True)
        else:
            embed.add_field(name='**Player Limit**:', value=str(Users), inline=True)
        embed.add_field(name='**Players Online**:', value=str(User_list), inline=False)
        embed.set_footer(text=discord.utils.utcnow().strftime('%Y-%m-%d | %H:%M'))
        embed_list.append(embed)

    return embed_list
