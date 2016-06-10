# -*- coding: utf-8 -*-
from amplify.agent.collectors.plus.util import upstream
from amplify.agent.common.context import context
from amplify.agent.collectors.plus.abstract import PlusStatusCollector

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class UpstreamCollector(PlusStatusCollector):

    short_name = 'plus_upstream'

    def collect(self):
        try:
            tuples = self.gather_data()

            for data, stamp in tuples:
                # workaround for supporting old N+ format
                # http://nginx.org/en/docs/http/ngx_http_status_module.html#compatibility
                peers = data['peers'] if 'peers' in data else data

                for peer in peers:
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
                                'failed to collect n+ upstream peer metrics %s due to %s' %
                                (method.__name__, exception_name)
                            )
                            context.log.debug('additional info:', exc_info=True)

                try:
                    self.increment_counters()
                except Exception as e:
                    exception_name = e.__class__.__name__
                    context.log.error(
                        'failed to increment n+ upstream counters due to %s' %
                        exception_name
                    )
                    context.log.debug('additional info:', exc_info=True)
        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.error(
                'failed to collect n+ upstream metrics due to %s' %
                exception_name
            )
            context.log.debug('additional info:', exc_info=True)

    def active_connections(self, data, stamp):
        upstream.collect_active_connections(self, data, stamp)

    def upstream_request(self, data, stamp):
        upstream.collect_upstream_request(self, data, stamp)

    def upstream_header_time(self, data, stamp):
        upstream.collect_upstream_header_time(self, data, stamp)

    def upstream_response_time(self, data, stamp):
        upstream.collect_upstream_response_time(self, data, stamp)

    def upstream_responses(self, data, stamp):
        upstream.collect_upstream_responses(self, data, stamp)

    def upstream_bytes(self, data, stamp):
        upstream.collect_upstream_bytes(self, data, stamp)

    def upstream_fails(self, data, stamp):
        upstream.collect_upstream_fails(self, data, stamp)

    def upstream_health_checks(self, data, stamp):
        upstream.collect_upstream_health_checks(self, data, stamp)

    def upstream_queue(self, data, stamp):
        upstream.collect_upstream_queue(self, data, stamp)
