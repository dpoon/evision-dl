# Copyright 2003 Dara Poon and the University of British Columbia

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

from .. import expected_conditions as EVEC
from .application import ApplicationScreen
from .request_pdf import RequestPDFScreen

logger = logging.getLogger(__name__)

class GPOScreen(ApplicationScreen):

    MANAGE_PDF_BUTTON = (By.XPATH, '//input[@type="button"][@value="Manage Applicant PDF"]')

    def process(self):
        self.activate_tab("Application\xa0Utilities")  # \xa0 = NO-BREAK SPACE
        self.open_window(
            action=lambda: self.click(self.MANAGE_PDF_BUTTON),
            expectation=EC.title_is("Manage Applicant PDF"),
            timeout=90
        )
        return RequestPDFScreen(self.robot)
