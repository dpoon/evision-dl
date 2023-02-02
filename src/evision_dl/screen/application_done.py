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

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .application import ApplicationScreen
from .application_details import ApplicationDetailsScreen

logger = logging.getLogger(__name__)

class ApplicationDoneScreen(ApplicationScreen):
    SAVE_BUTTON = (By.XPATH, '//input[@value="Save"]')
    NEXT_APPLICANT_BUTTON = (By.XPATH, '//input[@value="Next Applicant"][not(@disabled)]')

    def process(self):
        # Ensure that we are on the right window
        WebDriverWait(self.driver, 1).until(EC.presence_of_element_located(
            self.SAVE_BUTTON
        ))

        next_buttons = self.driver.find_elements(*self.NEXT_APPLICANT_BUTTON)
        if next_buttons:
            self.click(self.NEXT_APPLICANT_BUTTON)
            self.activate_tab('Application\xa0Details')     # \xa0 = NO-BREAK SPACE
            return ApplicationDetailsScreen(self.robot)
        else:
            return None
