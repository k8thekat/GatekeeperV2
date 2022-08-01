# **Gatekeeper V2**

Welcome to the efforts of countless hours of learning and failed attempts at writing code that culminated into this project known as Gatekeeper! Originally this started out as a bot to bring CubeCoders AMP to Discord with support for only Minecraft, but has evolved into this encompasing project of providing support for any type of server AMP can run along with providing as many of AMPs core features inside of Discord.





### Requirements
_________

- Python 3.1 or greater
- Pip 2.1 or greater
- Discord.py 2.0 or greater 
    - *Please visit: https://github.com/Rapptz/discord.py to install discord.py development version!*
- Cube Coders AMP License
    - *https://cubecoders.com/AMP*


### Getting Started

## *Launch Args*
    '-token', help='Bypasse tokens validation check.',required= False, action="store_true"
    '-dev', help='Enable development print statments.',required= False, action="store_true"
    '-debug', help='Enables DEBUGGING level for logging', required= False, action="store_true"
    '-discord', help='Disables Discord Intigration (Used for Testing)',required= False, action="store_false"
    'guildID', help='Set to your Discord Server ID for local Sync', default=None
    '-super', help='This leaves AMP Super Admin role intact, use at your own risk.', required= False, action="store_false"
       

## *Commands List*

    ?+ Bot
        - Settings - Lists all Bot Settings
        - Setup - Sets the Discord Role for Staff
        - Test - N/A
        - ping - Pong!
        - cog loader - Loads a specific Cog
        - cog unloader - Unloads a specific Cog
        - stop - Stops the Bot
        - restart - Restarts the Bot
        - status - Checks for AMP/DB and Displays Bot version information
        - sync - Syncs Bot commands to the guild
        !TBD - update - Will be used to check for Gatekeeper Updates (Doesn't work ATM)
        !TBD - log level - Adjusts the Log level ()

        ?+ Whitelist
            - Whitelist Channel set - Sets the Whitelist channel for the bot to listen too
            - Whitelist wait time - Sets the Whitelist wait time after message is recieved
            - Whitelist auto whitelist - Allows the bot to automatically Whitelist a Users request
            - Whitelist pending emoji - Set an Emoji to be applied to pending/waiting whitelist request
            - Whitelist done emoji - Set an Emoji for to be applied to finished whitelist requests

    ?+ DBServer
        !TBD(Do Not Use) - cleanup : Removes any DB Servers that are not in AMP instances
        !TBD(Do Not Use) - instance swap : Will be used for swapping instances via InstanceIDs

    ?+ User/Member Group
        - Info - Displays User information from the DB
        - Add - Adds a User to the DB
        - Update - Updates a user MC_IGN, MC_UUID, SteamID and Donator Flag
        - UUID - gets a users UUID!
        !- Test - N/A

    ?+ Server
        - list - Lists all available servers
        - start - Starts the specificed dedicated server
        - stop - Stops the specified dedicated server 
        - restart - restarts the specified dedicated server 
        - kill - kills the specificed dedicated server 
        - console msg - sends a message through the console for the specified dedicated server
        - backup - creates a backup of the dedicated server
        - status - displays a embeded message of the dedicated server with buttons for start,stop,kill and restart
        - users list - displays a list of connected users to the dedicated server
        - display name - sets the display name of the dedicated server in the DB
        - description - sets the description of the dedicated server in the DB
        - ip - sets the IP of the dedicated server in the DB
        - role - sets the role of the dedicated server in the DB

        ?+ Donator
            - true - Sets Donator Only Flag for the dedicated server to True
            - false - Sets the Donator Only flag for the dedicated server to False

        ?+ Console
            - on - Turns the console on for the dedicated server (default: on)
            - off - Turns off the console for the dedicated server
            - channel - Sets the discord channel for the dedicated server to output too
            - filter - Enable or Disable console filtering for the dedicated server

        ?+ Chat
            - channel - Sets the discord channel for the dedicated server to output its chat messages

        ?+ Whitelist
            - true - Sets the whitelist flag to true for the dedicated server
            - false - Sets the whitelist flag to false for the dedicated server
            - test - N/A
            - add - Adds the IGN to the dedicated server whitelist
            - remove - Removes the IGN from the dedicated server whitelist


### **Credits**
"Thank You" to everyone at CubeCoders Discord Server, especially IceofWrath, Mike, Greenlan and everyone else in their discord. 
Same goes to everyone over at Discord.py Discord Server, especially Solistic for all the silly questions I kept asking about embed's and Hybrid messages!