# -*- coding: utf-8 -*-
from amplify.agent.common.context import context
from amplify.agent.collectors.abstract import AbstractCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusObjectMetaCollector(AbstractCollector):

    short_name = 'plus_meta'

    def collect(self):
        # Note agent gets added currently in by amplify.agent.data.metad
        meta = {
            'type': self.object.type_template % (self.object.type if self.object.type != 'server_zone' else 'status_zone'),
            'local_name': self.object.local_name,
            'local_id': self.object.local_id,
            'root_uuid': None,
            'hostname': context.hostname if not context.app_config['credentials']['imagename']
                else context.app_config['credentials']['imagename'],
            'version': None,
            'warnings': []
        }

        for method in (
            self.root_uuid,
            self.version
        ):
            try:
                method(meta)
            except Exception as e:
                exception_name = e.__class__.__name__
                context.log.error(
                    'failed to collect meta %s due to %s' %
                    (method.__name__, exception_name)
                )
                context.log.debug('additional info:', exc_info=True)

        self.object.metad.meta(meta)

    def root_uuid(self, meta):
        meta['root_uuid'] = self.object.root_uuid or context.objects.root_object.uuid

    def version(self, meta):
        parent_obj = context.objects.find_parent(obj=self.object)
        meta['version'] = parent_obj.version
