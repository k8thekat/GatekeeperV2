from utils.db_instance_id_swap.button import Approve_Button, Cancel_Button
from DB import DBServer

from discord import Message
from discord.ui import View


class DB_Instance_ID_Swap(View):
    """DB Instance ID Swap View"""

    def __init__(self, discord_message: Message, timeout: float, from_db_server: DBServer, to_db_server: DBServer) -> None:
        super().__init__(timeout=timeout)
        self._from_db_server: DBServer = from_db_server
        self._to_db_server: DBServer = to_db_server
        self.add_item(Approve_Button(view=self, discord_message=discord_message))
        self.add_item(Cancel_Button(view=self, discord_message=discord_message))
