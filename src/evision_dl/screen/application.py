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

from retry import retry
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from ..screen import Screen
from ..xpath import string_literal as xpath_string

class ApplicationScreen(Screen):
    @retry(TimeoutException)
    def activate_tab(self, tab_label:str):
        li_xpath = '//li[@role="tab"][@title={}]'.format(xpath_string(tab_label))
        self.click((By.XPATH, li_xpath + '/a'))
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, li_xpath + '[@aria-selected="true"]'))
        )
