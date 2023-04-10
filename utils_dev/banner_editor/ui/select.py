from __future__ import annotations
import logging


from discord.ui import Select
from discord import Interaction, SelectOption, Message
from typing import TYPE_CHECKING

from utils_dev.banner_editor.edited_banner import Edited_DB_Banner

from utils_dev.banner_editor.ui.modal import Banner_Modal

if TYPE_CHECKING:
    from AMP import AMPInstance
    from utils_dev.banner_editor.edited_banner import Edited_DB_Banner
    from utils_dev.banner_editor.ui.view import Banner_Editor_View


class Banner_Editor_Select(Select):
    def __init__(self, edited_db_banner: Edited_DB_Banner, view: Banner_Editor_View, amp_server: AMPInstance, banner_message: Message, custom_id: str = None, min_values: int = 1, max_values: int = 1, row: int = None, disabled: bool = False, placeholder: str = None):
        self.logger = logging.getLogger()
        options = []
        self._banner_view = view

        self._edited_db_banner = edited_db_banner
        self._banner_message = banner_message

        self._amp_server = amp_server

        whitelist_options = [
            SelectOption(label="Whitelist Open Font Color", value='color_whitelist_open'),
            SelectOption(label="Whitelist Closed Font Color", value='color_whitelist_closed')]
        donator_options = [
            SelectOption(label="Donator Font Color", value='color_donator')]

        options = [
            SelectOption(label="Blur Background Intensity", value='blur_background_amount'),
            SelectOption(label="Header Font Color", value='color_header'),
            SelectOption(label="Body Font Color", value='color_body'),
            SelectOption(label="Host Font Color", value='color_host'),

            SelectOption(label="Server Online Font Color", value='color_status_online'),
            SelectOption(label="Server Offline Font Color", value='color_status_offline'),
            SelectOption(label="Player Limit Minimum Font Color", value='color_player_limit_min'),
            SelectOption(label="Player Limit Maximum Font Color", value='color_player_limit_max'),
            SelectOption(label="Players Online Font Color", value='color_player_online')
        ]

        # If Whitelist is disabled, remove the options from the list.
        if not self._amp_server.Whitelist_disabled:
            options = whitelist_options + options

        # If Donator Only is enabled; adds the option to set the color.
        if self._amp_server.Donator:
            options = options + donator_options

        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)

    async def callback(self, interaction: Interaction):
        if self.values[0] == 'blur_background_amount':
            input_type = 'int'
        else:
            input_type = 'color'

        self._banner_modal = Banner_Modal(input_type=input_type, title=f'{self.values[0].replace("_", " ")}', select_value=self.values[0], edited_db_banner=self._edited_db_banner, banner_message=self._banner_message, view=self._banner_view, amp_server=self._amp_server)
        await interaction.response.send_modal(self._banner_modal)

        self._first_interaction = False
