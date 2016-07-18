# -*- coding: utf-8 -*-
import netifaces

from amplify.agent.collectors.system.meta.common import CommonSystemMetaCollector
from amplify.agent.common.context import context
from amplify.agent.common.util import subp
from amplify.agent.common.util.host import alive_interfaces


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class ContainerMetaCollector(CommonSystemMetaCollector):
    """
    Docker meta collector.
    """
    short_name = 'container_meta'

    def __init__(self, **kwargs):
        super(ContainerMetaCollector, self).__init__(**kwargs)

    def collect(self):
        meta = super(ContainerMetaCollector, self).collect()
        meta.update({
            'imagename': self.object.imagename,
            'container_type': context.container_type or 'None',
            'uname': None,
            'network': {
                'interfaces': [],
                'default': None
            }
        })

        for method in (
            self.uname,
            self.network,
        ):
            try:
                method(meta)
            except Exception as e:
                exception_name = e.__class__.__name__
                context.log.error('failed to collect meta %s due to %s' % (method.__name__, exception_name))
                context.log.debug('additional info:', exc_info=True)

        self.object.metad.meta(meta)

    @staticmethod
    def uname(meta):
        """
        Collects uname for the container, without a hostname
        :param meta: {} of meta
        """
        uname_out, _ = subp.call('uname -s -r -v -m -p')
        meta['uname'] = uname_out.pop(0)

    @staticmethod
    def network(meta):
        """
        network -- Docker network meta report leaves out IP addresses since they will be different per container.
        """

        # collect info for all the alive interfaces
        for interface in alive_interfaces():
            addresses = netifaces.ifaddresses(interface)
            interface_info = {
                'name': interface,
                'mac': addresses.get(netifaces.AF_LINK, [{}])[0].get('addr')  # Collect MAC address.
            }

            meta['network']['interfaces'].append(interface_info)

        # get default interface name
        netstat_out, _ = subp.call("netstat -nr | egrep -i '^0.0.0.0|default'", check=False)
        if len(netstat_out) and netstat_out[0]:
            first_matched_line = netstat_out[0]
            default_interface = first_matched_line.split(' ')[-1]
        elif len(meta['network']['interfaces']):
            default_interface = meta['network']['interfaces'][0]['name']
        else:
            default_interface = None

        meta['network']['default'] = default_interface
