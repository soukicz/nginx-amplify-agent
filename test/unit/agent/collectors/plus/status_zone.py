# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.status_zone import NginxStatusZoneObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class StatusZoneCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(StatusZoneCollectorTestCase, self).setup_method(method)
        context.plus_cache = None
        context._setup_plus_cache()

    def test_gather_data(self):
        status_zone = NginxStatusZoneObject(local_name='hg.nginx.org', parent_local_id='nginx123', root_uuid='root123')
        status_zone.plus_status_internal_url_cache = 'test_status'

        # Get the status_zone collector
        status_zone_collector = status_zone.collectors[-1]

        context.plus_cache.put('test_status', (
            {
                "server_zones": {
                    "hg.nginx.org": {
                        "processing": 2,
                        "requests": 131714,
                        "responses": {"1xx": 0, "2xx": 96763, "3xx": 2343, "4xx": 627, "5xx": 17631, "total": 117364},
                        "discarded": 14348,
                        "received": 35855843,
                        "sent": 1542591786
                    }
                }
            },
            1
        ))

        data = status_zone_collector.gather_data()

        assert_that(data, not_(equal_to([])))
        assert_that(data, has_length(1))

    def test_collect(self):
        status_zone = NginxStatusZoneObject(local_name='hg.nginx.org', parent_local_id='nginx123', root_uuid='root123')
        status_zone.plus_status_internal_url_cache = 'test_status'

        # Get the status_zone collector
        status_zone_collector = status_zone.collectors[-1]
        assert_that(status_zone_collector.last_collect, equal_to(None))

        context.plus_cache.put('test_status', (
            {
                "server_zones": {
                    "hg.nginx.org": {
                        "processing": 2,
                        "requests": 0,
                        "responses": {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "total": 0},
                        "discarded": 0,
                        "received": 0,
                        "sent": 0
                    }
                }
            },
            1
        ))

        context.plus_cache.put('test_status', (
            {
                "server_zones": {
                    "hg.nginx.org": {
                        "processing": 2,
                        "requests": 131714,
                        "responses": {"1xx": 0, "2xx": 96763, "3xx": 2343, "4xx": 627, "5xx": 17631, "total": 117364},
                        "discarded": 14348,
                        "received": 35855843,
                        "sent": 1542591786
                    }
                }
            },
            2
        ))

        status_zone_collector.collect()
        assert_that(status_zone_collector.last_collect, equal_to(2))

        assert_that(status_zone.statsd.current, not_(has_length(0)))

        assert_that(status_zone.statsd.current, has_key('counter'))
        counters = status_zone.statsd.current['counter']

        for key in (
            'plus.http.request.count',
            'plus.http.response.count',
            'plus.http.status.1xx',
            'plus.http.status.2xx',
            'plus.http.status.3xx',
            'plus.http.status.4xx',
            'plus.http.status.5xx',
            'plus.http.status.discarded',
            'plus.http.request.bytes_sent',
            'plus.http.request.bytes_rcvd'
        ):
            assert_that(counters, has_key(key))

        assert_that(counters['plus.http.status.discarded'][0], equal_to([2, 14348]))
