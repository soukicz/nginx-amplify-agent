# -*- coding: utf-8 -*-
import os
from hamcrest import *

from test.base import BaseTestCase, container_test

from amplify.agent.common.util import container
from amplify.agent.common.context import context

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


@container_test
class ContainerTestCase(BaseTestCase):
    def test_is_docker(self):
        flag = container.is_docker()
        assert_that(flag, equal_to(True))

    def test_is_lxc(self):
        flag = container.is_lxc()
        assert_that(flag, equal_to(False))

        os.environ.setdefault('container', 'lxc')

        flag = container.is_lxc()
        assert_that(flag, equal_to(True))

    def test_container_environment(self):
        container_type = container.container_environment()
        assert_that(container_type, equal_to('docker'))

    def test_context(self):
        assert_that(context.container_type, equal_to('docker'))
