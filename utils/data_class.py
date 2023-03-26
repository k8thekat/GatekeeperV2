
import logging

from db import DBHandler
from amp_handler import AMPHandler
from amp_instance import AMPInstance


class Gatekeeper_Data():
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Gatekeeper_Data, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        self._logger = logging.getLogger("")
        self._DBHandler = DBHandler()
        self._DB = self._DBHandler.DB
        self._DBConfig = self._DBHandler.DBConfig

        self._AMPHandler: AMPHandler = AMPHandler()
        self._Core_AMP: AMPInstance = self._AMPHandler._Core_AMP
        self._AMP_Instances: dict[str, AMPInstance] = {}
