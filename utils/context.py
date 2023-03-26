from __future__ import annotations

from typing import TYPE_CHECKING, Union

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from Gatekeeper import Gatekeeper

class GatekeeperContext(commands.Context["Gatekeeper"]):
    bot: Gatekeeper


class GatekeeperGuildContext(GatekeeperContext):
    author: discord.Member
    guild: discord.Guild
    channel: Union[discord.VoiceChannel, discord.TextChannel, discord.Thread]
    me: discord.Member