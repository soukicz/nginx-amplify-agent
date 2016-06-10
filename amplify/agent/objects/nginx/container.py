# -*- coding: utf-8 -*-
from amplify.agent.collectors.nginx.metrics import ContainerNginxMetricsCollector

from amplify.agent.collectors.nginx.meta.centos import ContainerNginxCentosMetaCollector
from amplify.agent.collectors.nginx.meta.deb import ContainerNginxDebianMetaCollector
from amplify.agent.collectors.nginx.meta.common import ContainerNginxMetaCollector
from amplify.agent.common.util import host
from amplify.agent.objects.nginx.object import CommonNginxObject


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class ContainerNginxObject(CommonNginxObject):
    type = 'container_nginx'

    def __init__(self, **kwargs):
        super(ContainerNginxObject, self).__init__(**kwargs)

        meta_collector_class = ContainerNginxMetaCollector
        if host.os_name() == 'linux':
            if host.linux_name() in ('ubuntu', 'debian'):
                meta_collector_class = ContainerNginxDebianMetaCollector
            elif host.linux_name() in ('centos',):
                meta_collector_class = ContainerNginxCentosMetaCollector

        # Collector setup...
        self.collectors = [
            meta_collector_class(
                object=self, interval=self.intervals['meta']
            ),
            ContainerNginxMetricsCollector(
                object=self, interval=self.intervals['metrics']
            )
        ]

        self._setup_config_collector()
        self._setup_access_logs()
        self._setup_error_logs()
