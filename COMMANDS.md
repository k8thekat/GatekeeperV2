# **Commands List**
*This documentation is subject to change at any point and may not reflect recent changes*

## **Features**
___
- Paramaters such as `role`, `user` and `channel` support names or Discord IDs.
    - You can provide a partial name for any paramater and the bot will attempt to find the unique paramater. **CAUTION**: It will fail on duplicate entries!
        - See [Using paramaters with commands](#paramaters-and-how-to-use-them)
- All `server` paramaters support Server Nicknames and Display names!
    - See [Setting and Using Nicknames](#using-server-nicknames)


### **Using your commands!**
___
### Bot Commands: 
- `/bot moderator (role)` - Sets the Discord Role for Bot Moderator. 
    - **ATTENTION** - Please see `/bot permissions` for more control. 
- `/bot permissions (type)` - Sets the Bot Permissions to either `Default` or `Custom`.
    - **TIP**: Please see **[Permissions](/PERMISSIONS.md)** if you want `Custom` control over command usage.
- `/bot settings` - Lists Bot settings such as channels and whitelist status.
- `/bot ping` - Pong!
- `/bot load (path)` - Loads a specific Cog. *(eg. path = `/cogs/cog_template`)*
- `/bot unload (cogname)` - Unloads a specific Cog. *(eg. name = `cog_template`)*
- `/bot stop` - Stops the Bot.
- `/bot restart` - Restarts the Bot.
- `/bot status` - Replies with **AMP version** and if setup is complete, **DB version** and if setup is complete and **Displays Bot version information**.
    - **TIP**: This information is useful when reporting bugs/errors on Github!
- `/bot sync` - Syncs Gatekeeperv2 slash commands to your guild.
- `/bot donator (role)` - Sets the Donator Role for Donator Only AMP Server access.
    - **TIP**: This will prevent people without the role from requesting whitelist to Donator only Servers.
- `/bot display (flag)` - Allows the bot to automatically update the `/server display` embed messages.
    - **TIP**: Use the `/server display` command inplace of your "Server Info" or similar! 

### Whitelist Commands:
- `/bot whitelist auto (flag)` - Allows the bot to automatically Whitelist a Users request.
    - **ATTENTION**: `flag` must be *True or False*. Default is False.
        - **TIP**: This will not instantly whitelist the user if whitelist waittime is not set to zero.
- `/bot whitelist channel (channel)` - Sets the Discord channel for the bot to monitor for whitelist requests.
- `/bot whitelist waittime (time)` -  Sets the wait time for whitelist request after the message is received. *(eg. time = `5`)*
    - **REMINDER**: All time values are in **Minutes**! Please keep that in mind.
        - **TIP**: Set the value to zero to have the bot instantly whitelist users. Default value is 5 minutes!
- `/bot whitelist pending_emoji` - Set an Emoji to be applied to pending/waiting whitelist request.
    - **ATTENTION**: The reaction/emoji must be from your guild.
        - **TIP**: The bot will post a message and you react with the emoji/reaction you want to use! 
- `/bot whitelist done_emoji` - Set an Emoji for to be applied to finished whitelist requests.
    - **ATTENTION**: The reaction/emoji must be from your guild.
        - **TIP**: The bot will post a message and you react with the emoji/reaction you want to use! 

### Server Database Commands: 
- `/db cleanup` - Removes any Database Server entries that are not in your AMP Instances list.
- `/db swap (instanceID,instanceID)` - Use this to switch an AMP instance with another AMP Instance in the Database.


### User/Member Group Commands: 
- `/user info (user)` - Displays a Discord Users information and their Database information.
- `/user add (user,mc_ign,mc_uuid,steamid)` - Adds a User to the Database with the provided arguments.
    - **ATTENTION**: `user` is the **only required paramater**. 
        - **TIP**: Supports Discord Name/ID or Discord Display Name/Nickname's.
    - `mc_ign` and `mc_uuid` are optional.
        - **TIP**: When providing `mc_ign`, the bot will fetch the `mc_uuid` and set it for you in the Database if not provided.
    - `steamid` is optional. 
        - **TIP**: You can get someones `steamid` via their name at [Steam Finder](https://www.steamidfinder.com) or use `/user steamid (name)`
- `/user update (user,mc_ign,mc_uuid,steamid)` - Updates the Users Database information with the provided arguments.
- `/user uuid (mc_ign)` - Gets a users UUID! via Minecraft In-Game Name *(eg. mc_ign = k8_thekat)*
- `/user role (role)` - Sets a users permission role level. See [Permissions](/PERMISSIONS.md)
    - **TIP**: These have prefix's that you can set, allowing you to give people custom prefix's via a role for displaying inside of your Servers!
        - This only displays when sending a message from Discord to the Dedicated Server.


### Server Commands: 
- `/server display` - Lists all AMP Servers in Embeds with current information.
    - **TIP**: Those embeds get updated every minute! So use the command in a "Info" style channel and pin them!
- `/server start (server)` - Starts the specified dedicated server *(eg. name = `Vanilla MC`)*
    - **TIP**: `server` supports server nicknames that are set via `/server nickname add` command.
- `/server stop (server)` - Stops the specified AMP Dedicated server.
- `/server restart (server)` - Restarts the specified AMP Dedicated server.
- `/server kill (server)` - Kills the specified AMP Dedicated server. 
- `/server msg (message)` - Sends a message to the console for the specified AMP Dedicated server.
- `/server backup (server)` - Creates a backup of the AMP Dedicated server.
    - **ATTENTION**: Set's the Title to `user generated backup` where `user` is the command users Discord Name.
        - The Description gets set to the current Date and Time in UTC
- `/server status (server)` - Displays a embedded message of the AMP Dedicated server with status information and buttons for start, stop, kill and restart. 
    - **ATTENTION**: Everyone can see the buttons, but only people with proper permission can interact with the buttons.
    - **TIP**: To interact with the buttons the user must have the respective permisisons. See [Server Status Button Permissions](/PERMISSIONS.md#server-status-button-permissions).
- `/server users (server)` - Displays a list of connected users to the AMP Dedicated server.
- `/server displayname (server,name)` - Sets the display name of the AMP Dedicated server in the Database.
    - **ATTENTION**: This is used and displayed when commands such as `/server status` and `/server list` are used in place of the Instance Name.
    - **TIP**: You can use the `display name` in place of any `server` paramater for commands.
- `/server description (server,description)` - Sets the description of the AMP Dedicated server in the Database.
    - **ATTENTION**: This is only used and displayed when commands such as `/server status` and `/server list`.
- `/server IP (server,IP)` - Sets the IP of the AMP Dedicated server in the Database.
    - **ATTENTION**: This is only used and displayed when commands such as `/server status` and `/server list`.
    - **TIP**: `IP` is what you want your players to use to connect to the server!
- `/server role (server,role)` - Sets the role of the AMP Dedicated Server in the Database.
    - **ATTENTION**: This is the Discord Role the bot will give the User when requesting whitelist on said AMP Dedicated Server.
    - **TIP**: `role` can be a Discord Role ID or Discord Role Name.
- `/server prefix (server,prefix)` - Set a prefix to be displayed on Chat messages IN-game from other servers.
    - **ATTENTION**: Any messages from Discord to a Server will be prefixed with `[DISCORD]`, otherwise if it comes from another AMP Server it will use the server's prefix.
- `/server avatar (server,url)` - Sets the Avatar Icon for the specified AMP Dedicated Server.
    - **TIP**: Supports `webp`, `jpeg`, `jpg`, `png`, or `gif` if it's animated. 
        - `url` Can be set to **None** so it displays the default/original Icon created.
### Donator Commands:
- `/server donator true` - Sets Donator Only Flag for the AMP Dedicated server to True
    - **ATTENTION**: This doesn't prevent players without the rank from connecting; only for auto whitelisting purposes.
- `/server donator false` - Sets the Donator Only flag for the AMP Dedicated server to False
### Console Commands: 
- `/server console channel (server,channel)` - Sets the Discord Channel for the AMP Dedicated Server Console to output to.
    - **TIP**: You can type commands in the set channel similar to typing in AMP Console web GUI.
- `/server console filter (server,flag)` - Set Console filtering for the AMP Dedicated server.
    - **TIP**: Setting this to True will still display login/disconnect events, achievements, chat messages, console commands and anything else deemed important.
    - `flag` supports *True or False*
### Chat Commands: 
- `/server chat channel (server,channel)` - Sets the Discord Channel for the AMP Dedicated server to output its chat messages to.
    - **TIP**: Discord Users can talk back and forth to in-game users as if they were playing too!
### Whitelist Commands: 
- `/server whitelist true (server)` - Sets the whitelist flag to `true` for the AMP Dedicated server.
    - **ATTENTION**: This is only for Whitelisting purposes with auto-whitelist. This will not prevent players from connecting.
- `/server whitelist false (server)` - Sets the whitelist flag to false for the dedicated server.
- `/server whitelist add (server,user)` - Adds the IGN to the AMP Dedicated server whitelist.
    - `user` only supports in-game names.
- `/server whitelist remove (server,user)` - Removes the IGN from the AMP Dedicated server whitelist.
    - `user` only supports in-game names.

___

### **Setting Server Nicknames**:
- First thing to remember is the Nickname must be **UNIQUE**. 
    - No two AMP Servers can have the same Nickname in their list of Nicknames.
- These Nicknames will work during **auto-whitelist requests** allowing the bot to handle a variance of "Nicknames".
- Each AMP Server can have an unlimited amount of Nicknames; allowing for lots of variety.
    - **CAUTION**: Any SIMILARITIES between Server Nicknames will cause duplicate finds. See below.
        - *Example* - **Server 1**: `Vanilla MC` || **Server 2**: `Vanilla TDM` and you search for `Vanilla` would return multiple results.  

### Nickname Commands:
- `/server nickname add (server,nickname)` - Adds the specified `nickname` to the servers lists of nicknames.
    - **TIP**: These nicknames are searched for when doing Whitelist requests allowing more variance to find a specific server.
- `/server nickname remove (server,nickname)` - Removes the specificed `nickname` from the servers list of nicknames.
- `/server nickname list (server)` - Displays a list of the AMP Servers nicknames.

### **Interacting with your Server via Discord Channels**:
- Set your Discord Console Channels and Discord Chat Channels per Server via
    - `/server console channel (server,channel)`
    - `/server chat channel (server,channel)`
- After setting your Discord Console Channel you should see console messages be displayed to the Discord Channel.
    - **TIP**: You can filter these messages. See [/server console filter (server,flag)](/COMMANDS.md#console-commands)
    - **TIP**: You can type commands in the set channel similar to typing in AMP Console web GUI.
- After setting your Discord Chat Channel you can talk to players inside the server via Discord. 
    - Any message you send to that set channel; goes to that specific AMP Server and is sent like an in-game Chat Message.