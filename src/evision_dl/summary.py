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
from logging.handlers import MemoryHandler
from typing import Any, List, Optional, Tuple, Union

from .applicant import Applicant, ApplicantContextChangeEvent
from .download import (
    PDFFailureEvent,
    PDFGenerationCaveatEvent,
    PDFGenerationFailureEvent,
    PDFDownloadFailureEvent,
    PDFDownloadSuccessEvent,
)
from .event import Event, EventListener
from .robot import Robot, RobotFinishingEvent

logger = logging.getLogger(__name__)

class Summarizer(EventListener):
    def __init__(self, debug_log_replay_handler: Optional[MemoryHandler] = None):
        self.debug_log_replay_handler = debug_log_replay_handler
        self.current_applicant = None
        self.successes: List[Tuple[Any, PDFDownloadSuccessEvent]] = []
        self.caveats: List[Tuple[Any, PDFGenerationCaveatEvent]] = []
        self.failures: List[Tuple[Any, PDFFailureEvent]] = []

    def handle_event(self, robot:Robot, event:Event) -> None:
        if isinstance(event, ApplicantContextChangeEvent):
            self.discard_debug_log()
            self.current_applicant = event.applicant
        elif isinstance(event, PDFGenerationCaveatEvent):
            self.caveats.append((self.current_applicant, event))
        elif isinstance(event, PDFGenerationFailureEvent):
            self.failures.append((self.current_applicant, event))
        elif isinstance(event, PDFDownloadFailureEvent):
            self.failures.append((self.current_applicant, event))
        elif isinstance(event, PDFDownloadSuccessEvent):
            self.successes.append((self.current_applicant, event))
        elif isinstance(event, RobotFinishingEvent):
            if event.exception:
                self.emit_debug_log()
                # If we are crashing with an exception while there is a current
                # applicant context that hasn't been cleared yet, we should count
                # the current applicant as a failure.
                if self.current_applicant:
                    self.failures.append((self.current_applicant, PDFFailureEvent("crashed")))
            self.output_summary()
            self.discard_debug_log(impending_shutdown=True)

    def output_summary(self) -> None:
        logger.info("Downloaded {} PDFs successfully and {} unsuccessfully".format(
            len(self.successes), len(self.failures)
        ))
        if self.caveats:
            logger.warning("Caveats:")
            for applicant, event in self.caveats:
                logger.warning("{} has {}".format(applicant, event))
        if self.failures:
            logger.error("Recap of failures:")
            for applicant, event in self.failures:
                logger.error("{}".format(applicant))

    def discard_debug_log(self, impending_shutdown: bool = False) -> None:
        if self.debug_log_replay_handler:
            blackhole = logging.NullHandler()
            orig_target = self.debug_log_replay_handler.target
            self.debug_log_replay_handler.setTarget(blackhole)
            self.debug_log_replay_handler.flush()
            self.debug_log_replay_handler.setTarget(orig_target)

            # Pessimistically log this text, which might get emitted as an
            # explanatory header of an instant replay
            if not impending_shutdown:
                logger.debug(
                    '\n' +
                    '#' * 72 + '\n' +
                    "We encountered a problem!\n"
                    "Begin instant replay of recent log messages in detail\n" +
                    'v' * 72
                )

    def emit_debug_log(self) -> None:
        if self.debug_log_replay_handler:
            logger.debug(
                '\n' +
                '^' * 72 + '\n' +
                "End instant replay of log messages\n" +
                '#' * 72
            )
            self.debug_log_replay_handler.flush()