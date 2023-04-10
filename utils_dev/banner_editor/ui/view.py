from __future__ import annotations

from discord.ui import View
from discord import Message, Interaction


import logging

from typing import TYPE_CHECKING
from utils_dev.banner_editor.edited_banner import Edited_DB_Banner
from utils_dev.banner_editor.ui.select import Banner_Editor_Select
from utils_dev.banner_editor.ui.button import Save_Banner_Button, Reset_Banner_Button, Cancel_Banner_Button, Copy_To_All_Banner_Button, Copy_To_Banner_Button


if TYPE_CHECKING:
    from AMP import AMPInstance
    from AMP_Handler import AMPHandler
    from DB import DBBanner


class Banner_Editor_View(View):
    def __init__(self, amp_handler: AMPHandler, amp_server: AMPInstance, db_banner: DBBanner, banner_message: Message, timeout=None):
        self._logger = logging.getLogger()

        self._original_db_banner: DBBanner = db_banner
        self._edited_db_banner: Edited_DB_Banner = Edited_DB_Banner(db_banner)
        self._banner_message: Message = banner_message  # This is the message that the banner is attached to.
        self._amp_server: AMPInstance = amp_server
        self._amp_handler: AMPHandler = amp_handler
        self._first_interaction = Interaction
        self._first_interaction_bool: bool = True

        self._banner_editor_select = Banner_Editor_Select(custom_id='banner_editor', edited_db_banner=self._edited_db_banner, banner_message=self._banner_message, view=self, amp_server=self._amp_server)
        super().__init__(timeout=timeout)
        self.add_item(self._banner_editor_select)
        self.add_item(Save_Banner_Button(banner_message=self._banner_message, edited_banner=self._edited_db_banner, server=self._amp_server))
        self.add_item(Reset_Banner_Button(banner_message=self._banner_message, edited_banner=self._edited_db_banner, server=self._amp_server))
        self.add_item(Cancel_Banner_Button(banner_message=self._banner_message))
        self.add_item(Copy_To_Banner_Button(edited_banner=self._edited_db_banner))
        self.add_item(Copy_To_All_Banner_Button(banner_message=self._banner_message, edited_banner=self._edited_db_banner, amp_handler=self._amp_handler, amp_server=self._amp_server))
