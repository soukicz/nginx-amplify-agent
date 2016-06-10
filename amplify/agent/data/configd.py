# -*- coding: utf-8 -*-
import copy

from amplify.agent.data.abstract import CommonDataClient


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class ConfigdClient(CommonDataClient):
    def __init__(self, *args, **kwargs):
        # Import context as a class object to avoid circular import on statsd.  This could be refactored later.
        from amplify.agent.common.context import context
        self.context = context

        super(ConfigdClient, self).__init__(*args, **kwargs)

    def config(self, payload, checksum):
        self.current = {
            'data': payload,
            'checksum': checksum,
        }

    def flush(self):
        if not self.current:
            return {'object': self.object.definition}
            # Always return object definitions in case there are children and the definition is required to attached

        delivery = copy.deepcopy(self.current)
        self.current = {}
        return {
            'object': self.object.definition,
            'config': delivery,
            'agent': self.context.version
        }
