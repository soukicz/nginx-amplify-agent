# -*- coding: utf-8 -*-
from amplify.agent.objects.plus.abstract import PlusObject
from amplify.agent.objects.plus.collectors.upstream import UpstreamCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class NginxUpstreamObject(PlusObject):
    type = 'upstream'

    def __init__(self, *args, **kwargs):
        super(NginxUpstreamObject, self).__init__(**kwargs)

        self.collectors.append(UpstreamCollector(object=self, interval=self.intervals['metrics']))
