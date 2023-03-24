from __future__ import annotations
from DB import DBBanner


class Edited_DB_Banner(DBBanner):
    """DB_Banner for Banner Editor

    All `attrs` inside this class must have a `_` before them"""

    def __init__(self, db_banner: DBBanner):
        self._db_banner: DBBanner = db_banner
        super().__init__(DB=db_banner._db, ServerID=db_banner.ServerID)  # type:ignore (These `attrs` are set via a list.)

        self._invalid_keys: list[str] = ['_db', 'ServerID', 'background_path']
        self.reset_db()

    def save_db(self):
        for key in self._db_banner._attr_list:
            if key in self._invalid_keys:
                continue

            if getattr(self._db_banner, key) != getattr(self, key):
                setattr(self._db_banner, key, getattr(self, key))

        return self._db_banner

    def reset_db(self):
        for key in self._db_banner._attr_list:
            if key in self._invalid_keys:
                continue
            setattr(self, key, getattr(self._db_banner, key))
        return self._db_banner
