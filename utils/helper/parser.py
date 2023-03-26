from discord import Role, Guild, TextChannel, Member, VoiceChannel, User
from discord.ext import commands

from typing import Text, Union, Sequence
import logging
import difflib

from amp import AMPInstance
from Gatekeeper import Gatekeeper
from utils.context import GatekeeperGuildContext
from amp_handler import AMPHandler


def role_parse(parameter: str, context: GatekeeperGuildContext) -> Union[Role, None]:
    """This is the bot utils Role Parse Function\n
    It handles finding the specificed Discord `<role>` in multiple different formats.\n
    They can contain single quotes, double quotes and underscores. (" ",' ',_)\n
    returns `<role>` object if True, else returns `None`
    **Note** Use context.guild.id"""
    _logger = logging.getLogger()
    _logger.dev('Role Parse Called...')  # type:ignore

    guild: Guild | None = context.guild
    if isinstance(guild, Guild):
        role_list: Sequence[Role] = guild.roles
    else:
        return None

    # Role ID catch
    if parameter.isnumeric():
        role = guild.get_role(int(parameter))
        _logger.debug(f'Found the Discord Role {role}')
        return role
    else:
        # This allows a user to pass in a role in quotes double or single
        if parameter.find("'") != -1 or parameter.find('"'):
            parameter = parameter.replace('"', '')
            parameter = parameter.replace("'", '')

        # If a user provides a role name; this will check if it exists and return the ID
        for role in role_list:
            if role.name.lower() == parameter.lower():
                _logger.debug(f'Found the Discord Role {role}')
                return role

            # This is to handle roles with spaces
            parameter.replace('_', ' ')
            if role.name.lower() == parameter.lower():
                _logger.debug(f'Found the Discord Role {role}')
                return role

        # await context.reply(f'Unable to find the Discord Role: {parameter}')
        return None


def channel_parse(channel_name: Union[str, None], channel_id: Union[int, None], context: GatekeeperGuildContext) -> Union[TextChannel, VoiceChannel, None]:
    """This is the bot utils Channel Parse Function\n
    It handles finding the specificed Discord `<channel>` in multiple different formats, either numeric or alphanumeric.\n
    returns `<channel>` object if True, else returns `None`
    **Note** Use context.guild.id"""
    _logger = logging.getLogger()
    _logger.dev('Channel Parse Called...')  # type:ignore

    if channel_name == None and channel_id != None:
        channel = context.guild.get_channel(channel_id)
        if isinstance(channel, TextChannel):
            _logger.dev(f'Found the Discord Channel {channel.name}')  # type:ignore
            return channel

    if channel_id == None and channel_name != None:
        channel_list = context.guild.channels

        for channel in channel_list:
            # This should attempt to find a close match; difflib sorts the list with best match at top of list. So we return index [0].
            result: list[str] = difflib.get_close_matches(channel_name, channel.name, n=5)
            if result[0] and isinstance(channel, Union[TextChannel, VoiceChannel]):
                _logger.dev(f'Found a Match; {channel.name} is the closests match to {channel_name}')  # type:ignore
                return channel
        return None


def user_parse(user_name: Union[str, None], user_id: Union[int, None], context: GatekeeperGuildContext, client: Union[Gatekeeper, None]) -> Union[Member, User, None]:
    """This is the bot utils User Parse Function\n
    It handles finding the specificed Discord `<user>` in multiple different formats, either numeric or alphanumeric.\n
    It also supports '@', '#0000' and partial display name searching for user indentification (eg. k8thekat#1357)\n
    returns `<user>` object if True, else returns `None`
    **Note** Use client for "NON" guild searchs"""
    _logger = logging.getLogger()
    _logger.dev('User Parse Called...')  # type:ignore

    # if we are using the commands.Bot object; we can use  `get_user`
    if isinstance(client, commands.Bot):
        if user_name == None and user_id != None:
            possible_user: User | Member | None = client.get_user(user_id)
            if isinstance(possible_user, User):
                return possible_user
            else:
                return possible_user

    # if no commands.Bot object; we can use context and attempt to match via `get_member_named` if that fails;
    # lets do a partial match lookup using difflib and use the top result as our member object.
    if user_name != None and user_id == None:
        # first lets try to find an exact match.
        possible_user = context.guild.get_member_named(user_name)
        if isinstance(possible_user, Member):
            return possible_user

        else:
            guild_members = list(member.name for member in context.guild.members)
            results: list[str] = difflib.get_close_matches(user_name, guild_members, n=5)
            # Use the top result as an attempt to get a member object.
            possible_user = context.guild.get_member_named(results[0])
            if isinstance(possible_user, Member):
                _logger.dev(f'Found the Discord Member {possible_user.name}')  # type:ignore
                return possible_user
            return possible_user


def serverparse(instanceID=str) -> Union[AMPInstance, None]:
    """This is the botUtils Server Parse function.
    **Note** Use context.guild.id \n
    Returns `AMPInstance[server] <object>`"""
    _logger = logging.getLogger()
    _logger.dev('Bot Utility Server Parse')  # type:ignore
    cur_server: Union[AMPInstance, None] = None
    for instanceid, amp_object in AMPHandler().AMP_Instances.items():
        if instanceid == instanceID:
            cur_server = amp_object
            _logger.dev(f'Selected Server is {amp_object.InstanceName} - InstanceID: {instanceid}')  # type:ignore
            return cur_server

    return cur_server
