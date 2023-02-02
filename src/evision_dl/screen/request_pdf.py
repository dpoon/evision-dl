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
from .application import Screen

logger = logging.getLogger(__name__)

class RequestPDFScreen(Screen):

    CONTINUE_BUTTON = (By.XPATH, '//input[@value="CONTINUE"]')
    BACK_BUTTON = (By.XPATH, '//input[@value="BACK"]')
    EXIT_BUTTON = (By.XPATH, '//input[@type="button"][@value="EXIT"]')

    def process(self):
        # This page initially contains HTML like:
        #
        # <div><div id="pdf_doc_list">
        #   <label class="pdf-check">
        #     <input type="checkbox" onclick="$('#pdf_doc_list').find('input:checkbox').prop('checked', this.checked);" checked="checked">Select all documents
        #   </label>
        #   <select name="ANSWER.TTQ.MENSYS.4" id="ANSWER.TTQ.MENSYS.4" multiple="multiple" class="sv-form-control">
        #     <option value="93AF">Reference Letter (john doe.pdf, 21/Dec/2022)</option>
        #     <option value="MHD:00953">Transcripts & Diplomas  - Unofficial  (tscript.pdf, 21/Dec/2022)</option>
        #   </select>
        #   <input type="hidden" name="DUM_FIXT.TTQ.MENSYS.4">
        # </div></div><br>
        # </div></div>
        # <div><div>
        #   <input type="button" class="btn" value="EXIT" onclick="self.close()">
        #   <input type="submit" name="ANSWER.TTQ.MENSYS.5" id="ANSWER.TTQ.MENSYS.5." value="CONTINUE" class="btn">
        # </div></div>
        # 
        # ... and then the <select> element is manipulated to have
        # style="display: none;", and checkboxes like
        #
        # <label class="pdf-check">
        #   <input type="checkbox" name="ANSWER.TTQ.MENSYS.4" value="93AF" checked="checked">
        #   Reference Letter (john doe.pdf, 21/Dec/2022
        # </label>
        #
        # are appended after the DUM_FIXT.TTQ.MENSYS.4 element.
        #
        # Therefore, we must wait until that DOM manipulation finishes.
        WebDriverWait(self.driver, 90).until(
            EC.all_of(
                EC.presence_of_element_located((By.XPATH, '//input[@value="CONTINUE"]')),
                EC.none_of(
                    EC.visibility_of_any_elements_located(
                        (By.CSS_SELECTOR, '#sitspagecontent select.sv-form-control[multiple]'),
                    ),
                ),
                EC.presence_of_element_located((By.XPATH,
                    '//label[@class="pdf-check"]'
                        '/following-sibling::select[@class="sv-form-control"][@multiple]'
                        '/following-sibling::label[@class="pdf-check"]'
                )),
            )
        )

        # These documents tend to be encrypted, such that including them would
        # cause PDF concatenation to fail.
        self.deselect_unwanted_docs("Language Proficiency", "GRE")

        self.click(self.CONTINUE_BUTTON)

        # Wait for the "Select order of Document Types" page to render, as
        # evidenced by the presence of a "BACK" button
        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located(
            self.BACK_BUTTON
        ))

        # ... but actually click on the "CONTINUE" button
        self.click(self.CONTINUE_BUTTON)

        self.extract_pdf()

        new_top_window = WebDriverWait(self.driver, 10).until(
            EVEC.window_closed(lambda: self.click(self.EXIT_BUTTON))
        )
        self.driver.switch_to.window(new_top_window.handle)
        logger.debug("Switched back to window with title \"{}\"".format(self.driver.title))
        from .application_done import ApplicationDoneScreen
        return ApplicationDoneScreen(self.robot)

    def deselect_unwanted_docs(self, *partial_label_texts):
        for label in self.driver.find_elements(By.XPATH, '//label'):
            if any(bad in label.text for bad in partial_label_texts):
                label.click()

    def extract_pdf(self):
        # eVision bug (INC1040643): PDF merge may fail, in which case you'll see
        # "Please to download a copy of the document" instead of "Please
        # _click_here_ to download a copy of the document".
        #
        # It could also output instead:
        #
        # <div class="span12">
        #   <font color="red">Error:</font>
        #   There has been a processing error. Please try again or contact IT
        #   support for assistance and quote the following details:
        #   <br>
        #   Error ID: -3013
        #   <br>
        #   Application ID: 66378380|01|01.
        # </div>
        WebDriverWait(self.driver, 120).until(
            EC.any_of(
                EC.presence_of_element_located((By.LINK_TEXT, "click here")),
                EC.presence_of_element_located((By.XPATH, '//*[font[@color="red"]]')),
                EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#sitspagecontent div'), "Please to download a copy of the document"),
            )
        )
        if err := '\n'.join(e.text for e in self.driver.find_elements(By.XPATH, '//*[font[@color="red"]]')):
            self.robot.handle_unavailable_pdf(err)
        elif links := self.driver.find_elements(By.LINK_TEXT, "click here"):
            self.robot.handle_available_pdf(links[0].get_attribute('href'))
        else:
            self.robot.handle_unavailable_pdf()
