# -*- coding: utf-8 -*-
from amplify.agent.collectors.plus.meta.common import PlusObjectMetaCollector
from amplify.agent.common.context import context
from amplify.agent.objects.abstract import AbstractObject

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusObject(AbstractObject):
    """
    Common Plus object.  Supervisor for collectors and data client bucket.
    """
    type_template = 'nginx_%s'
    type = 'plus'

    def __init__(self, **kwargs):
        super(PlusObject, self).__init__(**kwargs)

        # Reset intervals to standardize intervals for all Plus objects
        self.intervals = context.app_config['containers']['plus']['poll_intervals']

        # TODO: Refactor root_uuid as a general property that queries root object from context. Perhaps cache like local_id.
        self.root_uuid = self.data.get('root_uuid') or (context.objects.root_object.uuid if context.objects.root_object else None)
        self.parent_local_id = self.data['parent_local_id']
        self.local_name = self.data['local_name']

        self.plus_status_internal_url_cache = None

        self.collectors = [
            PlusObjectMetaCollector(object=self, interval=self.intervals['meta'])
        ]

    @property
    def plus_status_internal_url(self):
        """
        Property that tracks back the plus_status_internal_url from the parent nginx object and caching it.  This cache
        works because child objects are stopped and unregistered when nginx objects are modified (restarted, etc.).
        """
        if not self.plus_status_internal_url_cache:
            parent_obj = context.objects.find_parent(obj_id=self.id)
            if parent_obj:
                self.plus_status_internal_url_cache = parent_obj.plus_status_internal_url
        return self.plus_status_internal_url_cache

    @property
    def definition(self):
        return {'type': self.type_template % self.type, 'local_id': self.local_id, 'root_uuid': self.root_uuid}

    @property
    def local_id_args(self):
        return self.parent_local_id, self.type, self.local_name
