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

from .. import expected_conditions as EVEC
from ..download import (
    PDFGenerationCaveatEvent,
    PDFGenerationFailureEvent,
    PDFGenerationSuccessEvent,
)
from .request_pdf import RequestPDFScreen

logger = logging.getLogger(__name__)

class RequestPDFTroubleshootingScreen(RequestPDFScreen):

    def process(self):
        self.wait_for_dom()

        self.docs = self._parse_doc_list()
        logger.debug("Documents available: {}".format(list(self.docs.values())))

        problematic_doc_ids = self.detect_problematic_docs()
        problematic_doc_names = [self.docs[d] for d in problematic_doc_ids]
        logger.warning("Problematic documents: {}".format(problematic_doc_names))
        self.robot.post_event(PDFGenerationCaveatEvent(problematic_doc_names))

        for doc_id in problematic_doc_ids:
            self.deselect_doc_by_id(doc_id)

        # Pretty sure it should work now, though errors are not 100% deterministic
        pdf_generation_event = self.try_generate_pdf() or \
            PDFGenerationFailureEvent("The attempt to isolate problematic documents didn't work")
        self.robot.post_event(pdf_generation_event)

        application_window = WebDriverWait(self.driver, 10).until(
            EVEC.window_closed(lambda: self.click(self.EXIT_BUTTON))
        )
        self.driver.switch_to.window(application_window.handle)
        from .application_done import ApplicationDoneScreen
        return ApplicationDoneScreen(self.robot)

    def detect_problematic_docs(self):
        return [
            doc_id for doc_id in self.docs
            if self.detect_problematic_doc(doc_id)
        ]

    def detect_problematic_doc(self, doc_id):
        # Deselect all docs except the one we are testing
        for doc in self.docs:
            if doc != doc_id:
                self.deselect_doc_by_id(doc)
        pdf_generation_event = self.try_generate_pdf()
        if isinstance(pdf_generation_event, PDFGenerationSuccessEvent):
            logger.debug("Document {} is OK".format(doc_id))
            return False
        else:
            logger.debug("Document {} is not OK".format(doc_id))
            return True

    def try_generate_pdf(self):
        pdf_generation_event = super().try_generate_pdf()

        # Got our result.  Close the result window and reopen it.
        application_window = WebDriverWait(self.driver, 10).until(
            EVEC.window_closed(lambda: self.click(self.EXIT_BUTTON))
        )
        self.driver.switch_to.window(application_window.handle)
        logger.debug("Switched back to window with title \"{}\"".format(self.driver.title))

        self.open_window(
            action=lambda: self.click(self.MANAGE_PDF_BUTTON),
            expectation=EC.title_is("Manage Applicant PDF"),
            timeout=90
        )

        self.wait_for_dom()

        # Ensure that the document list hasn't changed
        docs = self._parse_doc_list()
        if docs != self.docs:
            logger.warning("Documents available changed to: {}".format(docs))

        return pdf_generation_event

    def deselect_doc_by_id(self, doc_id):
        self.driver.find_element(By.XPATH, self._doc_checkbox_list_xpath(doc_id)).click()

    def _parse_doc_list(self):
        labels = self.driver.find_elements(By.XPATH, self._doc_checkbox_list_xpath())
        descriptions = [label.text.strip() for label in labels]
        ids = [
            checkbox.get_attribute('name') + '"' + checkbox.get_attribute('value')
            for checkbox in self.driver.find_elements(By.XPATH, self._doc_checkbox_list_xpath() + '/input')
        ]
        return dict(zip(ids, descriptions))
