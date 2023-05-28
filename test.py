
import asyncio


class DB_Spoof():
    def __init__(self):
        self.Nicknames = 'Temp Nickname List'
        self.Description = 'Temp Server Description'
        self.Donator = True
        self.Whitelist = True
        self.IP = 'MC.YourDNSorAMPIPHere.com'
        self.users = ['Kat', 'Dan', 'Lightning', 'Alain', 'Saiorie']


def walk_dir():
    import pathlib
    import importlib.util
    # cwd = pathlib.Path.cwd().joinpath('modules').glob('amp_*.py')
    cwd = pathlib.Path.cwd().joinpath('modules').iterdir()
    for folder in cwd:
        file_list = folder.glob('amp_*.py')
        for script in file_list:
            module_name = script.name[4:-3].capitalize()
            spec = importlib.util.spec_from_file_location(module_name, script)
            foo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(foo)
            print(dir(foo))
# walk_dir()


def test_dir():
    import pathlib
    file_check = pathlib.Path.cwd().joinpath('tokenstemplate.py')
    print(file_check)
    if file_check.exists():
        print('Found File')

# test_dir()


def re_search():
    import re
    flag = 'What in the holy hellGatekeeperV212412312312312'
    flag_reg = re.search("(gatekeeper)", flag.lower())
    if flag_reg != None:
        if flag_reg.group():
            print('Found a match')

# re_search()


def re_message_parse():
    # import modules.message_parserv2 as parse
    requests = ['Can i get re-whitelisted for TNP 5?  ign: rahz_vael',
                'server: Tnp5 Name: Speamy3',
                'Not sure if I need to resubmit a request or not  IGN: Codemeister101 TNP5',
                'Can I be whitelisted for E6 please ign aimhreidh1 ',
                'an i get a whitelist on E6 Normal    ing Solclaim',
                'server(s): TNP5, E6 ign: Clinomanic_Sloth',
                'IGN: Warteks; Server: DW20',
                'IGN: Kalvsund Server; Dw20',
                'I assume were allowed to be whitelisted in multiple servers, so may i ask to be whitelisted in tnp5?',
                'Can i please get whitelisted to e6']

    test = 'thisis a test to findserver44 test test server'
    # parse.ParseIGNServer(test)
    # for entry in requests:
    # print(parse.ParseIGNServer(entry))

# re_message_parse()


name = 'TobiShu_'


def name_Conversion(name):
    import json
    import requests
    """Converts an IGN to a UUID/Name Table \n
    `returns 'uuid'` else returns `None`, multiple results return `None`"""
    url = 'https://api.mojang.com/profiles/minecraft'
    header = {'Content-Type': 'application/json'}
    jsonhandler = json.dumps(name)
    post_req = requests.post(url, headers=header, data=jsonhandler)
    minecraft_user = post_req.json()
    print(minecraft_user)

# name_Conversion(name)


def dict_test():
    a = [{'Whitelist': 'True'}, {'Whitelist_wait_time': '5'}]
    index = 0
    for entry in a:
        print(list(entry.keys())[0], list(entry.values())[0])

# dict_test()


def path_libtest():
    import pathlib
    dircheck = pathlib.Path.exists(pathlib.Path.cwd().joinpath('logs'))
    # print(dircheck)
    # pathlib.Path.mkdir(pathlib.Path.cwd().joinpath('logs'))
    posix_path = pathlib.Path.as_posix(pathlib.Path.cwd().joinpath('logs'))
    print(type(posix_path), posix_path)

# path_libtest()


def parser_test():
    from modules.parser import Parser
    a = Parser()
    test = [
        "rahz_vael E6 whitelist please",
        "Ign acrophobis for e6 please",
        "Ign: Tefka E6 pls",
        "IGN:  xSardonic for E6 and Age of Fate (Sorry if late)"
    ]
    for entry in test:
        ign, server = a.ParseIGNServer(messages=entry)
        # print('IGN:',ign, '|| Servers:', server)
# parser_test()


