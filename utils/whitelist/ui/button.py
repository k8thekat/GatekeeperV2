from discord.ui import Button
from discord import Interaction, Message, ButtonStyle


from amp import AMPInstance
from Gatekeeper import Gatekeeper
from utils.whitelist.ui.view import Whitelist_view
from utils.check import async_rolecheck


class Accept_Whitelist_Button(Button):
    """Accepts the Whitelist Request"""

    def __init__(self, discord_message: Message, view: Whitelist_view, client: Gatekeeper, amp_server: AMPInstance, style=ButtonStyle.green):
        super().__init__(label='Accept', style=style)
        self._view: Whitelist_view = view
        self._discord_message: Message = discord_message
        self._amp_server: AMPInstance = amp_server
        self._client: Gatekeeper = client

    async def callback(self, interaction: Interaction):
        if await async_rolecheck(context=interaction, perm_node='whitelist_buttons'):
            self._view._logger.info(f'We Accepted a Whitelist Request by {self._view._whitelist_message.author.name}')
            await self._discord_message.edit(content=f'**{interaction.user.name}** -> Approved __{self._view._whitelist_message.author.name}__ Whitelist Request', view=None)
            await self._view._whitelist_handler()
            self._amp_server.addWhitelist(self._client.Whitelist_wait_list[self._view._whitelist_message.id]['dbuser'])  # FIXME -- Need to fix this function when I finish refactoring AMPInstance #type:ignore
            self._client.Whitelist_wait_list.pop(self._view._whitelist_message.id)
            self.disabled = True


class Deny_Whitelist_Button(Button):
    """Denys the Whitelist Request"""

    def __init__(self, discord_message: Message, view: Whitelist_view, client: Gatekeeper, amp_server: AMPInstance, style=ButtonStyle.red):
        super().__init__(label='Deny', style=style)
        self._view: Whitelist_view = view
        self._discord_message: Message = discord_message
        self._amp_server: AMPInstance = amp_server
        self._client: Gatekeeper = client

    async def callback(self, interaction: Interaction):
        if await async_rolecheck(context=interaction, perm_node='whitelist_buttons'):
            self._view._logger.info(f'We Denied a Whitelist Request by {self._view._whitelist_message.author.name}')
            await self._discord_message.edit(content=f'**{interaction.user.name}** -> Denied __{self._view._whitelist_message.author.name}__ Whitelist Request', view=None)
            await self._view._whitelist_message.channel.send(content=f'**{interaction.user.name}** Denied {self._view._whitelist_message.author.mention} whitelist request. Please contact a Staff Member.')
            self._client.Whitelist_wait_list.pop(self._view._whitelist_message.id)
            self.disabled = True
