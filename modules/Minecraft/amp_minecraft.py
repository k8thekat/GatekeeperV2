import modules.AMP as AMP


class AMPMinecraft(AMP.AMPInstance):
    """This is Minecraft Specific API calls for AMP"""
    def __init__(self, instanceID = 0, serverdata = {},Index = 0):
        super().__init__(instanceID, serverdata, Index)
        self.APImodule = 'MinecraftModule'

    @AMP.Login
    def addWhitelist(self,User:str):
        """Adds a User to the Whitelist File *Supports UUID or IGN*"""
        parameters = {'UserOrUUID': User}
        result = self.CallAPI(f'{self.APIModule}/AddToWhitelist', parameters)
        return result

    @AMP.Login
    def getWhitelist(self):
        """Returns a List of Dictionary Entries of all Whitelisted Users `{'name': 'IGN', 'uuid': '781a2971-c14b-42c2-8742-d1e2b029d00a'}`"""
        parameters = {}
        result = self.CallAPI(f'{self.APIModule}/GetWhitelist',parameters)
        return result['result']

    @AMP.Login
    def removeWhitelist(self,User:str):
        """Removes a User from the Whitelist File *Supports UUID or IGN*"""
        parameters = {'UserOrUUID': User}
        result = self.CallAPI(f'{self.APIModule}/RemoveWhitelistEntry',parameters)
        return result

    @AMP.Login
    def getHeadbyUUID(self,UUID:str):
        """Gets a Users Player Head via UUID"""
        parameters = {'id': UUID}
        result = self.CallAPI(f'{self.APIModule}/GetHeadByUUID', parameters)
        return result

    @AMP.Login
    def banUserID(self,ID:str):
        """Bans a User from the Server"""
        parameters = {'id': ID}
        result = self.CallAPI(f'{self.APIModule}/BanUserByID', parameters)
        return result