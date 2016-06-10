# -*- coding: utf-8 -*-
import requests_mock
import time

from copy import deepcopy
from hamcrest import *

from amplify.agent.common.context import context
from amplify.agent.supervisor import Supervisor
from test.base import RealNginxTestCase, nginx_plus_test, nginx_oss_test
from test.fixtures.defaults import DEFAULT_API_URL, DEFAULT_API_KEY

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class SupervisorTestCase(RealNginxTestCase):

    def setup_method(self, method):
        super(SupervisorTestCase, self).setup_method(method)
        self.old_cloud_config = deepcopy(context.app_config.config)

    def teardown_method(self, method):
        context.app_config.config = self.old_cloud_config
        super(SupervisorTestCase, self).teardown_method(method)

    def test_talk_to_cloud(self):
        """
        Checks that we apply all changes from cloud to agent config and object configs
        """
        supervisor = Supervisor()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 30.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"max_test_duration": 30.0, "run_test": false, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [{"$request_uri": "/api/timeseries"}]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            supervisor.init_object_managers()
            for container in supervisor.object_managers.itervalues():
                container._discover_objects()

            old_object_configs = deepcopy(supervisor.object_managers['nginx'].object_configs)

            supervisor.talk_to_cloud(force=True)
            for container in supervisor.object_managers.itervalues():
                container._discover_objects()

            # check that agent config was changed
            assert_that(context.app_config.config, not_(equal_to(self.old_cloud_config)))

            # check that object configs were also changed
            nginx_container = supervisor.object_managers['nginx']
            assert_that(nginx_container.object_configs, not_(equal_to(old_object_configs)))

    def test_filters_unchanged(self):
        """
        Checks that agent is able to determine filters changes
        """
        supervisor = Supervisor()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text='{"config": {"cloud": {"push_interval": 60.0, "talk_interval": 60.0, "api_timeout": 15.0}, "containers": {"nginx": {"max_test_duration": 30.0, "run_test": false, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "root_uuid": "6789abcde", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [{"$request_uri": "/api/timeseries"}]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
            )

            supervisor.init_object_managers()
            for object_manager_name in supervisor.object_manager_order:
                object_manager = supervisor.object_managers[object_manager_name]
                object_manager._discover_objects()
            old_nginx_configs = deepcopy(supervisor.object_managers['nginx'].object_configs)

            # talk 1st time - everything changes
            supervisor.talk_to_cloud(force=True)
            for container in supervisor.object_managers.itervalues():
                container._discover_objects()

            # check that agent config was changed
            assert_that(context.app_config.config, not_(equal_to(self.old_cloud_config)))
            self.old_cloud_config = deepcopy(context.app_config.config)

            # check that object configs were also changed (because filters were pushed)
            nginx_container = supervisor.object_managers['nginx']
            assert_that(nginx_container.object_configs, not_(equal_to(old_nginx_configs)))

            # talk 2nd time - changes again (filters)
            supervisor.talk_to_cloud(force=True)
            for object_manager_name in supervisor.object_manager_order:
                object_manager = supervisor.object_managers[object_manager_name]
                object_manager._discover_objects()

            # save some vars to check later
            old_nginx_configs = deepcopy(nginx_container.object_configs)
            nginx_object_init_time = supervisor.object_managers['nginx'].objects.objects[5].init_time

            time.sleep(2)

            # talk 3nd time - no change
            supervisor.talk_to_cloud(force=True)
            for object_manager_name in supervisor.object_manager_order:
                object_manager = supervisor.object_managers[object_manager_name]
                object_manager._discover_objects()

            # check that agent config was not changed
            assert_that(context.app_config.config, equal_to(self.old_cloud_config))

            # check that object configs were not changed
            nginx_container = supervisor.object_managers['nginx']
            assert_that(nginx_container.object_configs, equal_to(old_nginx_configs))

            # check that we still use previously created objects
            assert_that(
                supervisor.object_managers['nginx'].objects.objects[5].init_time,
                equal_to(nginx_object_init_time)
            )

    @nginx_plus_test
    def test_filters_applying_plus(self):
        self.mock_request_data = '{"config": {"cloud": {"push_interval": 60.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"max_test_duration": 30.0, "run_test": false, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "root_uuid": "6789abcde", "local_id": "b636d4376dea15405589692d3c5d3869ff3a9b26b0e7bb4bb1aa7e658ace1437"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [{"$request_uri": "/api/timeseries"}]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
        self.run_filters_applying_test()

    @nginx_oss_test
    def test_filters_applying_oss(self):
        self.mock_request_data = '{"config": {"cloud": {"push_interval": 60.0, "talk_interval": 60.0, "api_timeout": 10.0}, "containers": {"nginx": {"max_test_duration": 30.0, "run_test": false, "poll_intervals": {"metrics": 20.0, "configs": 20.0, "meta": 30.0, "discover": 10.0, "logs": 10.0}, "upload_ssl": true, "upload_config": true}, "system": {"poll_intervals": {"metrics": 20.0, "meta": 30.0, "discover": 10.0}}}}, "objects": [{"object":{"type":"nginx", "root_uuid": "6789abcde", "local_id": "151d8728e792f42e129337573a21bb30ab3065d59102f075efc2ded28e713ff8"}, "config":{"upload_ssl":true}, "filters":[ {"metric": "nginx.http.method.post", "filter_rule_id": 9, "data": [{"$request_uri": "/api/timeseries"}]} ] }], "messages": [], "versions": {"current": 0.29, "old": 0.26, "obsolete": 0.21}}'
        self.run_filters_applying_test()

    def run_filters_applying_test(self):
        supervisor = Supervisor()

        with requests_mock.mock() as m:
            m.post(
                '%s/%s/agent/' % (DEFAULT_API_URL, DEFAULT_API_KEY),
                text=self.mock_request_data
            )

            supervisor.init_object_managers()
            for manager_name in supervisor.object_manager_order:
                supervisor.object_managers[manager_name]._discover_objects()
            nginx_manager = supervisor.object_managers['nginx']
            nginx_obj = nginx_manager.objects.find_all(types=nginx_manager.types)[0]
            assert_that(nginx_obj.filters, has_length(0))

            # talk 1st time
            supervisor.talk_to_cloud(force=True)
            for manager_name in supervisor.object_manager_order:
                supervisor.object_managers[manager_name]._discover_objects()

            nginx_manager = supervisor.object_managers['nginx']
            nginx_obj = nginx_manager.objects.find_all(types=nginx_manager.types)[0]

            assert_that(nginx_obj.filters, has_length(1))
