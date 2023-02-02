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

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..screen import Screen
from .application_details import ApplicationDetailsScreen

logger = logging.getLogger(__name__)

class StartScreen(Screen):
    def process(self):
        self.driver.get('https://evision.as.it.ubc.ca/')
        logger.info("Waiting for user to log into eVision, bring up folder, and open the application of interest.")
        self.open_window(expectation=EC.title_is("Graduate Admissions Decision Processing"))
        logger.info("Detected application window; starting automation")
        return ApplicationDetailsScreen(self.robot)
