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

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .. import expected_conditions as EVEC

logger = logging.getLogger(__name__)

class ModalOverlay:
    @classmethod
    def find_on_screen(cls, screen_context):
        try:
            title_el = screen_context.driver.find_element(By.CSS_SELECTOR, 'div.ui-dialog .ui-dialog-title')
            content = screen_context.driver.find_element(By.CSS_SELECTOR, 'div.ui-dialog .ui-dialog-content').text
            buttons = screen_context.driver.find_elements(By.CSS_SELECTOR, 'div.ui-dialog .ui-dialog-buttonset > button')
            button_map = {b.text: b for b in buttons}
            return cls(screen_context, title_el, title_el.text, content, button_map)
        except (NoSuchElementException, StaleElementReferenceException):
            # Overlay disappeared already
            return None

    def __init__(self, screen_context, title_element, title, content, buttons={}):
        self.screen_context = screen_context
        self._title_element = title_element
        self.title = title
        self.content = content
        self.buttons = buttons

    def __str__(self):
        return "Modal overlay with title \"{}\", content \"{}\", buttons {}".format(
            self.title,
            self.content,
            list(self.buttons.keys())
        )

    def wait_for_disappearance(self, timeout=3600):
        return WebDriverWait(self.screen_context.driver, timeout).until(EC.staleness_of(self._title_element))

    def click_button(self, text):
        try:
            self.buttons[text].click()
        except StaleElementReferenceException:
            # Usually, our goal is to get rid of the overlay, so if the button
            # has disappeared already, that's probably fine.
            pass

######################################################################

# Abstract class
class Screen:
    def __init__(self, robot):
        self.robot = robot

    @property
    def driver(self):
        return self.robot.driver

    def process(self):
        logger.critical("{}.process() is unimplemented".format(self))
        raise NotImplementedError

    def open_window(self, action=None, expectation=lambda d: True, timeout=float('inf')):
        # Note: the timeout clock resets every time a wrong window opens
        conditions = [expectation, EVEC.window_opened(action)]
        while True:
            event = WebDriverWait(self.driver, timeout).until(EC.any_of(*conditions))
            if isinstance(event, EVEC.Window):
                conditions.pop()    # Don't try to open the window again
                self.driver.switch_to.window(event.handle)
            else:
                # expectation met
                return self.driver.current_window_handle

    def click(self, expectation, timeout=30):
        logger.debug("Clicking {}".format(expectation))
        for _ in range(90):
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(expectation)
                ).click()
            except ElementClickInterceptedException as e:
                last_exception = e
                if self._dismiss_modal_overlay():
                    logger.debug("Dismissed obscuring overlay; retrying click {}".format(expectation))
                else:
                    logger.error("Unable to dismiss obscuring overlay; failing to click {}".format(expectation))
                    raise
        else:
            logger.error("Giving up on dismissing any modal overlay")
            raise last_exception

    def _dismiss_modal_overlay(self):
        overlay = ModalOverlay.find_on_screen(self)
        if not overlay:
            logger.debug("Either some unknown element is obscuring the click target, or the overlay disappeared on its own just now.  Blindly retrying click...")
            return True
        elif overlay.title in ("Processing", "Loading"):
            logger.debug("Waiting for {} to disappear".format(overlay))
            return overlay.wait_for_disappearance()
        elif overlay.title == "Refresh?" and "No" in overlay.buttons:
            # Content: "This tab cannot automatically refresh after adding a new request. Would you like to refresh now?"
            overlay.click_button("No")
            return overlay.wait_for_disappearance()
        else:
            logger.error("Don't know how to handle {}".format(overlay))
            return False
