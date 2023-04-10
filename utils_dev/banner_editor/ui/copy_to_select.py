from discord.ui import Select
from discord import SelectOption, Interaction, utils
from numpy import delete
from DB import DBServer
from ..edited_banner import Edited_DB_Banner
import AMP_Handler
from AMP_Handler import AMPHandler


class Copy_To_Select(Select):
    def __init__(self, *, options: dict[str, str], edited_banner: Edited_DB_Banner) -> None:
        self._edited_banner: Edited_DB_Banner = edited_banner
        self._amp_handler: AMPHandler = AMP_Handler.getAMPHandler()
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
        await interaction.response.send_message(content=f"You selected **{server}**\n> Copying Settings... ", ephemeral=True, delete_after=60)
        db_server: DBServer | None = self._amp_handler.DB.GetServer(InstanceID=self.values[0])
        if db_server != None:
            self._edited_banner.ServerID = db_server.ID
        Edited_DB_Banner(db_banner=self._edited_banner).save_db()
        await interaction.edit_original_response(content=f'All finished.')
