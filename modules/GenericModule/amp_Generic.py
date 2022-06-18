#
import modules.AMP as AMP


class AMPGeneric(AMP.AMPInstance):
    def __init__(self, instanceID = 0, serverdata = {},Index = 0,Handler=None):
        #!TODO!
        super().__init__(instanceID,serverdata,Index,Handler=Handler)



class AMPGenericConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPGeneric):
        super().__init__(AMPInstance)