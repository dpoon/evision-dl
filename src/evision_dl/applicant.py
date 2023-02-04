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
import logging
from typing import Optional

from .event import Event, EventListener
from .robot import Robot

logger = logging.getLogger(__name__)

######################################################################

class Applicant(namedtuple('Applicant', 'student_number surname preferred_name')):
    def __str__(self) -> str:
        return "Applicant {}, {} ({})".format(self.surname, self.preferred_name, self.student_number)

######################################################################

class ApplicantContextChangeEvent(Event):
    def __init__(self, applicant:Optional[Applicant]):
        self.applicant = applicant

######################################################################

class ApplicantContextChangeListener(EventListener):
    def handle_event(self, robot: Robot, event: Event) -> None:
        if isinstance(event, ApplicantContextChangeEvent):
            if event.applicant is None:
                logger.debug("Cleared applicant context")
            else:
                logger.info(event.applicant)
