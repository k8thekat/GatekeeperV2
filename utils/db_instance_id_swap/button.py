from __future__ import annotations

from discord.ui import Button, View
from discord import ButtonStyle, Interaction, Message

from utils.db_instance_id_swap.view import DB_Instance_ID_Swap


class Approve_Button(Button):
    def __init__(self, view: DB_Instance_ID_Swap, discord_message: Message, style=ButtonStyle.green):
        self._view: DB_Instance_ID_Swap = view
        self.message: Message = discord_message
        super().__init__(label='Approve', style=style, custom_id='Approve_Button')

    async def callback(self, interaction: Interaction) -> None:
        to_db_server_ID: str = self._view._to_db_server.InstanceID
        to_db_server_Name: str = self._view._to_db_server.InstanceName
        self._view._to_db_server.delServer()
        self._view._from_db_server.InstanceID = to_db_server_ID
        await self.message.edit(content=f'Replaced **{self._view._from_db_server.InstanceName} ID: {self._view._from_db_server.InstanceID}** with **{to_db_server_Name} ID: {to_db_server_ID}**', view=None)


class Cancel_Button(Button):
    def __init__(self, view: DB_Instance_ID_Swap, discord_message: Message, style=ButtonStyle.red) -> None:
        self._view: DB_Instance_ID_Swap = view
        self.message: Message = discord_message
        super().__init__(label='Cancel', style=style, custom_id='Cancel_Button')

    async def callback(self, interaction: Interaction) -> Message:
        return await self.message.edit(content=f'Cancelling change of **{self._view._from_db_server.InstanceName}** Instance ID. ', view=None)
