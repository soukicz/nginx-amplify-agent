# -*- coding: utf-8 -*-
import netifaces

import netaddr
import psutil

from amplify.agent.collectors.system.meta.common import CommonSystemMetaCollector
from amplify.agent.common.context import context
from amplify.agent.common.util import subp
from amplify.agent.common.util.ec2 import AmazonEC2
from amplify.agent.common.util.host import alive_interfaces


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class SystemMetaCollector(CommonSystemMetaCollector):
    """
    OS meta collector
    Linux only right now
    """
    short_name = 'sys_meta'

    def __init__(self, **kwargs):
        super(SystemMetaCollector, self).__init__(**kwargs)

        self.hostname = self.object.data['hostname']
        self.ec2_metadata = AmazonEC2.read_meta()

    def collect(self):
        meta = super(SystemMetaCollector, self).collect()
        meta.update({
            'boot': int(psutil.boot_time()) * 1000,
            'hostname': self.hostname,
            'network': {
                'interfaces': [],
                'default': None
            },
            'ec2': None,
        })

        for method in (
            self.network,
            self.ec2
        ):
            try:
                method(meta)
            except Exception as e:
                exception_name = e.__class__.__name__
                context.log.error('failed to collect meta %s due to %s' % (method.__name__, exception_name))
                context.log.debug('additional info:', exc_info=True)

        self.object.metad.meta(meta)

    @staticmethod
    def network(meta):
        """ network """

        # collect info for all the alive interfaces
        for interface in alive_interfaces():
            addresses = netifaces.ifaddresses(interface)
            interface_info = {
                'name': interface
            }

            # collect ipv4 and ipv6 addresses
            for proto, key in {
                'ipv4': netifaces.AF_INET,
                'ipv6': netifaces.AF_INET6
            }.iteritems():
                # get the first address
                protocol_data = addresses.get(key, [{}])[0]
                if protocol_data:
                    addr = protocol_data.get('addr').split('%').pop(0)
                    netmask = protocol_data.get('netmask')

                    try:
                        prefixlen = netaddr.IPNetwork('%s/%s' % (addr, netmask)).prefixlen
                    except:
                        prefixlen = None

                    interface_info[proto] = {
                        'netmask': netmask,
                        'address': addr,
                        'prefixlen': prefixlen
                    }

            # collect mac address
            interface_info['mac'] = addresses.get(netifaces.AF_LINK, [{}])[0].get('addr')

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

    def ec2(self, meta):
        """ ec2 """
        if self.ec2_metadata:
            meta['ec2'] = self.ec2_metadata
