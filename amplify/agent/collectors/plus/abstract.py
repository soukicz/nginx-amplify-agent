# -*- coding: utf-8 -*-
import copy
import time

from amplify.agent.common.context import context
from amplify.agent.collectors.abstract import AbstractCollector

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusStatusCollector(AbstractCollector):
    """
    Common Plus status collector.  Collects data from parent object plus status cache.
    """
    short_name = "plus_status"

    def __init__(self, *args, **kwargs):
        super(PlusStatusCollector, self).__init__(*args, **kwargs)
        self.last_collect = None
        self.now = None
        self._set_now()

    def _set_now(self):
        self.now = time.time()

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
            self._set_now()
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
