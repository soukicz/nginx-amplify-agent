# -*- coding: utf-8 -*-
import netifaces

import psutil
from hamcrest import *

from amplify.agent.collectors.system.metrics import SystemMetricsCollector
from amplify.agent.managers.system import SystemManager
from test.base import BaseTestCase
from test.helpers import collected_metric

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class SystemMetricsCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(SystemMetricsCollectorTestCase, self).setup_method(method)
        manager = SystemManager()
        manager._discover_objects()
        system_obj = manager.objects.objects[manager.objects.objects_by_type[manager.type][0]]
        collector = SystemMetricsCollector(object=system_obj)
        collector.collect()
        collector.collect() # second collect is needed to properly collect all metrics
        self.metrics = system_obj.statsd.current

    def test_collect(self):
        # check counters
        assert_that(self.metrics, has_key('counter'))
        counters = self.metrics['counter']
        assert_that(counters, has_entry('system.net.bytes_rcvd', collected_metric()))
        assert_that(counters, has_entry('system.net.bytes_sent', collected_metric()))
        assert_that(counters, has_entry('system.net.drops_in.count', collected_metric()))
        assert_that(counters, has_entry('system.net.drops_out.count', collected_metric()))
        assert_that(counters, has_entry('system.net.listen_overflows', collected_metric()))
        assert_that(counters, has_entry('system.net.packets_in.count', collected_metric()))
        assert_that(counters, has_entry('system.net.packets_in.error', collected_metric()))
        assert_that(counters, has_entry('system.net.packets_out.count', collected_metric()))
        assert_that(counters, has_entry('system.net.packets_out.error', collected_metric()))
        assert_that(counters, has_entry(starts_with('system.io.iops_r|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.io.iops_w|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.io.kbs_r|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.io.kbs_w|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.net.bytes_rcvd|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.net.bytes_sent|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.net.drops_in.count|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.net.drops_out.count|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.net.packets_in.count|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.net.packets_in.error|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.net.packets_out.count|'), collected_metric()))
        assert_that(counters, has_entry(starts_with('system.net.packets_out.error|'), collected_metric()))

        # check gauges
        assert_that(self.metrics, has_key('gauge'))
        gauges = self.metrics['gauge']
        assert_that(gauges, has_entry('amplify.agent.cpu.system', collected_metric()))
        assert_that(gauges, has_entry('amplify.agent.cpu.user', collected_metric()))
        assert_that(gauges, has_entry('amplify.agent.mem.rss', collected_metric()))
        assert_that(gauges, has_entry('amplify.agent.mem.vms', collected_metric()))
        assert_that(gauges, has_entry('amplify.agent.status', collected_metric()))
        assert_that(gauges, has_entry('system.cpu.idle', collected_metric()))
        assert_that(gauges, has_entry('system.cpu.iowait', collected_metric()))
        assert_that(gauges, has_entry('system.cpu.stolen', collected_metric()))
        assert_that(gauges, has_entry('system.cpu.system', collected_metric()))
        assert_that(gauges, has_entry('system.cpu.user', collected_metric()))
        assert_that(gauges, has_entry('system.disk.free', collected_metric()))
        assert_that(gauges, has_entry('system.disk.in_use', collected_metric()))
        assert_that(gauges, has_entry('system.disk.total', collected_metric()))
        assert_that(gauges, has_entry('system.disk.used', collected_metric()))
        assert_that(gauges, has_entry('system.load.1', collected_metric()))
        assert_that(gauges, has_entry('system.load.15', collected_metric()))
        assert_that(gauges, has_entry('system.load.5', collected_metric()))
        assert_that(gauges, has_entry('system.mem.available', collected_metric()))
        assert_that(gauges, has_entry('system.mem.buffered', collected_metric()))
        assert_that(gauges, has_entry('system.mem.cached', collected_metric()))
        assert_that(gauges, has_entry('system.mem.free', collected_metric()))
        assert_that(gauges, has_entry('system.mem.pct_used', collected_metric()))
        assert_that(gauges, has_entry('system.mem.total', collected_metric()))
        assert_that(gauges, has_entry('system.mem.used', collected_metric()))
        assert_that(gauges, has_entry('system.swap.free', collected_metric()))
        assert_that(gauges, has_entry('system.swap.pct_free', collected_metric()))
        assert_that(gauges, has_entry('system.swap.total', collected_metric()))
        assert_that(gauges, has_entry('system.swap.used', collected_metric()))
        assert_that(gauges, has_entry(starts_with('system.disk.total|'), collected_metric()))
        assert_that(gauges, has_entry(starts_with('system.disk.used|'), collected_metric()))
        assert_that(gauges, has_entry(starts_with('system.disk.free|'), collected_metric()))
        assert_that(gauges, has_entry(starts_with('system.disk.in_use|'), collected_metric()))
        assert_that(gauges, has_entry(starts_with('system.io.wait_r|'), collected_metric()))
        assert_that(gauges, has_entry(starts_with('system.io.wait_w|'), collected_metric()))

    def test_agent_memory_info(self):
        gauges = self.metrics['gauge']
        assert_that(gauges['amplify.agent.mem.rss'], collected_metric(greater_than(0)))
        assert_that(gauges['amplify.agent.mem.vms'], collected_metric(greater_than(0)))


class MetricsParsersTestCase(BaseTestCase):

    def test_collect_only_alive_interfaces(self):
        container = SystemManager()
        container._discover_objects()

        os_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]
        collector = SystemMetricsCollector(object=os_obj)
        collector.collect()
        collector.collect()  # double collect is needed, because otherwise we do not collect metrics properly

        # get interfaces info
        all_interfaces = netifaces.interfaces()
        alive_interfaces = set()
        down_interfaces = set()
        for interface_name, interface in psutil.net_if_stats().iteritems():
            if interface.isup:
                alive_interfaces.add(interface_name)
            else:
                down_interfaces.add(interface_name)

        # check
        collected_metrics = os_obj.statsd.current
        net_metrics_found = False
        for metric in collected_metrics['counter'].keys():
            if metric.startswith('system.net.') and '|' in metric:
                net_metrics_found = True
                metric_name, label_name = metric.split('|')
                assert_that(all_interfaces, has_item(label_name))
                assert_that(alive_interfaces, has_item(label_name))
                assert_that(down_interfaces, not_(has_item(label_name)))
        assert_that(net_metrics_found, equal_to(True))

    # This test doesn't really belong here...but it was the only test file that had a usable statsd object.
    def test_flush_aggregation(self):
        container = SystemManager()
        container._discover_objects()

        os_obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]
        collector = SystemMetricsCollector(object=os_obj)
        collector.collect()
        collector.collect()  # double collect is needed, because otherwise we do not collect metrics properly

        flush = collector.object.statsd.flush()

        for type in flush['metrics'].keys():  # e.g. 'timer', 'counter', 'gauge', 'average'
            for key in flush['metrics'][type].keys():
                # Make sure there is only one item per item in the flush.
                assert_that(len(flush['metrics'][type][key]), equal_to(1))
