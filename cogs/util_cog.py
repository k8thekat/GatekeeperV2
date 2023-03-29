from discord import Interaction
from discord.app_commands import Choice

from utils.cogs.base_cog import Gatekeeper_Cog


class Util_cog(Gatekeeper_Cog):

    async def autocomplete_loadedcogs(self, interaction: Interaction, current: str) -> list[Choice[str]]:
        """Cog Autocomplete template."""
        choice_list: list[str] = []
        for key in self._client.cogs:
            if key not in choice_list:
                choice_list.append(key)
        return [Choice(name=choice, value=choice) for choice in choice_list if current.lower() in choice.lower()]

    @main_bot.group(name='cog')
    @role_check()
    async def bot_cog(context: commands.Context) -> None:
        """Cog Group Commands"""
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=client.Message_Timeout)

    @bot_cog.command(name='load')
    @role_check()
    async def bot_cog_loader(context: commands.Context, cog: str) -> None:
        """Load a specific cog, must provide path using '.' as a seperator. eg: 'cogs.my_cog'"""

        try:
            await client.load_extension(name=cog)
        except Exception as e:
            await context.send(f'**ERROR** Loading Extension `{cog}` - `{traceback.format_exc()}`', ephemeral=True, delete_after=client.Message_Timeout)
        else:
            await context.send(f'**SUCCESS** Loading Extension `{cog}`', ephemeral=True, delete_after=client.Message_Timeout)

    @bot_cog.command(name='unload')
    @role_check()
    @app_commands.autocomplete(cog=autocomplete_loadedcogs)
    async def bot_cog_unloader(context: commands.Context, cog: str) -> None:
        """Un-load a specific cog."""

        try:
            my_cog = client.cogs[cog]
            await my_cog.cog_unload()
            # await client.unload_extension(name=cog)
        except Exception as e:
            await context.send(f'**ERROR** Un-Loading Extension `{cog}` - `{traceback.format_exc()}`', ephemeral=True, delete_after=client.Message_Timeout)
        else:
            await context.send(f'**SUCCESS** Un-Loading Extension `{cog}`', ephemeral=True, delete_after=client.Message_Timeout)

    @bot_cog.command(name='reload')
    @role_check()
    async def bot_cog_reload(context: commands.Context) -> None:
        """Reloads all loaded Cogs inside the cogs folder."""

        await client.Handler.cog_auto_loader(reload=True)
        await context.send(f'**SUCCESS** Reloading All Extensions ', ephemeral=True, delete_after=client.Message_Timeout)

    @main_bot.group(name='utils')
    @role_check()
    async def bot_utils(context: commands.Context) -> None:
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=client.Message_Timeout)

    @bot_utils.command(name='clear')
    @app_commands.choices(all=[Choice(name='True', value=1), Choice(name='False', value=0)])
    @app_commands.describe(all='Default\'s to False, removes ALL commands from selected Channel regardless of sender when TRUE.')
    @app_commands.describe(channel='Default\'s to the Channel the command was run; otherwise applies to the channel selected')
    @role_check()
    async def clear(self, interaction: discord.Interaction, channel: Union[discord.VoiceChannel, discord.TextChannel, discord.Thread, None], amount: app_commands.Range[int, 0, 100] = 15, all: bool = False):
        """Cleans up Messages sent by anyone. Limit 100"""
        await interaction.response.defer()

        assert isinstance(
            interaction.channel, (discord.VoiceChannel, discord.TextChannel, discord.Thread))
        channel = channel or interaction.channel  # type:ignore
        messages: list[discord.Message]
        if all:
            messages = await channel.purge(limit=amount, bulk=False)
        else:
            messages = await channel.purge(limit=amount, check=self._self_check, bulk=False)

        return await channel.send(f'Cleaned up **{len(messages)} {"messages" if len(messages) > 1 else "message"}**. Wow, look at all this space!', delete_after=self._client._message_timeout)

    @bot_utils.command(name='roleid')
    @role_check()
    async def bot_utils_roleid(context: commands.Context, role: discord.Role) -> None:
        """Returns the role id for the specified role."""
        await context.send(f'**{role.name}** has the Discord role id of: `{role.id}`', ephemeral=True, delete_after=client.Message_Timeout)

    @bot_utils.command(name='channelid')
    @role_check()
    async def bot_utils_channelid(context: commands.Context, channel: discord.abc.GuildChannel) -> None:
        """Returns the channel id for the specified channel."""
        await context.send(f'**{channel.name}** has the channel id of: `{channel.id}`', ephemeral=True, delete_after=client.Message_Timeout)

    @bot_utils.command(name='userid')
    @role_check()
    async def bot_utils_userid(context: commands.Context, user: Union[discord.User, discord.Member]) -> None:
        """Returns the user id for the specified user."""
        await context.send(f'**{user.name} // {user.display_name}** has the user id of: `{user.id}`', ephemeral=True, delete_after=client.Message_Timeout)

    #!TODO! Need to finish developing this command.
    # @bot_utils.command(name='steamid')
    # @utils.role_check()
    # async def bot_utils_steamid(context:commands.Context, name:str):
    #     """Gets the SteamID of the Name provided."""
    #     client._logger.command(f'{context.author.name} used Bot Utils SteamID...') #type:ignore
    #     steam_id = client.uBot.name_to_steam_id(steamname= name)
    #     if steam_id:
    #         await context.send(content= f'**{name}** has the Steam ID of `{steam_id}`', ephemeral= True, delete_after= client.Message_Timeout)
    #     else:
    #         await context.send(content= f'Well I was unable to find that Steam User {name}.', ephemeral= True, delete_after= client.Message_Timeout)

    @bot_utils.command(name='uuid')
    @role_check()
    async def bot_utils_uuid(context: commands.Context, mc_ign: str) -> None:
        """This will convert a Minecraft IGN to a UUID if it exists"""
        await context.send(f'The UUID of **{mc_ign}** is: `{name_to_uuid_MC(mc_ign)}`', ephemeral=True, delete_after=client.Message_Timeout)

    @bot_utils.command(name='ping')
    @role_check()
    async def bot_utils_ping(context: commands.Context) -> None:
        """Pong..."""
        await context.send(f'Pong {round(client.latency * 1000)}ms', ephemeral=True, delete_after=client.Message_Timeout)

    @bot_utils.command(name='disconnect')
    @role_check()
    async def bot_utils_stop(context: commands.Context) -> None:
        """Closes the connection to Discord."""
        await context.send('Disconnecting from the Server...', ephemeral=True, delete_after=client.Message_Timeout)
        return await client.close()

    @bot_utils.command(name='restart')
    @role_check()
    async def bot_utils_restart(context: commands.Context):
        """This is the Gatekeeper restart function\n"""
        await context.send(f'**Currently Restarting the Bot, please wait...**', ephemeral=True, delete_after=client.Message_Timeout)
        sys.stdout.flush()
        os.execv(sys.executable, ['python3'] + sys.argv)

    @bot_utils.command(name='status')
    @role_check()
    async def bot_utils_status(context: commands.Context):
        """Status information for the Bot(Versions, AMP Connection, SQL DB Initialization)"""
        await context.send(embed=await bot_about_embed())
        # await context.send(content= f"""**Discord Version**: {discord.__version__}  //  **Python Version**: {sys.version}\n**Gatekeeperv2 Version**: {Version} // **SQL Database Version**: {client.DBHandler.DB_Version}\n**AMP Connected**: {client.AMPHandler.SuccessfulConnection} // **SQL Database**: {client.DBHandler.SuccessfulDatabase}""", ephemeral= True, delete_after= client.Message_Timeout)

    @bot_utils.command(name='message_timeout')
    @role_check()
    @app_commands.describe(time='Default is 60 seconds')
    async def bot_utils_message_timeout(context: commands.Context, time: int = 60):
        """Sets the Delete After time in seconds for ephemeral messages sent from Gatekeeperv2"""

        client.DBConfig.SetSetting('Message_Timeout', f'{time}')
        client.Message_Timeout = time

        content_str: str = f'will be deleted `{time}` seconds'
        if time == None:
            content_str = f'will no longer be deleted'

        await context.send(content=f'**Ephemeral Messages** {content_str} after being sent.', ephemeral=True, delete_after=client.Message_Timeout)

    @client.hybrid_group(name='bot')
    @role_check()
    async def main_bot(context: commands.Context) -> None:
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=client.Message_Timeout)

    @main_bot.command(name='donator')
    @role_check()
    async def bot_donator(context: commands.Context, role: discord.Role) -> None:
        """Sets the Donator Role for Donator Only AMP Server access."""
        client._logger.command(f'{context.author.name} used Bot Donator Role...')  # type:ignore
        client.DBConfig.SetSetting('Donator_role_id', role.id)
        await context.send(f'You are all set! Donator Role is now set to {role.mention}', ephemeral=True, delete_after=client.Message_Timeout)

    @main_bot.command(name='moderator')
    @commands.has_guild_permissions(administrator=True)
    async def bot_moderator(context: commands.Context, role: discord.Role) -> None:
        """Set the Discord Role for Bot Moderation"""
        client.DBConfig.SetSetting('Moderator_role_id', role.id)
        await context.send(f'Set Moderator Role to `{role.name}`.', ephemeral=True)

    @main_bot.command(name='permissions')
    @commands.has_guild_permissions(administrator=True)
    @app_commands.choices(permission=[Choice(name='Default', value=0), Choice(name='Custom', value=1)])
    async def bot_permissions(context: GatekeeperGuildContext, permission: Choice[int]):
        """Set the Bot to use Default Permissions or Custom"""

        # If we set to 0; we are using `Default` Permissions and need to unload the cog and commands related to custom permissions.
        if permission.value == 0:
            await context.send(f'You have selected `Default` permissions, removing permission commands...', ephemeral=True, delete_after=client.Message_Timeout)
            parent_command = client.get_command('user')
            if isinstance(parent_command, discord.ext.commands.Group):
                parent_command.remove_command('role')
            if 'cogs.Permissions_cog' in client.extensions:
                await client.unload_extension('cogs.Permissions_cog')

        # If we set to 1; we are using `Custom` Permissions.
        elif permission.value == 1:
            await context.send(f'You have selected `Custom` permissions, validating `bot_perms.json`', ephemeral=True, delete_after=client.Message_Timeout)
            await context.send(f'Visit https://github.com/k8thekat/GatekeeperV2/blob/main/PERMISSIONS.md', ephemeral=True, delete_after=client.Message_Timeout)
            # This validates the `bot_perms.json` file.
            if not await client.permissions_update():
                return await context.send(f'Error loading the Permissions Cog, please check your Console for errors.', ephemeral=True, delete_after=client.Message_Timeout)

        # Depending on which permissions; this will sync the updated commands available.
        cur_guild: Guild | None = client.get_guild(context.guild.id)
        if isinstance(cur_guild, Guild):
            client.tree.copy_global_to(guild=cur_guild)
            await client.tree.sync(guild=client.get_guild(context.guild.id))
            client.DBConfig.Permissions = permission.name
        await context.send(f'Finished setting Gatekeeper permissions to `{permission.name}`!', ephemeral=True, delete_after=client.Message_Timeout)

    @main_bot.command(name='settings')
    @role_check()
    async def bot_settings(context: commands.Context) -> None:
        """Displays currently set Bot settings"""
        await context.send(embed=bot_settings_embed(context=context), ephemeral=True, delete_after=(client.Message_Timeout * 3))  # Tripled the delay to help sort times.
