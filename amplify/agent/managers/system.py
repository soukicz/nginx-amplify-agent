# -*- coding: utf-8 -*-
from amplify.agent.common.context import context
from amplify.agent.managers.abstract import ObjectManager
from amplify.agent.objects.system.object import SystemObject

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class SystemManager(ObjectManager):
    """
    Manager for system objects
    Typically we have only one object since we run in a single OS
    """
    name = 'system_manager'
    type = 'system'
    types = ('system',)

    def _discover_objects(self):
        if not self.objects.find_all(types=self.types):
            data = dict(
                hostname=context.hostname,
                uuid=context.uuid
            )

            sys_object = SystemObject(data=data)
            self.objects.register(sys_object)
