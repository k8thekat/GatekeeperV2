from __future__ import annotations
from typing import Optional

from discord import View

from utils.banner_editor.ui.select import Copy_To_Select
from utils.banner_editor.edited_banner import Edited_DB_Banner


class Copy_To_View(View):
    def __init__(self, *, timeout: Optional[float] = None, select_options: dict[str, str], edited_banner: Edited_DB_Banner):
        super().__init__(timeout=timeout)
        self._edited_banner: Edited_DB_Banner = edited_banner
        self.add_item(Copy_To_Select(options=select_options, edited_banner=self._edited_banner))
