from discord import Interaction, app_commands

from amp_handler import AMPHandler
from utils.check import async_rolecheck


async def autocomplete_servers(interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocomplete for AMP Instance Names"""
    choice_list: dict[str, str] = AMPHandler().get_AMP_instance_names()
    if await async_rolecheck(interaction, perm_node='Staff') == True:
        return [app_commands.Choice(name=f"{value} | ID: {key}", value=key)for key, value in choice_list.items() if current.lower() in value.lower()][:25]
    else:
        return [app_commands.Choice(name=f"{value}", value=key)for key, value in choice_list.items() if current.lower() in value.lower()][:25]


async def autocomplete_servers_public(interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
    """Autocomplete for AMP Instance Names"""
    choice_list: dict[str, str] = AMPHandler().get_AMP_instance_names(public=True)
    return [app_commands.Choice(name=f"{value}", value=key)for key, value in choice_list.items() if current.lower() in value.lower()][:25]
