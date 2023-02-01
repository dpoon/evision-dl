from selenium.webdriver.common.by import By

from ..screen import Screen
from ..xpath import string_literal as xpath_string

class ApplicationScreen(Screen):
    def activate_tab(self, tab_label):
        self.click((By.XPATH, '//li[@role="tab"][@title={}]/a'.format(xpath_string(tab_label))))
