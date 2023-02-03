#!/usr/bin/env python3

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

"""
Launch a Firefox browser to download PDFs from eVision.
"""

import argparse
import logging
import logging.config
import os
import sys
import warnings

import colorama
from selenium import webdriver
from selenium.webdriver.firefox.service import Service

from evision_dl.applicant import ApplicantContextChangeListener
from evision_dl.download import Downloader
from evision_dl.logging import ColorFormatter
from evision_dl.robot import Robot
from evision_dl.summary import Summarizer
from evision_dl.screen.start import StartScreen

logger = logging.getLogger(__name__)

def parse_args(args):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dest_dir',
        help='Directory to which PDFs should be saved')
    parser.add_argument('--log-config', metavar='config.ini', type=argparse.FileType(), default=None,
        help='Python logging configuration (see https://docs.python.org/3/library/logging.config.html#logging-config-fileformat)')
    parser.add_argument('--webdriver-log', metavar='webdriver.log', default=os.devnull,
        help='Webdriver log file (such as geckodriver.log)')
    args = parser.parse_args(args)
    if not os.path.isdir(args.dest_dir):
        print("Directory '{0}' does not exist".format(args.dest_dir), file=sys.stderr)
        return None
    return {
        'dest_dir': args.dest_dir,
        'log_config': args.log_config,
        'webdriver_log': args.webdriver_log,
    }

def main(*argv):
    args = parse_args(argv or sys.argv[1:])
    if args is None:
        return 1

    # Enable support for ANSI color sequences in the Windows console
    colorama.init()
    if log_config := args.pop('log_config'):
        logging.config.fileConfig(log_config)
    else:
        ch = logging.StreamHandler()
        ch.setFormatter(ColorFormatter(
            format="%(asctime)s [%(levelname)s] @%(name)s %(message)s",
        ))
        logging.basicConfig(
            level=logging.INFO,
            handlers=[ch],
        )
 
    capabilities = webdriver.DesiredCapabilities().FIREFOX.copy()
    capabilities['acceptInsecureCerts'] = False
    with warnings.catch_warnings():
        # It seems that Selenium has deprecated every reasonable way to
        # configure Firefox settings!  We need to suppress the warning
        # about Capabilities being deprecated.
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        driver = webdriver.Firefox(
            capabilities=capabilities,
            service=Service(log_path=args.pop('webdriver_log'))
        )

    robot = Robot(driver)
    robot.add_event_listener(ApplicantContextChangeListener())
    robot.add_event_listener(Downloader(args['dest_dir']))
    robot.add_event_listener(Summarizer())
    return robot.run(StartScreen)

if __name__ == '__main__':
    sys.exit(main() or 0)
