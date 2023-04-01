from __future__ import annotations

from discord.ext.commands import Cog

import os
import logging

# from amp_handler import AMPHandler
# from amp import AMPInstance
# import db
from DB import DBHandler, Database, DBConfig
from Gatekeeper import Gatekeeper

#from utils.helper.command import Helper_Command


class Gatekeeper_Cog(Cog):
    _name: str = os.path.basename(__file__).title()
    # All our DB Related classes
    _DBHandler: DBHandler = DBHandler()
    _DB: Database = _DBHandler._DB
    _DBConfig: DBConfig = _DBHandler._DBConfig

    def __init__(self, client: Gatekeeper) -> None:
        # Core peices to be used.
        self._client: Gatekeeper = client
        self._logger = logging.getLogger()  # Point all print/logging statments here!

        # All our AMP Related class's
        # self._AMPHandler: AMPHandler = AMPHandler()
        # self._AMP: AMPInstance = self._AMPHandler.AMP  # Main AMP object
        # self.AMPInstances: dict[str, str] = self.AMPHandler.AMP_Instances #Main AMP Instance Dictionary

        # Any Helper classes here.
        #self._command_helper: Helper_Command = Helper_Command(self._client)
        self._logger.info(f'**SUCCESS** Initializing Cog**{self._name}**')
