import discord
from discord.ext.commands import Bot
import discord.ext.commands


import logging
import traceback


class Helper_Command():
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Helper_Command, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def _setup(self, client: Bot):
        self._logger = logging.getLogger("")
        self._client: Bot = client
        return self

    def sub_command_handler(self, command: str, sub_command) -> None:
        """This will get the `Parent` command and then add a `Sub` command to said `Parent` command."""
        parent_command = self._client.get_command(command)
        if isinstance(parent_command, discord.ext.commands.Group):
            try:
                parent_command.add_command(sub_command)

                self._logger.dev(f'Added {command} Parent Command: {parent_command}')  # type: ignore
            except discord.app_commands.errors.CommandAlreadyRegistered:
                return
            except Exception as e:
                self._logger.error(f'We encountered an error in `sub_command_handler` command:{command} sub_command:{sub_command} - {traceback.print_exception(e)}')

    def sub_group_command_handler(self, group: str, command) -> None:
        """Gets the `Command Group` and adds the `command` to said `Group`"""
        parent_group = self._client.get_command(group)
        if isinstance(parent_group, discord.ext.commands.hybrid.HybridGroup):
            try:
                parent_group.add_command(command)

                self._logger.dev(f'Added {group} to Parent Command Group: {parent_group}')  # type: ignore
            except discord.app_commands.errors.CommandAlreadyRegistered:
                return
            except Exception as e:
                self._logger.error(f'We encountered an error in `sub_group_command_handler` group:{group} command:{command} - {traceback.print_exception(e)}')

    def _remove_commands(self, parent_group: str, command: str) -> None:
        """This will remove a command from a group"""
        # Should call some form of sync command after; but I do not want to auto sync. Regardless the command tree will be cleaned up.
        group = self._client.get_command(parent_group)
        # the Group command could not exists on first startup; as the client has not been sync'd.
        if isinstance(group, discord.ext.commands.Group):

            self._logger.dev(f'Removed {command} from {parent_group}')  # type: ignore
            # TODO -- Not sure if this can fail or not. May need to verify this.
            group.remove_command(command)
