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
