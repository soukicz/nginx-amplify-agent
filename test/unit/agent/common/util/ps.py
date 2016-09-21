# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import RealNginxTestCase, future_test

from amplify.agent.managers.nginx import NginxManager
from amplify.agent.managers.system import SystemManager


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class PsutilsTestCase(RealNginxTestCase):
    """
    Overall test are for testing our calls to psutils and making sure they work.
    """
    def setup_method(self, method):
        super(PsutilsTestCase, self).setup_method(method)

        self.system_manager = SystemManager()
        self.system_manager._discover_objects()
        self.nginx_manager = NginxManager()
        self.nginx_manager._discover_objects()

        self.system_obj = self.system_manager.objects.objects[
            self.system_manager.objects.objects_by_type[self.system_manager.type][0]
        ]
        self.system_metrics_collector = self.system_obj.collectors[1]

        self.nginx_obj = self.nginx_manager.objects.objects[
            self.nginx_manager.objects.objects_by_type[self.nginx_manager.type][0]
        ]
        self.nginx_metrics_collector = self.nginx_obj.collectors[2]

    def teardown_method(self, method):
        self.system_manager = None
        self.nginx_manager = None
        super(PsutilsTestCase, self).teardown_method(method)

    def test_system_virtual_memory(self):
        assert_that(calling(self.system_metrics_collector.virtual_memory), not_(raises(Exception)))

    def test_system_swap(self):
        assert_that(calling(self.system_metrics_collector.swap), not_(raises(Exception)))

    def test_system_cpu(self):
        assert_that(calling(self.system_metrics_collector.cpu), not_(raises(Exception)))

    def test_system_disk_partitions(self):
        assert_that(calling(self.system_metrics_collector.disk_partitions), not_(raises(Exception)))

    def test_system_disk_io_counters(self):
        assert_that(calling(self.system_metrics_collector.disk_io_counters), not_(raises(Exception)))

    def test_system_net_io_counters(self):
        assert_that(calling(self.system_metrics_collector.net_io_counters), not_(raises(Exception)))

    def test_nginx_memory_info(self):
        assert_that(calling(self.nginx_metrics_collector.memory_info), not_(raises(Exception)))

    def test_nginx_workers_fds_count(self):
        assert_that(calling(self.nginx_metrics_collector.workers_fds_count), not_(raises(Exception)))

    # These next two tests have to be skipped due to calls to .handle_zombie() which raises a hamcrest exception.
    @future_test
    def test_nginx_workers_rlimit_nofile(self):
        assert_that(calling(self.nginx_metrics_collector.workers_rlimit_nofile), not_(raises(Exception)))

    @future_test
    def test_nginx_workers_io(self):
        assert_that(calling(self.nginx_metrics_collector.workers_io), not_(raises(Exception)))

    def test_nginx_workers_cpu(self):
        assert_that(calling(self.nginx_metrics_collector.workers_cpu), not_(raises(Exception)))
