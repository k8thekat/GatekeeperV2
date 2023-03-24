from discord.ui import View
from discord.ext import commands

from AMP import AMPInstance
from utils.amp_server.button import StartButton, StopButton, RestartButton, KillButton


class StatusView(View):
    def __init__(self, context: commands.Context, amp_server: AMPInstance, timeout=180):
        super().__init__(timeout=timeout)
        #self.context = context
        self.add_item(StartButton(amp_server, self, amp_server.StartInstance))
        self.add_item(StopButton(amp_server, self, amp_server.StopInstance))
        self.add_item(RestartButton(amp_server, self, amp_server.RestartInstance))
        self.add_item(KillButton(amp_server, self, amp_server.KillInstance))

    async def on_timeout(self):
        """This Removes all the Buttons after timeout has expired"""
        self.stop()
