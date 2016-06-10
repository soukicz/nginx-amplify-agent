# -*- coding: utf-8 -*-
from amplify.agent.common.context import context
from amplify.agent.common.util import host
from amplify.agent.collectors.system.meta.centos import DockerCentosMetaCollector
from amplify.agent.collectors.system.meta.container import ContainerMetaCollector
from amplify.agent.collectors.system.metrics import SystemMetricsCollector
from amplify.agent.objects.system.common import CommonSystemObject

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class ContainerSystemObject(CommonSystemObject):
    type = 'container'

    def __init__(self, **kwargs):
        super(ContainerSystemObject, self).__init__(**kwargs)

        self.imagename = self.data['imagename']

        meta_collector_class = ContainerMetaCollector
        if host.os_name() == 'linux' and host.linux_name() in ('centos',):
            meta_collector_class = DockerCentosMetaCollector

        self.collectors = [
            meta_collector_class(object=self, interval=self.intervals['meta']),
            SystemMetricsCollector(object=self, interval=self.intervals['metrics'])
        ]

    @property
    def definition(self):
        return {'type': self.type, 'imagename': self.imagename, 'uuid': self.uuid}

    def start(self):
        if not self.running and not context.cloud_restart:
            # log agent started event
            context.log.info(
                'agent started, version=%s pid=%s uuid=%s imagename=%s' %
                (context.version, context.pid, self.uuid, self.imagename)
            )

        super(ContainerSystemObject, self).start()

    def stop(self):
        if not context.cloud_restart:
            # log agent stopped event
            context.log.info(
                'agent stopped, version=%s pid=%s uuid=%s imagename=%s' %
                (context.version, context.pid, self.uuid, self.imagename)
            )

        super(ContainerSystemObject, self).stop()
