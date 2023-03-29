from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from discord.ui import Button
from discord import ButtonStyle, Interaction, Message, ButtonStyle

from utils.banner_editor.ui.modal import Copy_To_Modal
from utils.banner_editor.util import banner_file_handler
from utils.banner_creator import Banner_Generator
from utils.banner_editor.edited_banner import Edited_DB_Banner

if TYPE_CHECKING:
    from amp_instance import AMPInstance
    from amp_handler import AMPHandler


class Copy_To_Banner_Button(Button):
    """Coppies the current banner settings to the Text Input server."""

    def __init__(self, *, edited_banner: Edited_DB_Banner) -> None:
        super().__init__(style=ButtonStyle.blurple, label="Copy to..", emoji="\U000027a1")
        self._edited_banner: Edited_DB_Banner = edited_banner  # We need this for our view to copy the settings accross. So to the Modal first it goes.

    async def callback(self, interaction: Interaction) -> None:
        prompt: Copy_To_Modal = Copy_To_Modal(self._edited_banner)
        await interaction.response.send_modal(prompt)


class Save_Banner_Button(Button):
    """Saves the Banners current settings to the DB."""

    def __init__(self, banner_message: Message, server: AMPInstance, edited_banner: Edited_DB_Banner, style=ButtonStyle.green):
        super().__init__(label='Save', style=style, custom_id='Save_Button')
        self.logger = logging.getLogger()
        self._amp_server = server
        self._banner_message = banner_message
        self._edited_db_banner = edited_banner

    async def callback(self, interaction: Interaction):
        """This is called when a button is interacted with."""
        saved_banner = self._edited_db_banner.save_db()
        await interaction.response.defer()
        file = banner_file_handler(Banner_Generator(self._amp_server, saved_banner)._image_())
        await self._banner_message.edit(content='**Banner Settings have been saved.**', attachments=[file], view=None)


class Reset_Banner_Button(Button):
    """Resets the Banners current settings to the original DB."""

    def __init__(self, banner_message: Message, server: AMPInstance, edited_banner: Edited_DB_Banner, style=ButtonStyle.blurple):
        super().__init__(label='Reset', style=style, custom_id='Reset_Button')
        self.logger = logging.getLogger()
        self._amp_server = server
        self._banner_message = banner_message
        self._edited_db_banner = edited_banner

    async def callback(self, interaction: Interaction):
        """This is called when a button is interacted with."""
        saved_banner = self._edited_db_banner.reset_db()
        await interaction.response.defer()
        file = banner_file_handler(Banner_Generator(self._amp_server, saved_banner)._image_())
        await self._banner_message.edit(content='**Banner Settings have been reset.**', attachments=[file])


class Cancel_Banner_Button(Button):
    """Cancels the Banner Settings View"""

    def __init__(self, banner_message: Message, style=ButtonStyle.red):
        super().__init__(label='Cancel', style=style, custom_id='Cancel_Button')
        self.logger = logging.getLogger()
        self._banner_message = banner_message

    async def callback(self, interaction: Interaction):
        """This is called when a button is interacted with."""
        await interaction.response.defer()
        await self._banner_message.edit(content='**Banner Settings Editor has been Cancelled.**', attachments=[], view=None)


class Copy_To_All_Banner_Button(Button):
    """Copies the current banner settings to all Banners in the DB."""

    def __init__(self, banner_message: Message, edited_banner: Edited_DB_Banner, amp_handler: AMPHandler, amp_server: AMPInstance, style=ButtonStyle.secondary):
        super().__init__(style=style, label='Copy to All', custom_id='Copy to All')
        self._banner_message = banner_message
        self._edited_db_banner = edited_banner
        self._amp_handler: AMPHandler = amp_handler
        self._amp_instances = amp_handler._AMP_Instances
        self._amp_server = amp_server

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        self._edited_db_banner.save_db()
        await self._banner_message.edit(content=f'Copying settings...', attachments=[], view=None)

        for instanceid, object in self._amp_instances.items():
            #db_banner:DBBanner = self._db.GetServer(InstanceID=id).getBanner()
            # We update the Edited Banners ID and then write out its `attrs` so the DB is updated via `__setattr__`

            self._edited_db_banner.ServerID = self._amp_handler.DB.GetServer(InstanceID=instanceid).ID
            Edited_DB_Banner(db_banner=self._edited_db_banner).save_db()

        await self._banner_message.edit(content=f'Copied **{self._amp_server.InstanceName}** Banner settings to all other Server Banners.', attachments=[], view=None)
