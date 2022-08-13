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
import sqlite3
import os
import datetime
import json
import time
import logging

from AMP import AMPInstance


def dump_to_json(data):
    for entry in data:
        if type(data[entry]) == datetime.datetime:
            data[entry] = data[entry].isoformat()
        elif type(data[entry]) == bool:
            data[entry] = int(data[entry])
    return json.dumps(data)


Handler = None


class DBHandler():
	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.DB = Database(Handler = self)
		self.DBConfig = self.DB.GetConfig()
		self.SuccessfulDatabase = True

		#Always update this value when changing Tables!
		self.DB_Version = 1.3

		#This should ONLY BE TRUE on new Database's going forward. 
		if self.DBConfig.GetSetting('DB_Version') == None:
			self.DBUpdate = DBUpdate(self.DB,self.DB_Version)
			return

		#This is to handle 1.0.0 Converting to new DB Version systems.
		if type(self.DBConfig.GetSetting('DB_Version')) == str and self.DBConfig.GetSetting('DB_Version') == '1.0.0':
			self.DBConfig.SetSetting('DB_Version', '1.0')

		#self.DBConfig.SetSetting('DB_Version', 1.2)
		#This handles version checks and calling all updates from version 1.0
		if self.DB_Version > float(self.DBConfig.GetSetting('DB_Version')):
			self.logger.warn(f"**ATTENTION** Gatekeeperv2 Database is on Version: {self.DB_Version}, your Database is on Version: {self.DBConfig.GetSetting('DB_Version')}")
			self.DBUpdate = DBUpdate(self.DB,float(self.DBConfig.GetSetting('DB_Version')))
		
		self.logger.info(f'DB Handler Initialization...DB Version: {self.DBConfig.GetSetting("DB_Version")}')
	
	
	def dbWhitelistSetup(self):
		"""This is set Default AMP Specific Whitelist Settings"""
		try:
			#self.DBConfig.AddSetting('Whitelist_Format','**IGN**: minecraft_ign \n **SERVER**: servername')
			self.DBConfig.AddSetting('Whitelist_Channel', None)
			self.DBConfig.AddSetting('WhiteList_Wait_Time', 5)
			self.DBConfig.AddSetting('Auto_Whitelist', False)
			self.DBConfig.AddSetting('Whitelist_Emoji_Pending', None)
			self.DBConfig.AddSetting('Whitelist_Emoji_Done', None)
		except:
			self.logger.warning('**ATTENTION** DBConfig Default Whitelist Settings have been set.')

    def dbServerConsoleSetup(self, server: AMPInstance):
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
        if os.path.exists("discordBot.db"):
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

    def _InitializeDatabase(self):
        cur = self._db.cursor()

        cur.execute("""create table Servers (
						ID integer primary key,
						InstanceID text not null unique collate nocase,
						InstanceName text unique collate nocase,
						DisplayName text,
						Description text,
						IP text unique,
						Whitelist integer not null,
						Donator integer not null,
						Console_Flag integer not null,
						Console_Filtered integer not null,
						Discord_Console_Channel text nocase,
						Discord_Chat_Channel text nocase,
						Discord_Role text collate nocase,
						Discord_Reaction text nocase
						)""")

        cur.execute("""create table ServerNicknames (
						ID integer primary key,
						ServerID integer not null,
						Nickname text unique not null unique collate nocase,
						foreign key(ServerID) references Servers(ID)
						)""")

        cur.execute("""create table Users (
						ID integer primary key,
						DiscordID text not null unique collate nocase,
						DiscordName text collate nocase,
						MC_IngameName text collate nocase,
						MC_UUID text unique collate nocase,
						SteamID text unique collate nocase,
						Donator integer not null,
						Role text collate nocase,
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

    def _execute(self, SQL, params):
        Retry = 0

        while(1):
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

            except Exception as ex:
                raise Exception(ex)

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

    def _UpdateUser(self, dbuser, **args):
        # get the property to update
        entry = list(args.keys())[0]
        self._execute(f"Update users set {entry}=? where ID=?", (args[entry], dbuser.ID))
        jdata = dump_to_json({"Type": "UserUpdate", "UserID": dbuser.ID, "Field": entry, "Value": args[entry]})
        self._logdata(jdata)

	
	def AddServer(self, InstanceID:str, InstanceName:str=None, DisplayName:str=None, Description:str=None, IP:str=None, Whitelist:bool=False, Donator:bool=False, Console_Flag:bool=True, Console_Filtered:bool=True, Discord_Console_Channel:str=None, Discord_Chat_Channel:str=None, Discord_Role:str=None, Discord_Reaction:str=None):
		#try:
		return DBServer(db=self, InstanceID=InstanceID, InstanceName=InstanceName, DisplayName=DisplayName, Description=Description, IP=IP, Whitelist=Whitelist, Donator=Donator, Console_Flag=Console_Flag, Console_Filtered=Console_Filtered, Discord_Console_Channel=Discord_Console_Channel, Discord_Chat_Channel=Discord_Chat_Channel, Discord_Role=Discord_Role, Discord_Reaction=Discord_Reaction)
		#except:
			#return None

    def GetServer(self, InstanceID: str = None, Name: str = None):
        # print(InstanceID,Name)
        if not InstanceID and not Name:
            return None

        # we need to look for a server where the friendly name or nickname matches the provided name
        if InstanceID:
            (row, cur) = self._fetchone(f"select ID from Servers where InstanceID=?", (InstanceID,))
        else:
            (row, cur) = self._fetchone(f"select ID from Servers where InstanceName=? or DisplayName=?", (Name, Name))

        # if no rows then try nicknames
        if not row:
            if Name:
                cur.close()
                (row, cur) = self._fetchone(f"select ServerID as ID from ServerNicknames where Nickname=?", (Name,))

            if not row:
                cur.close()
                return None

        # create a new user to return and let the object populate itself
        ret = DBServer(ID=int(row["ID"]), db=self)

        cur.close()
        return ret

	def GetUser(self, value:str):
		#find the user
		(row, cur) = self._fetchone(f"select ID from Users where DiscordID=? or DiscordName=? or MC_IngameName=? or MC_UUID=? or SteamID=?", (value,value,value,value,value))
		if not row:
			cur.close()
			return None

        # create a new user object to return and let the object populate itself
        ret = DBUser(ID=int(row["ID"]), db=self)

        cur.close()
        return ret

    def AddUser(self, DiscordID: str = None, DiscordName: str = None, MC_IngameName: str = None, MC_UUID: str = None, SteamID: str = None, Donator: bool = False):
        try:
            return DBUser(db=self, DiscordID=DiscordID, DiscordName=DiscordName, MC_IngameName=MC_IngameName, MC_UUID=MC_UUID, SteamID=SteamID, Donator=Donator)
        except Exception as e:
            print('DBUser error', e)
            return None

    def GetAllUsers(self, Donator=None):
        # get all servers that we are on
        SQL = "Select ID from Users"
        SQLWhere = []
        SQLArgs = []

        # if(GlobalBanExpiration):
        # 	SQLWhere.append("GlobalBanExpiration <= ?")
        # 	SQLArgs.append(GlobalBanExpiration)
        if(Donator):
            SQLWhere.append("and Donator = ?")
            SQLArgs.append(Donator)
        # if(ServerModerator):
        # 	SQLWhere.append("ServerModerator = ?")
        # 	SQLArgs.append(ServerModerator)

        if len(SQLWhere):
            SQL = SQL + " where " + " and ".join(SQLWhere)

        (rows, cur) = self._fetchall(SQL, tuple(SQLArgs))
        ret = []
        for entry in rows:
            User = DBUser(self, ID=entry["ID"])
            ret.append(User)

        cur.close()
        return ret

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
        #global main_Database_Config
        # if self.DBHandler.DBConfig == None:
        # if main_Database_Config == None:
        #main_Database_Config = DBConfig(self)
        self.DBHandler.DBConfig = DBConfig(self)
        # return main_Database_Config
        #print('DB Config Get Config', self.DBHandler.DBConfig)
        return self.DBHandler.DBConfig

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
            qentries = ("?,"*Count)[:-1]
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
            qentries = ("?,"*Count)[:-1]
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
	def __init__(self, db:Database, ID:int=None, DiscordID:str=None, DiscordName:str=None, MC_IngameName:str=None, MC_UUID:str=None, SteamID:str=None, Donator:bool=False, Role:str=None):
		#set defaults
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
            super().__setattr__("DiscordID", int(self.DiscordID))
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

            SQL = SQL[:-1] + ") values (" + ("?,"*len(SQLVars))[:-1] + ")"
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

    def __setattr__(self, name: str, value):
        if (name == "ID") or (name[0] == "_"):
            return
        # elif name == "GlobalBanExpiration":
        # 	#make sure proper value
        # 	if (type(value) != datetime.datetime) and (type(value) != None):
        # 		raise Exception("Invalid type")
        elif name in ["Donator"]:
            # conver to bool
            value = bool(value)
        elif name == "DiscordID":
            # conver to int
            value = int(value)
        # elif name == "TimePlayed":
        # 	#conver to integer
        # 	value = int(value)

        # set value and update the user
        super().__setattr__(name, value)
        self._db._UpdateUser(self, **{name: value})

class DBServer:
    def __init__(self, db: Database, ID: int = None, InstanceID: str = None, InstanceName: str = None, DisplayName: str = None, Description: str = None, IP: str = None, Whitelist: bool = False, Donator: bool = False, Discord_Console_Channel: str = None, Discord_Chat_Channel: str = None, Discord_Role: str = None, Console_Flag: bool = True, Console_Filtered: bool = True, Discord_Reaction: str = None):
        # set defaults
        Params = locals()
        Params.pop("self")
        Params.pop("db")
        Params.pop("__class__")
        super().__setattr__("_db", db)
        for entry in Params:
            super().__setattr__(entry, Params[entry])

        if(self.ID != None):
            super().__setattr__("ID", int(self.ID))
        if(self.Discord_Console_Channel != None):
            super().__setattr__("Discord_Console_Channel", int(self.Discord_Console_Channel))
        if(self.Discord_Chat_Channel != None):
            super().__setattr__("Discord_Chat_Channel", int(self.Discord_Chat_Channel))

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

            DBFields = Params

            # create the sql line
            SQL = "insert into Servers ("
            SQLVars = []

            for entry in DBFields:
                if DBFields[entry] != None:
                    SQL += entry + ","
                    SQLVars.append(DBFields[entry])

            SQL = SQL[:-1] + ") values (" + ("?,"*len(SQLVars))[:-1] + ")"
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

    def __setattr__(self, name: str, value):
        if (name in ["ID", "Nicknames"]) or (name[0] == "_"):
            return
        # elif name == "MapCreationDate":
        # 	#make sure proper value
        # 	if type(value) != datetime.datetime:
        # 		raise Exception("Invalid type")
        elif name in ["Whitelist", "Donator"]:
            # conver to bool
            value = bool(value)
        # elif name in ["UserLimit"]:
        # 	value = int(value)
        elif name in ["Discord_Console_Channel", "Discord_Chat_Channel"]:
            if value != None:
                value = int(value)

        # set value and update the user
        super().__setattr__(name, value)
        self._db._UpdateServer(self, **{name: value})

    @property
    def Nicknames(self):
        # get all of the nicknames for this server
        (rows, cur) = self._db._fetchall("Select Nickname from ServerNicknames where ServerID=?", (self.ID,))
        Nicknames = []
        for entry in rows:
            Nicknames.append(entry["Nickname"])

        return Nicknames

    def AddNickname(self, Nickname: str):
        try:
            self._db._execute("Insert into ServerNicknames (ServerID, Nickname) values(?,?)", (self.ID, Nickname))
            jdata = dump_to_json({"Type": "AddServerNickname", "ServerID": self.ID, "Nickname": Nickname})
            self._db._logdata(jdata)
        except:
            return False
        return True

    def RemoveNickname(self, Nickname: str):
        self._db._execute("delete from ServerNicknames where ServerID=? and Nickname=?", (self.ID, Nickname))
        jdata = dump_to_json({"Type": "DeleteServerNickname", "ServerID": self.ID, "Nickname": Nickname})
        self._db._logdata(jdata)

    def GetAllServers(self):
        serverlist = []
        (rows, cur) = self._db._fetchall("Select ID from Servers")
        for entry in rows:
            serverlist.append(DBServer(ID=entry["ID"]))
        return serverlist

    def delServer(self):
        self._db._execute("delete from ServerNicknames where ServerID=?", (self.ID,))
        self._db._execute("delete from Servers where ID=?", (self.ID,))

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
            super().__setattr__(name, value)
            self._db._UpdateConfig(self._ConfigNameToID[name], name, value)

    def __getattribute__(self, name):
        val = super().__getattribute__(name)
        if name == "_ConfigNameToID":
            return val

        if name in self._ConfigNameToID:
            if (type(val) == str) and val.isnumeric():
                val = int(val)
        return val

    # list(self._ConfigNameToID.keys())
    def GetSettingList(self):
        settings = list(self._ConfigNameToID.keys())
        return settings

    def SetSetting(self, name: str, value):
        name = name.capitalize().replace(" ", "_").replace("-", "_")
        if name not in self._ConfigNameToID:
            self.AddSetting(name, value)
        else:
            setattr(self, name, value)

    def GetSetting(self, name: str):
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

class DBUpdate:
	def __init__(self,DB:Database,Version:float=None):
		self.logger = logging.getLogger(__name__)
		self.DB = DB
		self.DBConfig = self.DB.GetConfig()

		if Version == None:
			self.DBConfig.AddSetting('DB_Version',Version)

		if 1.1 > Version:
			self.logger.info('**ATTENTION** Updating DB to Version 1.1')
			self.DBConfig.AddSetting('Guild_ID', None)
			self.DBConfig.AddSetting('Moderator_role_id', None)
			self.DBConfig.AddSetting('Permissions', 'Default')
			self.DBConfig.SetSetting('DB_Version', '1.1')

		if 1.2 > Version:
			self.logger.info('**ATTENTION** Updating DB to Version 1.2')
			self.user_roles()
			self.DBConfig.SetSetting('DB_Version', '1.2')

		if 1.3 > Version:
			self.logger.info('**ATTENTION** Updating DB to Version 1.3')
			self.nicknames_unique
			self.DBConfig.SetSetting('DB_Version', '1.3')

	def user_roles(self):
		#create the sql line
		SQL = "alter table users add column Role text collate nocase default None;"
		#execute it
		self.DB._execute(SQL, ())

	def nicknames_unique(self):
		#create the sql line
		SQL = "alter table ServerNicknames add constraint Nickname unique;"
		#execute it
		self.DB._execute(SQL, ())
		


		