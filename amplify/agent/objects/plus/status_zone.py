# -*- coding: utf-8 -*-
from amplify.agent.collectors.plus.status_zone import StatusZoneCollector
from amplify.agent.objects.plus.abstract import PlusObject

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class NginxStatusZoneObject(PlusObject):
    type = 'server_zone'  # Needs to match the plus status JSON for collector's .gather_data() method.

    def __init__(self, *args, **kwargs):
        super(NginxStatusZoneObject, self).__init__(**kwargs)

        self.collectors.append(StatusZoneCollector(object=self, interval=self.intervals['metrics']))

    @property
    def definition(self):
        return {'type': self.type_template % 'status_zone', 'local_id': self.local_id, 'root_uuid': self.root_uuid}
