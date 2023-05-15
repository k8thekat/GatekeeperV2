from __future__ import annotations
import logging
from typing import TYPE_CHECKING

from discord.ui import Select
from discord import Interaction, SelectOption, Message, utils

from utils.banner_editor.edited_banner import Edited_DB_Banner
from utils.banner_editor.ui.modal import Banner_Modal
from amp_handler import AMPHandler

if TYPE_CHECKING:
    from DB import DBServer
    from amp_instance import AMPInstance
    from utils.banner_editor.ui.view_editor import Banner_Editor_View


class Copy_To_Select(Select):
    def __init__(self, *, options: dict[str, str], edited_banner: Edited_DB_Banner) -> None:
        self._edited_banner: Edited_DB_Banner = edited_banner
        self._amp_handler: AMPHandler = AMPHandler()
        self._select_options: list[SelectOption] = []
        # In this scenarion; the options aka AMP Instances come as {"InstanceID": "Instance Name"}
        for instanceid, instancename in options.items():
            cur: SelectOption = SelectOption(label=instancename, value=instanceid)
            self._select_options.append(cur)

        super().__init__(min_values=1, max_values=1, placeholder="Please select an Instance Name", options=self._select_options)

    async def callback(self, interaction: Interaction) -> None:
        # TODO -- This still needs to be tested.
        select_option = utils.get(self._select_options, value=self.values[0])
        if isinstance(select_option, SelectOption):
            server = select_option.label
        else:
            server = self.values[0]
        await interaction.response.send_message(content=f"You selected **{server}**\n> Copying Settings... ")
        db_server: DBServer | None = self._amp_handler._DB.GetServer(InstanceID=self.values[0])
        if db_server != None:
            self._edited_banner.ServerID = db_server.ID

        Edited_DB_Banner(db_banner=self._edited_banner).save_db()
        await interaction.edit_original_response(content=f'All finished.')


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
