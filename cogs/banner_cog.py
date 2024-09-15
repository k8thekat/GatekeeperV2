'''
   Copyright (C) 2021-2022 Katelynn Cadwallader.

   This file is part of Gatekeeper, the AMP Minecraft Discord Bot.

   Gatekeeper is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3, or (at your option)
   any later version.

   Gatekeeper is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
   or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
   License for more details.

   You should have received a copy of the GNU General Public License
   along with Gatekeeper; see the file COPYING.  If not, write to the Free
   Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
   02110-1301, USA. 

'''
from __future__ import annotations

import asyncio
import logging
import math
import os
import pathlib
import sqlite3
from datetime import datetime
from importlib.resources import is_resource

import discord
from discord import MessageType, app_commands
from discord.app_commands import Choice
from discord.ext import commands, tasks
from PIL import Image

import AMP_Handler
import DB as DB
import modules.banner_creator as BC
import utils
import utils_embeds
import utils_ui
from utils_dev.banner_editor.ui.view import Banner_Editor_View

# This is used to force cog order to prevent missing methods.
Dependencies = ["AMP_server_cog.py"]


class Banner(commands.Cog):
    def __init__(self, client: commands.Bot):
        self._client = client
        self.name = os.path.basename(__file__)
        self.logger = logging.getLogger()  # Point all print/logging statements here!

        self.AMPHandler = AMP_Handler.getAMPHandler()
        self.AMP = self.AMPHandler.AMP  # Main AMP object
        self.AMPInstances = self.AMPHandler.AMP_Instances  # Main AMP Instance Dictionary

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DB.DBConfig

        self.uBot = utils.botUtils(client)
        self.eBot = utils_embeds.botEmbeds(client)
        self.uiBot = utils_ui
        self.dBot = utils.discordBot(client)
        self.BC = BC

        self.uBot.sub_command_handler('server', self.amp_banner)  # This adds server specific amp_banner commands to the `/server` parent command.
        self.uBot.sub_command_handler('bot', self.banner_settings)
        self.uBot.sub_command_handler('bot', self.banner_group_group)

        if self.DBConfig.GetSetting('Banner_Auto_Update') == True:
            self.server_display_update.start()
            self.banner_loop_time_control.start()
            self.logger.dev(f'**{self.name.title()}** Server Display Banners Task Loop is Running: {self.server_display_update.is_running()}')

        self.logger.info(f'**SUCCESS** Loading Module **{self.name.title()}**')

    @property
    def _Message_Timeout(self):
        return self.DBConfig.Message_timeout

    @commands.Cog.listener('on_message_delete')
    async def on_message_delete(self, message: discord.Message):
        """This should handle if someone deletes the Display Messages."""

        # This should allow on_message_delete to ignore ephemeral message timed delete events.
        if hasattr(message, "type") and message.type == MessageType.chat_input_command:
            return

        self.logger.dev(f'{self.name.title()} `on_message_delete` event fired.. attempting to remove the message from the DB.')
        self.DB.Remove_Message_from_BannerGroup(messageid=message.id)

    @commands.Cog.listener('on_guild_channel_delete')
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        self.DB.Remove_Channel_from_BannerGroup(channelid=channel.id, guildid=channel.guild.id)

    async def autocomplete_banners(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """This is for a file listing of the `resources/banners` path."""
        banners = []
        _cwd = pathlib.Path.cwd().joinpath('resources/banners')
        banner_file_list = _cwd.iterdir()
        for entry in banner_file_list:
            banners.append(entry.name)
        return [app_commands.Choice(name=banner, value=banner) for banner in banners if current.lower() in banner.lower()][:25]

    async def autocomplete_bannergroups(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """This provides a Choice List of Banner Group Names"""
        banner_groups = self.DB.Get_All_BannerGroups()
        # If we don't have any entries. Send no results.
        if banner_groups == None or not len(banner_groups):
            return []
        return [app_commands.Choice(name=value, value=value)for key, value in banner_groups.items() if current.lower() in value.lower()][:25]

    async def autocomplete_bannergroups_channels(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        bg_channels = self.DB.Get_Channels_for_BannerGroup(interaction.namespace.group_name)
        try:
            # This could possibly fail if the "channel" gets deleted..and only if the `event` fails to fire.
            discord_channels = [interaction.guild.get_channel(value) for value in bg_channels]
            return [app_commands.Choice(name=channel.name, value=str(channel.id)) for channel in discord_channels if current.lower() in channel.name.lower()][:25]

        except:
            self.logger.error(f'We failed a `get_channel` inside of autocomplete_bannergroups_channels and defaulted to displaying the IDs')
            return [app_commands.Choice(name=str(value), value=str(value))for value in bg_channels if current.lower() in str(value).lower()][:25]

    async def banner_editor(self, context: commands.Context, amp_server: AMP_Handler.AMP.AMPInstance, db_server_banner=None):
        """Handles sending the banner."""
        db_server = self.DB.GetServer(amp_server.InstanceID)

        db_server_banner = db_server.getBanner()
        # Send a message so we can have a message.id to eidt later.
        sent_msg = await context.send('Creating Banner Editor...', ephemeral=True, delete_after=60)

        # Create my View first
        editor_view = Banner_Editor_View(amp_handler=self.AMPHandler, db_banner=db_server_banner, amp_server=amp_server, banner_message=sent_msg)
        banner_file = self.uiBot.banner_file_handler(self.BC.Banner_Generator(amp_server, db_server.getBanner())._image_())
        await sent_msg.edit(content='**Banner Editor**', attachments=[banner_file], view=editor_view)

    async def _embed_generator(self, banner_name: str, server_list: list[str], message_list: list[discord.Message], discord_guild: discord.Guild, discord_channel: discord.TextChannel):
        embed_list = await self.eBot.server_display_embed(server_list=server_list, guild=discord_guild, banner_name=banner_name)
        if len(embed_list) == 0:
            self.logger.warn('We failed to find any Banners for your Instances.')
            return
        ratio = math.ceil((len(embed_list) / 10))
        # compare ratio to len(message_list)
        # If our message list is way larger than our embeds; lets remove the extras. (1 msg to 10 embeds)
        # Lets also delete the Messages in discord
        if len(message_list) > ratio:
            for message in message_list[ratio:]:
                self.DB.Remove_Message_from_BannerGroup(messageid=message.id)
                await message.delete()

        # We have no Message IDs in the Database; so lets send new messages and store the IDs.
        # We have too many Embeds for the amount of Messages; we need to create some new ones.
        # Lets also delete the Messages in discord
        elif not len(message_list) or len(message_list) < ratio:
            # If we have messages; but we clearly didn't have enough. Lets remove all of them and send new ones.
            if len(message_list):
                for message in message_list:
                    self.DB.Remove_Message_from_BannerGroup(messageid=message.id)
                    await message.delete()

            for curpos in range(0, len(embed_list), 10):
                cur_message = await discord_channel.send(embeds=embed_list[curpos:(curpos + 9)])
                self.DB.Add_Message_to_BannerGroup(banner_groupname=banner_name, channelid=discord_channel.id, messageid=cur_message.id)

        elif len(message_list) == ratio:
            for curpos in range(0, len(message_list)):
                try:
                    # 0*10 = 0 : (0+1)*10 = 10 / 1*10 = 10 : (1+1)*10 = 20 / 2 *10 = 20 : (2+1)*10 = 30
                    # await message_list[curpos].edit(content= f"*Edited at {discord.utils.utcnow().strftime('%Y-%m-%d | %H:%M')}*", embeds=embed_list[curpos*10:(curpos+1)*10], attachments= [])
                    await message_list[curpos].edit(embeds=embed_list[curpos * 10:(curpos + 1) * 10], attachments=[])

                except discord.errors.Forbidden:
                    self.logger.error(f'{self._client.user.name} lacks permissions to edit messages in {discord_channel.name}, removing the Channel from {banner_name}.')
                    # self.DB.DelServerDisplayBanner(discord_guild.id, discord_channel.id)
                    self.DB.Remove_Channel_from_BannerGroup(channelid=discord_channel, guildid=discord_guild)

                except discord.errors.NotFound:
                    self.logger.error(f'{self._client.user.name} is unable to find the messages for {banner_name}, removing its messages.')
                    self.DB.Remove_Message_from_BannerGroup(messageid=message_list[curpos].id)

                await asyncio.sleep(2)

    async def _banner_generator(self, banner_name: str, server_list: list[str], message_list: list[discord.Message], discord_guild: discord.Guild, discord_channel: discord.TextChannel):
        banner_image_list = []

        for db_server in server_list:

            if db_server == None:
                self.DB.Remove_Server_from_BannerGroup(banner_groupname=banner_name, instanceID=db_server.InstanceID)

            if db_server.Hidden == 1:
                continue

            # We need the AMP object for the Banner Generator.
            try:
                amp_server = self.AMPHandler.AMP_Instances[db_server.InstanceID]
            except:
                if self.DBConfig.GetSetting("Auto_BG_Remove") == True:
                    self.DB.Remove_Server_from_BannerGroup(banner_groupname=banner_name, instanceID=db_server.InstanceID)
                else:
                    continue

            banner_file = self.uiBot.banner_file_handler(self.BC.Banner_Generator(amp_server, db_server.getBanner())._image_())
            # Store all the images as a `discord.File` for ease of iterations.
            banner_image_list.append(banner_file)

        if not len(banner_image_list):
            self.logger.warn('We failed to find any Banners for your Instances.')
            return

        # If we have too many messages; well we need to remove the remaining messages.
        # We also remove the discord Messages too.
        if len(message_list) > len(banner_image_list):
            # Since Banner Images are 1 image per 1 message; we can use the len of our banner_image_list as our index
            old_messages = message_list[len(banner_image_list):]
            for message in old_messages:
                self.DB.Remove_Message_from_BannerGroup(messageid=message.id)
                await message.delete()
                message_list.remove(message)

        # If our message_list is empty, we assume we haven't sent messages yet.
        # Or if the number of messages we have is less than the banner images, lets send new messages.
        elif not len(message_list) or (len(message_list) < len(banner_image_list)):
            # If we have messages; but we clearly didn't have enough. Lets remove all of them and send new ones.
            if len(message_list):
                for message in message_list:
                    try:
                        await message.delete()  # Remove any extra messages or existing messages.
                    except:
                        self.logger.error('Failed to find discord.Message object; removing Message from bannergroup.')
                    self.DB.Remove_Message_from_BannerGroup(messageid=message.id)

            for curpos in range(0, len(banner_image_list)):
                cur_message = await discord_channel.send(file=banner_image_list[curpos])
                self.DB.Add_Message_to_BannerGroup(banner_groupname=banner_name, channelid=discord_channel.id, messageid=cur_message.id)

        elif len(message_list) == len(banner_image_list):
            first_msg = True
            for curpos in range(0, len(message_list)):
                try:
                    if first_msg:
                        await message_list[curpos].edit(content=f"*Edited at {discord.utils.utcnow().strftime('%Y-%m-%d | %H:%M')}*", attachments=[banner_image_list[curpos]], embed=None)
                        first_msg = False
                    else:
                        await message_list[curpos].edit(attachments=[banner_image_list[curpos]], embed=None)

                except discord.errors.Forbidden:
                    self.logger.error(f'{self._client.user.name} lacks permissions to edit messages in {discord_channel.name}, removing the Channel from {banner_name}.')
                    self.DB.Remove_Channel_from_BannerGroup(channelid=discord_channel.id, guildid=discord_channel.guild.id)

                except discord.errors.NotFound:
                    self.logger.error(f'{self._client.user.name} is unable to find the messages for {banner_name}, removing its messages.')
                    self.DB.Remove_Message_from_BannerGroup(messageid=message_list[curpos].id)

                await asyncio.sleep(2)

    @tasks.loop(minutes=1)
    async def banner_loop_time_control(self):
        """Dynamically adjusts the `server_display_update` loop time."""
        base_time = 60  # seconds
        # for each message we have in the DB; lets add to our base_time so we can *hopefully* avoid API ratelimit from discord.
        num_messages = self.DB.get_all_bannergroup_messages()
        base_time += (num_messages * 10)

        if self.server_display_update.seconds == base_time:
            return
        else:
            self.logger.info(f'We adjusted our Banner Update time from {self.server_display_update.seconds} seconds to {base_time} seconds.')
            self.server_display_update.change_interval(seconds=base_time)

    @tasks.loop(seconds=60)
    async def server_display_update(self):
        """This will handle the constant updating of Server Display Messages"""
        if not self._client.is_ready():
            return

        if not self.DBConfig.GetSetting('Banner_Auto_Update'):
            return

        self.logger.info('**Updating Banner Displays**')

        Banners = self.DB.Get_All_BannerGroup_Info()
        # Banners structure = {916195413839712277: {'name': 'TestBannerGroup', 'guild_id': 602285328320954378, 'servers': [1], 'messages': [1079236992145051668]}}
        for key, value in Banners.items():
            self.logger.dev(f'Getting the Banner Group: {value["name"]} from the DB')
            discord_guild = self._client.get_guild(value['guild_id'])
            discord_channel = discord_guild.get_channel(key)

            # This should create a list of DBServer Objects.
            if len(value['servers']):
                servers = [self.DB.GetServer(ServerID=entry) for entry in value["servers"] if self.DB.GetServer(ServerID=entry) != [None or "None"]]

            messages = []
            # Removing any None values returned from the DB leaving us with an empty list.
            for entry in value['messages']:
                if entry in ['None', None]:
                    value['messages'].remove(entry)

            if len(value['messages']):
                # This should give us a list of partial message objects.
                messages = [discord_channel.get_partial_message(entry) for entry in value["messages"] if discord_channel.get_partial_message(entry) != [None]]

            if self.DBConfig.GetSetting('Banner_Type') == 1:
                await self._banner_generator(banner_name=value['name'], server_list=servers, message_list=messages, discord_channel=discord_channel, discord_guild=discord_guild)

            else:
                await self._embed_generator(banner_name=value['name'], server_list=servers, message_list=messages, discord_channel=discord_channel, discord_guild=discord_guild)

    @commands.hybrid_group(name='bannergroup')
    async def banner_group_group(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=30)

    @banner_group_group.command(name='create_group')
    @utils.role_check()
    async def banner_group_create(self, context: commands.Context, group_name: str):
        """Allows the User to Create a new Banner Group"""
        try:
            self.DB.Add_BannerGroup(name=group_name)
            return await context.send(content=f'We created a new Banner Group called `{group_name}` for you.', ephemeral=True, delete_after=self._client.Message_Timeout)
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in e.args[0]:
                return await context.send(content=f'Oops, it appears `{group_name}` already exists, please try again.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_group_group.command(name='info')
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_info(self, context: commands.Context, group_name: str):
        """Displays information pertaining to the selected Banner Group."""
        banner_info = self.DB.Get_one_BannerGroup_info(name=group_name)

        disc_chan_list = []
        servers = []
        if banner_info != None and len(banner_info):
            for key, value in banner_info.items():

                for entry in value['InstanceName']:
                    if entry not in servers and entry != None:
                        servers.append(entry)

                for entry in value['Discord_Channel']:
                    if entry not in disc_chan_list and entry != None:
                        disc_chan_list.append(context.guild.get_channel(entry).mention if context.guild.get_channel(entry) != None else entry)

        # If our lists are empty; add 'None' to prevent display issues.
        if not len(servers):
            servers.append('None')

        if not len(disc_chan_list):
            disc_chan_list.append('None')

        embed = discord.Embed(title=group_name, color=0x71368a, description=f"Settings...")
        embed.add_field(name="Servers", value="\n".join(servers), inline=False)
        embed.add_field(name="Channels", value="\n".join(disc_chan_list), inline=False)
        return await context.send(embed=embed, ephemeral=True, delete_after=(self._client.Message_Timeout * 2))

    @banner_group_group.command(name='rename')
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_rename(self, context: commands.Context, group_name: str, new_groupname: str):
        """Allows a User to rename the selected Banner Group."""
        try:
            self.DB.Update_BannerGroup(new_name=new_groupname, name=group_name)
            return await context.send(content=f'You are all set! We changed `{group_name}` name to `{new_groupname}`! Magic~', ephemeral=True, delete_after=self._client.Message_Timeout)

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in e.args[0]:
                return await context.send(content=f'Oops, it appears `{new_groupname}` already exists, please try again.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_group_group.command(name='add')
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_add(self, context: commands.Context, group_name: str, server: None | str = None, channel: None | discord.abc.GuildChannel = None):
        """Allows the User to add `Channel` or `Server` to a Banner Group."""
        c_status = True
        s_status = True

        if self.DB.Get_BannerGroup(name=group_name) == None:
            return await context.send(content=f'Oops, it appears that `{group_name}` does not exist, please create the banner group via `/bot bannergroup create_group {group_name}`', ephemeral=True, delete_after=self._client.Message_Timeout)

        if server == None and channel == None:
            return await context.send(content=f"Please select either a `Server` or `Channel` to add to the Banner Group.", ephemeral=True, delete_after=self._client.Message_Timeout)

        if server != None:
            db_server = self.DB.GetServer(InstanceID=server)
            s_status = self.DB.Add_Server_to_BannerGroup(banner_groupname=group_name, instanceID=server)

        if channel != None:
            c_status = self.DB.Add_Channel_to_BannerGroup(banner_groupname=group_name, channelid=channel.id, guildid=context.guild.id)

        if not c_status or not s_status:
            return await context.send(content=f"""It appears that {f' `{db_server.InstanceName}`'if server != None else ''}{' and 'if server != None and channel != None else ''}{channel.mention if channel != None else ''} already exists for **{group_name}**, please try again.""", ephemeral=True, delete_after=self._client.Message_Timeout)

        d_format = f"Looks like we just added"
        c_str = f"Banner Group: **{group_name}**\n{d_format}{f'` {db_server.InstanceName}`'if server != None else ''}{' and 'if server != None and channel != None else ''}{channel.mention if channel != None else ''}"
        return await context.send(content=c_str, ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_group_group.command(name='remove')
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    @app_commands.autocomplete(channel=autocomplete_bannergroups_channels)
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_remove(self, context: commands.Context, group_name, server: str = None, channel: str = None):
        """Allows the User to Remove a `Server` or `Channel` from a Banner Group"""

        if server != None:
            db_server = self.DB.GetServer(InstanceID=server)
            self.DB.Remove_Server_from_BannerGroup(banner_groupname=group_name, instanceID=server)

        if channel != None:
            if type(channel) != str:
                # If we got a discord.abc.GuildChannel (or similar object) We should be able to call `.id` on said object.
                channel = channel.id
            banner_info = self.DB.Get_Messages_for_BannerGroup(banner_groupname=group_name)
            if banner_info == None:
                return await context.send(content=f"Uhh it appears there is no entries for `{group_name}` in the database.", ephemeral=True, delete_after=self._Message_Timeout)
            for key, value in banner_info.items():
                cur_channel = self._client.get_channel(key)
                # We are going to find the old messages and delete them if possible.
                for entry in value['messages']:
                    try:
                        await cur_channel.get_partial_message(entry).delete()
                        self.logger.dev(f'Found message in channel and deleted message. id: {entry}')
                    except Exception as e:
                        self.logger.error(f'Was unable to delete a message id: {entry}, removing from DB')

            # We still need to `int` the channel object because on the off chance the channel has been deleted and the autocomplete fails to find said channel;
            # it will provide us with a str version of the `channel.id` that was stored in the DB. (Autocompletes want a `str` for value=)
            self.DB.Remove_Channel_from_BannerGroup(channelid=int(channel), guildid=context.guild.id)

        d_format = f"Looks like we just removed"
        c_str = f"Banner Group: **{group_name}**\n{d_format}{f'` {db_server.InstanceName}`'if server != None else ''}{' and 'if server != None and channel != None else ''}{f'`{self._client.get_channel(int(channel)).mention}`' if channel != None else ''}"
        return await context.send(content=c_str, ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_group_group.command(name='delete_group')
    @app_commands.autocomplete(group_name=autocomplete_bannergroups)
    async def banner_group_delete(self, context: commands.Context, group_name: str):
        """Allows the User to Delete an entire Banner Group"""
        banner_info = self.DB.Get_Messages_for_BannerGroup(banner_groupname=group_name)
        for key, value in banner_info.items():
            cur_channel = self._client.get_channel(key)
            # We are going to find the old messages and delete them if possible.
            for entry in value['messages']:
                try:
                    await cur_channel.get_partial_message(entry).delete()
                    self.logger.dev(f'Found message in channel and deleted message. id: {entry}')
                except Exception as e:
                    self.logger.error(f'Was unable to delete a message id: {entry}, removing from DB')

        self.DB.Delete_BannerGroup(name=group_name)
        await context.send(content=f"Bye Bye `{group_name}`, you will be missed for all of about 3.14159 seconds", ephemeral=True, delete_after=self._client.Message_Timeout)

    @commands.hybrid_group(name='banner')
    @utils.role_check()
    async def amp_banner(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=30)

    @amp_banner.command(name='background')
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    @app_commands.autocomplete(image=autocomplete_banners)
    @utils.role_check()
    async def amp_banner_background(self, context: commands.Context, server, image):
        """Sets the Background Image for the selected Server."""
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True, delete_after=self._client.Message_Timeout)

        db_server = self.DB.GetServer(amp_server.InstanceID)
        banner = db_server.getBanner()
        image_path = pathlib.Path.cwd().joinpath('resources/banners').as_posix() + '/' + image
        banner.background_path = image_path
        amp_server._setDBattr()
        my_image = Image.open(image_path)
        await context.send(content=f'Set **{amp_server.FriendlyName}** Banner Image to', file=self.uiBot.banner_file_handler(my_image), ephemeral=True, delete_after=self._client.Message_Timeout)

    @amp_banner.command(name='settings')
    @utils.role_check()
    @app_commands.autocomplete(server=utils.autocomplete_servers)
    async def amp_banner_settings(self, context: commands.Context, server):
        """Prompts the Banner Editor Menu"""
        self.logger.command(f'{context.author.name} used Server Banner Settings Editor...')
        amp_server = self.uBot.serverparse(server, context, context.guild.id)
        if amp_server == None:
            return await context.send(f"Hey, we uhh can't find the server **{server}**. Please try your command again <3.", ephemeral=True, delete_after=self._client.Message_Timeout)

        await self.banner_editor(context, amp_server)

    @commands.hybrid_group(name='banner_settings')
    async def banner_settings(self, context: commands.Context):
        if context.invoked_subcommand is None:
            await context.send('Invalid command passed...', ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_settings.command(name='auto_update')
    @utils.role_check()
    @app_commands.choices(flag=[Choice(name='True', value=1), Choice(name='False', value=0)])
    async def banner_autoupdate(self, context: commands.Context, flag: Choice[int] = 1):
        """Toggles Auto Updating of Banners On or Off."""
        self.logger.command(f'{context.author.name} used Bot Display Banners Auto Update...')

        if flag.value == 1:
            self.DBConfig.SetSetting('Banner_Auto_Update', True)

            if not self.server_display_update.is_running():
                self.server_display_update.start()
            if not self.banner_loop_time_control.is_running():
                self.banner_loop_time_control.start()

            return await context.send(f'All set! The bot will __Auto Update the Banners__ .', ephemeral=True, delete_after=self._client.Message_Timeout)
        if flag.value == 0:
            self.DBConfig.SetSetting('Banner_Auto_Update', False)

        if self.server_display_update.is_running():
            self.banner_loop_time_control.stop()
        if self.banner_loop_time_control.is_running():
            self.server_display_update.stop()

            return await context.send(f"Well, I guess I won't update the Banners anymore.", ephemeral=True, delete_after=self._client.Message_Timeout)
        else:
            return await context.send('Hey! You gotta pick `True` or `False`.', ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_settings.command(name='type')
    @utils.role_check()
    @app_commands.choices(type=[Choice(name='Custom Banner Images', value=1), Choice(name='Discord Embeds', value=0)])
    async def banner_type(self, context: commands.Context, type: Choice[int] = 0):
        """Selects which type of Server Banner(s) to Display, either Embeds or Images"""
        self.logger.command(f'{context.author.name} used Bot Banners Type...')

        if type.value == 0:
            self.DBConfig.SetSetting('Banner_Type', 0)
            return await context.send('Look at me, using **Discord Embeds**.. psht..I mean they atleast work.', ephemeral=True, delete_after=self._client.Message_Timeout)

        if type.value == 1:
            self.DBConfig.SetSetting('Banner_Type', 1)
            return await context.send('Looks like we are going to be using **Custom Banner Images**! Oooooh yea~', ephemeral=True, delete_after=self._client.Message_Timeout)

    @banner_settings.command(name='auto_remove')
    @utils.role_check()
    @app_commands.choices(flag=[Choice(name='True', value=1), Choice(name='False', value=0)])
    async def banner_auto_remove(self, context: commands.Context, flag: Choice[int] = 1):
        """Selects which type of Server Banner(s) to Display, either Embeds or Images"""
        self.logger.command(f'{context.author.name} used Bot Banners Auto Remove...')

        if flag.value == 0:
            self.DBConfig.SetSetting('Auto_BG_Remove', 0)
            return await context.send('We will be ignoring Servers that are removed from AMP.', ephemeral=True, delete_after=self._client.Message_Timeout)

        if flag.value == 1:
            self.DBConfig.SetSetting('Auto_BG_Remove', 1)
            return await context.send('We will be removing Servers from Banner groups when they are removed from AMP.', ephemeral=True, delete_after=self._client.Message_Timeout)


async def setup(client):
    await client.add_cog(Banner(client))
