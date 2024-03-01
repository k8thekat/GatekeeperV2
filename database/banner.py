BANNER_GROUP_SETUP_SQL = ("""create table BannerGroup (
                        ID integer primary key,
                        name text unique
                        )""")

BANNER_GROUP_SERVER_SETUP_SQL = ("""create table BannerGroupServers (
                ServerID integer not null,
                BannerGroupID integer not null,
                foreign key (ServerID) references Servers(ID),
                foreign key (BannerGroupID) references BannerGroup(ID)
                )""")

BANNER_GROUP_CHANNELS_SETUP_SQL = ("""create table BannerGroupChannels (
                ID integer primary key,
                Discord_Channel_ID integer,
                Discord_Guild_ID integer,
                BannerGroupID integer not null,
                foreign key (BannerGroupID) references BannerGroup(ID)
                )""")

BANNER_GROUP_MESSAGES_SETUP_SQL = ("""create table BannerGroupMessages (
                BannerGroupChannelsID integer not null,
                Discord_Message_ID integer,
                foreign key (BannerGroupChannelsID) references BannerGroupChannels(ID)
                )""")

SERVER_BANNERS_SETUP_SQL = ("""create table ServerBanners (
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
