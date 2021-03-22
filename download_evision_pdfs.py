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
# Include logger for debugging
import logging
import traceback
logger = logging.getLogger()
logging.basicConfig(  # Comment out logging.basicConfig when not debugging
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="2021-03-22_evision.log"
)
# Path to the Firefox driver (geckodriver)
os.environ['PATH'] = os.path.join(os.path.expanduser('~'), 'bin') + os.pathsep + os.environ['PATH']

def download(dest_file, url, headers=[]):
    logger.info("download(): SAVING DATA TO FILE {} FROM URL {} WITH HEADERS {}"
                .format(dest_file, url, headers))
    if not os.path.isdir(os.path.dirname(dest_file)):
        logger.info("download(): CREATING DIRECTORY FOR dest_file")
        os.makedirs(os.path.dirname(dest_file))
    with open(dest_file, 'wb') as f:
        logger.info("download(): WRITING TO dest_file {} ...".format(dest_file))
        if not url:
            print(u'Nothing to download to {1}!'.format(url, dest_file))
            logger.info("download(): NOTHING TO DOWNLOAD")
            return
        print(u'Downloading {0} to {1}...'.format(url, dest_file), end=None)
        opener = build_opener()
        opener.addheaders = headers
        logger.info("download(): opener = {}".format(opener))
        res = opener.open(url)  # Python 3 can do with opener.open(url) as res:
        try:
            f.write(res.read())
            print(u' Done.')
        finally:
            res.close()
            logger.info("download(): FINISHED DOWNLOAD")

def click(driver, *expectation):
    while True:
        logger.info("click(): ATTEMPTING {} AT URL {}".format(expectation, driver.current_url))
        try:
            return WebDriverWait(driver, 90).until(
                EC.presence_of_element_located(expectation)
            ).click()
        except TimeoutException:
            logger.error("click(): TIMEOUT EXCEPTION")
        except ElementClickInterceptedException:
            logger.warning("click(): CLICK INTERCEPTED")
            # Element is obscured, perhaps by an overlay
            try:
                # "Refresh? Yes/No" overlay: click "No".
                logger.info("click(): ATTEMPTING REFRESH")
                WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[contains(concat(" ", normalize-space(@class), " "), " ui-dialog ")][//span[text()="Refresh?"]]//button[text()="No"]')
                    )
                ).click()
            except TimeoutException:
                logger.error("click(): TIMEOUT EXCEPTION WHILE ATTEMPTING REFRESH")
                # Another overlay, perhaps "Loading, please wait..."
                #print("Retrying click...")
                pass

def click_button_open_window(driver, button):
    """
    Click a button that opens a new browser window, returning a handle to
    the newly opened window.
    """
    while True:
        logger.info("click_button_open_window(): ATTEMPTING TO CLICK {} AT {}".format(button, driver.current_url))
        try:
            return WebDriverWait(driver, 10).until(window_opened(
                lambda: button.click()
            ))
        except (TimeoutException, ElementClickInterceptedException) as e:
            if isinstance(e, TimeoutException):
                logger.error("click_button_open_window(): TIMEOUT EXCEPTION")
            else:
                logger.error("click_button_open_window(): ELEMENT CLICK INTERCEPTED EXCEPTION")
            # Click may have failed if the button was outside the viewport,
            # or if another UI element such as a scrollbar had obscured it.
            # Try to scroll the button into a better position.
            try:
                button.send_keys('\n', Keys.DOWN)
            except ElementNotInteractableException:
                logger.error("click_button_open_window(): AFTER SCROLLING, ELEMENT NOT INTERACTABLE EXCEPTION")
                pass
        except (ElementNotInteractableException) as e:
            logger.error("click_button_open_window(): ELEMENT NOT INTERACTABLE EXCEPTION")
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
    logger.info("save(): SAVING DATA TO dest_file {}".format(dest_file))
    """
    Save the URL (or the URL of the current browser window) to the given
    destination file.  if a multiprocessing pool is specified, the downloading
    will be backgrounded.
    """
    cookie_string = '; '.join(
        '{0}={1}'.format(cookie['name'], cookie['value'])
        for cookie in driver.get_cookies()
    )
    logger.info("save(): dest_file = {}, url = {}, current_url = {} cookie_string = {}"
                .format(dest_file, url, driver.current_url, cookie_string))
    download_args = (
        dest_file,
        url if url is not None else driver.current_url,
        [('Cookie', cookie_string)],
    )
    logger.info("save(): download_args = {}".format(download_args))
    if mp_pool:
        logger.info("save(): DOWNLOADING ASYNC")
        mp_pool.apply_async(download, download_args)
    else:
        logger.info("save(): DOWNLOADING")
        download(*download_args)

