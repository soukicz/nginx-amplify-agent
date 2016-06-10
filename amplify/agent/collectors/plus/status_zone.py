# -*- coding: utf-8 -*-
from amplify.agent.collectors.plus.util import status_zone
from amplify.agent.common.context import context
from amplify.agent.collectors.plus.abstract import PlusStatusCollector

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class StatusZoneCollector(PlusStatusCollector):

    short_name = 'plus_status_zone'

    def collect(self):
        try:
            tuples = self.gather_data()

            for data, stamp in tuples:
                for method in (
                    self.http_request,
                    self.http_responses,
                    self.http_discarded,
                    self.http_bytes
                ):
                    try:
                        method(data, stamp)
                    except Exception as e:
                        exception_name = e.__class__.__name__
                        context.log.error(
                            'failed to collect n+ status_zone metrics %s due to %s' %
                            (method.__name__, exception_name)
                        )
                        context.log.debug('additional info:', exc_info=True)
        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.error(
                'failed to collect n+ status_zone metrics due to %s' %
                exception_name
            )
            context.log.debug('additional info:', exc_info=True)

    def http_request(self, data, stamp):
        status_zone.collect_http_request(self, data, stamp)
        self.increment_counters()

    def http_responses(self, data, stamp):
        status_zone.collect_http_responses(self, data, stamp)
        self.increment_counters()

    def http_discarded(self, data, stamp):
        status_zone.collect_http_discarded(self, data, stamp)
        self.increment_counters()

    def http_bytes(self, data, stamp):
        status_zone.collect_http_bytes(self, data, stamp)
        self.increment_counters()
