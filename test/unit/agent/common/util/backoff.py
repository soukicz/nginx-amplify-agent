# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

import amplify.agent.common.util.backoff as backoff


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class BackoffUtilTestCase(BaseTestCase):
    def test_single(self):
        delay = backoff.exponential_delay(1)

        assert_that(delay, is_not(None))
        assert_that(delay, is_(greater_than_or_equal_to(0)))
        assert_that(delay, is_(less_than(backoff.TIMEOUT_PERIOD)))

    def test_double(self):
        delay = backoff.exponential_delay(2)

        assert_that(delay, is_not(None))
        assert_that(delay, is_(greater_than_or_equal_to(0)))
        assert_that(delay, is_(less_than(backoff.TIMEOUT_PERIOD * backoff.EXPONENTIAL_COEFFICIENT)))

    def test_max(self):
        delay = backoff.exponential_delay(600)

        assert_that(delay, is_not(None))
        assert_that(delay, is_(greater_than_or_equal_to(0)))
        assert_that(delay, is_(less_than(backoff.MAXIMUM_TIMEOUT)))

    def test_max_2(self):
        original_max = backoff.MAXIMUM_TIMEOUT
        backoff.MAXIMUM_TIMEOUT = 2
        delay = backoff.exponential_delay(1)

        assert_that(delay, is_not(None))
        assert_that(delay, is_(greater_than_or_equal_to(0)))
        assert_that(delay, is_(less_than(2)))

        # reset
        backoff.MAXIMUM_TIMEOUT = original_max

    def test_bad(self):
        delay = backoff.exponential_delay(0)

        assert_that(delay, is_not(None))
        assert_that(delay, equal_to(0))
