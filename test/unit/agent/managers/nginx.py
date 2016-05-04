# -*- coding: utf-8 -*-
import re

from hamcrest import *

from amplify.agent.common.util import subp
from amplify.agent.managers.nginx import NginxManager
from test.base import RealNginxTestCase

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class NginxManagerTestCase(RealNginxTestCase):

    def get_master_workers(self):
        master, workers = None, []
        ps, _ = subp.call('ps -xa -o pid,ppid,command | egrep "PID|nginx" | grep -v egrep')
        for line in ps:
            # 21355     1 nginx: master process /usr/sbin/nginx
            gwe = re.match(r'\s*(?P<pid>\d+)\s+(?P<ppid>\d+)\s+(?P<cmd>.+)\s*', line)

            # if not parsed - switch to next line
            if not gwe or 'py.test' in line:
                continue

            pid = int(gwe.group('pid'))
            cmd = gwe.group('cmd')

            if 'nginx: master process' in cmd:
                master = pid
            else:
                workers.append(pid)
        return master, workers

    def test_find_all(self):
        container = NginxManager()
        nginxes = container._find_all()
        assert_that(nginxes, has_length(1))

        definition, data = nginxes.pop(0)
        assert_that(data, has_key('pid'))
        assert_that(data, has_key('workers'))

        # get ps info
        master, workers = self.get_master_workers()

        assert_that(master, equal_to(data['pid']))
        assert_that(workers, equal_to(data['workers']))

    def test_restart(self):
        old_master, old_workers = self.get_master_workers()

        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))
        obj = container.objects.find_all(obj_id=container.objects.objects_by_type[container.type][0])[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))

        self.restart_nginx()
        new_master, new_workers = self.get_master_workers()

        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))
        obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]
        assert_that(obj.pid, not_(equal_to(old_master)))
        assert_that(obj.pid, equal_to(new_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))

    def test_reload(self):
        old_master, old_workers = self.get_master_workers()

        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(1))
        obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]
        # The following assertion is unreliable for some reason.
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))

        self.reload_nginx()
        new_master, new_workers = self.get_master_workers()
        assert_that(new_master, equal_to(old_master))

        container._discover_objects()
        obj = container.objects.find_all(obj_id=container.objects.objects_by_type[container.type][0])[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))

    def test_two_instances(self):
        container = NginxManager()
        container._discover_objects()
        obj = container.objects.objects[container.objects.objects_by_type[container.type][0]]

        self.start_second_nginx()

        container._discover_objects()
        assert_that(container.objects.objects_by_type[container.type], has_length(2))

        local_ids = map(lambda x: x.local_id, container.objects.find_all(types=container.types))
        assert_that(local_ids, has_item(obj.local_id))
