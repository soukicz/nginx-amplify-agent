# -*- coding: utf-8 -*-
import copy
import time

from hamcrest import *

import amplify.agent.common.context

from amplify.agent.managers.nginx import NginxManager

from test.base import RealNginxTestCase, nginx_plus_test, disabled_test

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class NginxObjectTestCase(RealNginxTestCase):

    def setup_method(self, method):
        super(NginxObjectTestCase, self).setup_method(method)
        self.original_app_config = copy.deepcopy(amplify.agent.common.context.context.app_config.config)

    def teardown_method(self, method):
        amplify.agent.common.context.context.app_config.config = copy.deepcopy(self.original_app_config)
        super(NginxObjectTestCase, self).teardown_method(method)

    @nginx_plus_test
    def test_plus_status_discovery(self):
        """
        Checks that for plus nginx we collect two status urls:
        - one for web link (with server name)
        - one for agent purposes (local url)
        """
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # get nginx object
        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        # check all plus status urls
        assert_that(nginx_obj.plus_status_enabled, equal_to(True))
        assert_that(nginx_obj.plus_status_internal_url, equal_to('https://127.0.0.1:443/plus_status'))
        assert_that(nginx_obj.plus_status_external_url, equal_to('http://status.naas.nginx.com:443/plus_status_bad'))

    @nginx_plus_test
    def test_bad_plus_status_discovery(self):
        self.stop_first_nginx()
        self.start_second_nginx(conf='nginx_bad_status.conf')
        container = NginxManager()
        container._discover_objects()

        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # get nginx object
        nginx_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        # check all plus status urls
        assert_that(nginx_obj.plus_status_enabled, equal_to(True))
        assert_that(nginx_obj.plus_status_internal_url, none())
        assert_that(nginx_obj.plus_status_external_url, equal_to('http://bad.status.naas.nginx.com:82/plus_status'))

    @nginx_plus_test
    def test_bad_plus_status_discovery_with_config(self):
        amplify.agent.common.context.context.app_config['nginx']['plus_status'] = '/foo_plus'
        amplify.agent.common.context.context.app_config['nginx']['stub_status'] = '/foo_basic'

        self.stop_first_nginx()
        self.start_second_nginx(conf='nginx_bad_status.conf')
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        # self.http_request should look like this
        # [
        # first - internal plus statuses
        # 'http://127.0.0.1:82/plus_status', 'https://127.0.0.1:82/plus_status',
        # 'http://127.0.0.1/foo_plus', 'https://127.0.0.1/foo_plus',
        #
        # then external plus statuses
        # 'http://bad.status.naas.nginx.com:82/plus_status', 'https://bad.status.naas.nginx.com:82/plus_status',
        #
        # finally - stub statuses
        # 'http://127.0.0.1:82/basic_status', 'https://127.0.0.1:82/basic_status',
        # 'http://127.0.0.1/foo_basic', 'https://127.0.0.1/foo_basic'
        # ]

        assert_that(self.http_requests[2], equal_to('http://127.0.0.1/foo_plus'))
        assert_that(self.http_requests[-2], equal_to('http://127.0.0.1/foo_basic'))

    def test_bad_stub_status_discovery_with_config(self):
        amplify.agent.common.context.context.app_config['nginx']['stub_status'] = '/foo_basic'

        self.stop_first_nginx()
        self.start_second_nginx(conf='nginx_bad_status.conf')
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))

        assert_that(self.http_requests[-1], equal_to('https://127.0.0.1/foo_basic'))
        assert_that(self.http_requests[-2], equal_to('http://127.0.0.1/foo_basic'))

    def test_skip_parse_on_reload(self):
        # wrap NginxConfig.full_parse with a method that counts how many times it's been called
        from amplify.agent.objects.nginx.config.config import NginxConfig

        def count_full_parse_calls(config_obj):
            NginxConfig.__full_parse_calls += 1
            config_obj.__full_parse()

        NginxConfig.__full_parse_calls = 0
        NginxConfig.__full_parse = NginxConfig.full_parse
        NginxConfig.full_parse = count_full_parse_calls

        manager = NginxManager()
        manager._discover_objects()

        # check that the config has only been parsed once (at startup)
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(NginxConfig.__full_parse_calls, equal_to(1))

        # reload nginx and discover objects again so manager will recognize it
        self.reload_nginx()
        time.sleep(2)
        manager._discover_objects()

        # metrics collector will cause the nginx object to need a restart because pids have changed
        metrics_collector = nginx_obj.collectors[2]
        metrics_collector.collect(no_delay=True)
        manager._discover_objects()

        # check that the config was not parsed again after the restart
        nginx_obj = manager.objects.find_all(types=manager.types)[0]
        assert_that(NginxConfig.__full_parse_calls, equal_to(1))

        # check that the new nginx object's config collector won't call full_parse
        config_collector = nginx_obj.collectors[0]
        config_collector.collect(no_delay=True)
        assert_that(NginxConfig.__full_parse_calls, equal_to(1))

        # check that the config collector will still call full parse if config changes
        config_collector.previous['files'] = {}
        config_collector.collect(no_delay=True)
        assert_that(NginxConfig.__full_parse_calls, equal_to(2))

    # TODO: Fill out these tests once we move our test containers to Ubuntu 16.04

    @disabled_test
    def test_start_syslog_listener(self):
        pass

    @disabled_test
    def test_not_start_syslog_listener(self):
        pass
