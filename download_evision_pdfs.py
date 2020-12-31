#! C:\Users\kcheung\Desktop\eVision\Scripts\python

######################################################################
# To install the necessary prerequisites:
#
# Download geckodriver-*-macos.tar.gz from
# https://github.com/mozilla/geckodriver/releases and unpack geckodriver into
# the ~/bin directory (or elsewhere in your PATH).
#
# easy_install --user selenium
######################################################################

"""
Launch a Firefox browser to download PDFs from eVision.
"""

from __future__ import print_function
import argparse
import os
import re
import sys
from multiprocessing import Pool
from time import sleep
try:
    # Python 2
    from urllib2 import build_opener
    from urlparse import urlparse
except:
    # Python 3
    from urllib.request import build_opener
    from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import \
    ElementClickInterceptedException, \
    ElementNotInteractableException, \
    NoSuchElementException, \
    StaleElementReferenceException, \
    TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
# Path to the Firefox driver (geckodriver)
os.environ['PATH'] = os.path.join(os.path.expanduser('~'), 'bin') + os.pathsep + os.environ['PATH']

def download(dest_file, url, headers=[]):
    if not os.path.isdir(os.path.dirname(dest_file)):
        os.makedirs(os.path.dirname(dest_file))
    with open(dest_file, 'wb') as f:
        if not url:
            print(u'Nothing to download to {1}!'.format(url, dest_file))
            return
        print(u'Downloading {0} to {1}...'.format(url, dest_file), end=None)
        opener = build_opener()
        opener.addheaders = headers
        res = opener.open(url)  # Python 3 can do with opener.open(url) as res:
        try:
            f.write(res.read())
            print(u' Done.')
        finally:
            res.close()
def click(driver, *expectation):
    while True:
        try:
            return WebDriverWait(driver, 90).until(
                EC.presence_of_element_located(expectation)
            ).click()
        except ElementClickInterceptedException:
            # Element is obscured, perhaps by an overlay
            try:
                # "Refresh? Yes/No" overlay: click "No".
                WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[contains(concat(" ", normalize-space(@class), " "), " ui-dialog ")][//span[text()="Refresh?"]]//button[text()="No"]')
                    )
                ).click()
            except TimeoutException:
                # Another overlay, perhaps "Loading, please wait..."
                #print("Retrying click...")
                pass

def click_button_open_window(driver, button):
    """
    Click a button that opens a new browser window, returning a handle to
    the newly opened window.
    """
    while True:
        try:
            return WebDriverWait(driver, 10).until(window_opened(
                lambda: button.click()
            ))
        except (TimeoutException, ElementClickInterceptedException) as e:
            # Click may have failed if the button was outside the viewport,
            # or if another UI element such as a scrollbar had obscured it.
            # Try to scroll the button into a better position.
            try:
                button.send_keys('\n', Keys.DOWN)
            except ElementNotInteractableException:
                pass
        except (ElementNotInteractableException) as e:
            #print(e)
            pass

class window_opened(object):
    """
    An expected condition to be used with WebDriverWait(...).until(...), to
    perform an action that opens a new browser window.  This object should
    be initialized with a zero-argument callback that, when invoked, performs
    the action that would open the window.
    """
    def __init__(self, action=None):
        self.action = action
        self.orig_windows = None

    def __call__(self, driver):
        if self.orig_windows is None:
            self.orig_windows = set(driver.window_handles)
            if self.action:
                self.action()
        new_windows = set(driver.window_handles) - self.orig_windows
        if new_windows:
            return new_windows.pop()

def save(driver, dest_file, url=None, mp_pool=None):
    """
    Save the URL (or the URL of the current browser window) to the given
    destination file.  if a multiprocessing pool is specified, the downloading
    will be backgrounded.
    """
    cookie_string = '; '.join(
        '{0}={1}'.format(cookie['name'], cookie['value'])
        for cookie in driver.get_cookies()
    )
    download_args = (
        dest_file,
        url if url is not None else driver.current_url,
        [('Cookie', cookie_string)],
    )
    if mp_pool:
        mp_pool.apply_async(download, download_args)
    else:
        download(*download_args)

def navigate_to_first_app(driver):
    """
    Direct the user to log in to eVision and open the folder listing the 
    applicants of interest.  Return the window that contains the applicant table.
    """
    driver.get('https://evision.as.it.ubc.ca/')
    print("Please log in to eVision, then bring up evaluation folder and open the first application of interest.")
    while True:
        app_window = WebDriverWait(driver, float('inf')).until(window_opened())
        driver.switch_to.window(app_window)
        try:
            click(driver, By.LINK_TEXT, "GPO")
            return app_window
        except TimeoutException:
            pass        # This wasn't the window we were looking for?


