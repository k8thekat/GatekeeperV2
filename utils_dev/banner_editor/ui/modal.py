from __future__ import annotations
from discord.ui import Modal
from discord import Interaction, Message

from typing import Optional
import difflib

from git import TYPE_CHECKING

import AMP_Handler
from utils_dev.banner_editor.ui.textinput import Copy_To_TextInput, Banner_Color_Input, Banner_Blur_Input
from utils_dev.banner_editor.ui.view2 import Copy_To_View

from utils_ui import banner_file_handler
import modules.banner_creator as BC

if TYPE_CHECKING:
    from AMP import AMPInstance
    from utils_dev.banner_editor.edited_banner import Edited_DB_Banner
    from utils_dev.banner_editor.ui.view import Banner_Editor_View


class Copy_To_Modal(Modal):
    """Used for Copy To Button within the Banner Settings Editor View."""

    def __init__(self, edited_banner: Edited_DB_Banner, title: str = "Copy To Server", timeout: Optional[float] = None) -> None:
        super().__init__(title=title, timeout=timeout)
        self._edited_banner: Edited_DB_Banner = edited_banner  # Need to pass this along to our view...
        self._amp_instance_names: dict[str, str] = AMP_Handler.getAMPHandler().get_AMP_instance_names()
        self._txt_input: Copy_To_TextInput = Copy_To_TextInput()
        self.add_item(self._txt_input)

    async def on_submit(self, interaction: Interaction) -> None:
        result: list[str] = difflib.get_close_matches(self._txt_input.value, self._amp_instance_names.values(), n=5)

        # TODO need to generate our view with the results.
        result_options: dict[str, str] = {}
        for value in result:
            for instanceid in self._amp_instance_names:
                if self._amp_instance_names[instanceid] == value:
                    result_options[instanceid] = value
                    break

        copy_to_view: Copy_To_View = Copy_To_View(select_options=result_options, edited_banner=self._edited_banner)
        await interaction.response.send_message(content=f"{self._txt_input.value} was provided. Here is the matching Servers..", view=copy_to_view, ephemeral=True)
        # await interaction.response.defer()


class Banner_Modal(Modal):
    def __init__(self, input_type: str, select_value: str, title: str, view: Banner_Editor_View, edited_db_banner: Edited_DB_Banner, banner_message: Message, amp_server: AMPInstance, timeout=None, custom_id='Banner Modal'):
        self._edited_db_banner = edited_db_banner
        self._banner_message = banner_message
        self._banner_view = view

        self._amp_server = amp_server

        self._select_value = select_value  # This is the Select Option Choice that was made.
        self._input_type = input_type
        super().__init__(title=title, timeout=timeout, custom_id=custom_id)

        if self._input_type == 'color':
            self._color_code_input = Banner_Color_Input(edited_db_banner=self._edited_db_banner, select_value=self._select_value, view=self._banner_view)
            self.add_item(self._color_code_input)

        if self._input_type == 'int':
            self._int_code_input = Banner_Blur_Input(edited_db_banner=self._edited_db_banner, select_value=self._select_value, view=self._banner_view)
            self.add_item(self._int_code_input)

    async def on_submit(self, interaction: Interaction):
        # Depending on the Selection made; changes the validation code and the reply.
        if self._input_type == 'int':
            if await self._int_code_input.callback() == False:
                await interaction.response.send_message(f'Please provide a Number only. {self._int_code_input.value}', ephemeral=True)

        if self._input_type == 'color':
            if await self._color_code_input.callback() == False:
                await interaction.response.send_message(content=f'Please provide a proper Hex color Code. {self._color_code_input._value}', ephemeral=True)

        # Regardless we defer the interaction; because we only care if it fails as seen above.\
        if self._banner_view._first_interaction:
            await interaction.response.defer()
        # Then we send the updated Banner object to the View.
        await self._banner_message.edit(attachments=[banner_file_handler(BC.Banner_Generator(self._amp_server, self._edited_db_banner)._image_())], view=self._banner_view)
