# -*- coding: utf-8 -*-
import copy

from amplify.agent.common.context import context
from amplify.agent.collectors.abstract import AbstractMetricsCollector

from amplify.agent.collectors.plus.util.cache import CACHE_COLLECT_INDEX
from amplify.agent.collectors.plus.util.upstream import UPSTREAM_COLLECT_INDEX
from amplify.agent.collectors.plus.util.status_zone import STATUS_ZONE_COLLECT_INDEX

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusStatusCollector(AbstractMetricsCollector):
    """
    Common Plus status collector.  Collects data from parent object plus status cache.
    """
    short_name = "plus_status"
    collect_index = []

    def __init__(self, *args, **kwargs):
        super(PlusStatusCollector, self).__init__(*args, **kwargs)
        self.last_collect = None
        self.register(*self.collect_index)

    def gather_data(self, area=None, name=None):
        """
        Common data gathering method.  This method will open the stored Plus status JSON payload, navigate to the proper
        area (e.g. 'upstreams', 'server_zones', 'caches') and specific named object (e.g. 'http_cache') and grab the
        data structure.

        Only gathers data since last collect.

        :param area: Str
        :param name: Str
        :return: List Zipped tuples of data, stamp in order of oldest first.
        """
        if not area:
            area = '%ss' % self.object.type

        if not name:
            name = self.object.local_name

        data = []
        stamps = []

        try:
            for status, stamp in reversed(context.plus_cache[self.object.plus_status_internal_url]):
                if stamp > self.last_collect:
                    data.append(copy.deepcopy(status[area][name]))
                    stamps.append(stamp)
                else:
                    break  # We found the last collected payload
        except:
            context.default_log.error('%s collector gather data failed' % self.object.definition_hash, exc_info=True)
            raise

        if data and stamps:
            self.last_collect = stamps[0]

        return zip(reversed(data), reversed(stamps))  # Stamps are gathered here for future consideration.

    def collect(self):
        try:
            for data, stamp in self.gather_data():
                self.collect_from_data(data, stamp)
                try:
                    self.increment_counters()
                except Exception as e:
                    self.handle_exception(self.increment_counters, e)

        except Exception as e:
            self.handle_exception(self.gather_data, e)

    def collect_from_data(self, data, stamp):
        """
        Defines what plus status collectors should do with each (data, stamp) tuple returned from gather_data
        """
        super(PlusStatusCollector, self).collect(self, data, stamp)


class CacheCollector(PlusStatusCollector):
    short_name = 'plus_cache'
    collect_index = CACHE_COLLECT_INDEX


class StatusZoneCollector(PlusStatusCollector):
    short_name = 'plus_status_zone'
    collect_index = STATUS_ZONE_COLLECT_INDEX


class UpstreamCollector(PlusStatusCollector):
    short_name = 'plus_upstream'
    collect_index = UPSTREAM_COLLECT_INDEX

    def collect_from_data(self, data, stamp):
        """
        Aggregates all peer metrics as a single "upstream" entity.
        """
        # data.get('peers', data) is a workaround for supporting an old N+ format
        # http://nginx.org/en/docs/http/ngx_http_status_module.html#compatibility
        for peer in data.get('peers', data):
            super(UpstreamCollector, self).collect_from_data(peer, stamp)
        try:
            self.finalize_latest()
        except Exception as e:
            self.handle_exception(self.finalize_latest, e)
