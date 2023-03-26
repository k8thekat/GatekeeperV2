from __future__ import annotations
from discord import ButtonStyle
from discord.ui import Button

from utils.check import async_rolecheck
from amp import AMPInstance

import asyncio
import logging


class ServerButton(Button):
    """Custom Start Button for when Servers are Offline."""

    def __init__(self, server: AMPInstance, function, label: str, callback_label: str, callback_disabled: bool, style=ButtonStyle.green, context=None) -> None:
        super().__init__(label=label, style=style, custom_id=label)
        self.logger = logging.getLogger()
        self.server: AMPInstance = server
        self.context = context
        self._label: str = label
        self.permission_node: str = 'server.' + self._label.lower()

        self.callback_label: str = callback_label
        self.callback_disabled: bool = callback_disabled

        self._function = function

    async def callback(self, interaction):
        """This is called when a button is interacted with."""
        if not await async_rolecheck(interaction, self.permission_node):
            return interaction.response.send_message(content='You do not have permission to do that..', ephemeral=True, delete_after=30)
        self._interaction = interaction
        self.label = self.callback_label
        self.disabled = self.callback_disabled
        self._function()
        await interaction.response.edit_message(view=self._view)
        await asyncio.sleep(30)
        await self.reset()

    async def reset(self):
        self.logger.info('Resetting Buttons...')
        self.label = self._label
        self.disabled = False
        # server_embed = await self._view.update_view()
        await self._interaction.followup.edit_message(message_id=self._interaction.message.id, view=self._view)


class StartButton(ServerButton):
    def __init__(self, server, view, function) -> None:
        super().__init__(server=server, function=function, label='Start', callback_label='Starting...', callback_disabled=True, style=ButtonStyle.green)


class StopButton(ServerButton):
    def __init__(self, server, view, function) -> None:
        super().__init__(server=server, function=function, label='Stop', callback_label='Stopping...', callback_disabled=True, style=ButtonStyle.red)


class RestartButton(ServerButton):
    def __init__(self, server, view, function) -> None:
        super().__init__(server=server, function=function, label='Restart', callback_label='Restarting...', callback_disabled=True, style=ButtonStyle.blurple)


class KillButton(ServerButton):
    def __init__(self, server, view, function) -> None:
        super().__init__(server=server, function=function, label='Kill', callback_label='Killed...', callback_disabled=True, style=ButtonStyle.danger)
