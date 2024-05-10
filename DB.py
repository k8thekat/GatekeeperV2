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

import datetime
import json
import logging
import pathlib
import sqlite3
import time
from typing import Union

from DB_Update import DB_Update


def dump_to_json(data):
    for entry in data:
        if type(data[entry]) == datetime.datetime:
            data[entry] = data[entry].isoformat()
        elif type(data[entry]) == bool:
            data[entry] = int(data[entry])
    return json.dumps(data)


Handler = None
#!DB Version
DB_Version = 3.0


class DBHandler():
    def __init__(self):
        global DB_Version
        self.logger = logging.getLogger(__name__)
        self.DB = Database(Handler=self)
        self.DBConfig = self.DB.DBConfig
        self.SuccessfulDatabase = True
        self.Bot_Version = ''
        self.bot_sync_required = False

        # Always update this value when changing Tables!
        self.DB_Version = DB_Version

        # self.DBConfig.SetSetting('DB_Version', 2.5)
        # This should ONLY BE TRUE on new Database's going forward.
        if self.DBConfig.GetSetting('DB_Version') == None and self.DB.DBExists:
            DB_Update(self.DB, 1.0)
            return

        # This is to handle 1.0.0 Converting to new DB Version systems.
        if type(self.DBConfig.GetSetting('DB_Version')) == str and self.DBConfig.GetSetting('DB_Version') == '1.0.0':
            self.DBConfig.SetSetting('DB_Version', '1.0')

        # This handles version checks and calling all updates from version 1.0
        if self.DB_Version > float(self.DBConfig.GetSetting('DB_Version')):
            self.logger.warn(f"**ATTENTION** Gatekeeperv2 Database is on Version: {self.DB_Version}, your Database is on Version: {self.DBConfig.GetSetting('DB_Version')}")
            self.DBUpdate = DB_Update(self.DB, float(self.DBConfig.GetSetting('DB_Version')))

        self.logger.info(f'DB Handler Initialization...DB Version: {self.DBConfig.GetSetting("DB_Version")}')

    def dbServerConsoleSetup(self, server):
        """This sets the DB Server Console_Flag, Console_Filtered and Discord_Console_Channel to default values"""
        self.DB_Server = self.DB.GetServer(server.InstanceID)
        try:
            self.DB_Server.Console_Flag = True
            self.DB_Server.Console_Filtered = True
            self.DB_Server.Discord_Console_Channel = None  # Should be a str, can be an int. eg 289450670581350401
        except:
            self.logger.warning(f'**ATTENTION** DBConfig Default Console Settings have been set for {server.FriendlyName}')


def getDBHandler() -> DBHandler:
    global Handler
    if Handler == None:
        Handler = DBHandler()
    return Handler


