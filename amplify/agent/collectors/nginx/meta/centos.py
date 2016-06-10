# -*- coding: utf-8 -*-
from amplify.agent.collectors.nginx.meta.common import (
    NginxCommonMetaCollector, NginxMetaCollector, ContainerNginxMetaCollector
)
from amplify.agent.common.util import subp

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class CommonNginxCentosMetaCollector(NginxCommonMetaCollector):
    """
    Redefines package search method
    """

    def find_packages(self, meta):
        """
        Find a package with running binary
        """
        package, version = None, None

        rpm_qf_out, rpm_qf_err = subp.call(
            'rpm -qf %s ' % self.object.bin_path + '--queryformat="%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}' + '\\n"',
            check=False
        )

        if rpm_qf_out and rpm_qf_out[0]:
            package, version = rpm_qf_out[0].split(' ')

        if rpm_qf_err:
            if 'is not owned by' in rpm_qf_err[0]:
                meta['warnings'].append('self-made binary, is not from any nginx package')

        if not package:
            return

        meta['packages'] = {package: version}


class NginxCentosMetaCollector(CommonNginxCentosMetaCollector, NginxMetaCollector):
    pass


class ContainerNginxCentosMetaCollector(CommonNginxCentosMetaCollector, ContainerNginxMetaCollector):
    pass
