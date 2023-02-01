import logging
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..applicant_context import ApplicantContext
from ..xpath import string_literal as xpath_string
from .application import ApplicationScreen
from .gpo import GPOScreen

logger = logging.getLogger(__name__)

class ApplicationDetailsScreen(ApplicationScreen):
    def process(self):
        applicant = self.extract_applicant_context()
        self.robot.handle_switch_to_applicant(applicant)
        self.activate_tab("GPO")
        return GPOScreen(self.robot)

    def extract_applicant_context(self):
        self.activate_tab("Personal\xa0Details")  # \xa0 = NO-BREAK SPACE
        h3_text = self.driver.find_element(By.TAG_NAME, 'h3').text
        student_number = re.findall(r"Student No: (\d{8})", h3_text)[0]
        surname = self._extract_table_text("Family Name(Surname):")
        preferred_name = self._extract_table_text("Preferred Name:") or \
            self._extract_table_text("Given Name:")
        return ApplicantContext(student_number, surname, preferred_name)

    def _extract_table_text(self, label):
        td = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//td[strong[text()={}]]'.format(xpath_string(label))))
        )
        return td.text.replace(label, '', 1).strip()
