# -*- coding: utf-8 -*-
from amplify.agent.common.context import context
from amplify.agent.objects.plus.abstract import PlusStatusCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class StatusZoneCollector(PlusStatusCollector):

    short_name = 'plus_status_zone'

    def collect(self):
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
                        'failed to collect status_zone data %s due to %s' %
                        (method.__name__, exception_name)
                    )
                    context.log.debug('additional info:', exc_info=True)

    def http_request(self, data, stamp):
        counted_vars = {
            'plus.http.request.count': data['requests']
        }
        self.increment_counters(counted_vars, stamp)

    def http_responses(self, data, stamp):
        responses = data['responses']

        counted_vars = {
            'plus.http.response.count': responses['total'],
            'plus.http.status.1xx': responses['1xx'],
            'plus.http.status.2xx': responses['2xx'],
            'plus.http.status.3xx': responses['3xx'],
            'plus.http.status.4xx': responses['4xx'],
            'plus.http.status.5xx': responses['5xx']
        }
        self.increment_counters(counted_vars, stamp)

    def http_discarded(self, data, stamp):
        counted_vars = {
            'plus.http.status.discarded': data['discarded']
        }
        self.increment_counters(counted_vars, stamp)

    def http_bytes(self, data, stamp):
        counted_vars = {
            'plus.http.request.bytes_sent': data['sent'],
            'plus.http.request.bytes_rcvd': data['received']
        }
        self.increment_counters(counted_vars, stamp)
