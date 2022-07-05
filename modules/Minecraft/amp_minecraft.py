import AMP
import requests
import json
    
class AMPMinecraft(AMP.AMPInstance):
    """This is Minecraft Specific API calls for AMP"""
    def __init__(self, instanceID = 0, serverdata = {},Index = 0, Handler=None):
        super().__init__(instanceID, serverdata, Index,Handler= Handler)
        
        #self.APImodule = 'MinecraftModule'
        #self.Console = AMPMinecraftConsole(self)

    def name_Conversion(self,name): 
        """Converts an IGN to a UUID/Name Table \n
        `returns 'uuid'` else returns `None`, multiple results return `None`"""
        url = 'https://api.mojang.com/profiles/minecraft'
        header = {'Content-Type': 'application/json'}
        jsonhandler = json.dumps(name)
        post_req = requests.post(url, headers=header, data=jsonhandler)
        minecraft_user = post_req.json()

        if len(minecraft_user) == 0: 
            return None

        if len(minecraft_user) > 1:
            return None

        else:
            return minecraft_user[0]['id'] #returns [{'id': 'uuid', 'name': 'name'}] 

    def name_History(self,mc_user_uuid):
        """Requires `user_UUID` WTF Does this even return? Possible a Dictionary List?"""
        url = f'https://api.mojang.com/user/profiles/{mc_user_uuid}/names'
        post_req = requests.get(url)
        return post_req.json()[-1]

   
    def addWhitelist(self,User:str):
        """Adds a User to the Whitelist File *Supports UUID or IGN*"""
        self.Login()
        parameters = {'UserOrUUID': User}
        result = self.CallAPI(f'{self.APIModule}/AddToWhitelist', parameters)
        return result

    def getWhitelist(self):
        """Returns a List of Dictionary Entries of all Whitelisted Users `{'name': 'IGN', 'uuid': '781a2971-c14b-42c2-8742-d1e2b029d00a'}`"""
        self.Login()
        parameters = {}
        result = self.CallAPI(f'{self.APIModule}/GetWhitelist',parameters)
        return result['result']

    def removeWhitelist(self,User:str):
        """Removes a User from the Whitelist File *Supports UUID or IGN*"""
        self.Login()
        parameters = {'UserOrUUID': User}
        result = self.CallAPI(f'{self.APIModule}/RemoveWhitelistEntry',parameters)
        return result


    def checkWhitelist(self,user_UUID):
        """Checks if the User is already in the whitelist file.
        Returns `True` if the UUID is found."""
        self.Login()
        server_whitelist = self.getWhitelist()
        for entry in server_whitelist:
            if user_UUID == entry['uuid']:
                return True

    def getHeadbyUUID(self,UUID:str):
        """Gets a Users Player Head via UUID"""
        self.Login()
        parameters = {'id': UUID}
        result = self.CallAPI(f'{self.APIModule}/GetHeadByUUID', parameters)
        return result

    def banUserID(self,ID:str):
        """Bans a User from the Server"""
        self.Login()
        parameters = {'id': ID}
        result = self.CallAPI(f'{self.APIModule}/BanUserByID', parameters)
        return result

#!TODO! Need to figure the super() Init for the new console.
class AMPMinecraftConsole(AMP.AMPConsole):
    def __init__(self,AMPInstance = AMPMinecraft):
        super().__init__(self,AMPInstance)
        #self.AMPMinecraft = AMPMinecraft
