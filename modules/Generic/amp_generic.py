#
import AMP as AMP
import os

DisplayImageSources = ['Generic']
class AMPGeneric(AMP.AMPInstance):
    def __init__(self, instanceID = 0, serverdata = {},Index = 0,Handler=None):
        super().__init__(instanceID,serverdata,Index,Handler=Handler)
        
        self.Console = AMPGenericConsole(AMPInstance = self)

        print(os.path.basename(__file__),self.Running, 'instanceID',self.InstanceID)


class AMPGenericConsole(AMP.AMPConsole):
    def __init__(self, AMPInstance = AMPGeneric):
        super().__init__(AMPInstance)