def request_pdf(driver):
    app_window = driver.current_window_handle
    while True:
        try:
            click(driver, By.LINK_TEXT, "GPO")
            # Want "Application Utilities" link, but By.LINK_TEXT fails when
            # there is a space
            click(driver, By.PARTIAL_LINK_TEXT, "Utilities")
            pdf_button = WebDriverWait(driver, 90).until(EC.presence_of_element_located(
                (By.XPATH, '//input[@type="button"][@value="Manage Applicant PDF"]')
            ))
            pdf_window = click_button_open_window(driver, pdf_button)
            for _ in range(5):
                for button in driver.find_elements(By.XPATH, '//button'):
                    if button.text == "No":
                        button.click()
                        break
            driver.switch_to.window(pdf_window)
            break
        except StaleElementReferenceException:
            pass
    continue_button = WebDriverWait(driver, 90).until(EC.presence_of_element_located(
        (By.XPATH, '//input[@value="CONTINUE"]')
    ))
    for label in driver.find_elements(By.XPATH, '//label'):
        if any(bad in label.text for bad in ["Language Proficiency", "GRE"]):
            label.click()
    continue_button.click()
    WebDriverWait(driver, 120).until(EC.presence_of_element_located(
        (By.XPATH, '//input[@value="BACK"]')
    ))
    driver.find_element(By.XPATH, '//input[@type="submit"][@value="CONTINUE"]').click()
    # eVision bug (INC1040643): PDF merge may fail, in which case you'll see
    # "Please to download a copy of the document" instead of "Please
    # _click_here_ to download a copy of the document".
    for _ in range(120):
        try:
            if any("Please to download" in div.text or
                   "There has been a processing error" in div.text
                   for div in driver.find_elements(By.TAG_NAME, 'div')):
                pdf_url = None
                break
            pdf_url = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.LINK_TEXT, "click here")
            )).get_attribute('href')
            break
        except (StaleElementReferenceException, TimeoutException):
            pass        # Try again
    click(driver, By.XPATH, '//input[@value="EXIT"]')
    driver.switch_to.window(app_window)
    return pdf_url


def extract_app_identity(driver):
    def extract_table_text(label):
        # TODO: XPATH-escape the label
        td = driver.find_element(By.XPATH, '//td[strong[text()="' + label + '"]]')
        return td.text.replace(label, '', 1).strip()
    # Want "Application Details" link, but By.LINK_TEXT fails when there is a space
    click(driver, By.PARTIAL_LINK_TEXT, "Details")
    # Want "Personal Details" link, but By.LINK_TEXT fails when there is a space
    click(driver, By.PARTIAL_LINK_TEXT, "Personal")
    click(driver, By.XPATH, '//h4[text()="Applicant Personal Details"]')
    surname = extract_table_text("Family Name(Surname):")
    preferred_name = extract_table_text("Preferred Name:") or extract_table_text("Given Name:")
    h3_text = driver.find_element(By.TAG_NAME, 'h3').text
    student_number = re.findall(r"Student No: (\d{8})", h3_text)[0]
    return surname, preferred_name, student_number

def process_apps(driver, dest_dir):
    while True:
        try:
            surname, preferred_name, student_number = extract_app_identity(driver)
        except TimeoutException:
            # Who knows what went wrong!  Try clicking "Previous Applicant", then
            # "Next Applicant" and hopefully we'll get another chance.
            print("Web application did not behave as expected.  Clicking "
                """"Previous Applicant", then "Next Applicant" to try again.""")
            click(driver, By.PARTIAL_LINK_TEXT, "Previous")
            click(driver, By.PARTIAL_LINK_TEXT, "Next")
            continue
        dest_file = os.path.join(
            dest_dir, u'{0}, {1} ({2}).pdf'.format(
                ' ' + surname if surname.startswith('.') else surname,
                preferred_name,
                student_number
            )
        )
        pdf_url = request_pdf(driver)
        yield pdf_url, dest_file

        next_buttons = driver.find_elements(
            By.XPATH, '//input[@value="Next Applicant"][not(@disabled)]'
        )
        if not next_buttons:
            break
        next_buttons[0].click()


def parse_args(args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dest_dir',
        help='Directory to which PDFs should be saved')
    parser.add_argument('--webdriver-log', metavar='PATH', default=os.devnull,
        help='Webdriver log file (such as geckodriver.log)')
    args = parser.parse_args(args)
    if not os.path.isdir(args.dest_dir):
        print("Directory '{0}' does not exist".format(args.dest_dir), file=sys.stderr)
        return None
    return {
        'dest_dir': args.dest_dir,
        'webdriver_log': args.webdriver_log,
    }


def main(*argv):
    args = parse_args(argv or sys.argv[1:])
    if args is None:
        return 1

    download_pool = None #Pool(2)
    driver = webdriver.Firefox(service_log_path=args.pop('webdriver_log'))
    try:
        navigate_to_first_app(driver)
        for pdf_url, dest_file in process_apps(driver, args['dest_dir']):
            save(driver, dest_file, pdf_url or '', download_pool)
    except KeyboardInterrupt:
        pass
    print('Finishing downloads...')
    if download_pool is not None:
        download_pool.close()
        download_pool.join()

if __name__ == '__main__':
    sys.exit(main() or 0)