def db_server_info():
    import db
    dbhandler = db.getDBHandler()
    curdb = dbhandler.DB
    db_servers = curdb.GetAllServers()
    # print(servers)
    user_entries = ['terraswoopforce', 'auroras', 'server', 'starbound', 'counter-strike', 'go']
    list_of_server_names = []
    for server in db_servers:
        dbserver = curdb.GetServer(Name=server)
        list_of_server_names.append(server.replace('_', ' ').lower())
        for nickname in dbserver.Nicknames:
            list_of_server_names.append(nickname.lower())

    list_of_server_names.sort(reverse=True)
    for i in range(0, len(list_of_server_names)):
        list_of_server_names[i] = list_of_server_names[i].split()

    # use the length of the list entry inside of the server names/nicknames list eg mylist[1,2] to entry[0:len(mylist)].
    index = 0
    possible_servers = []
    while index < len(user_entries):
        found_server = None
        for curserver in list_of_server_names:
            # print(user_entries[index:index+len(curserver)])
            if user_entries[index:index + len(curserver)] == curserver:
                found_server = curserver
                break
        if found_server != None:
            index += len(found_server)
            possible_servers.append(" ".join(found_server))
        else:
            index += 1

# db_server_info()


def role_perms_test():
    import bot_perms
    roles = bot_perms.Roles
    user_role = 'Admin'  # This will be fetched from the DB.. if its not equal to None.
    command_perm_node = 'server.list'
    user_discord_role_id = 123456789
    command_super_node = command_perm_node.split(".")[0] + '.*'
    for role in roles:
        if user_role in role['name']:
            print('Found Role in permissions list', user_role, role['name'])
            if command_super_node in role['permissions']:
                print('Found Super perm node', command_super_node)
                command_perm_node_false_check = '-' + command_perm_node
                if command_perm_node_false_check in role['permissions']:
                    if command_perm_node_false_check[1:] == command_perm_node:
                        print('This perm node has been denied even though you have global permissions.', command_perm_node_false_check, command_perm_node)
                        return

            for perm in role['permissions']:
                if command_perm_node == perm:
                    print('Found command perm node in Roles Permissions list.', command_perm_node, perm)
                    return
                else:
                    print('No permission node found', perm)
                    continue

        if user_discord_role_id == role['discord_role_id']:
            print('User has the discord role ID for a permissions role', user_discord_role_id, role['discord_role_id'], role['name'])
            if command_super_node in role['permissions']:
                print('Found Super perm node')
            for perm in role['permissions']:
                if command_perm_node == perm:
                    print('Found command perm node in Roles Permissions list.', command_perm_node, perm)
                    return
                else:
                    print('No permission node found', perm)
                    continue

# role_perms_test()


def path_config():
    path = 'H:/VSC/Projects/Discord Bot/modules/Valheim/cog_valheim.py'
    path_strlist = path.split("/")
    # print(path_strlist)
    print((".").join(path.split("/")[-4:])[:-3])

# path_config()


def bot_perms_check():
    import json
    import pathlib

    # Load the file
    jsonfile = pathlib.Path.cwd().joinpath('bot_perms.json')
    file = json.load(open(jsonfile, 'r'))
    print(file['Roles'])


class botPerms():
    def __init__(self):
        self._last_modified = 0
        self.permissions = None
        self.validate_and_load()

    def validate_and_load(self):
        import json
        import pathlib
        self.json_file = pathlib.Path.cwd().joinpath('bot_perms.json')
        if self.json_file.stat().st_mtime > self._last_modified:
            try:
                self.permissions = json.load(open(self.json_file, 'r'))
                self._last_modified = self.json_file.stat().st_mtime
            except json.JSONDecodeError:
                self.permissions = None
                print('ERROR')
                # self.logger.critical('Unable to load your permissions file. Please check your formatting.')


