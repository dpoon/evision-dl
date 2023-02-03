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
import os
from urllib.request import build_opener
from urllib.parse import urlparse

from .applicant import Applicant, ApplicantContextChangeEvent
from .event import Event, EventListener
from .robot import Robot

######################################################################

class PDFGenerationEvent(Event):
    pass

class PDFGenerationCaveatEvent(PDFGenerationEvent):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "problematic PDF documents: {}".format(self.message)

class PDFGenerationFailureEvent(PDFGenerationEvent):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "no PDF: {}" + (": " + self.message if self.message else '')

class PDFGenerationSuccessEvent(PDFGenerationEvent):
    def __init__(self, url, http_headers):
        self.url = url
        self.http_headers = http_headers

    def __str__(self):
        return "PDF available at {}".format(self.url)

######################################################################

class PDFDownloadEvent(Event):
    def __init__(self, applicant):
        self.applicant = applicant

class PDFDownloadFailureEvent(PDFDownloadEvent):
    def __init__(self, applicant, exception):
        super().__init__(applicant)
        self.exception = exception

    def __str__(self):
        return "Failed to download PDF for {}: {}".format(self.applicant, self.exception)

class PDFDownloadSuccessEvent(PDFDownloadEvent):
    def __init__(self, applicant, dest_path):
        super().__init__(applicant)
        self.dest_path = dest_path

    def __str__(self):
        return "Downloaded PDF for {} to {}".format(self.applicant, self.dest_path)

######################################################################

logger = logging.getLogger(__name__)

class Downloader(EventListener):
    def __init__(self, dest_dir):
        self.dest_dir = dest_dir
        self.current_applicant = None

    def handle_event(self, robot, event):
        if isinstance(event, ApplicantContextChangeEvent):
            self.current_applicant = event.applicant
        elif isinstance(event, PDFGenerationFailureEvent):
            self._handle_unavailable_pdf(event.message)
            robot.post_event(ApplicantContextChangeEvent(None))
        elif isinstance(event, PDFGenerationSuccessEvent):
            try:
                dest_path = self._handle_available_pdf(event.url, event.http_headers)
                robot.post_event(PDFDownloadSuccessEvent(self.current_applicant, dest_path))
            except Exception as e:
                logger.error(e)
                robot.post_event(PDFDownloadFailureEvent(self.current_applicant, e))
        elif isinstance(event, PDFDownloadEvent):
            robot.post_event(ApplicantContextChangeEvent(None))

    def _handle_unavailable_pdf(self, error_msg):
        logger.error("No PDF generated for {}".format(self.current_applicant))
        dest_path = self._pdf_dest_path_for_applicant()
        with open(dest_path, 'wb') as f:
            # Just make an empty file as evidence of the failure
            pass
        return dest_path

    def _handle_available_pdf(self, url, http_headers):
        # Downloading files using the webdriver is complicated.  We don't know
        # whether the browser will display the PDF, launch a helper application
        # to view it, use a plugin, or save it.  If saving, it's hard to
        # control the destination directory and the overwrite behavior.
        #
        # It's easier to download it using Python instead.
        logger.debug("PDF URL {}".format(url))
        dest_path = self._pdf_dest_path_for_applicant()
        opener = build_opener()
        opener.addheaders = http_headers
        with opener.open(url) as res, open(dest_path, 'wb') as f:
            f.write(res.read())
        logger.info("Downloaded PDF to {}".format(dest_path))
        return dest_path

    def _pdf_dest_path_for_applicant(self):
        surname = self.current_applicant.surname
        preferred_name = self.current_applicant.preferred_name
        student_number = self.current_applicant.student_number
        # Fill in filename template, guarding against directory traversal attacks
        filename = '{sn}, {prefname} ({nnnnnnnn}){EXT}pdf'.format(
            sn=' ' + surname if surname.startswith(os.path.curdir) else surname,
            prefname=preferred_name,
            nnnnnnnn=student_number,
            EXT=os.path.extsep,
        ).replace(os.path.sep, ' ')
        return os.path.join(self.dest_dir, filename)