def navigate_to_first_app(driver):
    """
    Direct the user to log in to eVision and open the folder listing the 
    applicants of interest.  Return the window that contains the applicant table.
    """
    driver.get('https://evision.as.it.ubc.ca/')
    print("Please log in to eVision, then bring up evaluation folder and open the first application of interest.")
    while True:
        logger.info("navigate_to_first_app(): WAITING FOR LOGIN")
        app_window = WebDriverWait(driver, float('inf')).until(window_opened())
        logger.info("navigate_to_first_app(): WINDOW OPENED")
        driver.switch_to.window(app_window)
        logger.info("navigate_to_first_app(): SWITCHED TO WINDOW {}".format(driver.current_url))
        try:
            click(driver, By.LINK_TEXT, "GPO")
            return app_window
        except TimeoutException:
            logger.error("navigate_to_first_app(): TIMEOUT WHILE TRYING TO CLICK LINK \"GPO\"")
            pass        # This wasn't the window we were looking for?


def request_pdf(driver):
    app_window = driver.current_window_handle
    logger.info("request_pdf(): app_window = {}".format(app_window))
    while True:
        logger.info("request_pdf(): ATTEMPTING TO GET PDF URL FROM {}".format(driver.current_url))
        try:
            click(driver, By.LINK_TEXT, "GPO")
            # Want "Application Utilities" link, but By.LINK_TEXT fails when
            # there is a space
            click(driver, By.PARTIAL_LINK_TEXT, "Utilities")
            pdf_button = WebDriverWait(driver, 90).until(EC.presence_of_element_located(
                (By.XPATH, '//input[@type="button"][@value="Manage Applicant PDF"]')
            ))
            logger.info("request_pdf(): pdf_button = {}".format(pdf_button))
            pdf_window = click_button_open_window(driver, pdf_button)
            logger.info("request_pdf(): pdf_window = {}".format(pdf_window))
            logger.info("request_pdf(): SEARCHING FOR BUTTON WITH TEXT 'No'...")
            for i in range(5):
                logger.info("request_pdf(): ITERATION {}".format(i))
                for button in driver.find_elements(By.XPATH, '//button'):
                    logger.info("request_pdf(): button = {}".format(button))
                    if button.text == "No":
                        logger.info("request_pdf(): CLICKING BUTTON")
                        button.click()
                        break
            driver.switch_to.window(pdf_window)
            logger.info("request_pdf(): SWITCHING TO WINDOW pdf_window = {}")
            break
        except TimeoutException:
            logger.error("request_pdf(): TIMEOUT EXCEPTION WHILE LOCATING pdf_button")
        except StaleElementReferenceException:
            logger.error("request_pdf(): STALE ELEMENT REFERENCE EXCEPTION")
            pass
    logger.info("request_pdf(): LOCATING BUTTON LABELLED 'CONTINUE'...")
    try:
        continue_button = WebDriverWait(driver, 90).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="CONTINUE"]')
        ))
    except TimeoutException:
        logger.error("request_pdf(): TIMEOUT EXCEPTION WHILE LOCATING continue_button")
    for label in driver.find_elements(By.XPATH, '//label'):
        logger.info("request_pdf(): ITERATING THROUGH LABEL {}".format(label))
        if any(bad in label.text for bad in ["Language Proficiency", "GRE"]):
            logger.info("request_pdf(): CLICKING LABEL CONTAINING {}".format(["Language Proficiency", "GRE"]))
            label.click()
    continue_button.click()
    logger.info("request_pdf(): LOCATING BUTTON LABELLED 'BACK'...")
    try:
        WebDriverWait(driver, 120).until(EC.presence_of_element_located(
            (By.XPATH, '//input[@value="BACK"]')
        ))
    except TimeoutException:
        logger.error("request_pdf(): TIMEOUT EXCEPTION WHILE LOCATING 'BACK' BUTTON")
    logger.info("request_pdf(): CLICK BUTTON LABELLED 'CONTINUE'")
    driver.find_element(By.XPATH, '//input[@type="submit"][@value="CONTINUE"]').click()
    # eVision bug (INC1040643): PDF merge may fail, in which case you'll see
    # "Please to download a copy of the document" instead of "Please
    # _click_here_ to download a copy of the document".
    for _ in range(120):
        try:
            # if any("Please to download" in div.text or
            #
            #        "There has been a processing error" in div.text
            #
            #        for div in driver.find_elements(By.TAG_NAME, 'div')):
            for div in driver.find_elements(By.TAG_NAME, 'div'):
                if "Please to download" in div.text or "There has been a processing error" in div.text:
                    pdf_url = None
                    logger.warning("request_pdf(): PROCESSING ERROR AT ELEMENT {}".format(div))
                    break
            logger.info("request_pdf(): LOCATING PDF URL FROM HREF...")
            pdf_url = WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.LINK_TEXT, "click here")
            )).get_attribute('href')
            break
        except (StaleElementReferenceException, TimeoutException) as e:
            if isinstance(e, TimeoutException):
                logger.error("request_pdf(): TIMEOUT EXCEPTION WHILE GETTING pdf_url")
            else:
                logger.error("request_pdf(): STALE ELEMENT REFERENCE EXCEPTION WHILE GETTING pdf_url")
            pass        # Try again
    logger.info("request_pdf(): CLICKING ELEMENT LABELLED 'EXIT'")
    click(driver, By.XPATH, '//input[@value="EXIT"]')
    logger.info("request_pdf(): SWITCHING TO WINDOW {}".format(app_window))
    driver.switch_to.window(app_window)
    return pdf_url


