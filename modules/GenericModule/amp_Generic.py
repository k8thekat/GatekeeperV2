#
import modules.AMP as AMP


class AMPGeneric(AMP.AMPInstance):
    def __init__(self, instanceID = 0, serverdata = {},Index = 0):
        super().__init__(self,instanceID,serverdata,Index,default_console= True)



class AMPGenericConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPGeneric):
        super().__init__(AMPInstance)