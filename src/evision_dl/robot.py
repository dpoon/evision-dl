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

import logging

from .event import Event, EventListener

logger = logging.getLogger(__name__)

######################################################################

class RobotFinishingEvent(Event):
    def __init__(self, exception=None):
        self.exception = exception

######################################################################

class Robot:
    def __init__(self, driver):
        self.driver = driver
        self.event_listeners = set()

    def add_event_listener(self, listener):
        self.event_listeners.add(listener)

    def post_event(self, event):
        # TODO: exception handling
        for listener in self.event_listeners:
            listener.handle_event(self, event)

    def run(self, initial_screen_class):
        try:
            screen = initial_screen_class(self)
            while screen:
                screen = screen.process()
            self.post_event(RobotFinishingEvent())
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt")
            self.post_event(RobotFinishingEvent())
            return 2
        except Exception as e:
            logger.critical("Crashed with uncaught exception", exc_info=e)
            self.post_event(RobotFinishingEvent(e))
            return 1