def extract_app_identity(driver):
    logger.info("extract_app_identity(): STARTING...")
    def extract_table_text(label):
        # TODO: XPATH-escape the label
        logger.info("extract_table_text(): EXTRACT DATA AT LABEL {}".format(label))
        td = driver.find_element(By.XPATH, '//td[strong[text()="' + label + '"]]')
        td_formatted = td.text.replace(label, '', 1).strip()
        logger.info("extract_table_text(): FOUND {}, RETURNING FORMATTED DATA {}"
                    .format(td, td_formatted))
        return td_formatted
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
        logger.info("process_apps(): STARTING...")
        try:
            surname, preferred_name, student_number = extract_app_identity(driver)
        except TimeoutException:
            # Who knows what went wrong!  Try clicking "Previous Applicant", then
            # "Next Applicant" and hopefully we'll get another chance.
            logger.error("process_apps(): TIMEOUT EXCEPTION, CLICKING 'Previous' THEN 'Next'")
            print("Web application did not behave as expected.  Clicking "
                """"Previous Applicant", then "Next Applicant" to try again.""")
            click(driver, By.PARTIAL_LINK_TEXT, "Previous")
            click(driver, By.PARTIAL_LINK_TEXT, "Next")
            logger.info("process_apps(): CLICKED 'Previous' THEN 'Next', CONTINUING...")
            continue
        logger.info("process_apps(): surname = {}, preferred_name = {}, student_number = {}"
                    .format(surname, preferred_name, student_number))
        dest_file = os.path.join(
            dest_dir, u'{0}, {1} ({2}).pdf'.format(
                ' ' + surname if surname.startswith('.') else surname,
                preferred_name,
                student_number
            )
        )
        logger.info("process_apps(): PATH TO dest_file = {}".format(dest_file))
        pdf_url = request_pdf(driver)
        logger.info("process_apps(): pdf_url = {}".format(pdf_url))
        yield pdf_url, dest_file

        next_buttons = driver.find_elements(
            By.XPATH, '//input[@value="Next Applicant"][not(@disabled)]'
        )
        logger.info("process_apps(): next_buttons = {}".format(next_buttons))
        if not next_buttons:
            logger.warning("process_apps(): NO ELEMENT FOUND FOR next_buttons")
            break
        next_buttons[0].click()


def parse_args(args):
    logger.info("parse_args(): START PARSING...")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dest_dir',
        help='Directory to which PDFs should be saved')
    parser.add_argument('--webdriver-log', metavar='PATH', default=os.devnull,
        help='Webdriver log file (such as geckodriver.log)')
    args = parser.parse_args(args)
    logger.info("parse_args(): INPUTTED DATA: dest_dir = {}, webdriver-log = {}".format(args.dest_dir, args.webdriver_log))
    if not os.path.isdir(args.dest_dir):
        print("Directory '{0}' does not exist".format(args.dest_dir), file=sys.stderr)
        logger.error("parse_args(): DIRECTORY {} DOES NOT EXIST".format(args.dest_dir))
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
    logger.info("DRIVER OBJECT: {}".format(driver))
    try:
        navigate_to_first_app(driver)
        for pdf_url, dest_file in process_apps(driver, args['dest_dir']):
            save(driver, dest_file, pdf_url or '', download_pool)
    except KeyboardInterrupt:
        logger.info("KEYBOARD INTERRUPT")
        pass
    except Exception as e:
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        logger.error("CAUGHT ERROR: {} \n {}".format(repr(e), traceback_str))
        raise e
    print('Finishing downloads...')
    if download_pool is not None:
        logger.info("CLEARING download_pool...")
        download_pool.close()
        download_pool.join()
    logger.info("FINISHED")

if __name__ == '__main__':
    sys.exit(main() or 0)
