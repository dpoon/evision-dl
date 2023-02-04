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

from __future__ import annotations
import logging
from typing import Any, Dict, Callable, Optional, TYPE_CHECKING

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from .. import expected_conditions as EVEC
if TYPE_CHECKING:
    from ..robot import Robot

logger = logging.getLogger(__name__)

######################################################################

# Abstract class
class Screen:
    def __init__(self, robot: 'Robot'):
        self.robot = robot

    @property
    def driver(self) -> WebDriver:
        return self.robot.driver

    def process(self) -> None:
        logger.critical("{}.process() is unimplemented".format(self))
        raise NotImplementedError

    def open_window(self, action: Callable[[], Any] = lambda: None, expectation: Callable[[WebDriver], bool] = lambda d: True, timeout: float=float('inf')) -> str:
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

    def click(self, locator, timeout: float = 30) -> None:
        logger.debug("Clicking {}".format(locator))
        last_exception = None
        for _ in range(90):
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                ).click()
            except ElementClickInterceptedException as e:
                last_exception = e
                if self._dismiss_modal_overlay():
                    logger.debug("Dismissed obscuring overlay; retrying click {}".format(locator))
                else:
                    logger.error("Unable to dismiss obscuring overlay; failing to click {}".format(locator))
                    raise
        else:
            logger.error("Giving up on dismissing any modal overlay")
            assert last_exception is not None
            raise last_exception

    def _dismiss_modal_overlay(self) -> bool:
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

######################################################################

class ModalOverlay:
    @classmethod
    def find_on_screen(cls, screen: Screen) -> Optional[ModalOverlay]:
        try:
            title_el = screen.driver.find_element(By.CSS_SELECTOR, 'div.ui-dialog .ui-dialog-title')
            content = screen.driver.find_element(By.CSS_SELECTOR, 'div.ui-dialog .ui-dialog-content').text
            buttons = screen.driver.find_elements(By.CSS_SELECTOR, 'div.ui-dialog .ui-dialog-buttonset > button')
            button_map = {b.text: b for b in buttons}
            return cls(screen, title_el, title_el.text, content, button_map)
        except (NoSuchElementException, StaleElementReferenceException):
            # Overlay disappeared already
            return None

    def __init__(self, screen: Screen, title_element: WebElement, title: str, content: str, buttons: Dict[str, WebElement] = {}):
        self.screen = screen
        self._title_element = title_element
        self.title = title
        self.content = content
        self.buttons = buttons

    def __str__(self) -> str:
        return "Modal overlay with title \"{}\", content \"{}\", buttons {}".format(
            self.title,
            self.content,
            list(self.buttons.keys())
        )

    def wait_for_disappearance(self, timeout: float = 3600) -> bool:
        return WebDriverWait(self.screen.driver, timeout).until(EC.staleness_of(self._title_element))

    def click_button(self, text: str) -> None:
        try:
            self.buttons[text].click()
        except StaleElementReferenceException:
            # Usually, our goal is to get rid of the overlay, so if the button
            # has disappeared already, that's probably fine.
            pass
