import logging
import os
from urllib.request import build_opener
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class Robot:
    def __init__(self, driver, opts):
        self.driver = driver
        self.opts = opts
        self._user_agent = self.driver.execute_script('return navigator.userAgent')
        self._current_applicant = None
        self.success_count = self.error_count = 0

    def run(self, initial_screen_class):
        try:
            screen = initial_screen_class(self)
            while screen:
                screen = screen.process()
        except KeyboardInterrupt:
            logger.error("Keyboard interrupt")
            return 2
        except Exception:
            logger.exception("Crashed with uncaught exception")
            self.error_count += 1
            return 1
        finally:
            logger.info("Downloaded {} PDFs successfully and {} unsuccessfully".format(
                self.success_count, self.error_count
            ))

    def handle_switch_to_applicant(self, applicant):
        logger.info(applicant)
        self._current_applicant = applicant

    def handle_unavailable_pdf(self, error_msg=''):
        logger.error("No PDF generated for {}".format(self._current_applicant))
        dest_path = self._pdf_dest_path_for_applicant()
        with open(dest_path, 'wb') as f:
            # Just make an empty file as evidence of the failure
            pass
        self.error_count += 1

    def handle_available_pdf(self, url):
        # Downloading files using the webdriver is complicated.  We don't know
        # whether the browser will display the PDF, launch a helper application
        # to view it, use a plugin, or save it.  If saving, it's hard to
        # control the destination directory and the overwrite behavior.
        #
        # It's easier to download it using Python instead.
        logger.debug("PDF URL {}".format(url))
        dest_path = self._pdf_dest_path_for_applicant()
        cookie_string = '; '.join(
            '{0}={1}'.format(cookie['name'], cookie['value'])
            for cookie in self.driver.get_cookies()
        )
        opener = build_opener()
        opener.addheaders = [
            ('Cookie', cookie_string),
            # The User-Agent must match the browser's, else eVision will
            # invalidate the whole session
            ('User-Agent', self._user_agent),
        ]
        with opener.open(url) as res, open(dest_path, 'wb') as f:
            f.write(res.read())
        logger.info("Downloaded PDF to {}".format(dest_path))
        self._current_applicant = None
        self.success_count += 1

    def _pdf_dest_path_for_applicant(self):
        surname = self._current_applicant.surname
        preferred_name = self._current_applicant.preferred_name
        student_number = self._current_applicant.student_number
        # Fill in filename template, guarding against directory traversal attacks
        filename = '{sn}, {prefname} ({nnnnnnnn}){EXT}pdf'.format(
            sn=' ' + surname if surname.startswith(os.path.curdir) else surname,
            prefname=preferred_name,
            nnnnnnnn=student_number,
            EXT=os.path.extsep,
        ).replace(os.path.sep, ' ')
        return os.path.join(self.opts['dest_dir'], filename)
