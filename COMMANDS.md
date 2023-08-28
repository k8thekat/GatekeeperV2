# **Commands List**
*This documentation is subject to change at any point and may not reflect recent changes*

### **Using your commands!**
- Most commands are using some form of `autocomplete` or `choices` to help users.
___
### <u>Bot Commands</u>: 
- `/bot moderator (role)` - Sets the Discord Role for Bot Moderator. 
    - **ATTENTION**: Requires Discord Administrator to use!
    - **TIP**: Please see `/bot permissions` for more control. 
- `/bot permissions (type)` - Sets the Bot Permissions to either `Default` or `Custom`.
    - **ATTENTION**: Requires Discord Administrator to use!
    - **TIP**: Please see **[Permissions](/PERMISSIONS.md)** if you want `Custom` control over command usage.
- `/bot settings` - Lists Bot settings such as channels and whitelist status.
- `/bot donator (role)` - Sets the Donator Role for Donator Only AMP Server access.
    - **TIP**: This will prevent people without the role from requesting whitelist to Donator only Servers.

### <u>Bot Utils Commands</u>: 
- `/bot utils ping` - Pong!
- `/bot utils disconnect` - Closes the Connection with the Bot.
- `/bot utils restart` - Restarts the Bot.
- `/bot utils status` - Replies with **AMP version** and if setup is complete, **DB version** and if setup is complete and **Displays Bot version information**.
    - **TIP**: This information is useful when reporting bugs/errors on Github!
- `/bot utils sync (reset, local)` - Sync functionality for Gatekeeperv2
    - `reset` `(true/false)` if `True` will clear all commands from the Command Tree and then re-sync's the command tree.
    - `local` `(true/false)` if `True` makes the sync or reset happen to the `guild` the command is used in.
- `/bot utils roleid (role)` - Returns the role ID for the selected Discord Role.
- `/bot utils channelid (channel)` - Returns the Channel ID for the selected Discord Channel
- `/bot utils userid (user)` - Returns the User ID for the selected Discord User.
- `/bot utils uuid (mc_ign)` - This will convert a Minecraft IGN to a UUID if it exists.
- `/bot utils clear (channel, amountm, all)` - Delete(s) the Specified amount of Messages Sent by the Bot.
    - If `all` is set to `True` this will clear ALL messages regardless of sender.
- `/bot utils message_timeout (time)` - Sets the Delete After time in seconds for ephemeral messages sent from Gatekeeperv2.

### <u>Bot Cog Commands</u>: 
- `/bot cog load (path)` - Loads a specific Cog. *(eg. path = `/cogs/cog_template`)*
- `/bot cog unload (cogname)` - Unloads a specific Cog. *(eg. name = `cog_template`)*
- `/bot cog reload` - Reloads all currently loaded Cogs.

### <u>Bot Banner_Settings Commands</u>: 
- `/bot banner_settings auto_update (flag)` - Allows the bot to automatically update the Banner Group messages.
- `/bot banner_settings type (type)` - Select which type of Banner to display via Banner Group messages.

### <u>Bot BannerGroup Commands</u>: 
- `/bot bannergroup create_group (group_name)` - Creates a new Banner Group
- `/bot bannergroup add (group_name, server, channel)` - Allows the User to add `Channel` or `Server` to a Banner Group.
- `/bot bannergroup remove (group_name, server, channel)` - Allows the User to remove a `Server` or `Channel` from a Banner Group
- `/bot bannergroup rename (group_name, new_groupname)` - Allows a User to rename the selected Banner Group.
- `/bot bannergroup info (group_name)` - Displays information pertaining to the selected Banner Group.
- `/bot bannergroup delete_group (group_name)` - Allows the User to Delete an entire Banner Group.

### <u>Bot Regex_Pattern Commands</u>:
- See [Regex How-to](/REGEX.md) for full documentation.
- `/bot regex_pattern list` - Displays an Embed list of All Regex Patterns
- `/bot regex_pattern add (name, filter_type, pattern)` - Adds a Regex pattern to the Database
    - **TIP**: `pattern` is used in a re.search().
- `/bot regex_pattern delete (name)` - Remove a Regex Pattern from the Database
- `/bot regex_pattern update (name, new_name, filter_type, pattern)` - Update a Regex Patterns Name, Pattern and or Type.
    - **TIP**: `new_name` must not match the original `name`
    - `filter_type` dictates where the match will be sent. (eg. `Event` would send all matches to the `Event Channel` for said Server - See [Regex](/README.md) for examples.)

### <u>Bot Whitelist Commands</u>:
- `/bot whitelist auto (flag)` - Allows the bot to automatically Whitelist a Users request.
    - **ATTENTION**: `flag` must be *True or False*. Default is False.
        - **TIP**: This will not instantly whitelist the user if whitelist waittime is not set to zero.
