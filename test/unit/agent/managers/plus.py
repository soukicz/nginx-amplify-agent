# -*- coding: utf-8 -*-
import time
from hamcrest import *

from test.base import RealNginxTestCase, nginx_plus_test

from amplify.agent.common.context import context
from amplify.agent.managers.nginx import NginxManager
from amplify.agent.managers.plus import PlusManager


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusManagerTestCase(RealNginxTestCase):
    def setup_method(self, method):
        super(PlusManagerTestCase, self).setup_method(method)
        context.objects = None
        context._setup_object_tank()

    def teardown_method(self, method):
        context.objects = None
        context._setup_object_tank()
        super(PlusManagerTestCase, self).teardown_method(method)

    @nginx_plus_test
    def test_discover(self):
        nginx_manager = NginxManager()
        nginx_manager._discover_objects()
        assert_that(nginx_manager.objects.objects_by_type[nginx_manager.type], has_length(1))

        # get nginx object
        nginx_obj = nginx_manager.objects.objects[nginx_manager.objects.objects_by_type[nginx_manager.type][0]]

        # get metrics collector - the third in the list
        metrics_collector = nginx_obj.collectors[2]

        # run plus status - twice, because counters will appear only on the second run
        metrics_collector.plus_status()
        time.sleep(1)
        metrics_collector.plus_status()

        plus_manager = PlusManager()
        plus_manager._discover_objects()
        assert_that(plus_manager.objects.find_all(types=plus_manager.types), has_length(2))
