from discord.ui import View
from discord.ext import commands
from discord import Message

from Gatekeeper import Gatekeeper
from amp import AMPInstance
import db
from db import Database
from utils.whitelist.ui.button import Accept_Whitelist_Button, Deny_Whitelist_Button
from utils.whitelist.base import whitelist_reply_handler
from utils.helper.parser import user_parse, role_parse


import random
from typing import Union
import logging


class Whitelist_view(View):
    """Whitelist Request View"""

    def __init__(self, client: Gatekeeper, discord_message: Message, whitelist_message: Message, amp_server: AMPInstance, context: commands.Context, timeout: Union[float, None] = None):
        self._logger = logging.getLogger()  # type:ignore
        self._DB: Database = db.getDBHandler().DB
        self._client: Gatekeeper = client
        self._context = context
        self._whitelist_message: Message = whitelist_message
        self._amp_server: AMPInstance = amp_server

        # This is for when Auto-Whitelisting is Disabled to prevent the View from timing out...
        if timeout != None:
            # Converts my Minutes value I pass in into seconds which is what `Views` rely on..
            timeout: float = (timeout * 60)

        super().__init__(timeout=timeout)
        self.add_item(Accept_Whitelist_Button(discord_message=discord_message, view=self, client=client, amp_server=amp_server))
        self.add_item(Deny_Whitelist_Button(discord_message=discord_message, view=self, client=client, amp_server=amp_server))

    async def _whitelist_handler(self):
        db_server = self.DB.GetServer(self._amp_server.InstanceID)
        self.logger.dev(f'Whitelist Request; Attempting to Whitelist {self._whitelist_message.author.name} on {db_server.FriendlyName}')
        # This handles all the Discord Role stuff.
        if db_server != None and db_server.Discord_Role != None:
            discord_role = role_parse(db_server.Discord_Role, self._context, self._context.guild.id)
            discord_user = user_parse(self._context.author.id, self._context, self._context.guild.id)
            await discord_user.add_roles(discord_role, reason='Auto Whitelisting')

        # This is for all the Replies
        if len(self.DB.GetAllWhitelistReplies()) != 0:
            whitelist_reply = random.choice(self.DB.GetAllWhitelistReplies())
            await self._context.message.channel.send(content=f'{self._context.author.mention} \n{whitelist_reply_handler(message= whitelist_reply, context= self._context, server= self._amp_server)}', delete_after=self._client.Message_Timeout)
        else:
            await self._context.message.channel.send(content=f'You are all set! We whitelisted {self._context.author.mention} on **{db_server.FriendlyName}**', delete_after=self._client.Message_Timeout)
