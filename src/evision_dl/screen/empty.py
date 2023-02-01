import logging

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..screen import Screen
from .application_details import ApplicationDetailsScreen

logger = logging.getLogger(__name__)

class EmptyScreen(Screen):
    def process(self):
        self.driver.get('https://evision.as.it.ubc.ca/')
        logger.info("Waiting for user to log into eVision, bring up folder, and open the application of interest.")
        self.open_window(expectation=EC.title_is("Graduate Admissions Decision Processing"))
        logger.info("Detected application window; starting automation")
        return ApplicationDetailsScreen(self.robot)
