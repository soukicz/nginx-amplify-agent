# -*- coding: utf-8 -*-
import copy


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


def collect_cache_size(collector, data, stamp):
    collector.object.statsd.gauge('plus.cache.size', data['size'], stamp=stamp)


def collect_cache_metrics(collector, data, stamp):
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

        collector.aggregate_counters(copy.deepcopy(counted_vars), stamp=stamp)


CACHE_COLLECT_INDEX = [
    collect_cache_size,
    collect_cache_metrics,
]
