# -*- coding: utf-8 -*-
from amplify.agent.common.context import context

from amplify.agent.objects.abstract import AbstractObject


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class CommonSystemObject(AbstractObject):
    type = 'common_system'

    def __init__(self, **kwargs):
        super(CommonSystemObject, self).__init__(**kwargs)

        # Have to override intervals here because new container sub objects.
        self.intervals = context.app_config['containers'].get('system', {}).get('poll_intervals', {'default': 10})

        self.uuid = self.data['uuid']

    @property
    def definition(self):
        return None
