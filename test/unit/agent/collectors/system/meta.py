# -*- coding: utf-8 -*-
import netifaces

import psutil
from hamcrest import *

from amplify.agent.collectors.system.meta.container import ContainerMetaCollector
from amplify.agent.collectors.system.meta.system import SystemMetaCollector
from amplify.agent.common.context import context
from amplify.agent.common.util import subp
from amplify.agent.managers.system import SystemManager
from test.base import BaseTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class MetaParsersTestCase(BaseTestCase):

    def test_parse_only_alive_interfaces(self):
        container = SystemManager()
        container._discover_objects()

        os_obj = container.objects.find_all(types=container.types)[0]
        collector = SystemMetaCollector(object=os_obj)
        collector.collect()

        # get interfaces info
        all_interfaces = netifaces.interfaces()
        alive_interfaces = set()
        down_interfaces = set()
        for interface_name, interface in psutil.net_if_stats().iteritems():
            if interface.isup:
                alive_interfaces.add(interface_name)
            else:
                down_interfaces.add(interface_name)

        # check intefaces
        collected_interfaces = os_obj.metad.current['network']['interfaces']
        for interface_info in collected_interfaces:
            name = interface_info['name']
            assert_that(all_interfaces, has_item(name))
            assert_that(alive_interfaces, has_item(name))
            assert_that(down_interfaces, not_(has_item(name)))

    def test_default_interface(self):
        container = SystemManager()
        container._discover_objects()

        os_obj = container.objects.find_all(types=container.types)[0]
        collector = SystemMetaCollector(object=os_obj)
        collector.collect()

        default_from_netstat, _ = subp.call(
            'netstat -nr | egrep -i "^0.0.0.0|default" | head -1 | sed "s/.*[ ]\([^ ][^ ]*\)$/\\1/"'
        )[0]

        default_interface = os_obj.metad.current['network']['default']

        assert_that(default_interface, equal_to(default_from_netstat))


class ContainerMetaParsersTestCase(BaseTestCase):

    def setup_method(self, method):
        super(ContainerMetaParsersTestCase, self).setup_method(method)
        context.app_config['credentials']['imagename'] = 'DockerTest'

    def teardown_method(self, method):
        context.app_config['credentials']['imagename'] = None
        super(ContainerMetaParsersTestCase, self).setup_method(method)

    def test_special_parse_restrictions(self):
        container = SystemManager()
        container._discover_objects()

        os_obj = container.objects.find_all(types=container.types)[0]
        collector = ContainerMetaCollector(object=os_obj)
        assert_that(collector.short_name, equal_to('container_meta'))

        collector.collect()
        collected_meta = os_obj.metad.current

        assert_that(collected_meta, not_(has_key('boot')))
        assert_that(collected_meta, not_(has_key('hostname')))
        assert_that(collected_meta, not_(has_key('ec2')))

    def test_parse_only_alive_interfaces(self):
        container = SystemManager()
        container._discover_objects()

        os_obj = container.objects.find_all(types=container.types)[0]
        collector = ContainerMetaCollector(object=os_obj)
        collector.collect()

        # get interfaces info
        all_interfaces = netifaces.interfaces()
        alive_interfaces = set()
        down_interfaces = set()
        for interface_name, interface in psutil.net_if_stats().iteritems():
            if interface.isup:
                alive_interfaces.add(interface_name)
            else:
                down_interfaces.add(interface_name)

        # check intefaces
        collected_interfaces = os_obj.metad.current['network']['interfaces']
        for interface_info in collected_interfaces:
            name = interface_info['name']
            assert_that(all_interfaces, has_item(name))
            assert_that(alive_interfaces, has_item(name))
            assert_that(down_interfaces, not_(has_item(name)))

            # Docker special check
            assert_that(interface_info, not_(has_key('ipv4')))
            assert_that(interface_info, not_(has_key('ipv6')))

    def test_default_interface(self):
        container = SystemManager()
        container._discover_objects()

        os_obj = container.objects.find_all(types=container.types)[0]
        collector = ContainerMetaCollector(object=os_obj)
        collector.collect()

        default_from_netstat, _ = subp.call(
            'netstat -nr | egrep -i "^0.0.0.0|default" | head -1 | sed "s/.*[ ]\([^ ][^ ]*\)$/\\1/"'
        )[0]

        default_interface = os_obj.metad.current['network']['default']

        assert_that(default_interface, equal_to(default_from_netstat))
