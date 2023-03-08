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
whitelist.buttons #For Approve, Deny Buttons

staff #Changes layout of Server Autocomplete to show IDs

bot.*
bot.settings
bot.donator
bot.moderator
bot.permissions

bot.bannergroup.*
bot.bannergroup.rename
bot.bannergroup.remove
bot.bannergroup.add
bot.bannergroup.delete_group
bot.bannergroup.info
bot.bannergroup.create_group

bot.utils.*
bot.utils.message_timeout
bot.utils.roleid
bot.utils.ping
bot.utils.channelid
bot.utils.uuid
bot.utils.userid
bot.utils.status
bot.utils.sync
bot.utils.clear
bot.utils.restart
bot.utils.disconnect

bot.regex_pattern.*
bot.regex_pattern.update
bot.regex_pattern.add
bot.regex_pattern.list
bot.regex_pattern.delete

bot.banner_settings.*
bot.banner_settings.type
bot.banner_settings.auto_update

bot.cog.*
bot.cog.reload
bot.cog.load
bot.cog.unload

server.*
server.broadcast
server.restart
server.update
server.start
server.stop
server.users
server.status
server.backup
server.kill
server.display
server.msg

server.regex.*
server.regex.add
server.regex.list
server.regex.delete

server.banner.*
server.banner.settings
server.banner.background

server.console.*
server.console.filter
server.console.channel

server.settings.*
server.settings.role
server.settings.host
server.settings.avatar
server.settings.prefix
server.settings.donator
server.settings.info
server.settings.hidden
server.settings.displayname

server.whitelist.*
server.whitelist.add
server.whitelist.true
server.whitelist.false
server.whitelist.remove
server.whitelist.disabled

server.chat.*
server.chat.channel

server.event.*
server.event.channel

bot.whitelist.*
bot.whitelist.auto
bot.whitelist.wait_time
bot.whitelist.request_channel
bot.whitelist.donator_bypass

bot.whitelist_reply.*
bot.whitelist_reply.list
bot.whitelist_reply.add
bot.whitelist_reply.remove

whitelist_request

dbserver.*
dbserver.cleanup
dbserver.change_instance_id

user.*
user.update
user.info
user.add
```