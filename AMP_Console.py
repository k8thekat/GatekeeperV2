"""
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
"""

from __future__ import annotations

import logging
import re
import threading
import time
import traceback
from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING, TypedDict

import DB

if TYPE_CHECKING:
    from AMP import AMPInstance
    from AMP_Handler import AMPHandler
    from DB import DBServer


class ConsoleEntry(TypedDict):
    Contents: str
    Source: str
    Timestamp: str
    Type: str


class AMPConsole:
    FILTER_TYPE_CONSOLE = 0
    FILTER_TYPE_EVENT = 1
    FILTER_TYPE_BLACKLIST = 0
    FILTER_TYPE_WHITELIST = 1

    def __init__(self, AMPInstance: AMPInstance) -> None:
        self.logger = logging.getLogger()

        self.AMPInstance: AMPInstance = AMPInstance
        self.AMPHandler: AMPHandler | None = AMPInstance.AMPHandler
        self.AMP_Console_Threads = self.AMPHandler.AMP_Console_Threads

        self.DBHandler = DB.getDBHandler()
        self.DB = self.DBHandler.DB  # Main Database object
        self.DBConfig = self.DBHandler.DBConfig
        self.DB_Server: DBServer | None = self.DB.GetServer(InstanceID=self.AMPInstance.InstanceID)

        self.console_thread = None
        self.console_thread_running = False

        self.console_messages = []
        self.console_message_list = []
        self.console_message_lock = threading.Lock()

        self.console_chat_messages = []
        self.console_chat_message_lock = threading.Lock()

        self.console_event_messages = []
        self.console_event_message_lock = threading.Lock()

        self.logger.dev(f"**SUCCESS** Setting up {self.AMPInstance.FriendlyName} Console")
        self.console_init()

    def console_init(self) -> None:
        """This starts our console threads..."""
        if self.AMPInstance.Console_Flag:
            try:
                # self.AMP_Modules[DIS] = getattr(class_module,f'AMP{module_name}')
                # self.AMP_Console_Modules[DIS] = getattr(class_module,f'AMP{module_name}Console')
                name = "Generic"
                if (
                    self.AMPInstance.DisplayImageSource in self.AMPHandler.AMP_Console_Modules
                ):  # Should be AMP_Console_Modules: {Module_Name: 'Module_class_object'}
                    name = self.AMPInstance.DisplayImageSource

                self.logger.dev(f"Loaded {name} for {self.AMPInstance.FriendlyName}")

                # This starts the console parse on our self in a separate thread.
                self.console_thread = threading.Thread(target=self.console_parse_loop, name=self.AMPInstance.FriendlyName)

                # This adds the AMPConsole Thread Object into a dictionary with the key value of AMPInstance.InstanceID
                self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.console_thread

                if self.AMPInstance.Running and self.AMPInstance._ADScheck() and self.AMPInstance.ADS_Running:
                    self.console_thread.start()
                    self.console_thread_running = True
                    self.logger.dev(f"**SUCCESS** Starting Console Thread for {self.AMPInstance.FriendlyName}...")

            except Exception:
                self.AMP_Console_Threads[self.AMPInstance.InstanceID] = self.AMPHandler.AMP_Console_Modules["Generic"]
                self.logger.critical(
                    f"**ERROR** Failed to Start the Console for {self.AMPInstance.FriendlyName}...with {traceback.format_exc()}"
                )

    def console_parse_loop(self) -> None:
        """This handles AMP Console Updates; turns them into bite size messages and sends them to Discord"""
        time.sleep(5)
        last_entry_time = 0
        while 1:
            time.sleep(1)

            if not self.console_thread_running:
                time.sleep(10)
                continue

            if not self.AMPInstance.Running:
                time.sleep(10)
                continue

            console = self.AMPInstance.ConsoleUpdate()
            if isinstance(console, dict) and "ConsoleEntries" not in console:
                self.logger.error(f"Console Entries not found for {self.AMPInstance.FriendlyName}")
                self.AMPInstance._ADScheck()
                continue

            if isinstance(console, bool) or console == None:
                self.logger.error(f"Console Update Failed {self.AMPInstance.FriendlyName}")
                self.AMPInstance._ADScheck()
                continue

            console_entries: list[ConsoleEntry] = console["ConsoleEntries"]
            for entry in console_entries:
                # This prevents old messages from getting handled again and spamming on restart.
                try:
                    entry_time = datetime.fromtimestamp(float(entry["Timestamp"][6:-2]) / 1000, tz=UTC)
                except:
                    # This is to support v2.6.0.0 of AMP API.
                    entry_time: datetime = datetime.fromisoformat(entry["Timestamp"])
                if last_entry_time == 0:
                    last_entry_time = entry_time
                    break

                if entry_time < last_entry_time:
                    last_entry_time = entry_time
                    continue

                self.logger.dev(
                    f"Name: {self.AMPInstance.FriendlyName} | DisplayImageSource: {self.AMPInstance.DisplayImageSource} | Console Channel: {self.AMPInstance.Discord_Console_Channel}\n Console Entry: {entry}"
                )
                # This will add the Servers Discord_Chat_Prefix to the beginning of any of the messages.
                # Its done down here to prevent breaking of any existing filtering.
                # TODO - Unsure what I was using this for. Removing the logic at this time.
                # if self.DB_Server is not None and self.DB_Server.Discord_Chat_Prefix != None:
                #     entry["Prefix"] = self.DB_Server.Discord_Chat_Prefix

                # This should handle server events(such as join/leave/disconnects)
                # if self.console_events(entry):
                # continue

                # This will vary depending on the server type.
                # I don't want to filter out the chat message here though. Just send it to two different places!
                if self.console_chat(entry):
                    continue

                # This will filter any messages such as errors or mods loading, etc..
                # if self.console_filter(entry):
                #    continue

                if len(entry["Contents"]) > 1500:
                    index_hunt = entry["Contents"].find(";")
                    if index_hunt == -1:
                        continue

                    msg_len_index = entry["Contents"].rindex(";")

                    while msg_len_index > 1500:
                        msg_len_index_end = msg_len_index
                        msg_len_index = entry["Contents"].rindex(";", 0, msg_len_index_end)

                        if msg_len_index < 1500:
                            new_msg = entry["Contents"][0:msg_len_index]
                            self.console_message_list.append(new_msg.lstrip())
                            entry["Contents"] = entry["Contents"][msg_len_index + 1 : len(entry["Contents"])]
                            msg_len_index = len(entry["Contents"])
                            continue
                else:
                    self.console_message_list.append(entry["Contents"])

            if len(self.console_message_list) > 0:
                bulkentry = ""
                for entry in self.console_message_list:
                    if len(bulkentry + entry) < 1500:
                        bulkentry = bulkentry + entry + "\n"

                    else:
                        self.console_message_lock.acquire()
                        self.console_messages.append(bulkentry[:-1])
                        self.console_message_lock.release()
                        self.logger.debug(self.AMPInstance.FriendlyName + bulkentry[:-1])
                        bulkentry = entry + "\n"

                if len(bulkentry):
                    self.console_message_lock.acquire()
                    self.console_messages.append(bulkentry[:-1])
                    self.console_message_lock.release()
                    self.logger.debug(self.AMPInstance.FriendlyName + bulkentry[:-1])

            self.console_message_list = []

        self.logger.warning(f"{self.AMPInstance.FriendlyName} Thread Loop is Ending")

    def console_filter(self, message: ConsoleEntry) -> bool:
        """Controls what will be sent to the Discord Console Channel via AMP Console. \n
        Return `True` to Continue, `False` to Return Message"""
        self.logger.dev(
            f"Console Filtered: {bool(self.AMPInstance.Console_Filtered)} | Console Filtered Type: {self.AMPInstance.Console_Filtered_Type}"
        )
        if self.AMPInstance.Console_Filtered:
            # This is to prevent Regex filtering on Chat Messages.
            if message["Type"] == "Chat":
                return False

            # 0 = Blacklist | 1 = Whitelist (0 = False/ 1 = True)
            return_bool = bool(self.AMPInstance.Console_Filtered_Type)

            if self.DB_Server is None:
                return False
            regex = self.DB_Server.GetServerRegexPatterns()

            if len(regex) == 0:
                return return_bool

            for pattern in regex:
                flag = re.search(regex[pattern]["Pattern"], message["Contents"])
                if flag != None:
                    # 0 = Console | 1 = Event
                    # This is Console Regex Filtering
                    self.logger.dev(f"Regex Pattern Type: {regex[pattern]['Type']} == Console Filter Type")
                    if regex[pattern]["Type"] == self.FILTER_TYPE_CONSOLE:
                        return not return_bool

                    # This is Event Regex Filtering
                    self.logger.dev(f"Regex Pattern Type: {regex[pattern]['Type']} == Event Filter Type")
                    if regex[pattern]["Type"] == self.FILTER_TYPE_EVENT:
                        if return_bool == True:  # If Whitelist; then allow Event messages to be handled.
                            self.console_event_message_lock.acquire()
                            self.console_event_messages.append(message["Contents"])
                            self.console_event_message_lock.release()
                        return not return_bool
            else:
                self.logger.dev(f"Filtered Message: {message}")
                return return_bool
        return False

    def console_chat(self, message: ConsoleEntry) -> None | bool:
        """This will handle all player chat messages from AMP to Discord.\n
        Format's Server Chat Messages for better readability to the Console"""
        # {'Timestamp': '/Date(1657587898574)/', 'Source': 'IceOfWraith', 'Type': 'Chat', 'Contents': 'This is a local message','Prefix': 'Discord_Chat_Prefix}
        # Currently all servers set "Type" to Chat! So lets use those.
        self.logger.dev(
            f"Chat Channel: {self.AMPInstance.Discord_Chat_Channel} | Chat Prefix: {self.DB_Server.Discord_Chat_Prefix} | Event Channel: {self.AMPInstance.Discord_Event_Channel}"
        )
        if message["Type"] == "Chat":
            for sender in self.AMPInstance.SenderFilterList:
                if message["Source"].lower() == sender.lower():
                    self.logger.dev(f"Filtered Message: {message}")
                    return

            # Removed the odd character for color indicators on text
            message["Contents"] = message["Contents"].replace("�", "")

            self.console_chat_message_lock.acquire()
            self.console_chat_messages.append(message)
            self.console_chat_message_lock.release()

            self.console_message_lock.acquire()
            self.console_messages.append(f"{message['Source']}: {message['Contents']}")
            self.console_message_lock.release()
            return True
        return False

    # def console_events(self, message):
    #     """This will handle all player join/leave/disconnects and other achievements. THIS SHOULD ALWAYS RETURN FALSE!
    #     ALL events go to `self.console_event_messages` """
    #     return False
