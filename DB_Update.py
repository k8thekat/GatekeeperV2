import logging
import sys

class DB_Update:
    def __init__(self, DB, Version:float=None):
        self.logger = logging.getLogger(__name__)
        self.DB = DB
        self.DBConfig = self.DB.DBConfig

        if Version == None:
            self.DBConfig.AddSetting('DB_Version', 1.0)

        if 1.1 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.1')
            self.DBConfig.AddSetting('Guild_ID', None)
            self.DBConfig.AddSetting('Moderator_role_id', None)
            self.DBConfig.AddSetting('Permissions', 0)
            self.DBConfig.AddSetting('Whitelist_Request_Channel', None)
            self.DBConfig.AddSetting('WhiteList_Wait_Time', 5)
            self.DBConfig.AddSetting('Auto_Whitelist', False)
            self.DBConfig.AddSetting('Whitelist_Emoji_Pending', None)
            self.DBConfig.AddSetting('Whitelist_Emoji_Done', None)
            self.DBConfig.SetSetting('DB_Version', '1.1')

        if 1.2 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.2')
            self.user_roles()
            self.DBConfig.SetSetting('DB_Version', '1.2')

        if 1.3 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.3')
            #self.nicknames_unique()
            self.DBConfig.SetSetting('DB_Version', '1.3')

        if 1.4 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.4')
            self.user_Donator_removal()
            self.DBConfig.SetSetting('DB_Version', '1.4')

        if 1.5 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.5')
            self.server_Discord_reaction_removal()
            self.DBConfig.SetSetting('DB_Version', '1.5')

        if 1.6 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.6')
            self.server_Discord_Chat_prefix()
            self.server_Discord_event_channel()
            self.server_Avatar_url()
            #self.DBConfig.AddSetting('Server_Info_Display', None)
            #self.DBConfig.AddSetting('Auto_Display', True)
            self.DBConfig.SetSetting('DB_Version', '1.6')
        
        if 1.7 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.7')
            self.DBConfig.AddSetting('Banner_Auto_Update', True)
            self.server_banner_table()
            self.whitelist_reply_table()
            self.DBConfig.DeleteSetting('Server_Info_Display')
            self.DBConfig.DeleteSetting('Auto_Display')
            self.DBConfig.SetSetting('DB_Version', '1.7')
        
        if 1.8 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.8')
            self.server_hide_column()
            #self.server_ip_constraint_update()
            self.server_display_name_reset()
            #self.server_display_name_constraint_update()
            self.DBConfig.SetSetting('DB_Version', '1.8')

        if 1.9 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 1.9')
            self.banner_table_creation()
            self.DBConfig.SetSetting('DB_Version', '1.9')

        if 2.1 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 2.1')
            self.server_ip_name_change()
            self.DBConfig.SetSetting('DB_Version', '2.1')

        if 2.2 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 2.2')
            self.DBConfig.DeleteSetting('Embed_Auto_Update')
            self.banner_name_conversion()
            self.DBConfig.SetSetting('DB_Version', '2.2')

        if 2.4 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 2.4')
            self.server_table_whitelist_disabled_column()
            self.regex_pattern_table_creation()
            self.server_regex_pattern_table_creation()
            self.server_console_filter_type()
            self.DBConfig.AddSetting('Message_Timeout', 60)
            self.DBConfig.SetSetting('DB_Version', '2.4')

        if 2.5 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 2.5')
            self.DBConfig.AddSetting('Banner_Type', 0)
            self.DBConfig.SetSetting('DB_Version', '2.5')

        if 2.6 > Version:
            self.logger.info('**ATTENTION** Updating DB to Version 2.6')
            #self.user_MC_IngameName_unique_constraint()
            self.DBConfig.DeleteSetting('Whitelist_Emoji_Pending')
            self.DBConfig.DeleteSetting('Whitelist_Emoji_Done')
            self.DBConfig.SetSetting('DB_Version', '2.6')
        
        if 2.7 > Version:
            """Hotfix for Failed Table creation in version 2.4"""
            self.logger.info('**ATTENTION** Updating DB to Version 2.7')
            self.server_add_FriendlyName_column()
            try:
                SQL = 'select * from ServerRegexPatterns'
                self.DB._execute(SQL, ())
            except:
                self.server_regex_pattern_table_creation()
            self.DBConfig.SetSetting('DB_Version', '2.7')
        
        if 2.8 > Version:
            """Adds Donator Bypass and Donator Role ID"""
            self.logger.info('**ATTENTION** Updating DB to Version 2.8')
            self.db_config_add_donator_setting()
            self.DBConfig.SetSetting('DB_Version', '2.8')

        if 2.9 > Version:
            """Updated the Banner Display System to use the new Group System."""
            self.logger.info('**ATTENTION** Updating DB to Version 2.9')
            self.add_bannergroup_table()
            self.add_bannergroupservers_table()
            self.add_bannergroupchannels_table()
            self.add_bannergroupmessages_table()
            self.DBConfig.SetSetting('DB_Version', '2.9')

        if 3.0 > Version:
            """Updated the Banner Display System to use the new Group System."""
            self.logger.info('**ATTENTION** Updating DB to Version 3.0')
            self.add_bannergroup_table()
            self.add_bannergroupservers_table()
            self.add_bannergroupchannels_table()
            self.add_bannergroupmessages_table()
            self.DBConfig.SetSetting('DB_Version', '3.0')


    def user_roles(self):
        try:
            SQL = "alter table users add column Role text collate nocase default None"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'user_roles {e}')
            sys.exit(-1)

    def nicknames_unique(self):
        try:
            SQL = "alter table ServerNicknames add constraint Nickname unique"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'nicknames_unique {e}')
            sys.exit(-1)

    def user_Donator_removal(self):
        try:
            SQL = "alter table users drop column Donator"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'user_Donator_removal {e}')
            sys.exit(-1)

    def server_Discord_reaction_removal(self):
        try:
            SQL = "alter table servers drop column Discord_Reaction"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_Discord_reaction_removal {e}')
            sys.exit(-1)

    def server_Discord_Chat_prefix(self):
        try:
            SQL = "alter table servers add column Discord_Chat_Prefix text"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_Discord_Chat_prefix {e}')
            sys.exit(-1)

    def server_Discord_event_channel(self):
        try:
            SQL = "alter table servers add column Discord_Event_Channel text nocase"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_Discord_event_channel {e}')
            sys.exit(-1)

    def server_Avatar_url(self):
        try:
            SQL = "alter table servers add column Avatar_url text"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_Avatar_url {e}')
            sys.exit(-1)

    def server_banner_table(self):
        try:
            SQL = 'create table ServerEmbed (ID integer primary key, Discord_Guild_ID text nocase, Discord_Channel_ID text nocase, Discord_Message_ID text)'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_banner_table {e}')
            sys.exit(-1)
    
    def whitelist_reply_table(self):
        try:
            SQL = 'create table WhitelistReply (ID integer primary key, Message text)'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'whitelist_reply_table {e}')
            sys.exit(-1)
    
    def server_hide_column(self):
        """1.8 Update"""
        try:
            SQL = 'alter table servers add column Hidden integer default 0'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_hide_column {e}')
            sys.exit(-1)

    def server_ip_constraint_update(self):
        """SQLITE does not support dropping UNIQUE constraint"""
        try:
            SQL = 'alter table servers drop constraint IP unique'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_ip_constraint_update {e}')
            sys.exit(-1)

    def server_display_name_reset(self):
        try:
            SQL= 'update Servers set DisplayName=InstanceName'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_display_name_reset {e}')
            sys.exit(-1)

    def server_display_name_constraint_update(self):
        """SQLITE does not support adding UNIQUE constraint"""
        try:
            SQL = "alter table Servers add constraint DisplayName unique"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_display_name_constraint_update {e}')
            sys.exit(-1)

    def banner_table_creation(self):
        try:
            SQL = 'create table ServerBanners (ServerID integer not null, background_path text, blur_background_amount integer, color_header text, color_body text, color_host text, color_whitelist_open text, color_whitelist_closed text, color_donator text, color_status_online text, color_status_offline text, color_player_limit_min text, color_player_limit_max text, color_player_online text, foreign key(ServerID) references Servers(ID))'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'banner_table_creation {e}')
            sys.exit(-1)
    
    def server_ip_name_change(self):
        try:
            # SQL = 'select IP from Servers limit 1'
            # self.DB._execute(SQL, ())

            # SQL = "alter table Servers drop column IP"
            # self.DB._execute(SQL, ())

            SQL = 'alter table Servers add column Host text'
            self.DB._execute(SQL, ())
            return
        except Exception as e:
            self.logger.error(e)
            pass

        try:
            SQL = 'select Display_IP from Servers limit 1'
            self.DB._execute(SQL, ())

            SQL = 'alter table Servers drop column Display_IP'
            self.DB._execute(SQL, ())

            SQL = 'alter table Servers add column Host text'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_ip_name_change {e}')
            sys.exit(-1)
        
    def banner_name_conversion(self):
        try:
            SQL = 'select * from ServerEmbed limit 1'
            self.DB._execute(SQL, ())

            SQL = 'alter table ServerEmbed rename to ServerDisplayBanners'
            self.DB._execute(SQL, ())
            return
        except:
            pass

        try:
            SQL = 'select * from ServerDisplayBanners'
            self.DB._execute(SQL, ())
            return
        except:
            pass

        try:
            SQL = 'create table ServerDisplayBanners (ID integer primary key,Discord_Guild_ID text nocase,Discord_Channel_ID text nocase, Discord_Message_ID text nocase)'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'banner_name_conversion {e}')
            sys.exit(-1)

    def server_table_whitelist_disabled_column(self):
        try:
            SQL = 'alter table Servers add column Whitelist_disabled integer not null default 0'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_table_whitelist_disabled_column {e}')
            sys.exit(-1)

    def regex_pattern_table_creation(self):
        try:
            SQL = 'create table RegexPatterns (ID integer primary key, Name text unique not null, Type integer not null, Pattern text unique not null)'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'regex_pattern_table_creation {e}')
            sys.exit(-1)

    def server_regex_pattern_table_creation(self):
        try:
            SQL = 'create table ServerRegexPatterns (ServerID integeter not null, RegexPatternID integer not null, foreign key (RegexPatternID) references RegexPatterns(ID), foreign key(ServerID) references Servers(ID) UNIQUE(ServerID, RegexPatternID))'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_regex_pattern_table_creation {e}')
            sys.exit(-1)

    def server_console_filter_type(self):
        try:
            SQL = 'alter table Servers add column Console_Filtered_Type integer not null default 0'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_console_filter_type {e}')
            sys.exit(-1)
        
    def server_add_FriendlyName_column(self):
        try:
            SQL = 'select FriendlyName from Servers'
            self.DB._execute(SQL, ())
            return
        except:
            pass

        try:
            SQL = 'alter table Servers add column FriendlyName text'
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'server_add_FriendlyName_column {e}')
            sys.exit(-1)
    
    def db_config_add_donator_setting(self):
        #Adds support for Donator related functionality.
        try:
            self.DBConfig.AddSetting("Donator_Bypass", False)
            self.DBConfig.AddSetting("Donator_role_id", None)
        except Exception as e:
            self.logger.critical(f'db_config_add_donator_settings {e}')


    def add_bannergroup_table(self):
        try:
            SQL = "create table BannerGroup (ID integer primary key, name text unique)"
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'add_bannergroup_table {e}')

    def add_bannergroupservers_table(self):
        try:
            SQL = """create table BannerGroupServers (
                        ServerID integer not null,
                        BannerGroupID integer not null,
                        foreign key (ServerID) references Servers(ID),
                        foreign key (BannerGroupID) references BannerGroup(ID)
                        )"""
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'add_bannergroupservers_table {e}')

    def add_bannergroupchannels_table(self):
        try:
            SQL = """create table BannerGroupChannels (
                        ID integer primary key,
                        Discord_Channel_ID integer,
                        Discord_Guild_ID integer,
                        BannerGroupID integer not null,
                        foreign key (BannerGroupID) references BannerGroup(ID)
                        )"""
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'add_bannergroupchannels_table {e}')

    def add_bannergroupmessages_table(self):
        try:
            SQL = """create table BannerGroupMessages (
                        BannerGroupChannelsID integer not null,
                        Discord_Message_ID integer,
                        foreign key (BannerGroupChannelsID) references BannerGroupChannels(ID)
                        )"""
            self.DB._execute(SQL, ())
        except Exception as e:
            self.logger.critical(f'add_bannergroupmessages_table {e}')