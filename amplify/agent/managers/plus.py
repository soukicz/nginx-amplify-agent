# -*- coding: utf-8 -*-
from amplify.agent.common.context import context
from amplify.agent.managers.abstract import ObjectManager
from amplify.agent.objects.plus.cache import NginxCacheObject
from amplify.agent.objects.plus.status_zone import NginxStatusZoneObject
from amplify.agent.objects.plus.upstream import NginxUpstreamObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


# This will be the home of a separate manager which traverses all Nginx Plus objects and manages the child objects from
# the Plus status.
class PlusManager(ObjectManager):
    """
    Manager for Plus objects (Cache, StatusZone, Upstream).  Traverses all Nginx objects and looks for Plus instances.
    After identifying Nginx-Plus instances, it queries the plus_cache for the object in order to manage the child Plus
    objects much like NginxManager does for Nginx objects.
    """
    name = 'plus_manager'
    type = 'plus'
    types = ('cache', 'server_zone', 'upstream')

    def _discover_objects(self):
        # Find nginx_plus
        plus_nginxs = filter(lambda x: x.plus_status_enabled, context.objects.find_all(types=('nginx',)))

        existing_hashes = []
        discovered_hashes = []
        for nginx in plus_nginxs:
            plus_status, stamp = context.plus_cache.get_last(nginx.plus_status_internal_url)

            if not plus_status or not stamp:
                continue  # skip nginx plus's that haven't collected their first plus_status payload

            existing_hashes = map(lambda x: x.local_id, self.objects.find_all(parent_id=nginx.id))

            # Caches
            for cache_name in plus_status['caches']:
                cache_hash = NginxCacheObject.hash_local(nginx.local_id, NginxCacheObject.type, cache_name)

                discovered_hashes.append(cache_hash)

                if cache_hash not in existing_hashes:
                    # New object -- create it.
                    new_cache = NginxCacheObject(parent_local_id=nginx.local_id, local_name=cache_name)

                    self.objects.register(new_cache, parent_id=nginx.id)

            # Status Zones
            for status_zone_name in plus_status['server_zones']:
                status_zone_hash = NginxStatusZoneObject.hash_local(
                    nginx.local_id, NginxStatusZoneObject.type, status_zone_name
                )

                discovered_hashes.append(status_zone_hash)

                if status_zone_hash not in existing_hashes:
                    new_status_zone = NginxStatusZoneObject(parent_local_id=nginx.local_id, local_name=status_zone_name)

                    self.objects.register(new_status_zone, parent_id=nginx.id)

            # Upstreams
            for upstream_name in plus_status['upstreams']:
                upstream_hash = NginxUpstreamObject.hash_local(nginx.local_id, NginxUpstreamObject.type, upstream_name)

                discovered_hashes.append(upstream_hash)

                if upstream_hash not in existing_hashes:
                    new_upstream = NginxUpstreamObject(parent_local_id=nginx.local_id, local_name=upstream_name)

                    self.objects.register(new_upstream, parent_id=nginx.id)

        dropped_hashes = filter(lambda x: x not in discovered_hashes, existing_hashes)
        if len(dropped_hashes):
            for nginx in plus_nginxs:
                for obj in self.objects.find_all(parent_id=nginx.id):
                    if obj.local_id in dropped_hashes:
                        obj.stop()
                        self.objects.unregister(obj)
