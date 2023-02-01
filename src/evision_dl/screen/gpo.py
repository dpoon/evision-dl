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
