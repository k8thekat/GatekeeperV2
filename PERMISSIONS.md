# **Permissions**

This section is for those wanting to really "Fine Tune" your permissions. 

## **Features**
___
- Gatekeeperv2 has the ability to set permissions *per command* or *globally* across a command tree.
    - *See below for [How to use!](#using-your-permission-nodes)*
- You can make as many "Roles" as you want and can assign them to Discord users however you want! 
    - The only restriction is that **ANY ROLE** you give a Discord User via the `/user role` command **MUST EXIST** in the `bot_perms` file or it won't work.





### **Using your Permission Nodes**
___

### Adding Permissions:
- Simply place the permission node inside the Roles permissions list.
    - **REMINDER**: You want to place the permission node inside the `opening "[" and closing "]"`, each entry needs `quotes('single' or "double")` and between each entry needs to be a `comma(,)`. *(eg `'-bot.status', '-bot.)*
    ```python
    {'name': 'Admin',
    'discord_role_id': "None",
    'permissions': 
        ['bot.status', #This is ALLOWING the command '/bot status'
        'bot.ping',
        'bot.sync']} 
    ```
### Removing Permissions:
- Simply place the permission node inside the Roles permissions list with a `-` in front of it. *(eg. `-bot.status`)*
    - **REMINDER**: You want to place the permission node inside the `opening "[" and closing "]"`, each entry needs `quotes('single' or "double")` and between each entry needs to be a `comma(,)`. *(eg `'-bot.status', '-bot.ping'`)*
    ```python
    {'name': 'Admin',
    'discord_role_id': "None",
    'permissions': 
        ['-bot.status', #This is REMOVING the permissions node bot.status preventing the role from using the command '/bot status'
        'bot.ping',
        'bot.restart']} 
    ```

### Adding Wildcard Permissions:
- Adding the permission node `server.*` would give the Role full access to any `/server` command.
    - *Location of the wildcard does not matter.*
- **TIP**: You can __REMOVE__ permission for a specific command simply by adding a `-` before the permission node *(eg. `-server.list`)* 
    - The user would still have access to all other `/server` commands __EXCEPT__ `/server list`.
    ```python
    {'name': 'Admin',
    'discord_role_id': "None",
    'permissions': 
        ['bot.*', #This is my wildcard, allowing me to use any command that starts with '/bot'
        '-bot.status']} #This is REMOVING the permission to use the command '/bot status' even though the wildcard exists.
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
___
```
'bot.*',
'bot.ping',
'bot.cogload',
'bot.cogunload',
'bot.stop',
'bot.restart',
'bot.status',
'bot.sync',
'bot.settings',
'bot.whitelist.*',
'bot.whitelist.channel',
'bot.whitelist.waittime',
'bot.whitelist.auto',
'bot.whitelist.pendingemoji',
'bot.whitelist.doneemoji',
'user.*',
'user.info',
'user.add',
'user.update',
'user.uuid',
'dbserver.*',
'dbserver.cleanup',
'dbserver.swap',
'server.*',
'server.info',
'server.display',
'server.avatar',
'server.start',
'server.stop',
'server.restart',
'server.kill',
'server.msg',
'server.backup',
'server.status',
'server.users',
'server.displayname',
'server.description',
'server.ip',
'server.role',
'server.whitelist.*',
'server.whitelist.true',
'server.whitelist.false',
'server.whitelist.add',
'server.whitelist.remove',
'server.donator.*',
'server.donator.true',
'server.donator.false',
'server.console.*',
'server.console.on',
'server.console.off',
'server.console.channel',
'server.console.filter',
'server.console.interact',
'server.chat.channel',
'server.nickname.*',
'server.nickname.add',
'server.nickname.remove',
'server.nickname.list',

