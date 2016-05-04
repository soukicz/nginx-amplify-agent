# -*- coding: utf-8 -*-
import hashlib
import re

import psutil
from amplify.agent.data.eventd import INFO

from amplify.agent.common.util import subp
from amplify.agent.common.context import context
from amplify.agent.managers.abstract import ObjectManager
from amplify.agent.objects.nginx.object import NginxObject
from amplify.agent.objects.nginx.binary import get_prefix_and_conf_path

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class NginxManager(ObjectManager):
    """
    Maanger for Nginx objects.
    """
    name = 'nginx_manager'
    type = 'nginx'
    types = ('nginx',)

    def _discover_objects(self):
        # save the current_ids
        existing_hashes = [obj.definition_hash for obj in self.objects.find_all(types=self.types)]

        # discover nginxs
        nginxs = self._find_all()

        # process all found nginxs
        discovered_hashes = []
        while len(nginxs):
            try:
                definition, data = nginxs.pop()
                definition_hash = NginxObject.hash(definition)
                discovered_hashes.append(definition_hash)

                if definition_hash not in existing_hashes:
                    # New object -- create it
                    data.update(self.object_configs.get(definition_hash, {}))  # push cloud config
                    new_obj = NginxObject(data=data)

                    # Send discover event.
                    new_obj.eventd.event(
                        level=INFO,
                        message='nginx-%s master process found, pid %s' % (new_obj.version, new_obj.pid)
                    )

                    self.objects.register(new_obj, parent_id=self.objects.root_id)
                elif definition_hash in existing_hashes:
                    for obj in self.objects.find_all(types=self.types):
                        if obj.definition_hash == definition_hash:
                            current_obj = obj
                            break  # TODO: Think about adding a definition hash - id map to objects tank.

                    if current_obj.need_restart:
                        # restart object if needed
                        context.log.debug('config was changed (pid %s)' % current_obj.pid)
                        data.update(self.object_configs.get(definition_hash, {}))  # push cloud config
                        new_obj = NginxObject(data=data)

                        # Send nginx config changed event.
                        new_obj.eventd.event(
                            level=INFO,
                            message='nginx-%s config changed, read from %s' % (new_obj.version, new_obj.conf_path)
                        )

                        new_obj.id = current_obj.id

                        # stop and deregister children
                        for child_obj in self.objects.find_all(
                                obj_id=current_obj.id,
                                children=True,
                                include_self=False
                        ):
                            child_obj.stop()
                            self.objects.unregister(obj=child_obj)

                        self.objects.objects[current_obj.id] = new_obj  # Replace old object in tank.
                        current_obj.stop()  # stop old object
                    elif current_obj.pid != data['pid']:
                        # check that the object pids didn't change
                        context.log.debug(
                            'nginx was restarted (pid was %s now %s)' % (
                                current_obj.pid, data['pid']
                            )
                        )
                        data.update(self.object_configs.get(definition_hash, {}))
                        new_obj = NginxObject(data=data)

                        # Send nginx master process restart/reload event.
                        new_obj.eventd.event(
                            level=INFO,
                            message='nginx-%s master process restarted/reloaded, new pid %s, old pid %s' % (
                                new_obj.version,
                                new_obj.pid,
                                current_obj.pid
                            )
                        )

                        new_obj.id = current_obj.id

                        # stop and unregister children
                        for child_obj in self.objects.find_all(
                                obj_id=current_obj.id,
                                children=True,
                                include_self=False
                        ):
                            self.objects.unregister(obj=child_obj)

                        self.objects.objects[current_obj.id] = new_obj
                        current_obj.stop()  # stop old object
                    elif current_obj.workers != data['workers']:
                        # check workers on reload
                        context.log.debug(
                            'nginx was reloaded (workers were %s now %s)' % (
                                current_obj.workers, data['workers']
                            )
                        )
                        current_obj.workers = data['workers']
            except psutil.NoSuchProcess:
                context.log.debug('nginx is restarting/reloading, pids are changing, agent is waiting')

        # check if we left something in objects (nginx could be stopped or something)
        dropped_hashes = filter(lambda x: x not in discovered_hashes, existing_hashes)
        if len(dropped_hashes):
            for dropped_hash in dropped_hashes:
                for obj in self.objects.find_all(types=self.types):
                    if obj.definition_hash == dropped_hash:
                        dropped_obj = obj
                        break  # TODO: Think about adding a definition hash - id map to objects tank.

                context.log.debug('nginx was stopped (pid was %s)' % dropped_obj.pid)

                for child_obj in self.objects.find_all(
                        obj_id=dropped_obj.id,
                        children=True,
                        include_self=False
                ):
                    child_obj.stop()
                    self.objects.unregister(child_obj)

                dropped_obj.stop()
                self.objects.unregister(dropped_obj)

    @staticmethod
    def _find_all():
        """
        Tries to find all master processes

        :return: list of dict: nginx object definitions
        """
        # get ps info
        ps_cmd = "ps xao pid,ppid,command | grep 'nginx[:]'"
        try:
            ps, _ = subp.call(ps_cmd)
            context.log.debug('ps nginx output: %s' % ps)
        except:
            context.log.error('failed to find running nginx via %s' % ps_cmd)
            context.log.debug('additional info:', exc_info=True)
            return []

        # calculate total amount of nginx master processes
        # if no masters - return
        masters_amount = len(filter(lambda x: 'nginx: master process' in x, ps))
        if masters_amount == 0:
            context.log.debug('nginx masters amount is zero')
            return []

        # collect all info about processes
        masters = {}
        try:
            for line in ps:
                # parse ps response line:
                # 21355     1 nginx: master process /usr/sbin/nginx
                gwe = re.match(r'\s*(?P<pid>\d+)\s+(?P<ppid>\d+)\s+(?P<cmd>.+)\s*', line)

                # if not parsed - go to the next line
                if not gwe:
                    continue

                pid, ppid, cmd = int(gwe.group('pid')), int(gwe.group('ppid')), gwe.group('cmd')

                # match daemonized master and skip the other stuff
                if 'nginx: master process' in cmd and ppid == 1:
                    # get path to binary, prefix and conf_path
                    try:
                        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(cmd)
                    except:
                        context.log.error('failed to find bin_path, prefix and conf_path for %s' % cmd)
                        context.log.debug('', exc_info=True)
                    else:
                        # calculate local id
                        local_id = hashlib.sha256('%s_%s_%s' % (bin_path, conf_path, prefix)).hexdigest()

                        if pid in masters:
                            masters[pid].update(
                                dict(
                                    version=version,
                                    bin_path=bin_path,
                                    conf_path=conf_path,
                                    prefix=prefix,
                                    pid=pid,
                                    local_id=local_id
                                )
                            )
                        else:
                            masters[pid] = dict(
                                version=version,
                                bin_path=bin_path,
                                conf_path=conf_path,
                                prefix=prefix,
                                pid=pid,
                                local_id=local_id,
                                workers=[]
                            )
                # match worker
                elif 'nginx: worker process' or 'nginx: cache manager process' in cmd:
                    if ppid in masters:
                        masters[ppid]['workers'].append(pid)
                    else:
                        masters[ppid] = dict(workers=[pid])
        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.error('failed to parse ps results due to %s' % exception_name)
            context.log.debug('additional info:', exc_info=True)

        # collect results
        results = []
        for pid, description in masters.iteritems():
            if 'bin_path' in description:  # filter workers with non-executable nginx -V (relative paths, etc)
                definition = {
                    'local_id': description['local_id'],
                    'type': NginxManager.type,
                    'root_uuid': context.objects.root_object.uuid if context.objects.root_object else None
                }
                results.append((definition, description))
        return results
