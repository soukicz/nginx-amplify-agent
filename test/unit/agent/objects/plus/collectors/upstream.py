# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.upstream import NginxUpstreamObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
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
                            }
                        ]
                    }
                }
            },
            1
        ))

        upstream_collector.collect()
        assert_that(upstream_collector.last_collect, equal_to(1))

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

        assert_that(counters['plus.upstream.health.checks'][0], equal_to([1, 22161]))
