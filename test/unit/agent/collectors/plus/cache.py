# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.object import NginxCacheObject

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class CacheCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(CacheCollectorTestCase, self).setup_method(method)
        context.plus_cache = None
        context._setup_plus_cache()

    def test_gather_data(self):
        cache_obj = NginxCacheObject(local_name='http_cache', parent_local_id='nginx123', root_uuid='root123')
        # Do a quick override of plus_status_internal_url_cache
        cache_obj.plus_status_internal_url_cache = 'test_status'

        # Get the cache collector
        cache_collector = cache_obj.collectors[-1]

        # Insert some dummy data
        context.plus_cache.put('test_status', (
            {
                "caches": {
                    "http_cache": {
                        "size": 434008064,
                        "max_size": 536870912,
                        "cold": False,
                        "hit": {
                            "responses": 54893,
                            "bytes": 641803539
                        },
                        "stale": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "updating": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "revalidated": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "miss": {
                            "responses": 192066,
                            "bytes": 8238562837,
                            "responses_written": 113330,
                            "bytes_written": 3495778334
                        },
                        "expired": {
                            "responses": 14182,
                            "bytes": 470184322,
                            "responses_written": 12213,
                            "bytes_written": 452070350
                        },
                        "bypass": {
                            "responses": 88963,
                            "bytes": 674403658,
                            "responses_written": 88962,
                            "bytes_written": 674402934
                        }
                    }
                }
            },
            1
        ))

        data = cache_collector.gather_data()

        assert_that(data, not_(equal_to([])))
        assert_that(data, has_length(1))

    def test_collect(self):
        cache_obj = NginxCacheObject(local_name='http_cache', parent_local_id='nginx123', root_uuid='root123')
        # Do a quick override of plus_status_internal_url_cache
        cache_obj.plus_status_internal_url_cache = 'test_status'

        # Get the cache collector
        cache_collector = cache_obj.collectors[-1]
        assert_that(cache_collector.last_collect, equal_to(None))

        # Insert some dummy data
        context.plus_cache.put('test_status', (
            {
                "caches": {
                    "http_cache": {
                        "size": 0,
                        "max_size": 0,
                        "cold": False,
                        "hit": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "stale": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "updating": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "revalidated": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "miss": {
                            "responses": 0,
                            "bytes": 0,
                            "responses_written": 0,
                            "bytes_written": 0
                        },
                        "expired": {
                            "responses": 0,
                            "bytes": 0,
                            "responses_written": 0,
                            "bytes_written": 0
                        },
                        "bypass": {
                            "responses": 0,
                            "bytes": 0,
                            "responses_written": 0,
                            "bytes_written": 0
                        }
                    }
                }
            },
            1
        ))

        context.plus_cache.put('test_status', (
            {
                "caches": {
                    "http_cache": {
                        "size": 434008064,
                        "max_size": 536870912,
                        "cold": False,
                        "hit": {
                            "responses": 54893,
                            "bytes": 641803539
                        },
                        "stale": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "updating": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "revalidated": {
                            "responses": 0,
                            "bytes": 0
                        },
                        "miss": {
                            "responses": 192066,
                            "bytes": 8238562837,
                            "responses_written": 113330,
                            "bytes_written": 3495778334
                        },
                        "expired": {
                            "responses": 14182,
                            "bytes": 470184322,
                            "responses_written": 12213,
                            "bytes_written": 452070350
                        },
                        "bypass": {
                            "responses": 88963,
                            "bytes": 674403658,
                            "responses_written": 88962,
                            "bytes_written": 674402934
                        }
                    }
                }
            },
            2
        ))

        cache_collector.collect()
        assert_that(cache_collector.last_collect, equal_to(2))

        assert_that(cache_obj.statsd.current, not_(has_length(0)))

        assert_that(cache_obj.statsd.current, has_key('counter'))
        counters = cache_obj.statsd.current['counter']

        for key in (
            'plus.cache.revalidated.bytes',
            'plus.cache.expired',
            'plus.cache.updating.bytes',
            'plus.cache.miss',
            'plus.cache.bypass.bytes',
            'plus.cache.revalidated',
            'plus.cache.updating',
            'plus.cache.hit.bytes',
            'plus.cache.stale',
            'plus.cache.stale.bytes',
            'plus.cache.hit',
            'plus.cache.expired.bytes',
            'plus.cache.bypass',
            'plus.cache.miss.bytes'
        ):
            assert_that(counters, has_key(key))

        assert_that(counters['plus.cache.hit'][0], equal_to([2, 54893]))
        assert_that(counters['plus.cache.hit.bytes'][0], equal_to([2, 641803539]))