- `/bot whitelist channel (channel)` - Sets the Discord channel for the bot to monitor for whitelist requests.
- `/bot whitelist wait_time (time)` -  Sets the wait time for whitelist request after the message is received. *(eg. time = `5`)*
    - **REMINDER**: All time values are in **Minutes**! Please keep that in mind.
        - **TIP**: Set the value to zero to have the bot instantly whitelist users. Default value is 5 minutes!
- `/bot whitelist_reply add (message)` - Adds the message to the possibly list of replies the bot can use during Whitelist handling.
    - **TIP**: Messages support the following parameteres.
        - `<user>` - Which changes to use the message author's name inside your message.
        - `<server>` - Which returns with the provided AMP Instance Name or Display Name respectively.
        - `<guild>` - Which changes to the Discord Guild Name.
        - `<#channelid>` - Which is replaces with a channel jump_to link. Simply use `<#` and `>` wrapped around the channel's id. *(eg. `<#1234567890>`)*
            - It will create a jump_to link during usage; but it gets saved into the DB as the example.
- `/bot whitelist_reply remove (message)` - Removes the selected message from the list of replies the bot can use during Whitelist handling.
- `/bot whitelist_reply list` - Lists all the currently available replies the bot can use during Whitelist handling.
- `/bot whitelist donator_bypass (flag)` - This turns `ON` or `Off` Donator Bypass of Auto-Whitelisting `wait_time`.
- `/bot whitelist request_channel (channel)` - Sets the Whitelist Request Channel for the Bot to send Whitelist requests for Staff approval.

### <u>Whitelist_Request Commands</u>:
- `/whitelist_request (server, ign)` - Allows a user to request Whitelist for a specific Server.
    - **TIP**: `ign` is optional if the Discord User has done this before and or already in the Database.

