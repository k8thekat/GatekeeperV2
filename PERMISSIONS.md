# **Permissions**

This section is for those wanting to really "Fine Tune" your permissions. 

## **Features**
___
- Gatekeeperv2 has the ability to set permissions *per command* or *globally* across a command tree.
    - *See below for [How to use!](#using-your-permission-nodes)*
- You can make as many "Roles" as you want and can assign them to Discord users however you want! 
    - The only restriction is that **ANY ROLE** you give a Discord User via the `/user role` command **MUST EXIST** in the `bot_perms` file or it won't work.

## **Enabling Custom Permissons**
- After configuring your `bot_perms.json` file, simply restart Gatekeeper and use the command `/bot permissions` and select `Custom`
    - Gatekeeper will verify the file, reporting any issues it finds and exiting. You must restart the bot after fixing your permissions file.
        - **TIP**: I strongly recommend keeping a backup of the file when making changes. 
        - **WARNING**: **Gatekeeper will NOT START** if you are set to `Custom` and the file is invalid.
    - **TIP** - The bot will still respect those with __Discord Administrator Permission__ privelage under `Role -> Advanced Permissions`.
        - **WARNING**: The bot will no longer respect the role set by `/bot moderator`, it is completely bypassed.

### **Setting up your Permissions File**
- Each role must have a `name`, `discord_role_id`, `prefix` and `permissions`. 
    - **ATTENTION**: All these values must exist! `discord_role_id` and `prefix` are the only ones that can be set to `"None"`
    - **TIP**: You can get a Discord role's ID via the `/bot roleid (role)` command.
    ```python
    "name": "Admin", #This field can be set to any name/phrase you want to set as a "role" 
    "discord_role_id": "1004516841932214373", #This must be the numeric value you get from Copy Role ID in developer mode.
    "prefix": "Admin", #This will be displayed when a User with this role talks On Discord and is sent to the Dedicated Server.
    "permissions": [
        "bot.status",
        "bot.ping",
        "bot.sync"]
    ```

### **Using your Permission Nodes**
___

### Adding Permissions:
- Simply place the permission node inside the Roles permissions list.
    - **REMINDER**: You want to place the permission node inside the `opening "[" and closing "]"`, each entry needs `quotes("double")` and between each entry needs to be a `comma(,)`. *(eg `'-bot.status', '-bot.)*
    
    ```python
    {"name": "Admin",
    "discord_role_id": "1004516841932214373", #Must be a Discord Role ID.
    "prefix":
    "permissions": 
        ["bot.status", #This is ALLOWING the command '/bot status'
        "bot.ping",
        "bot.sync"]} 
    ```
### Removing Permissions:
- Simply place the permission node inside the Roles permissions list with a `-` in front of it. *(eg. `-bot.status`)*
    - **REMINDER**: You want to place the permission node inside the `opening "[" and closing "]"`, each entry needs `quotes("double")` and between each entry needs to be a `comma(,)`. *(eg `"-bot.status", "-bot.ping"`)*
    ```python
    {"name": "Admin",
    "discord_role_id": "1004516841932214373",
    "permissions": 
        ["-bot.status", #This is REMOVING the permissions node bot.status preventing the role from using the command '/bot status'
        "bot.ping",
        "bot.restart"]} 
    ```

### Adding Wildcard Permissions:
- Adding the permission node `server.*` would give the Role full access to any `/server` command.
    - *Location of the wildcard does not matter.*
- **TIP**: You can __REMOVE__ permission for a specific command simply by adding a `-` before the permission node *(eg. `-server.list`)* 
    - The user would still have access to all other `/server` commands __EXCEPT__ `/server list`.
    ```python
    {"name": "Admin",
    "discord_role_id": "1004516841932214373",
    "permissions": 
        ["bot.*", #This is my wildcard, allowing me to use any command that starts with '/bot'
        "-bot.status"]} #This is REMOVING the permission to use the command '/bot status' even though the wildcard exists.
    ```

___
### Server Status Button Permissions:
- For a User to interact with the buttons from the `/server status` command. They need the respective permission nodes.
    - **Start Button** requires `server.start`
    - **Stop Button** requires `server.stop`
    - **Restart Button** requires `server.restart`
    - **Kill Button** requires `server.kill`
___
### Discord Console Channel Permissions:
- For a user to interact/send console commands via the Discord Console Channel. They need `server.console.interact`
    - See [Commands-Interacting via Discord Channels](/COMMANDS.md#interacting-with-your-server-via-discord-channels)
___
#### **Full Permission Node List**
- This list may be missing permissions. You have been warned, check your logger for permission nodes.
___
```py
"bot.*",
"bot.settings",
"bot.roleid",
"bot.channelid",
"bot.userid",
"bot.ping",
"bot.cogload",
"bot.cogunload",
"bot.stop",
"bot.restart",
"bot.status",
"bot.sync",
"bot.donator",
"bot.embed.*",
"bot.embed.auto.update",
"whitelist.*",
"whitelist.auto",
"whitelist.channel",
"whitelist.waittime",
"whitelist.pendingemoji",
"whitelist.doneemoji",
"whitelist.reply.*",
"whitelist.reply.add",
"whitelist.reply.remove",
"whitelist.reply.list",
"dbserver.*",
"dbserver.cleanup",
"dbserver.swap",
"user.*",
"user.info",
"user.add",
"user.update",
"user.uuid",
"user.role",
"user.steamid",
"server.*",
"server.display",
"server.start",
"server.stop",
"server.restart",
"server.kill",
"server.msg",
"server.settings.info",
"server.backup",
"server.status",
"server.users",
"server.broadcast",
"server.settings.*",
"server.settings.displayname",
"server.settings.description",
"server.settings.ip",
"server.settings.role",
"server.settings.prefix",
"server.settings.avatar",
"server.settings.donator",
"server.settings.hidden",
"server.console.*",
"server.console.channel",
"server.console.filter",
"server.console.interact",
"server.chat.channel",
"server.event.channel",
"server.whitelist.*",
"server.whitelist.true",
"server.whitelist.false",
"server.whitelist.add",
"server.whitelist.remove",
"server.nickname.*",
"server.nickname.add",
"server.nickname.remove",
"server.nickname.list"
```