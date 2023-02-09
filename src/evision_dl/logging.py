# Copyright 2003 Dara Poon and the University of British Columbia
#
# This file is part of evision-dl.
#
# evision-dl is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# evision-dl is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# evision-dl. If not, see <https://www.gnu.org/licenses/>.

from logging import (
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
    Formatter,
    LogRecord,
)
from typing import Sequence, Tuple

import colorama

DEFAULT_LEVEL_COLORS = (
    (DEBUG, ''),
    (INFO, colorama.Fore.WHITE),
    (WARNING, colorama.Fore.YELLOW),
    (ERROR, colorama.Fore.RED),
    (CRITICAL, colorama.Fore.LIGHTRED_EX),
)

DEFAULT_FMT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)'

class ColorFormatter(Formatter):
    def __init__(self, fmt: str = DEFAULT_FMT, level_colors: Sequence[Tuple[int, str]] = DEFAULT_LEVEL_COLORS, **kwargs):
        self._formats = [
            (level, Formatter(color + fmt + colorama.Style.RESET_ALL, **kwargs))
            for level, color in sorted(level_colors)
        ]

    def format(self, record: LogRecord) -> str:
        formatter = next(
            formatter for levelno, formatter in self._formats
            if levelno >= record.levelno
        )
        return formatter.format(record)
