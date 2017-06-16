#!/usr/bin/env python
import optparse
import sys
import unittest2
import fix_path
import os
import logging

USAGE = """%prog SDK_PATH TEST_PATH
Run unit tests for App Engine apps.

SDK_PATH    Path to the SDK installation
TEST_PATH   Path to package containing test modules"""


def main(sdk_path, test_path):
    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()
    if os.path.isfile(test_path):
        suite = unittest2.loader.TestLoader().discover(
            os.path.dirname(test_path), os.path.basename(test_path))
    else:
        suite = unittest2.loader.TestLoader().discover(test_path)
    unittest2.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    parser = optparse.OptionParser(USAGE)
    options, args = parser.parse_args()
    if len(args) != 2:
        print 'Error: Exactly 2 arguments required.'
        parser.print_help()
        sys.exit(1)
    SDK_PATH = args[0]
    TEST_PATH = args[1]

    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.ERROR)

    main(SDK_PATH, TEST_PATH)