class Database:
    def __init__(self, Handler=None):
        self.DBExists = False

        db_file = pathlib.Path("discordBot.db")
        if pathlib.Path.exists(db_file):
            self.DBExists = True

        if Handler:
            self.DBHandler = Handler
        else:
            self.DBHandler = getDBHandler()

        self._db = sqlite3.connect("discordBot.db", detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        if not self.DBExists:
            self._InitializeDatabase()
            # self._InitializeDefaultData()
        self.DBConfig = self.GetConfig()

    def _InitializeDatabase(self):
        global DB_Version
        cur = self._db.cursor()

        cur.execute("""create table Servers (
                        ID integer primary key,
                        InstanceID text not null unique collate nocase,
                        InstanceName text,
                        FriendlyName text,
                        DisplayName text,
                        Host text,
                        Whitelist integer not null,
                        Whitelist_disabled integer not null,
                        Donator integer not null,
                        Console_Flag integer not null,
                        Console_Filtered integer not null,
                        Console_Filtered_Type integer not null,
                        Discord_Console_Channel text nocase,
                        Discord_Chat_Channel text nocase,
                        Discord_Chat_Prefix text,
                        Discord_Event_Channel text nocase,
                        Discord_Role text collate nocase,
                        Avatar_url text,
                        Hidden integer not null
                        )""")

        cur.execute("""create table RegexPatterns (
                        ID integer primary key,
                        Name text unique not null,
                        Type integer not null,
                        Pattern text unique not null
                        )""")

        cur.execute("""create table ServerRegexPatterns (
                        ServerID integer not null,
                        RegexPatternID integer not null,
                        foreign key (RegexPatternID) references RegexPatterns(ID),
                        foreign key (ServerID) references Servers(ID)
                        UNIQUE(ServerID, RegexPatternID)
                        )""")

        cur.execute("""create table Users (
                        ID integer primary key,
                        DiscordID text not null unique collate nocase,
                        DiscordName text collate nocase,
                        MC_IngameName text unique collate nocase,
                        MC_UUID text unique collate nocase,
                        SteamID text unique collate nocase,
                        Role text collate nocase
                        )""")

        cur.execute("""create table BannerGroup (
                        ID integer primary key,
                        name text unique
                        )""")

        cur.execute("""create table BannerGroupServers (
                        ServerID integer not null,
                        BannerGroupID integer not null,
                        foreign key (ServerID) references Servers(ID),
                        foreign key (BannerGroupID) references BannerGroup(ID)
                        )""")

        cur.execute("""create table BannerGroupChannels (
                        ID integer primary key,
                        Discord_Channel_ID integer,
                        Discord_Guild_ID integer,
                        BannerGroupID integer not null,
                        foreign key (BannerGroupID) references BannerGroup(ID)
                        )""")

        cur.execute("""create table BannerGroupMessages (
                        BannerGroupChannelsID integer not null,
                        Discord_Message_ID integer,
                        foreign key (BannerGroupChannelsID) references BannerGroupChannels(ID)
                        )""")

        cur.execute("""create table ServerBanners (
                        ServerID integer not null,
                        background_path text,
                        blur_background_amount integer,
                        color_header text,
                        color_body text,
                        color_host text,
                        color_whitelist_open text,
                        color_whitelist_closed text,
                        color_donator text,
                        color_status_online text,
                        color_status_offline text,
                        color_player_limit_min text,
                        color_player_limit_max text,
                        color_player_online text,
                        foreign key(ServerID) references Servers(ID)
                        )""")

        cur.execute("""create table WhitelistReply (
                        ID integer primary key,
                        Message text
                        )""")

        cur.execute("""create table Log (
                        ID integer primary key,
                        Log text not null,
                        LogDate timestamp default (datetime('now'))
                        )""")

        cur.execute("""create table Config (
                        ID integer primary key,
                        Name text not null unique,
                        Value text
                        )""")

        self._db.commit()

        # Any Default Config Settings should go here during INIT.
        # Still keep the ones in Update; just in case existing DBs need updating.
        self._AddConfig('DB_Version', DB_Version)
        self._AddConfig('Guild_ID', None)
        self._AddConfig('Moderator_role_id', None)
        self._AddConfig('Permissions', 0)  # 0 = Default | 1 = Custom
        # self._AddConfig('Server_Info_Display', None)
        self._AddConfig('Whitelist_Request_Channel', None)
        self._AddConfig('WhiteList_Wait_Time', 5)
        self._AddConfig('Auto_Whitelist', False)
        # self._AddConfig('Whitelist_Emoji_Pending', ':arrows_counterclockwise:')
        # self._AddConfig('Whitelist_Emoji_Done', ':ballot_box_with_check:')
        self._AddConfig('Banner_Auto_Update', True)
        self._AddConfig('Banner_Type', 0)  # 0 = Discord embeds | 1 = Custom Banner Images
        self._AddConfig('Bot_Version', None)
        self._AddConfig('Message_Timeout', 60)
        # Donator Settings
        self._AddConfig('Donator_Bypass', False)
        self._AddConfig("Donator_role_id", None)
        # Prevent Server being removed from Banner Group
        self._AddConfig("Auto_BG_Remove", False)

    def _execute(self, SQL, params):
        Retry = 0

        while (1):
            try:
                cur = self._db.cursor()
                cur.execute(SQL, params)
                cur.close()
                self._db.commit()
                return

            except sqlite3.OperationalError as ex:
                # if locked then try up to 3 times before bailing
                if Retry == 3:
                    raise Exception(ex)
                Retry += 1
                time.sleep(0.1)
                continue

            except Exception as e:
                raise e

    def _fetchone(self, SQL, params):
        cur = self._db.cursor()
        cur.execute(SQL, params)
        return (cur.fetchone(), cur)

    def _fetchall(self, SQL, params):
        cur = self._db.cursor()
        cur.execute(SQL, params)
        return (cur.fetchall(), cur)

    def _logdata(self, data):
        self._execute("insert into log(log) values(?)", (data,))

    def _UpdateServer(self, dbserver, **args):
        # get the property to update
        entry = list(args.keys())[0]
        self._execute(f"Update servers set {entry}=? where ID=?", (args[entry], dbserver.ID))
        jdata = dump_to_json({"Type": "ServerUpdate", "ServerID": dbserver.ID, "Field": entry, "Value": args[entry]})
        self._logdata(jdata)

    def _UpdateBanner(self, dbbanner, **args):
        entry = list(args.keys())[0]
        self._execute(f"Update ServerBanners set {entry}=? where ServerID=?", (args[entry], dbbanner.ServerID))
        jdata = dump_to_json({"Type": "BannerUpdate", "ServerID": dbbanner.ServerID, "Field": entry, "Value": args[entry]})
        self._logdata(jdata)

    def _UpdateUser(self, dbuser, **args):
        # get the property to update
        entry = list(args.keys())[0]
        self._execute(f"Update users set {entry}=? where ID=?", (args[entry], dbuser.ID))
        jdata = dump_to_json({"Type": "UserUpdate", "UserID": dbuser.ID, "Field": entry, "Value": args[entry]})
        self._logdata(jdata)

    def AddServer(self, InstanceID: str, InstanceName: str = None, FriendlyName: str = None):
        return DBServer(db=self, InstanceID=InstanceID, InstanceName=InstanceName, FriendlyName=FriendlyName)

    def GetServer(self, InstanceID: str = None, ServerID: str = None):
        if not InstanceID and not ServerID:
            return None

        if ServerID:
            return DBServer(ID=int(ServerID), db=self)

        (row, cur) = self._fetchone("select ID from Servers where InstanceID=?", (InstanceID,))
        if not row:
            cur.close()
            return None
        # create a new server to return and let the object populate itself
        ret = DBServer(ID=int(row["ID"]), db=self)

        cur.close()
        return ret

    def GetAllServers(self):
        """Gets all Servers current in the DB"""
        serverlist = {}
        SQLArgs = []

        (rows, cur) = self._fetchall("Select ID from Servers", tuple(SQLArgs))
        for entry in rows:
            Server = DBServer(self, ID=entry["ID"])
            serverlist[Server.InstanceID] = ('InstanceName: ' + Server.InstanceName)

        cur.close()
        return serverlist

    def GetUser(self, value: str):
        """Finds a User using either DiscordID, DiscordName, MC_InGameName, MC_UUID, or SteamID."""
        # find the user
        (row, cur) = self._fetchone(f"select ID from Users where DiscordID=? or DiscordName=? or MC_IngameName=? or MC_UUID=? or SteamID=?", (value, value, value, value, value))
        if not row:
            cur.close()
            return None

        # create a new user object to return and let the object populate itself
        ret = DBUser(ID=int(row["ID"]), db=self)

        cur.close()
        return ret

    def AddUser(self, DiscordID: str = None, DiscordName: str = None, MC_IngameName: str = None, MC_UUID: str = None, SteamID: str = None):
        try:
            return DBUser(db=self, DiscordID=DiscordID, DiscordName=DiscordName, MC_IngameName=MC_IngameName, MC_UUID=MC_UUID, SteamID=SteamID)
        except Exception as e:
            print('DBUser error', e)
            return None

    def GetAllUsers(self):
        # get all servers that we are on
        SQL = "Select ID from Users"
        SQLWhere = []
        SQLArgs = []

        if len(SQLWhere):
            SQL = SQL + " where " + " and ".join(SQLWhere)

        (rows, cur) = self._fetchall(SQL, tuple(SQLArgs))
        ret = []
        for entry in rows:
            User = DBUser(self, ID=entry["ID"])
            ret.append(User)

        cur.close()
        return ret

    def AddRegexPattern(self, Name: str, Pattern: str, Type: int) -> bool:
        """Adds a entry to table RegexPatterns, else Updates a matching pattern."""
        try:
            self._execute("INSERT into RegexPatterns(Name, Type, Pattern) values(?, ?, ?)", (Name, Type, Pattern))
        except Exception as e:
            print(e)
            return False
        return True

    def DelRegexPattern(self, ID: int = None, Name: str = None) -> bool:
        """Removes a entry RegexPatterns Table using either its `Name` or `ID`"""
        if ID == None:
            (row, cur) = self._fetchone("SELECT ID FROM RegexPatterns WHERE Name=?", (Name,))
            if not row:
                cur.close()
                return False
            ID = row["ID"]
            cur.close()
        try:
            self._execute("DELETE FROM ServerRegexPatterns WHERE RegexPatternID =?", (ID,))
        except Exception as e:
            print(e)

        self._execute("DELETE FROM RegexPatterns WHERE ID=?", (ID,))
        return True

    def GetRegexPattern(self, ID: int = None, Name: str = None):
        """Returns RegexPatterns Table \n
        Returns `row['ID'] = {'Name': row['Name'], 'Type': row['Type'], 'Pattern': row['Pattern']}`
        """
        (row, cur) = self._fetchone("SELECT ID, Name, Type, Pattern FROM RegexPatterns WHERE Name=? or ID=?", (Name, ID))
        if not row:
            cur.close()
            return False

        regex = {'ID': row['ID'], 'Name': row['Name'], 'Type': row['Type'], 'Pattern': row['Pattern']}
        cur.close()
        return regex

    def UpdateRegexPattern(self, Pattern: str = None, Type: int = None, ID: int = None, Pattern_Name: str = None, Name: str = None) -> bool:
        """Update a Regex Pattern in the RegexPatterns Table using either its `Name` or `ID`"""
        if ID == None:
            (row, cur) = self._fetchone("SELECT ID FROM RegexPatterns WHERE Name=?", (Pattern_Name,))
            if not row:
                cur.close()
                return False
            ID = row["ID"]
            cur.close()

        SQL = "UPDATE RegexPatterns SET "
        SQL_Val = ''
        SQLArgs = []

        args = locals()
        for arg in args:
            if args[arg] != None and arg in ['Pattern', 'Type', 'Name']:
                if len(SQL_Val):
                    SQL_Val = SQL_Val + ','

                SQL_Val = SQL_Val + f'{arg}=? '
                SQLArgs.append(args[arg])

        SQL = SQL + SQL_Val + 'WHERE ID=?'
        SQLArgs.append(ID)  # Need to append ID last.
        self._execute(SQL, tuple(SQLArgs))
        return True

    def GetAllRegexPatterns(self):
        """Gets all Regex Patterns from the RegexPatterns Table. \n
        Returns `dict[entry['ID']] = {'Name': entry['Name'], 'Type': entry['Type'], 'Pattern': entry['Pattern']}`"""
        regex_patterns = {}
        SQLArgs = []
        (rows, cur) = self._fetchall("SELECT ID, Name, Type, Pattern FROM RegexPatterns ORDER BY ID", tuple(SQLArgs))
        for entry in rows:
            regex_patterns[entry['ID']] = {'Name': entry['Name'], 'Type': entry['Type'], 'Pattern': entry['Pattern']}

        cur.close()
        return regex_patterns

    def GetAllWhitelistReplies(self):
        """Gets all Whitelist Replies currently in the DB"""
        whitelist_replies = []
        SQLArgs = []

        (rows, cur) = self._fetchall("SELECT ID, Message FROM WhitelistReply ORDER BY ID", tuple(SQLArgs))
        for entry in rows:
            # reply = {'ID' : entry["ID"], 'Message' : entry["Message"]}
            # reply = {entry["Message"]}
            whitelist_replies.append(entry['Message'])

        cur.close()
        return whitelist_replies

    def AddWhitelistReply(self, Message: str = None):
        """Adds a Whitelist Reply to the DB"""
        self._execute("INSERT INTO WhitelistReply(Message) values(?)", (Message,))
        return

    def DeleteWhitelistReply(self, Message: str = None):
        """Deletes a Whitelist Reply from the DB"""
        self._execute("DELETE FROM WhitelistReply WHERE Message=?", (Message,))
        return

    # Banner Group ----------------------------------------------------------------------------------------------------------------------------------------------------------
    def Add_BannerGroup(self, name: str):
        """Creates a Banner Group Table with the provided `name`"""
        self._execute("INSERT INTO BannerGroup(name) values(?)", (name,))
        return

    def Get_BannerGroup(self, name: str = None, ID: int = None):
        """Selects a Banner Group Table matching the `name` provided."""
        (ret, cur) = self._fetchone("SELECT ID FROM BannerGroup WHERE name=? or ID=?", (name, ID,))
        if not ret:
            return None
        cur.close()
        return ret["ID"]

    def Update_BannerGroup(self, new_name: str, name: str):
        """Update a Banner Group"""
        banner_id = self.Get_BannerGroup(name)
        (ret, cur) = self._fetchone("UPDATE BannerGroup SET name=? WHERE ID=?", (new_name, banner_id))
        if not ret:
            return
        cur.close()
        return

    def Get_one_BannerGroup_info(self, name: str) -> Union[None, dict[str, int]]:
        """Gets a Specific Banner Groups full information\n
        return `Banner_info[entry['name']] = {'InstanceName': list[entry['InstanceName']], 'Discord_Channel': list[entry['Discord_Channel_ID']]}`"""
        banner_id = self.Get_BannerGroup(name)
        Banner_info = {}
        (row, cur) = self._fetchall("""SELECT BG.*, Servers.InstanceName FROM Servers, BannerGroup as BG, BannerGroupServers as BGS 
                                    WHERE BG.ID=? AND Servers.ID=BGS.ServerID AND BGS.BannerGroupID=BG.ID""", (banner_id,))

        if row:
            for entry in row:
                if entry['name'] not in Banner_info:
                    Banner_info[entry['name']] = {'InstanceName': [], 'Discord_Channel': []}

                if entry['InstanceName'] not in Banner_info[entry['name']]['InstanceName']:
                    Banner_info[entry['name']]['InstanceName'].append(entry['InstanceName'])

        (row, cur) = self._fetchall("""SELECT BG.*, BGC.Discord_Channel_ID FROM BannerGroup as BG, BannerGroupChannels as BGC
                                    WHERE BG.ID=? AND BGC.BannerGroupID=BG.ID""", (banner_id,))
        if row:
            for entry in row:
                if entry['name'] not in Banner_info:
                    Banner_info[entry['name']] = {'InstanceName': [], 'Discord_Channel': []}

                if entry['Discord_Channel_ID'] not in Banner_info[entry['name']]['Discord_Channel']:
                    Banner_info[entry['name']]['Discord_Channel'].append(entry['Discord_Channel_ID'])

        cur.close()
        return Banner_info

    def Get_All_BannerGroups(self) -> Union[None, dict[str, str]]:
        """Gets all BannerGroups Names/IDs\n
        returns `Banners[entry["ID"]] = entry["name"]`"""
        Banners = {}
        (row, cur) = self._fetchall("SELECT * FROM BannerGroup", ())
        if not row:
            return
        for entry in row:
            Banners[entry["ID"]] = entry["name"]
        cur.close()
        return Banners

    def Delete_BannerGroup(self, name: str):
        """Removes a Banner Group."""
        banner_id = self.Get_BannerGroup(name)
        if banner_id != None:
            self._execute("DELETE FROM BannerGroupServers WHERE BannerGroupID=?", (banner_id,))
            (row, cur) = self._fetchall("SELECT ID FROM BannerGroupChannels WHERE BannerGroupID=?", (banner_id,))
            if row:
                for entry in row:
                    self._execute("DELETE FROM BannerGroupMessages WHERE BannerGroupChannelsID=?", (entry["ID"],))
                    self._execute("DELETE FROM BannerGroupChannels WHERE ID=?", (entry["ID"],))

            # Lastly we delete our BannerGroup Table entry.
            self._execute("DELETE FROM BannerGroup WHERE ID=?", (banner_id,))
            cur.close()

    def Get_All_BannerGroup_Info(self) -> Union[None, dict[str, int]]:
        """Gets all the BannerGroups and sorts them by `Discord_Channel_ID`.\n
        `example: {916195413839712277: {'name': 'TestBannerGroup', 'guild_id': 602285328320954378, 'servers': [1], 'messages': [1079236992145051668]}}`"""
        Banners = {}
        # We need to get each BannerGroupID and then get the corresponding Discord_Message_IDs, ServerIDs and Name from related tables.
        (row, cur) = self._fetchall("""SELECT BGC.*, BGS.ServerID, BG.name, BG.ID, BGM.Discord_Message_ID
                                        FROM BannerGroup as BG, BannerGroupServers as BGS, BannerGroupChannels as BGC 
                                        LEFT JOIN BannerGroupMessages as BGM                       
                                        ON BGM.BannerGroupChannelsID=BGC.ID
                                        WHERE BGS.BannerGroupID=BG.ID and BGC.BannerGroupID=BG.ID
                                        ORDER BY BGC.Discord_Channel_ID""", ())

        for entry in row:
            # if BannerGroupChannels.Discord_Channel_ID not in Banners:
            if entry["Discord_Channel_ID"] not in Banners:
                Banners[entry["Discord_Channel_ID"]] = {"name": entry["name"], "guild_id": entry["Discord_Guild_ID"], "servers": [], "messages": []}

            # if BannerGroupServers.ServerID not in Banners:
            if entry["ServerID"] not in Banners[entry["Discord_Channel_ID"]]["servers"]:
                Banners[entry["Discord_Channel_ID"]]["servers"].append(entry["ServerID"])

            # if BannerGroupMessages.Discord_Message_ID not in Banners
            if entry["Discord_Message_ID"] not in Banners[entry["Discord_Channel_ID"]]["messages"]:
                Banners[entry["Discord_Channel_ID"]]["messages"].append(entry["Discord_Message_ID"])

        cur.close()
        return Banners

    def Add_Server_to_BannerGroup(self, banner_groupname: str, instanceID: str):
        """Add a Server to an existing Banner Group."""
        banner_id = self.Get_BannerGroup(banner_groupname)
        (ret, cur) = self._fetchone("SELECT ID FROM Servers WHERE InstanceID=?", (instanceID,))
        # If we fail to find the Server by Instance ID; just return.
        if not ret:
            cur.close()
            return

        server_id = ret["ID"]
        # Lets use our ServerID and attempt to find a match in our DB. Ideally we don't want a match; so we can add an entry. Otherwise we return.
        (ret, cur) = self._fetchone("SELECT ServerID FROM BannerGroupServers WHERE ServerID=? and BannerGroupID=?", (server_id, banner_id))
        if not ret and banner_id != None:
            self._execute("INSERT INTO BannerGroupServers(ServerID, BannerGroupID) values(?, ?)", (server_id, banner_id))
            return True
        cur.close()
        return False

    def Remove_Server_from_BannerGroup(self, banner_groupname: str, instanceID: str):
        """Removes a Server from an existing Banner Group."""
        (ret, cur) = self._fetchone("SELECT ID FROM Servers WHERE InstanceID=?", (instanceID,))
        if not ret:
            return
        banner_id = self.Get_BannerGroup(banner_groupname)
        print(ret["ID"], banner_id)
        if banner_id != None:
            self._execute("DELETE FROM BannerGroupServers WHERE ServerID=? AND BannerGroupID=?", (ret["ID"], banner_id))
        cur.close()

    def Add_Channel_to_BannerGroup(self, banner_groupname: str, channelid: int, guildid: int):
        """Add a Channel to a BannerGroups listing."""
        banner_id = self.Get_BannerGroup(banner_groupname)
        (ret, cur) = self._fetchone("SELECT ID FROM BannerGroupChannels WHERE Discord_Channel_ID=? and Discord_Guild_ID=? and BannerGroupID=?", (channelid, guildid, banner_id))
        if not ret and banner_id != None:
            self._execute("INSERT INTO BannerGroupChannels(Discord_Channel_ID, Discord_Guild_ID, BannerGroupID) values(?, ?, ?)", (channelid, guildid, banner_id))
            return True
        cur.close()
        return False

    def Remove_Channel_from_BannerGroup(self, channelid: int, guildid: int):
        """Remove a Channel from a BannerGroups listing, this also removes any related Banner Group Message table entries."""
        (ret, cur) = self._fetchone("SELECT BannerGroupID FROM BannerGroupChannels WHERE Discord_Channel_ID=? and Discord_Guild_ID=?", (channelid, guildid))
        if not ret:
            return
        banner_id = ret["BannerGroupID"]
        (ret, cur) = self._fetchone("SELECT ID FROM BannerGroupChannels WHERE BannerGroupID=? AND Discord_Channel_ID=?", (banner_id, channelid))
        if not ret:
            return
        self._execute("DELETE FROM BannerGroupMessages WHERE BannerGroupChannelsID=?", (ret["ID"],))
        self._execute("DELETE FROM BannerGroupChannels WHERE BannerGroupID=? AND Discord_Channel_ID=? AND Discord_Guild_ID=?", (banner_id, channelid, guildid))
        cur.close()

    def Get_Channels_for_BannerGroup(self, banner_groupname: str):
        """Returns a list of existing BannerGroups Discord Channel IDs."""
        banner_id = self.Get_BannerGroup(banner_groupname)
        bgc_list = []
        if banner_id != None:
            # We need to get the BGC ID matching the Banner Group ID and Discord Channel ID First.
            (row, cur) = self._fetchall("SELECT Discord_Channel_ID FROM BannerGroupChannels WHERE BannerGroupID=?", (banner_id,))
            if not row:
                return
            for entry in row:
                if entry['Discord_Channel_ID'] not in bgc_list:
                    bgc_list.append(entry['Discord_Channel_ID'])
            cur.close()
            return bgc_list

    def Add_Message_to_BannerGroup(self, banner_groupname: str, channelid: int, messageid: int):
        """Adds a Discord Message ID to a BannerGroup"""
        banner_id = self.Get_BannerGroup(banner_groupname)
        if banner_id != None:
            # We need to get the BannerGroupChannel ID and add Messages using its ID
            (ret, cur) = self._fetchone("SELECT ID from BannerGroupChannels WHERE BannerGroupID=? AND Discord_Channel_ID=?", (banner_id, channelid))
            if not ret:
                return
            BGC_ID = ret["ID"]
            cur.close()
            self._execute("INSERT INTO BannerGroupMessages(BannerGroupChannelsID, Discord_Message_ID) values(?, ?)", (BGC_ID, messageid))

    def Remove_Message_from_BannerGroup(self, messageid: int):
        """Removes a Discord Message ID from a BannerGroup"""
        self._execute("DELETE FROM BannerGroupMessages WHERE Discord_Message_ID=?", (messageid,))

    def Get_Messages_for_BannerGroup(self, banner_groupname: str):
        """Returns a dictionary with key = `Discord_Channel_ID` and value = list[`Discord_Message_ID`]"""
        banner_id = self.Get_BannerGroup(banner_groupname)
        if banner_id == None:
            return
        (ret, cur) = self._fetchall("""SELECT Discord_Message_ID, BannerGroupChannels.ID, BannerGroupChannels.Discord_Channel_ID FROM BannerGroupMessages, BannerGroupChannels 
                                    WHERE BannerGroupChannels.BannerGroupID=? and BannerGroupMessages.BannerGroupChannelsID=BannerGroupChannels.ID""", (banner_id,))
        banner_info = {}
        for entry in ret:
            if entry["Discord_Channel_ID"] not in banner_info:
                banner_info[entry["Discord_Channel_ID"]] = {'messages': []}
            if entry["Discord_Message_ID"] not in banner_info[entry["Discord_Channel_ID"]]:
                banner_info[entry["Discord_Channel_ID"]]["messages"].append(entry["Discord_Message_ID"])
        cur.close()
        return banner_info

    def get_all_bannergroup_messages(self):
        """Grabs all entries inside BannerGroupMessages table"""
        (ret, cur) = self._fetchone("""SELECT count(Discord_Message_ID) AS num FROM BannerGroupMessages""", ())
        cur.close()
        if not ret:
            return 0
        else:
            return ret["num"]

    def _AddConfig(self, Name, Value):
        self._execute("Insert into config(Name, Value) values(?, ?)", (Name, Value))
        (ret, cur) = self._fetchone("Select ID from Config where Name=?", (Name,))
        if not ret:
            return None
        ID = int(ret["ID"])
        cur.close()
        jdata = dump_to_json({"Type": "AddConfig", "Name": Name, "Value": Value})
        self._logdata(jdata)
        return ID

    def GetConfig(self):
        return DBConfig(self)

    def _DeleteConfig(self, ConfigID, ConfigName):
        self._execute("Delete from Config where ID=?", (ConfigID,))
        jdata = dump_to_json({"Type": "DeleteConfig", "Name": ConfigName})
        self._logdata(jdata)

    def _UpdateConfig(self, ID, Name, Value):
        self._execute("Update Config set Value=? where ID=?", (Value, ID))
        jdata = dump_to_json({"Type": "UpdateConfig", "Name": Name, "Value": Value})
        self._logdata(jdata)

    def GetLog(self, AfterTime: datetime.datetime = None, BeforeTime: datetime.datetime = None, StartingID: int = None, Limit: int = 100):
        SQL = "Select L.ID, L.Log, L.LogDate from Log L"
        Params = []
        if StartingID or AfterTime or BeforeTime:
            NeedAND = False
            SQL += " Where "
            if StartingID:
                SQL += " L.ID >= ? "
                Params.append(StartingID)
                NeedAND = True
            if AfterTime:
                if NeedAND:
                    SQL += " and "
                SQL += " L.LogDate > "
                Params.append(AfterTime)
                NeedAND = True
            if BeforeTime:
                if NeedAND:
                    SQL += " and "
                SQL += " L.LogDate < "
                Params.append(BeforeTime)
                NeedAND = True
        SQL += " order by L.LogDate "
        if Limit:
            SQL += " Limit ?"
            Params.append(Limit)

        NeededUsers = []
        NeededServers = []
        (rows, cur) = self._fetchall(SQL, tuple(Params))
        ret = []
        for entry in rows:
            logentry = {}
            logentry["ID"] = entry["ID"]
            logentry["Log"] = json.loads(entry["Log"])
            logentry["Date"] = entry["LogDate"]
            ret.append(logentry)

            # if we have a userid, serverid, or modid in the log json then store it as needed
            if ("UserID" in logentry["Log"]) and (logentry["Log"]["UserID"] not in NeededUsers):
                NeededUsers.append(logentry["Log"]["UserID"])
            if ("ModID" in logentry["Log"]) and (logentry["Log"]["ModID"] not in NeededUsers):
                NeededUsers.append(logentry["Log"]["ModID"])
            if ("ServerID" in logentry["Log"]) and (logentry["Log"]["ServerID"] not in NeededServers):
                NeededServers.append(logentry["Log"]["ServerID"])

        cur.close()

        # go get all of the users to fill in
        Users = {}
        while len(NeededUsers):
            Count = len(NeededUsers)
            if len(NeededUsers) > 50:
                Count = 50
            qentries = ("?," * Count)[:-1]
            Params = tuple(NeededUsers[0:Count])
            NeededUsers = NeededUsers[Count:]
            (rows, cur) = self._fetchall(f"Select ID, DiscordID, DiscordName, IngameName, UUID from Users where ID in ({qentries})", tuple(Params))
            for entry in rows:
                Users[int(entry["ID"])] = {"DiscordID": int(entry["DiscordID"]), "DiscordName": entry["DiscordName"], "IngameName": entry["IngameName"], "UUID": entry["UUID"]}
            cur.close()

        # get servers
        Servers = {}
        while len(NeededServers):
            Count = len(NeededServers)
            if len(NeededServers) > 50:
                Count = 50
            qentries = ("?," * Count)[:-1]
            Params = tuple(NeededServers[0:Count])
            NeededServers = NeededServers[Count:]
            (rows, cur) = self._fetchall(f"Select ID, InstanceName from Servers where ID in ({qentries})", tuple(Params))
            for entry in rows:
                Servers[int(entry["ID"])] = entry["InstanceName"]
            cur.close()

        # now update all log entries
        for entry in ret:
            if "UserID" in entry["Log"]:
                UID = int(entry["Log"]["UserID"])
                if UID in Users:
                    entry["Log"].pop("UserID")
                    entry["Log"]["User_DiscordID"] = int(Users[UID]["DiscordID"])
                    entry["Log"]["User_DiscordName"] = Users[UID]["DiscordName"]
                    entry["Log"]["User_IngameName"] = Users[UID]["IngameName"]
            if "ModID" in entry["Log"]:
                MID = int(entry["Log"]["ModID"])
                if MID in Users:
                    entry["Log"].pop("ModID")
                    entry["Log"]["Mod_DiscordID"] = int(Users[MID]["DiscordID"])
                    entry["Log"]["Mod_DiscordName"] = Users[MID]["DiscordName"]
                    entry["Log"]["Mod_IngameName"] = Users[MID]["IngameName"]
            if "ServerID" in entry["Log"]:
                if entry["Log"]["ServerID"] in Servers:
                    entry["Log"]["Server"] = Servers[int(entry["Log"]["ServerID"])]
                    entry["Log"].pop("ServerID")

        return ret


class DBUser:
    ID: int
    DiscordID: str
    DiscordName: str
    MC_IngameName: str
    MC_UUID: str
    SteamID: str
    Role: str

    def __init__(self, db: Database, ID: int = None, DiscordID: str = None, DiscordName: str = None, MC_IngameName: str = None, MC_UUID: str = None, SteamID: str = None, Role: str = None):
        # set defaults
        Params = locals()
        Params.pop("self")
        Params.pop("db")
        Params.pop("__class__")
        super().__setattr__("_db", db)
        for entry in Params:
            super().__setattr__(entry, Params[entry])

        # if given a database and ID then look up our values
        if ID:
            (row, cur) = self._db._fetchone("Select * From Users where ID=?", (ID,))
            if row:
                for entry in row.keys():
                    super().__setattr__(entry, row[entry])
            else:
                raise Exception(f"Unable to locate User ID {ID}")
            cur.close()
            super().__setattr__("ID", int(self.ID))
            # super().__setattr__("DiscordID", int(self.DiscordID))
        else:
            # we should have a discord id
            if not DiscordID or DiscordID == 0:
                raise Exception("Missing discord ID on new user")

            # add user to the database
            DBFields = Params

            # create the sql line
            SQL = "insert into users ("
            SQLVars = []

            for entry in DBFields:
                if DBFields[entry] != None:
                    SQL += entry + ","
                    SQLVars.append(DBFields[entry])

            SQL = SQL[:-1] + ") values (" + ("?," * len(SQLVars))[:-1] + ")"
            # create the tuple needed
            SQLTuple = tuple(SQLVars)

            # execute it
            self._db._execute(SQL, SQLTuple)

            # now find the ID
            (row, cur) = self._db._fetchone("Select ID From Users where DiscordID=?", (DiscordID,))
            if row:
                super().__setattr__("ID", int(row["ID"]))
            else:
                raise Exception(f"Unable to locate new user with Discord ID {DiscordID}")
            cur.close()

            jdata = dump_to_json({"Type": "AddUser", "UserID": self.ID})
            self._db._logdata(jdata)

        super().__setattr__("DiscordID", int(self.DiscordID))

    def __setattr__(self, name: str, value):
        if (name == "ID") or (name[0] == "_"):
            return

        elif name == "DiscordID":
            # conver to int
            value = int(value)

        # set value and update the user
        super().__setattr__(name, value)
        self._db._UpdateUser(self, **{name: value})


class DBServer:
    """DB Server Attributes:
        `InstanceID: str` \n
        `InstanceName: str` \n
        `FriendlyName: str` \n
        `DisplayName: str` \n
        `Description: str` \n
        `Host: str` \n
        `Whitelist: bool (0/1)` \n
        `Whitelist_disabled: bool` \n
        `Donator: bool (0/1)` \n
        `Discord_Console_Channel: int` \n
        `Discord_Chat_Channel: int` \n
        `Discord_Chat_Prefix: str` \n
        `Discord_Event_Channel: int` \n
        `Discord_Role: int` \n
        `Console_Flag: bool (0/1)` \n
        `Console_Filtered: bool (0/1)` \n
        `Console_Filtered_Type: integer (0 = Blacklist| 1 = Whitelist)` \n
        `Avatar_url: str` \n
        `Hidden: bool (0/1)` \n
        """

    def __init__(self, db: Database, ID: int = None, InstanceID: str = None, InstanceName: str = None, FriendlyName: str = None):
        # set defaults
        Params = locals()
        Params.pop("self")
        Params.pop("db")
        Params.pop("__class__")
        super().__setattr__("_db", db)
        server_attr = {'DisplayName': None,
                       'Description': None,
                       'Host': '192.168.1.1',
                       'Whitelist': False,
                       'Whitelist_disabled': 0,
                       'Donator': 0,
                       'Console_Flag': 1,
                       'Console_Filtered': 0,
                       'Console_Filtered_Type': 0,
                       'Discord_Console_Channel': None,
                       'Discord_Chat_Channel': None,
                       'Discord_Chat_Prefix': None,
                       'Discord_Event_Channel': None,
                       'Discord_Role': None,
                       'Avatar_url': None,
                       'Hidden': 0
                       }

        for key, value in server_attr.items():
            super().__setattr__(key, value)

        for entry in Params:
            super().__setattr__(entry, Params[entry])

        if (self.ID is not None):
            super().__setattr__("ID", int(self.ID))

        # if given a database and ID then look up our values
        if ID:
            (row, cur) = self._db._fetchone("Select * From Servers where ID=?", (ID,))
            if row:
                for entry in row.keys():
                    super().__setattr__(entry, row[entry])
            else:
                raise Exception(f"Unable to locate Server ID {ID}")
            cur.close()
        else:
            # we should have an InstanceID
            if not InstanceID or (not len(InstanceID)):
                raise Exception("Missing friendly name on server")

            # add server to the database after making sure the friendly name isn't already used as a nickname
            server = self._db.GetServer(InstanceID)
            if server:
                raise Exception("InstanceID already found")

           # DBFields = Params

            # create the sql line
            SQL = "insert into Servers ("
            SQLVars = []

            for key, value in Params.items():
                if value is not None:
                    SQL += key + ","
                    SQLVars.append(value)

            for key, value in server_attr.items():
                if value is not None:
                    SQL += key + ","
                    SQLVars.append(value)

            SQL = SQL[:-1] + ") values (" + ("?," * len(SQLVars))[:-1] + ")"
            # create the tuple needed
            SQLTuple = tuple(SQLVars)

            # execute it
            self._db._execute(SQL, SQLTuple)

            # now find the ID
            (row, cur) = self._db._fetchone("Select ID From Servers where InstanceID=?", (InstanceID,))
            if row:
                super().__setattr__("ID", int(row["ID"]))
            else:
                raise Exception(f"Unable to locate new server with InstanceID {InstanceID}")
            cur.close()

            jdata = dump_to_json({"Type": "AddServer", "ServerID": self.ID, "InstanceID": InstanceID})
            self._db._logdata(jdata)

        if (self.Discord_Console_Channel is not None):
            super().__setattr__("Discord_Console_Channel", int(self.Discord_Console_Channel))
        if (self.Discord_Chat_Channel is not None):
            super().__setattr__("Discord_Chat_Channel", int(self.Discord_Chat_Channel))
        if (self.Discord_Event_Channel is not None):
            super().__setattr__("Discord_Event_Channel", int(self.Discord_Event_Channel))
        if (self.Discord_Role is not None):
            super().__setattr__("Discord_Role", int(self.Discord_Role))

    def __setattr__(self, name: str, value):
        if (name in ["ID"]) or (name[0] == "_"):
            return

        elif name in ["Whitelist", "Donator", "Console_Flag", "Console_Filtered"]:
            # convert to bool
            value = bool(value)

        elif name in ["Discord_Console_Channel", "Discord_Chat_Channel", "Discord_Event_Channel", "Discord_Role", "Console_Filtered_Type"]:
            if value is not None:
                value = int(value)

        # set value and update the user
        super().__setattr__(name, value)
        self._db._UpdateServer(self, **{name: value})

    def delServer(self):
        # self._db._execute("delete from ServerNicknames where ServerID=?", (self.ID,))
        self._db._execute("delete from Servers where ID=?", (self.ID,))

    def setDisplayName(self, DisplayName: str):
        try:
            self._db._execute("update Servers set DisplayName=? where ID=?", (DisplayName, self.ID))
        except:
            return False
        jdata = dump_to_json({"Type": "UpdateServerDisplayName", "ServerID": self.ID, "DisplayName": DisplayName})
        self._db._logdata(jdata)

    def getBanner(self, background_path: str = None):
        return DBBanner(self._db, self.ID, background_path)

    def AddServerRegexPattern(self, ID: int = None, Name: str = None):
        """Adds the provided RegexPattern ID/Name to the ServerRegexPatterns Table."""
        if ID == None:
            (row, cur) = self._db._fetchone("SELECT ID from RegexPatterns WHERE Name=?", (Name,))
            if not row:
                cur.close()
                return False
            ID = row["ID"]

        try:
            self._db._execute("INSERT into ServerRegexPatterns (RegexPatternID, ServerID) values(?,?)", (ID, self.ID))

        except Exception as e:
            print(e)
            return False
        return True

    def DelServerRegexPattern(self, ID: int = None, Name: str = None):
        """Removes the provided RegexPattern ID/Name from the ServerRegexPatterns Table."""
        if ID == None:
            (row, cur) = self._db._fetchone("SELECT ID from RegexPatterns WHERE Name=?", (Name,))
            if not row:
                cur.close()
                return False
            ID = row["ID"]

        self._db._execute("DELETE from ServerRegexPatterns where RegexPatternID=? and ServerID=?", (ID, self.ID))
        return True

    def GetServerRegexPatterns(self):
        """Gets all Regex Patterns related to Server \n
        Returns `dict['ID': {'Name': entry['Name'], 'Type': entry['Type'], 'Pattern': entry['Pattern']}]`"""
        regex_patterns = {}
        SQLArgs = []
        (rows, cur) = self._db._fetchall("SELECT RP.ID, RP.Name, RP.Type, RP.Pattern FROM ServerRegexPatterns SRP, RegexPatterns RP WHERE SRP.ServerID=? and SRP.RegexPatternID = RP.ID", (self.ID,))
        for entry in rows:
            regex_patterns[entry['ID']] = {'Name': entry['Name'], 'Type': entry['Type'], 'Pattern': entry['Pattern']}

        cur.close()
        return regex_patterns


class DBConfig:
    def __init__(self, db: Database = None):
        # set defaults
        Params = locals()
        Params.pop("self")
        Params.pop("db")
        super().__setattr__("_db", db)

        # get the known config settings
        super().__setattr__("_ConfigNameToID", {})
        (rows, cur) = self._db._fetchall("Select ID, Name, Value from Config", ())
        for entry in rows:
            self._ConfigNameToID[entry["Name"].capitalize()] = entry["ID"]
            super().__setattr__(entry["Name"].capitalize(), entry["Value"])
        cur.close()

    def __setattr__(self, name, value):
        if name in self._ConfigNameToID:
            if type(value) == bool:
                value = int(value)
            super().__setattr__(name, value)
            self._db._UpdateConfig(self._ConfigNameToID[name], name, value)

    def __getattribute__(self, name):
        val = super().__getattribute__(name)
        if name == "_ConfigNameToID":
            return val

        if name == 'Message_Timeout':
            if (type(val) == str) and val == 'None':
                val = None

            if (type(val) == str) and val.isnumeric():
                val = int(val)

        if name in self._ConfigNameToID:
            if (type(val) == str) and val.isnumeric():
                val = int(val)

        return val

    # list(self._ConfigNameToID.keys())
    def GetSettingList(self) -> list[str]:
        settings = list(self._ConfigNameToID.keys())
        return settings

    def SetSetting(self, name: str, value):
        name = name.capitalize().replace(" ", "_").replace("-", "_")
        if name not in self._ConfigNameToID:
            self.AddSetting(name, value)
        else:
            setattr(self, name, value)

    def GetSetting(self, name: str) -> str:
        name = name.capitalize().replace(" ", "_").replace("-", "_")
        if name not in self._ConfigNameToID:
            return None
        return getattr(self, name)

    def AddSetting(self, name: str, value):
        name = name.capitalize().replace(" ", "_").replace("-", "_")
        if name not in self._ConfigNameToID:
            super().__setattr__(name, value)
            self._ConfigNameToID[name] = self._db._AddConfig(name, value)

    def DeleteSetting(self, name: str):
        name = name.capitalize()
        if name not in self._ConfigNameToID:
            return
        self._db._DeleteConfig(self._ConfigNameToID[name], name)
        super().__delattr__(name)
        self._ConfigNameToID.pop(name)


class DBBanner:
    def __init__(self, DB: Database, ServerID: int = None, background_path: str = None):
        self._attr_list = {'_db': DB,
                           'ServerID': int(ServerID),
                           'background_path': background_path,
                           'blur_background_amount': 0,
                           'color_header': "#85c1e9",
                           'color_body': "#f2f3f4",
                           'color_host': "#5dade2",
                           'color_whitelist_open': "#f7dc6f",
                           'color_whitelist_closed': "#cb4335",
                           'color_donator': "#212f3c",
                           'color_status_online': "#28b463",
                           'color_status_offline': "#e74c3c",
                           'color_player_limit_min': "#ba4a00",
                           'color_player_limit_max': "#5dade2",
                           'color_player_online': "#f7dc6f"}

        for attr in self._attr_list:
            super().__setattr__(attr, self._attr_list[attr])

        (row, cur) = self._db._fetchone("Select * from ServerBanners where ServerID=?", (self.ServerID,))
        if row:
            for entry in row.keys():
                super().__setattr__(entry, row[entry])

        else:
            # create the sql line
            SQL = "insert into ServerBanners ("
            SQLVars = []

            for entry in self._attr_list:
                if entry.startswith('_'):
                    continue
                SQL += entry + ","
                SQLVars.append(self._attr_list[entry])

            SQL = SQL[:-1] + ") values (" + ("?," * len(SQLVars))[:-1] + ")"
            # create the tuple needed
            SQLTuple = tuple(SQLVars)

            # execute it
            self._db._execute(SQL, SQLTuple)

        cur.close()

    def __setattr__(self, name: str, value):

        if name == 'blur_background_amount':
            value = int(value)

        super().__setattr__(name, value)

        if not name.startswith("_"):
            self._db._UpdateBanner(self, **{name: value})
