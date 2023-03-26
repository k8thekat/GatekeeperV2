
from discord.ext import commands
from discord import Guild
from amp import AMPInstance

from typing import Union


def whitelist_reply_handler(message: str, context: commands.Context, server: Union[AMPInstance, None]) -> str:
    """Handles the reply message for the whitelist event\n
    Supports the following: \n
    `<user>` - Uses the Message Author's Name/IGN \n
    `<server>` - Uses the AMP Server Name \n 
    `<guild>` - Uses the Guild Name \n"""

    if message.find('<user>') != -1:
        message = message.replace('<user>', context.author.name)

    if message.find('<guild>') != -1:
        if isinstance(context.guild, Guild):
            message = message.replace('<guild>', context.guild.name)

    if server is not None and message.find('<server>') != -1:
        server_name: str = server.FriendlyName or server.InstanceName
        if server.DisplayName != None:
            server_name = server.DisplayName
        message = message.replace('<server>', server_name)

    return message
