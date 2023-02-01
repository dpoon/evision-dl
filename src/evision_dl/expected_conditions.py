from collections import namedtuple
import logging

logger = logging.getLogger(__name__)

Window = namedtuple('Window', 'handle')

class window_opened(object):
    """
    An expected condition to be used with WebDriverWait(...).until(...), to
    perform an action that opens a new browser window.  This object should
    be initialized with a zero-argument callback that, when invoked, performs
    the action that would open the window.
    """
    def __init__(self, action=None):
        self.action = action
        self.orig_windows = None

    def __call__(self, driver):
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
    def __init__(self, action=None):
        self.action = action
        self.orig_windows = None

    def __call__(self, driver):
        if self.orig_windows is None:
            self.orig_windows = driver.window_handles
            if self.action:
                self.action()
        current_windows = driver.window_handles
        if len(current_windows) < len(self.orig_windows):
            return Window(current_windows.pop())