### <u>User/Member Group Commands</u>: 
- `/user info (user)` - Displays a Discord Users information and their Database information.
- `/user add (user, mc_ign, mc_uuid, steamid)` - Adds a User to the Database with the provided arguments.
    - **ATTENTION**: `user` is the **only required paramater**. 
        - **TIP**: Supports Discord Name/ID or Discord Display Name/Nickname's.
    - `mc_ign` and `mc_uuid` are optional.
        - **TIP**: When providing `mc_ign`, the bot will fetch the `mc_uuid` and set it for you in the Database if not provided.
    - `steamid` is optional. 
        - **TIP**: You can get someones `steamid` via their name at [Steam Finder](https://www.steamidfinder.com) or use `/user steamid (name)`
- `/user update (user, mc_ign, steamid)` - Updates the Users Database information with the provided arguments.

### <u>AMP Server Database Commands</u>: 
- `/dbserver cleanup` - Removes any Database Server entries that are not in your AMP Instances list.
- `/dbserver change_instance_id (from_server, to_server)` - Use this to switch an AMP instance with another AMP Instance in the Database.

### <u>AMP Server Commands</u>: 
- `/server update` - Updates the current list of AMP servers. *(This is also done every 30 seconds)*
    - **TIP**: This is used when creating a new Instance and needing to update the bots listings.
- `/server start (server)` - Starts the specified dedicated server.
    - **TIP**: `server` supports server nicknames that are set via `/server nickname add` command.
- `/server stop (server)` - Stops the specified AMP Dedicated server.
- `/server restart (server)` - Restarts the specified AMP Dedicated server.
- `/server kill (server)` - Kills the specified AMP Dedicated server. 
- `/server msg (server, message)` - Sends a message to the console for the specified AMP Dedicated server.
- `/server broadcast (prefix, message)` - Sends a Broadcast to all AMP Servers with the specified Prefix
- `/server users (server)` - Shows a list of the currently connected Users to the Server.
- `/server status (server)`- AMP Server Status(TPS, Player Count, CPU Usage, Memory Usage and Online Players)
- `/server backup (server)` - Creates a backup of the AMP Dedicated server.
    - **ATTENTION**: Set's the Title to `<user> generated backup` where `<user>` is the command users Discord Name.
        - The Description gets set to the current Date and Time in UTC

### <u>AMP Server Regex Commands</u>:
- See [Regex How-to](/REGEX.md) for full documentation.
- `/server regex add (server, name)` - Adds a Regex Pattern to the Server Regex List
- `/server regex delete (server, name)` - Deletes a Regex pattern from the Server Regex List.
- `/server regex list (server)` - Displays an Embed list of all the Server Regex Patterns.

### <u>AMP Server Settings Commands</u>:
- `/server settings info (server)` - Displays information such as IP, Donator Only, Whitelist Open, Discord Role, Discord Chat/Console/Event Channels and Nicknames.
- `/server settings hidden (server, flag)` - Hides or Shows the Server from Autocomplete lists when *NON-Moderators* are using slash commands.
- `/server settings host (server, host)` - Sets the Host of the AMP Dedicated server in the Database.
    - **ATTENTION**: This is only used and displayed when commands such as `/server status` and `/server list`.
    - **TIP**: `Host` is what you want your players to use to connect to the server!
- `/server settings role (server, role)` - Sets the role of the AMP Dedicated Server in the Database.
    - **ATTENTION**: This is the Discord Role the bot will give the User when requesting whitelist on said AMP Dedicated Server.
    - **TIP**: `role` can be a Discord Role ID or Discord Role Name.
- `/server settings whitelist (server, flag)` - Sets the whitelist to `flag` for the AMP Dedicated server.
    - Using the flag `Disabled` hides the `Whitelist Open/Closed` from the Banner. 
        - Simply set the flag to `True` or `False` for the Banner to show `Whitelist Open/Closed` respectively.
    - **ATTENTION**: This is only for Whitelisting purposes with auto-whitelist. This will not prevent players from connecting if already Whitelisted.
- `/server settings prefix (server, prefix)` - Set a prefix to be displayed on Chat messages IN-game from other servers.
    - **ATTENTION**: Any messages from Discord to a Server will be prefixed with `[DISCORD]`, otherwise if it comes from another AMP Server it will use the server's prefix.
- `/server settings status (server)` - Displays a embedded message of the AMP Dedicated server with status information and buttons for start, stop, kill and restart. 
    - **ATTENTION**: Everyone can see the buttons, but only people with proper permission can interact with the buttons.
    - **TIP**: To interact with the buttons the user must have the respective permisisons. See [Server Status Button Permissions](/PERMISSIONS.md#server-status-button-permissions).
- `/server settings displayname (server, name)` - Sets the display name of the AMP Dedicated server in the Database.
    - **ATTENTION**: This is used and displayed when commands such as `/server status` and `/server list` are used in place of the Instance Name.
    - **TIP**: You can use the `display name` in place of any `server` paramater for commands.
- `/server settings avatar (server, url)` - Sets the Avatar Icon for the specified AMP Dedicated Server.
    - **TIP**: Supports `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated. 
        - `url` Can be set to **None** so it displays the default/original Icon created.
- `/server settings donator (flag)` - Sets Donator Only Flag for the AMP Dedicated server to `True` or `False`
    - **ATTENTION**: This doesn't prevent players already whitelisted without the rank from connecting; only for auto whitelisting purposes.

### <u>AMP Server Console Commands</u>: 
- `/server console channel (server, channel)` - Sets the Discord Channel for the AMP Dedicated Server Console to output to.
    - **TIP**: You can type commands in the set channel similar to typing in AMP Console web GUI.
- `/server console filter (server, flag, filter_type)` - Set Console filtering for the AMP Dedicated server.
    - `flag` supports *True or False*. Simply enables/disabled filtering.
    - **TIP**: Setting the `filter_type` to either `whitelist` or `blacklist` can have mixed results depending on the `regex` patterns you have set.
        - See [Regex](/REGEX.md#how-console-filtering-can-affect-your-regex-patterns)

### <u>AMP Server Chat Commands</u>: 
- `/server chat channel (server, channel)` - Sets the Discord Channel for the AMP Dedicated server to output its chat messages to.
    - **TIP**: Discord Users can talk back and forth to in-game users as if they were playing too!

### <u>AMP Server Event Commands</u>:
- `/server event channel (server, channel)`- Sets the Event Channel for the provided AMP Dedicated Server to output event type messages to.
    - **ATTENTION**: This is events such as join/leave and achievements. Currently experimental, some may be missed.

### <u>AMP Server Whitelist Commands</u>: 
- `/server whitelist add (server, user)` - Adds the IGN to the AMP Dedicated server whitelist.
    - `user` only supports in-game names.
- `/server whitelist remove (server, user)` - Removes the IGN from the AMP Dedicated server whitelist.
    - `user` only supports in-game names.

### <u>AMP Server Banner Commands</u>:
- `/server banner settings (server)` - Prompts the Banner Editor View.
- `/server banner background (server, background_image)` - Select the Background Image to be used as the Banner Image for the selected AMP Server.
___

### **Interacting with your AMP Server via Discord Channels**:
- Set your Discord Channels per Server via
    - `/server console channel (server, channel)`
    - `/server chat channel (server, channel)`
    - `/server event channel (server, channel)`
- After setting your Discord Console Channel you should see console messages be displayed to the Discord Channel.
    - **TIP**: You can filter these messages. See [/server console filter (server, flag, filter_type)](/COMMANDS.md#console-commands)
        - Also take a look at [Regex Filtering](/REGEX.md)
    - **TIP**: You can type commands in the set channel similar to typing in AMP Console web GUI.
        - You must prefix any command with `.`; example `./list` would pass `/list` to the Console.

- After setting your Discord Chat Channel you can talk to players inside the server via Discord. 
    - Any message you send to that set channel; goes to that specific AMP Server and is sent like an in-game Chat Message.