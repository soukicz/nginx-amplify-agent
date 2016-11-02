# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.util import net


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class NetTestCase(BaseTestCase):
    def test_ipv4_address(self):
        host, port = net.ipv4_address(address='10.10.10.10:443')
        assert_that(host, equal_to('10.10.10.10'))
        assert_that(port, equal_to('443'))

        host, port = net.ipv4_address(address='443')
        assert_that(host, equal_to('*'))
        assert_that(port, equal_to('443'))

        host, port = net.ipv4_address(address='10.10.10.10')
        assert_that(host, equal_to('10.10.10.10'))
        assert_that(port, equal_to('80'))

        host, port = net.ipv4_address(address='*')
        assert_that(host, equal_to('*'))
        assert_that(port, equal_to('80'))
