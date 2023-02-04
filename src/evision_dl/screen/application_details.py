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
import re

from retry import retry
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from ..applicant import Applicant
from ..download import ApplicantContextChangeEvent
from ..xpath import string_literal as xpath_string
from . import Screen
from .application import ApplicationScreen
from .gpo import GPOScreen

logger = logging.getLogger(__name__)

class ApplicationDetailsScreen(ApplicationScreen):
    def process(self) -> Screen:
        self.activate_tab("Personal\xa0Details")  # \xa0 = NO-BREAK SPACE
        applicant = self.extract_applicant_context()
        self.robot.post_event(ApplicantContextChangeEvent(applicant))
        self.activate_tab("GPO")
        return GPOScreen(self.robot)

    @retry(StaleElementReferenceException)
    def extract_applicant_context(self) -> Applicant:
        h3_text = self.driver.find_element(By.TAG_NAME, 'h3').text
        student_number = re.findall(r"Student No: (\d{8})", h3_text)[0]
        surname = self._extract_table_text("Family Name(Surname):")
        preferred_name = self._extract_table_text("Preferred Name:") or \
            self._extract_table_text("Given Name:")
        return Applicant(student_number, surname, preferred_name)

    def _extract_table_text(self, label:str) -> str:
        td = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//td[strong[text()={}]]'.format(xpath_string(label))))
        )
        return td.text.replace(label, '', 1).strip()
