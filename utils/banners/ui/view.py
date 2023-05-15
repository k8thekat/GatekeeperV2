# This to house the View to send with each banner image
# Add a button for URLs and then possibly Whitelist (use a bool to determin display)


from typing import Optional
from discord.ui import View
from DB import DBServer


class Banner_View(View):
    def __init__(self, dbserver: DBServer, timeout: float | None = 180):
        self._dbserver = dbserver
        self._url: str = None
        self._whitelist: str = None
        super().__init__(timeout=timeout)
        # TODO - Check DB Server for a url - set that below and use that as the click link for the button.
        if self._dbserver.url != None:
            self.add_item()
            self._url = self._dbserver.url
