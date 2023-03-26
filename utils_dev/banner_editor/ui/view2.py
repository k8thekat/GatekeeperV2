from __future__ import annotations
from discord.ui import View
from typing import Optional

from utils_dev.banner_editor.edited_banner import Edited_DB_Banner
from utils_dev.banner_editor.ui.select import Copy_To_Select


class Copy_To_View(View):
    def __init__(self, *, timeout: Optional[float] = None, select_options: dict[str, str], edited_banner: Edited_DB_Banner):
        super().__init__(timeout=timeout)
        self._edited_banner: Edited_DB_Banner = edited_banner
        self.add_item(Copy_To_Select(options=select_options, edited_banner=self._edited_banner))
