#Full List of Permission Nodes
# [
#         'bot.*',
#         'bot.ping',
#         'bot.cogload',
#         'bot.cogunload',
#         'bot.stop',
#         'bot.restart',
#         'bot.status',
#         'bot.sync',
#         'bot.settings',
#         'bot.whitelist.*',
#         'bot.whitelist.channel',
#         'bot.whitelist.waittime',
#         'bot.whitelist.auto',
#         'bot.whitelist.pendingemoji',
#         'bot.whitelist.doneemoji',
#         'user.*',
#         'user.info',
#         'user.add',
#         'user.update',
#         'user.uuid',
#         'dbserver.*',
#         'dbserver.cleanup',
#         'dbserver.swap',
#         'server.*',
#         'server.list',
#         'server.start',
#         'server.stop',
#         'server.restart',
#         'server.kill',
#         'server.msg',
#         'server.backup',
#         'server.status',
#         'server.users',
#         'server.displayname',
#         'server.description',
#         'server.ip',
#         'server.role',
#         'server.whitelist.*',
#         'server.whitelist.true',
#         'server.whitelist.false',
#         'server.whitelist.add',
#         'server.whitelist.remove',
#         'server.donator.*',
#         'server.donator.true',
#         'server.donator.false',
#         'server.console.*',
#         'server.console.on',
#         'server.console.off',
#         'server.console.channel',
#         'server.console.filter',
#         'server.chat.channel',
#         ]

Roles = [
    {
    'name': 'Admin',
    'discord_role_id': None,
    'permissions': [
        'bot.*',
        'user.*',
        'server.*',
        'server.whitelist.*',
        'server.donator.*',
        'server.console.*',
        'server.chat.channel',
        ]
    },

    {
    'name': 'Moderator',
    'discord_role_id': None,
    'permissions': [
        'bot.*',
        'user.*',
        'server.*',
        'server.whitelist.*',
        'server.donator.*',
        'server.console.*',
        'server.chat.channel',
        ]
 
    },

    {
    'name': 'Maintenance',
    'discord_role_id': None,
    'permissions': []
    },
    {
    'name': 'Staff',
    'discord_role_id': None,
    'permissons': []
    },
    {
    'name': 'General',
    'discord_role_id': None,
    'permissons':[]
    }
    
]