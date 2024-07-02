CREATE TABLE
    IF NOT EXISTS version (value TEXT COLLATE NOCASE NOT NULL) STRICT;

-- Local discord guild id storage for table references.
CREATE TABLE
    IF NOT EXISTS guilds (guild_id INTEGER UNIQUE NOT NULL) STRICT;

-- Unique per guild settings.
CREATE TABLE
    IF NOT EXISTS settings (
        guild_id INTEGER NOT NULL,
        mod_role_id INTEGER,
        donator_role_id INTEGER,
        msg_timeout INTEGER,
        auto_update_banner INTEGER DEFAULT 1,
        banner_type INTEGER DEFAULT 1, -- 1 = IMAGES, 0 = EMBEDS
        auto_whitelist INTEGER DEFAULT 0,
        whitelist_request_channel_id INTEGER,
        FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
    ) STRICT;

-- Store whitelist string replies the bot can pick from based upon a guild_id.
CREATE TABLE
    IF NOT EXISTS whitelist_replies (
        guild_id INTEGER NOT NULL,
        reply TEXT NOT NULL,
        FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
    ) STRICT;

-- Used to commands permissions and will exist in a customer decorator command check.
CREATE TABLE
    IF NOT EXISTS owners (
        guild_id INTEGER NOT NULL,
        user_id INTEGER UNIQUE,
        FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE,
        UNIQUE (guild_id, user_id)
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS prefixes (
        guild_id INTEGER NOT NULL,
        prefix TEXT,
        FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE,
        UNIQUE (guild_id, prefix)
    ) STRICT;

-- AMP Instance table.
CREATE TABLE
    IF NOT EXISTS instances (
        instance_id TEXT NOT NULL UNIQUE,
        instance_name TEXT NOT NULL,
        created_at REAL
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS instance_settings (
        instance_id TEXT NOT NULL,
        description INTEGER DEFAULT 1,
        host TEXT DEFAULT "localhost",
        password TEXT DEFAULT "",
        whitelist INTEGER DEFAULT 0,
        whitelist_button INTEGER DEFAULT 0,
        emoji TEXT DEFAULT "",
        donator INTEGER DEFAULT 0,
        donator_bypass INTEGER DEFAULT 0, -- Donator's can bypass Whitelist wait time.
        metrics INTEGER DEFAULT 0,
        status INTEGER DEFAULT 1,
        unique_visitors INTEGER DEFAULT 0,
        discord_console_channel_id INTEGER DEFAULT 0,
        discord_role_id INTEGER DEFAULT 0,
        avatar_url TEXT DEFAULT "",
        hidden INTEGER DEFAULT 0,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        UNIQUE (instance_id)
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS instance_buttons (
        instance_id TEXT NOT NULL,
        button_name TEXT NOT NULL,
        button_url TEXT NOT NULL,
        button_style INTEGER NOT NULL,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        UNIQUE (instance_id)
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS instance_metrics (
        instance_id TEXT NOT NULL,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        UNIQUE (instance_id)
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS instance_banner_settings (
        instance_id TEXT NOT NULL,
        image_path TEXT,
        blur_background_amount INTEGER DEFAULT 0,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        UNIQUE (instance_id)
    ) STRICT;

-- !! THIS TABLE MUST MATCH `banner_element_position`. !!
CREATE TABLE
    IF NOT EXISTS banner_element_color (
        instance_id TEXT NOT NULL,
        name TEXT DEFAULT "#85C1E9",
        description TEXT DEFAULT "#F2F3F4",
        host TEXT DEFAULT "#5DADE2",
        password TEXT DEFAULT "#FFFFFF",
        whitelist_open TEXT DEFAULT "#F7DC6F",
        whitelist_closed TEXT DEFAULT "#CB4335",
        donator TEXT DEFAULT "#212F3C",
        status_online TEXT DEFAULT "#28B463",
        status_offline TEXT DEFAULT "#E74C3C",
        status_other TEXT DEFAULT "#E74C3C",
        metrics TEXT DEFAULT "#00FFFF",
        unique_visitors TEXT DEFAULT "#EFEB0D",
        player_limit_min TEXT DEFAULT "#BA4A00",
        player_limit_max TEXT DEFAULT "#5DADE2",
        players_online TEXT DEFAULT "#F7DC6F",
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE UNIQUE (instance_id)
    ) STRICT;

-- TODO: change default values for a "decent" layout of a banner display.
-- !! THIS TABLE MUST MATCH `banner_element_color`. !!
CREATE TABLE
    IF NOT EXISTS banner_element_position (
        instance_id TEXT NOT NULL,
        name INTEGER DEFAULT 1638400, -- 25, 0
        description INTEGER DEFAULT 0,
        host INTEGER DEFAULT 0,
        password INTEGER DEFAULT 0,
        whitelist_open INTEGER DEFAULT 0,
        whitelist_closed INTEGER DEFAULT 0,
        donator INTEGER DEFAULT 0,
        status_online INTEGER DEFAULT 0,
        status_offline INTEGER DEFAULT 0,
        status_other INTEGER DEFAULT 0,
        metrics INTEGER DEFAULT 0,
        unique_visitors INTEGER DEFAULT 0,
        player_limit_min INTEGER DEFAULT 0,
        player_limit_max INTEGER DEFAULT 0,
        players_online INTEGER DEFAULT 0,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE UNIQUE (instance_id)
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS banner_group (group_id INTEGER PRIMARY KEY, name TEXT UNIQUE) STRICT;

CREATE TABLE
    IF NOT EXISTS banner_group_instances (
        instance_id TEXT NOT NULL,
        group_id INTEGER NOT NULL,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        FOREIGN KEY (group_id) REFERENCES banner_group (group_id) ON DELETE CASCADE
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS banner_group_channels (
        id INTEGER PRIMARY KEY,
        discord_guild_id INTEGER,
        discord_channel_id INTEGER,
        group_id INTEGER NOT NULL,
        FOREIGN KEY (group_id) REFERENCES banner_group (id) ON DELETE CASCADE,
        UNIQUE (discord_guild_id, discord_channel_id, group_id)
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS banner_group_messages (
        group_channel_id INTEGER NOT NULL,
        discord_message_id INTEGER,
        FOREIGN KEY (group_channel_id) REFERENCES banner_group_channels (id) ON DELETE CASCADE,
        UNIQUE (group_channel_id, discord_message_id)
    ) STRICT;

-- Users table to store discord user ids
CREATE TABLE
    IF NOT EXISTS users (user_id INTEGER UNIQUE NOT NULL) STRICT;

-- IGN table
-- Related to discord user ids table, will CASCADE on delete.
CREATE TABLE
    IF NOT EXISTS ign (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        type_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
        UNIQUE (name, type_id),
        UNIQUE (type_id, user_id)
    ) STRICT;

CREATE TABLE
    IF NOT EXISTS ign_metrics (
        ign_id INTEGER NOT NULL,
        instance_id TEXT NOT NULL,
        last_login REAL,
        playtime INTEGER,
        created_at REAL,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        FOREIGN KEY (ign_id) REFERENCES ign (id) ON DELETE CASCADE,
        UNIQUE (ign_id, instance_id)
    ) STRICT;

-- This will be used to determine what instances a user can
-- interact with via `/commands` based upon their discord user id.
CREATE TABLE
    IF NOT EXISTS user_instances (
        user_id INTEGER NOT NULL,
        instance_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        UNIQUE (user_id, instance_id)
    ) STRICT;

-- This will be used to determine what instances a discord user can
-- interact with via `/commands` based upon their discord role id.
CREATE TABLE
    IF NOT EXISTS role_instances (
        role_id INTEGER NOT NULL,
        instance_id TEXT NOT NULL,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        UNIQUE (role_id, instance_id)
    ) STRICT;

-- This will be used to determine what instances a discord user can
-- interact with via `/commands` based upon the discord guild id.
CREATE TABLE
    IF NOT EXISTS guild_instances (
        guild_id INTEGER NOT NULL,
        instance_id TEXT NOT NULL,
        FOREIGN KEY (instance_id) REFERENCES instances (instance_id) ON DELETE CASCADE,
        FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE,
        UNIQUE (guild_id, instance_id)
    ) STRICT;