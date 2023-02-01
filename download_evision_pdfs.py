#!/usr/bin/env python3

######################################################################
# To install the necessary prerequisites:
#     pip install --user selenium
#
# Selenium >= 4.6 will automatically download the necessary driver
# to interface with Firefox.
######################################################################

"""
Launch a Firefox browser to download PDFs from eVision.
"""

import argparse
import logging
import logging.config
import os
import sys
import warnings

from selenium import webdriver
from selenium.webdriver.firefox.service import Service

from evision_dl.robot import Robot
from evision_dl.screen.empty import EmptyScreen

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

    if log_config := args.pop('log_config'):
        logging.config.fileConfig(log_config)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] @%(name)s %(message)s",
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
    Robot(driver, args).run(EmptyScreen)

if __name__ == '__main__':
    sys.exit(main() or 0)
