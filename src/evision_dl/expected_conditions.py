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

from collections import namedtuple
from typing import Any, Callable, Optional
import logging

from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

Window = namedtuple('Window', 'handle')

class window_opened(object):
    """
    An expected condition to be used with WebDriverWait(...).until(...), to
    perform an action that opens a new browser window.  This object should
    be initialized with a zero-argument callback that, when invoked, performs
    the action that would open the window.
    """
    def __init__(self, action: Optional[Callable[[], Any]] = None):
        self.action = action
        self.orig_windows = None

    def __call__(self, driver: WebDriver) -> Optional[Window]:
        if self.orig_windows is None:
            self.orig_windows = set(driver.window_handles)
            if self.action:
                self.action()
        new_windows = set(driver.window_handles) - self.orig_windows
        if new_windows:
            return Window(new_windows.pop())

class window_closed(object):
    """
    An expected condition to be used with WebDriverWait(...).until(...), to
    perform an action that closes a new browser window.  This object should
    be initialized with a zero-argument callback that, when invoked, performs
    the action that would close a window.
    """
    def __init__(self, action: Optional[Callable[[], Any]] = None):
        self.action = action
        self.orig_windows = None

    def __call__(self, driver: WebDriver) -> Optional[Window]:
        if self.orig_windows is None:
            self.orig_windows = driver.window_handles
            if self.action:
                self.action()
        current_windows = driver.window_handles
        if len(current_windows) < len(self.orig_windows):
            return Window(current_windows.pop())