def perm_node_check(permission_node: str):
    """Checks a Users for a DB Role then checks for that Role inside of bot_perms.py, then checks that Role for the proper permission node."""

    bPerms = botPerms()
    roles = bPerms.permissions['Roles']
    # DBHandler = DB.getDBHandler()
    # main_DB = DBHandler.DB
    # DBConfig = DBHandler.DBConfig

    # logger = logging.getLogger()

    # Lets get our DB user and check if they exist.
    # DB_user = main_DB.GetUser(str(context.author.id))

    # Lets also check for their DB Role
    user_role = 'Moderator'
    if user_role == None:
        return False

    # Need to turn author roles into a list of ints.
    command_perm_node = permission_node
    # This is to check for Super perm nodes such as `server.*`
    command_super_node = command_perm_node.split(".")[0] + '.*'
    for role in roles:
        if user_role.lower() in role['name'].lower():
            print('Found Role in permissions list', user_role, role['name'])
            if command_super_node in role['permissions']:
                print('Found Super perm node', command_super_node)
                command_perm_node_false_check = '-' + command_perm_node
                if command_perm_node_false_check in role['permissions']:
                    if command_perm_node_false_check[1:] == command_perm_node:
                        print('This perm node has been denied even though you have global permissions.')
                        # logger.dev('This perm node has been denied even though you have global permissions.',command_perm_node_false_check,command_perm_node)
                        return False

            if permission_node in role['permissions']:
                print('Found command perm node in Roles Permissions list.')
                return True


def word_wrap():
    from PIL import ImageFont
    import pathlib
    _font = pathlib.Path("resources/fonts/ReemKufiFun-Regular.ttf").as_posix()
    _font_Body_size = 25
    test_str = 'All the Mods 7 To the Sky is the sequel to the popular atm6 sky, we have taken feedback from the first iteration to make this pack the best we have to offer, adding in mods that were not in the first, such as Twilight Forest and Alchemistry, followed by the mod ex machinis, an automation addon for ex nihilo built in house by ATM to take you from early, all the way to end game automated resources.'

    split_char = ' '
    if test_str.find(split_char) == -1:
        print('Failed to find split char')
        return None

    split_test_str = test_str.split(split_char)
    temp_list = []
    limit = 1000  # Pixels
    temp_str = ''
    truncate = False
    for i in range(0, len(split_test_str)):
        temp_str += split_test_str[i] + split_char
        if ImageFont.truetype(_font, _font_Body_size).getsize(temp_str)[0] < limit:
            continue

        elif truncate == True:
            print('temp str', temp_str)
            return temp_str

        elif truncate == False:
            temp_list.append(temp_str)
            temp_str = ''

    # print('temp list', temp_list)
    # Could Join on new line here or control how much to display.. etc
    print('temp list w/ newline:', "\n".join(temp_list))
# word_wrap()


a = '123456'


def my_func(a: str):
    if len(a) == 7 and a[0] == '#':
        a = a[1:]

    if re.search('([0-9a-f]{6})$', a) and len(a) == 6:
        print('Found Hex', a)
        return
    else:
        print('Failed')
        return

# my_func(a)


async def api():
    from amp_instance import AMP_Instance
    from amp_ads import AMP_ADS
    # from amp_api import AMP_API
    from pprint import pprint
    import logging
    logging.getLogger().setLevel(logging.INFO)
    # amp = AMP_Instance()  # main AMP class
    ADS = AMP_ADS()
    # amp_api = AMP_API()
    ADS._val_settings()
    await ADS.getInstances()
    # for entry in instance_data["result"][0]["AvailableInstances"]:
    # pprint(entry)
    # if "DeploymentArgs" in entry:
    #     print(entry["DeploymentArgs"])

    # if "ModuleDisplayName" in entry:
    #     print(entry["ModuleDisplayName"])

    # elif "Module" in entry:
    #     print(entry["Module"])


asyncio.run(api())


# check_SessionPermissions()
# check_GatekeeperRole_Permissions()
#

AMPUSER_id
AMPUSER_info
_roleID
SUPERADMIN_roleID


#Instance Attrs for Permissions
_have_AMP_botRole - _have_role
_AMP_botRole_exists - _role_exists
_have_superAdmin X