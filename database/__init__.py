'''
   Copyright (C) 2021-2022 Katelynn Cadwallader.

   This file is part of Gatekeeper, the AMP Minecraft Discord Bot.

   Gatekeeper is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3, or (at your option)
   any later version.

   Gatekeeper is distributed in the hope that it will be useful, but WITHOUT
   ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
   or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
   License for more details.

   You should have received a copy of the GNU General Public License
   along with Gatekeeper; see the file COPYING.  If not, write to the Free
   Software Foundation, 51 Franklin Street - Fifth Floor, Boston, MA
   02110-1301, USA. 
'''
from __future__ import annotations

__title__ = "Gatekeeper Database"
__author__ = "k8thekat"
__license__ = "GNU"
__version__ = "0.0.1a"
__credits__ = "Discord.py and AMP by CubeCoders"

from typing import Literal, NamedTuple


class VersionInfo(NamedTuple):
    Major: int
    Minor: int
    Revision: int
    releaseLevel: Literal["alpha", "beta", "release"]


version_info: VersionInfo = VersionInfo(Major=1, Minor=0, Revision=1, releaseLevel="alpha")

del NamedTuple, Literal, VersionInfo