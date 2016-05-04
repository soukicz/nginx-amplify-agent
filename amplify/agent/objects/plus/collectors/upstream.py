# -*- coding: utf-8 -*-
from amplify.agent.common.context import context
from amplify.agent.objects.plus.abstract import PlusStatusCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class UpstreamCollector(PlusStatusCollector):

    short_name = 'plus_upstream'

    def collect(self):
        tuples = self.gather_data()

        for data, stamp in tuples:
            for peer in data['peers']:
                # This loop will aggregate all peer metrics as a single "upstream" entity.
                for method in (
                    self.active_connections,
                    self.upstream_request,
                    self.upstream_header_time,
                    self.upstream_response_time,
                    self.upstream_responses,
                    self.upstream_bytes,
                    self.upstream_fails,
                    self.upstream_health_checks,
                    self.upstream_queue,
                ):
                    try:
                        method(peer, stamp)
                    except Exception as e:
                        exception_name = e.__class__.__name__
                        context.log.error(
                            'failed to collect upstream data %s due to %s' %
                            (method.__name__, exception_name)
                        )
                        context.log.debug('additional info:', exc_info=True)

    def active_connections(self, data, stamp):
        self.object.statsd.gauge('plus.upstream.conn.active', data['active'], stamp=stamp)

    def upstream_request(self, data, stamp):
        counted_vars = {
            'plus.upstream.request.count': data['requests']
        }
        self.increment_counters(counted_vars, stamp)

    def upstream_header_time(self, data, stamp):
        if 'header_time' in data:
            time_in_seconds = float(data['header_time']) / 1000
            self.object.statsd.timer('plus.upstream.header.time', float('%.3f' % time_in_seconds), stamp=stamp)

    def upstream_response_time(self, data, stamp):
        if 'response_time' in data:
            time_in_seconds = float(data['response_time']) / 1000
            self.object.statsd.timer('plus.upstream.response.time', float('%.3f' % time_in_seconds), stamp=stamp)

    def upstream_responses(self, data, stamp):
        responses = data['responses']

        counted_vars = {
            'plus.upstream.response.count': responses['total'],
            'plus.upstream.status.1xx': responses['1xx'],
            'plus.upstream.status.2xx': responses['2xx'],
            'plus.upstream.status.3xx': responses['3xx'],
            'plus.upstream.status.4xx': responses['4xx'],
            'plus.upstream.status.5xx': responses['5xx']
        }
        self.increment_counters(counted_vars, stamp)

    def upstream_bytes(self, data, stamp):
        counted_vars = {
            'plus.upstream.bytes_sent': data['sent'],
            'plus.upstream.bytes_rcvd': data['received']
        }
        self.increment_counters(counted_vars, stamp)

    def upstream_fails(self, data, stamp):
        counted_vars = {
            'plus.upstream.fails.count': data['fails'],
            'plus.upstream.unavail.count': data['unavail']
        }
        self.increment_counters(counted_vars, stamp)

    def upstream_health_checks(self, data, stamp):
        health_checks = data['health_checks']

        counted_vars = {
            'plus.upstream.health.checks': health_checks['checks'],
            'plus.upstream.health.fails': health_checks['fails'],
            'plus.upstream.health.unhealthy': health_checks['unhealthy']
        }
        self.increment_counters(counted_vars, stamp)

    def upstream_queue(self, data, stamp):
        queue = data.get('queue')

        if queue:
            self.object.statsd.gauge('plus.upstream.queue.size', queue['size'], stamp=stamp)

            counted_vars = {
                'plus.upstream.queue.overflows': queue['overflows'],
            }
            self.increment_counters(counted_vars, stamp)
