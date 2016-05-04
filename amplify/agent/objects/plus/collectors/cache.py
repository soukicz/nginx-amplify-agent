# -*- coding: utf-8 -*-
from amplify.agent.common.context import context
from amplify.agent.objects.plus.abstract import PlusStatusCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class CacheCollector(PlusStatusCollector):

    short_name = 'plus_cache'

    def collect(self):
        tuples = self.gather_data()

        for data, stamp in tuples:
            for method in (
                self.cache_size,
                self.cache_metrics
            ):
                try:
                    method(data, stamp)
                except Exception as e:
                    exception_name = e.__class__.__name__
                    context.log.error(
                        'failed to collect server_zone data %s due to %s' %
                        (method.__name__, exception_name)
                    )
                    context.log.debug('additional info:', exc_info=True)

    def cache_size(self, data, stamp):
        self.object.statsd.gauge('plus.cache.size', data['size'], stamp=stamp)

    def cache_metrics(self, data, stamp):
        types = [
            'bypass',
            'expired',
            'hit',
            'miss',
            'revalidated',
            'stale',
            'updating'
        ]

        for label in types:
            data_bucket = data[label]

            counted_vars = {
                'plus.cache.%s' % label: data_bucket['responses'],
                'plus.cache.%s.bytes' % label: data_bucket['bytes'],
            }
            self.increment_counters(counted_vars, stamp)
