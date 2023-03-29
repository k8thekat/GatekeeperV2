import aiofiles
import os
import re
from PIL import Image
import io

from discord import File, Interaction
from discord.app_commands import Choice


async def count_lines(path: str, filetype: str = ".py", skip_venv: bool = True) -> int:
    lines: int = 0
    for i in os.scandir(path):
        if i.is_file():
            if i.path.endswith(filetype):
                if skip_venv and re.search(r"(\\|/)?venv(\\|/)", i.path):
                    continue
                lines += len((await (await aiofiles.open(i.path, "r")).read()).split("\n"))
        elif i.is_dir():
            lines += await count_lines(i.path, filetype)
    return lines


async def count_others(path: str, filetype: str = ".py", file_contains: str = "def", skip_venv: bool = True) -> int:
    line_count: int = 0
    for i in os.scandir(path):
        if i.is_file():
            if i.path.endswith(filetype):
                if skip_venv and re.search(r"(\\|/)?venv(\\|/)", i.path):
                    continue
                line_count += len(
                    [line for line in (await (await aiofiles.open(i.path, "r")).read()).split("\n") if file_contains in line]
                )
        elif i.is_dir():
            line_count += await count_others(i.path, filetype, file_contains)
    return line_count
