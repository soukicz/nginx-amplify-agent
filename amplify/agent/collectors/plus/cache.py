# -*- coding: utf-8 -*-
from amplify.agent.collectors.plus.util import cache
from amplify.agent.common.context import context
from amplify.agent.collectors.plus.abstract import PlusStatusCollector

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class CacheCollector(PlusStatusCollector):

    short_name = 'plus_cache'

    def collect(self):
        try:
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
                            'failed to collect n+ cache metrics %s due to %s' %
                            (method.__name__, exception_name)
                        )
                        context.log.debug('additional info:', exc_info=True)
        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.error(
                'failed to collect n+ cache metrics due to %s' %
                exception_name
            )
            context.log.debug('additional info:', exc_info=True)

    def cache_size(self, data, stamp):
        cache.collect_cache_size(self, data, stamp)

    def cache_metrics(self, data, stamp):
        cache.collect_cache_metrics(self, data, stamp)
        self.increment_counters()
