# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.upstream import NginxUpstreamObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard", "Arie van Luttikhuizen"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class UpstreamCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(UpstreamCollectorTestCase, self).setup_method(method)
        context.plus_cache = None
        context._setup_plus_cache()

    def test_gather_data(self):
        upstream = NginxUpstreamObject(local_name='trac-backend', parent_local_id='nginx123', root_uuid='root123')
        upstream.plus_status_internal_url_cache = 'test_status'

        # Get the upstream collector
        upstream_collector = upstream.collectors[-1]

        context.plus_cache.put('test_status', (
            {
                "upstreams": {
                    "trac-backend": {
                        "peers": [
                            {
                                "id": 0,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 0,
                                "requests": 50411,
                                "responses": {"1xx": 0, "2xx": 49034, "3xx": 507, "4xx": 864, "5xx": 6, "total": 50411},
                                "sent": 22594151,
                                "received": 2705341138,
                                "fails": 0,
                                "unavail": 0,
                                "health_checks": {"checks": 22161, "fails": 0, "unhealthy": 0, "last_passed": True},
                                "downtime": 0,
                                "downstart": 0,
                                "selected": 1456184367000
                            }
                        ]
                    }
                }
            },
            1
        ))

        data = upstream_collector.gather_data()

        assert_that(data, not_(equal_to([])))
        assert_that(data, has_length(1))

    def test_collect(self):
        upstream = NginxUpstreamObject(local_name='trac-backend', parent_local_id='nginx123', root_uuid='root123')
        upstream.plus_status_internal_url_cache = 'test_status'

        # Get the upstream collector
        upstream_collector = upstream.collectors[-1]
        assert_that(upstream_collector.last_collect, equal_to(None))

        context.plus_cache.put('test_status', (
            {
                "upstreams": {
                    "trac-backend": {
                        "peers": [
                            {
                                "id": 0,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 0,
                                "requests": 0,
                                "responses": {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "total": 0},
                                "sent": 0,
                                "received": 0,
                                "fails": 0,
                                "unavail": 0,
                                "health_checks": {"checks": 0, "fails": 0, "unhealthy": 0, "last_passed": True},
                                "downtime": 0,
                                "downstart": 0,
                                "selected": 1456184367000
                            }
                        ]
                    }
                }
            },
            1
        ))

        context.plus_cache.put('test_status', (
            {
                "upstreams": {
                    "trac-backend": {
                        "peers": [
                            {
                                "id": 0,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 0,
                                "requests": 50411,
                                "responses": {"1xx": 0, "2xx": 49034, "3xx": 507, "4xx": 864, "5xx": 6, "total": 50411},
                                "sent": 22594151,
                                "received": 2705341138,
                                "fails": 0,
                                "unavail": 0,
                                "health_checks": {"checks": 22161, "fails": 0, "unhealthy": 0, "last_passed": True},
                                "downtime": 0,
                                "downstart": 0,
                                "selected": 1456184367000
                            },
                            {
                                "id": 0,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 0,
                                "requests": 50412,
                                "responses": {"1xx": 0, "2xx": 49034, "3xx": 507, "4xx": 864, "5xx": 6, "total": 50411},
                                "sent": 22594151,
                                "received": 2705341138,
                                "fails": 0,
                                "unavail": 0,
                                "health_checks": {"checks": 22160, "fails": 0, "unhealthy": 0, "last_passed": True},
                                "downtime": 0,
                                "downstart": 0,
                                "selected": 1456184367000
                            }
                        ]
                    }
                }
            },
            2
        ))

        upstream_collector.collect()
        assert_that(upstream_collector.last_collect, equal_to(2))

        assert_that(upstream.statsd.current, not_(has_length(0)))

        assert_that(upstream.statsd.current, has_key('counter'))
        counters = upstream.statsd.current['counter']

        for key in (
            'plus.upstream.fails.count', 'plus.upstream.bytes_sent', 'plus.upstream.bytes_rcvd',
            'plus.upstream.status.1xx', 'plus.upstream.status.5xx', 'plus.upstream.health.fails',
            'plus.upstream.status.2xx', 'plus.upstream.health.unhealthy', 'plus.upstream.request.count',
            'plus.upstream.health.checks', 'plus.upstream.response.count', 'plus.upstream.unavail.count',
            'plus.upstream.status.3xx', 'plus.upstream.status.4xx'
        ):
            assert_that(counters, has_key(key))

        assert_that(counters['plus.upstream.health.checks'][0], equal_to([2, 44321]))

    def test_collect_negative(self):
        upstream = NginxUpstreamObject(local_name='trac-backend', parent_local_id='nginx123', root_uuid='root123')
        upstream.plus_status_internal_url_cache = 'test_status'

        # Get the upstream collector
        upstream_collector = upstream.collectors[-1]
        assert_that(upstream_collector.last_collect, equal_to(None))

        # Put some data
        context.plus_cache.put('test_status', (
            {
                "upstreams": {
                    "trac-backend": {
                        "peers": [
                            {
                                "id": 0,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 1,
                                "requests": 50411,
                                "responses": {"1xx": 1, "2xx": 49034, "3xx": 507, "4xx": 864, "5xx": 6,
                                              "total": 50411},
                                "sent": 22594151,
                                "received": 2705341138,
                                "fails": 1,
                                "unavail": 1,
                                "health_checks": {"checks": 22161, "fails": 1, "unhealthy": 1, "last_passed": True},
                                "downtime": 1,
                                "downstart": 1,
                                "selected": 1456184367000
                            },
                            {
                                "id": 1,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 0,
                                "requests": 50412,
                                "responses": {"1xx": 0, "2xx": 49034, "3xx": 507, "4xx": 864, "5xx": 6,
                                              "total": 50411},
                                "sent": 22594151,
                                "received": 2705341138,
                                "fails": 0,
                                "unavail": 0,
                                "health_checks": {"checks": 22160, "fails": 0, "unhealthy": 0, "last_passed": True},
                                "downtime": 0,
                                "downstart": 0,
                                "selected": 1456184367000
                            }
                        ]
                    }
                }
            },
            1
        ))

        # Put some data where counters are reset for some reason/peer also removed
        context.plus_cache.put('test_status', (
            {
                "upstreams": {
                    "trac-backend": {
                        "peers": [
                            {
                                "id": 0,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 0,
                                "requests": 0,
                                "responses": {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "total": 0},
                                "sent": 0,
                                "received": 0,
                                "fails": 0,
                                "unavail": 0,
                                "health_checks": {"checks": 0, "fails": 0, "unhealthy": 0, "last_passed": True},
                                "downtime": 0,
                                "downstart": 0,
                                "selected": 1456184367000
                            }
                        ]
                    }
                }
            },
            2
        ))

        upstream_collector.collect()
        assert_that(upstream_collector.last_collect, equal_to(2))

        assert_that(upstream.statsd.current, not_(has_length(0)))

        # Check that no counters were reported because they are all negative
        assert_that(upstream.statsd.current, not_(has_key('counter')))

        # Put some data back after "reset"
        context.plus_cache.put('test_status', (
            {
                "upstreams": {
                    "trac-backend": {
                        "peers": [
                            {
                                "id": 0,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 0,
                                "requests": 50411,
                                "responses": {"1xx": 0, "2xx": 49034, "3xx": 507, "4xx": 864, "5xx": 6,
                                              "total": 50411},
                                "sent": 22594151,
                                "received": 2705341138,
                                "fails": 0,
                                "unavail": 0,
                                "health_checks": {"checks": 22161, "fails": 0, "unhealthy": 0, "last_passed": True},
                                "downtime": 0,
                                "downstart": 0,
                                "selected": 1456184367000
                            },
                            {
                                "id": 0,
                                "server": "10.0.0.1:8080",
                                "backup": False,
                                "weight": 1,
                                "state": "up",
                                "active": 0,
                                "requests": 50412,
                                "responses": {"1xx": 0, "2xx": 49034, "3xx": 507, "4xx": 864, "5xx": 6,
                                              "total": 50411},
                                "sent": 22594151,
                                "received": 2705341138,
                                "fails": 0,
                                "unavail": 0,
                                "health_checks": {"checks": 22160, "fails": 0, "unhealthy": 0, "last_passed": True},
                                "downtime": 0,
                                "downstart": 0,
                                "selected": 1456184367000
                            }
                        ]
                    }
                }
            },
            3
        ))

        # Check to see collect happened after skipping negative
        upstream_collector.collect()
        assert_that(upstream_collector.last_collect, equal_to(3))

        assert_that(upstream.statsd.current, not_(has_length(0)))

        assert_that(upstream.statsd.current, has_key('counter'))
        counters = upstream.statsd.current['counter']

        for key in (
                'plus.upstream.fails.count', 'plus.upstream.bytes_sent', 'plus.upstream.bytes_rcvd',
                'plus.upstream.status.1xx', 'plus.upstream.status.5xx', 'plus.upstream.health.fails',
                'plus.upstream.status.2xx', 'plus.upstream.health.unhealthy', 'plus.upstream.request.count',
                'plus.upstream.health.checks', 'plus.upstream.response.count', 'plus.upstream.unavail.count',
                'plus.upstream.status.3xx', 'plus.upstream.status.4xx'
        ):
            assert_that(counters, has_key(key))

        assert_that(counters['plus.upstream.health.checks'][0], equal_to([3, 44321]))

    def test_upstream_peer_count(self):
        upstream = NginxUpstreamObject(local_name='trac-backend', parent_local_id='nginx123', root_uuid='root123')
        upstream.plus_status_internal_url_cache = 'test_status'
        upstream_collector = upstream.collectors[-1]
        assert_that(upstream_collector.last_collect, equal_to(None))

        test_peer = {
             "id": 0,
             "server": "10.0.0.1:8080",
             "backup": False,
             "weight": 1,
             "state": "up",
             "active": 0,
             "requests": 0,
             "responses": {"1xx": 100, "2xx": 200, "3xx": 300, "4xx": 400, "5xx": 500, "total": 1500},
             "sent": 0,
             "received": 0,
             "fails": 0,
             "unavail": 0,
             "health_checks": {"checks": 0, "fails": 0, "unhealthy": 0, "last_passed": True},
             "downtime": 0,
             "downstart": 0,
             "selected": 1456184367000
        }

        gauges = upstream.statsd.current['gauge']

        # drop data with two different peer counts into the plus_cache, then collect the data
        context.plus_cache.put('test_status', ({"upstreams": {"trac-backend": {"peers": [test_peer] * 1}}}, 3))
        context.plus_cache.put('test_status', ({"upstreams": {"trac-backend": {"peers": [test_peer] * 2}}}, 14))
        upstream_collector.collect()
        assert_that(gauges['plus.upstream.peer.count'], equal_to([(14, 2)]))

        # shows that the metric works even if the plus_cache data has been collected before
        context.plus_cache.put('test_status', ({"upstreams": {"trac-backend": {"peers": [test_peer] * 4}}}, 16))
        context.plus_cache.put('test_status', ({"upstreams": {"trac-backend": {"peers": [test_peer] * 2}}}, 20))
        context.plus_cache.put('test_status', ({"upstreams": {"trac-backend": {"peers": [test_peer] * 8}}}, 99))
        upstream_collector.collect()
        assert_that(gauges['plus.upstream.peer.count'], equal_to([(99, 8)]))

        # shows that only peers with state == 'up' count towards upstream.peer.count
        test_peer['state'] = 'down'
        context.plus_cache.put('test_status', ({"upstreams": {"trac-backend": {"peers": [test_peer] * 5}}}, 110))
        upstream_collector.collect()
        assert_that(gauges['plus.upstream.peer.count'], equal_to([(99, 8)]))  # doesn't change because state is 'down'

        test_peer['state'] = 'up'
        context.plus_cache.put('test_status', ({"upstreams": {"trac-backend": {"peers": [test_peer] * 2}}}, 120))
        upstream_collector.collect()
        assert_that(gauges['plus.upstream.peer.count'], equal_to([(120, 2)]))
