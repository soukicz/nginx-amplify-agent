# -*- coding: utf-8 -*-
import time
import logging
from logging.handlers import SysLogHandler

from hamcrest import *

from amplify.agent.pipelines.syslog import SyslogTail, SYSLOG_ADDRESSES, AmplifyAddresssAlreadyInUse
from test.base import BaseTestCase, disabled_test


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class SyslogTailTestCase(BaseTestCase):
    def setup_method(self, method):
        super(SyslogTailTestCase, self).setup_method(method)
        self.tail = SyslogTail(address=('localhost', 514), interval=0.1)

        # Set up python logger
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        self.handler = SysLogHandler(address=('localhost', 514))
        self.handler.setFormatter(logging.Formatter(' amplify: %(message)s'))
        self.logger.addHandler(self.handler)

    def teardown_method(self, method):
        # Revert logger stuff
        self.handler.close()
        self.handler = None
        self.logger = None

        # Kill the SyslogTail
        self.tail.stop()
        self.tail = None

    def test_overall(self):
        time.sleep(0.1)  # Release GIL so async listener can "hear" the DGRAMs
        count = 1
        while count <= 5:
            self.logger.debug('This is message #%s' % count)
            count += 1

        time.sleep(0.1)  # Release GIL so async listener can handle DGRAMs

        # Check to see that SyslogListener read 5 messages
        assert_that(self.tail.cache, has_length(count-1))

        # Check the cache directly to make sure messages were decoded.
        for i in xrange(5):
            assert_that(self.tail.cache[i], equal_to(u'This is message #%s\x00' % (i+1)))

        # Go through and check the messages via iteration
        count = 1
        for line in self.tail:
            assert_that(line, equal_to(u'This is message #%s\x00' % count))
            count += 1

        # Check that cache was cleared after iteration
        assert_that(self.tail.cache, has_length(0))

    # TODO: test_overall doesn't work if there are other tests run with it...why?
    # The tests below pass, but will cause test_overall to fail if run...so skipped for now.
    @disabled_test
    def test_addresses(self):
        assert_that(('localhost', 514), is_in(SYSLOG_ADDRESSES))

    @disabled_test
    def test_socket_conflict(self):
        assert_that(
            calling(SyslogTail).with_args(address=('localhost', 514)),
            raises(AmplifyAddresssAlreadyInUse)
        )
