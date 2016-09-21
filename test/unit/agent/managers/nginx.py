# -*- coding: utf-8 -*-
import re
import time

from hamcrest import *

from amplify.agent.common.util import subp
from amplify.agent.common.context import context
from amplify.agent.managers.nginx import NginxManager
from test.base import RealNginxTestCase, BaseTestCase, container_test
from test.helpers import DummyRootObject

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
        assert_that(container.objects.find_all(types=container.types), has_length(1))
        obj = container.objects.find_all(types=container.types)[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))

        self.restart_nginx()
        new_master, new_workers = self.get_master_workers()

        container._discover_objects()
        assert_that(container.objects.find_all(types=container.types), has_length(1))
        obj = container.objects.find_all(types=container.types)[0]
        assert_that(obj.pid, not_(equal_to(old_master)))
        assert_that(obj.pid, equal_to(new_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))

    def test_reload(self):
        old_master, old_workers = self.get_master_workers()

        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.find_all(types=container.types), has_length(1))
        obj = container.objects.find_all(types=container.types)[0]
        # The following assertion is unreliable for some reason.
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))

        self.reload_nginx()
        new_master, new_workers = self.get_master_workers()
        assert_that(new_master, equal_to(old_master))

        container._discover_objects()
        obj = container.objects.find_all(types=container.types)[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))

    def test_two_instances(self):
        container = NginxManager()
        container._discover_objects()
        obj = container.objects.find_all(types=container.types)[0]

        self.start_second_nginx()

        container._discover_objects()
        assert_that(container.objects.find_all(types=container.types), has_length(2))

        local_ids = map(lambda x: x.local_id, container.objects.find_all(types=container.types))
        assert_that(local_ids, has_item(obj.local_id))

    def test_find_none(self):
        # Kill running NGINX so that it finds None
        subp.call('pgrep nginx |sudo xargs kill -SIGKILL', check=False)
        self.running = False

        # Setup dummy object
        context.objects.register(DummyRootObject())

        container = NginxManager()
        nginxes = container._find_all()
        assert_that(nginxes, has_length(0))

        root_object = context.objects.root_object
        assert_that(root_object.eventd.current, has_length(1))

        # Reset objects...
        context.objects = None
        context._setup_object_tank()


@container_test
class DockerNginxManagerTestCase(NginxManagerTestCase):

    def test_restart(self):
        old_master, old_workers = self.get_master_workers()

        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.find_all(types=container.types), has_length(1))
        obj = container.objects.find_all(types=container.types)[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))
        assert_that(obj.type, equal_to('container_nginx'))

        self.restart_nginx()
        new_master, new_workers = self.get_master_workers()

        container._discover_objects()
        assert_that(container.objects.find_all(types=container.types), has_length(1))
        obj = container.objects.find_all(types=container.types)[0]
        assert_that(obj.pid, not_(equal_to(old_master)))
        assert_that(obj.pid, equal_to(new_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))
        assert_that(obj.type, equal_to('container_nginx'))

    def test_reload(self):
        old_master, old_workers = self.get_master_workers()

        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.find_all(types=container.types), has_length(1))
        obj = container.objects.find_all(types=container.types)[0]
        # The following assertion is unreliable for some reason.
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, equal_to(old_workers))
        assert_that(obj.type, equal_to('container_nginx'))

        self.reload_nginx()
        new_master, new_workers = self.get_master_workers()
        assert_that(new_master, equal_to(old_master))

        container._discover_objects()
        obj = container.objects.find_all(types=container.types)[0]
        assert_that(obj.pid, equal_to(old_master))
        assert_that(obj.workers, not_(equal_to(old_workers)))
        assert_that(obj.workers, equal_to(new_workers))
        assert_that(obj.type, equal_to('container_nginx'))

    def test_two_instances(self):
        container = NginxManager()
        container._discover_objects()
        assert_that(container.objects.find_all(types=container.types), has_length(1))
        obj = container.objects.find_all(types=container.types)[0]
        assert_that(obj.type, equal_to('container_nginx'))

        self.start_second_nginx()

        container._discover_objects()
        assert_that(container.objects.find_all(types=container.types), has_length(2))

        local_ids = map(lambda x: x.local_id, container.objects.find_all(types=container.types))
        assert_that(local_ids, has_item(obj.local_id))


class SupervisorNginxManagerTestCase(BaseTestCase):
    def setup_method(self, method):
        super(SupervisorNginxManagerTestCase, self).setup_method(method)
        subp.call('supervisord')

    def teardown_method(self, method):
        subp.call('pgrep supervisor | sudo xargs kill -SIGKILL')
        subp.call('pgrep nginx | sudo xargs kill -SIGKILL')
        super(SupervisorNginxManagerTestCase, self).teardown_method(method)

    def test_find_all(self):
        out = subp.call('ps xao pid,ppid,command | grep "supervisor[d]" | tr -s " "')[0]
        supervisors = [map(int, line.strip().split()[:2]) for line in out if 'supervisord' in line]
        assert_that(supervisors, has_length(1))
        supervisor_pid, supervisor_ppid = supervisors[0]
        assert_that(supervisor_ppid, equal_to(1))

        time.sleep(2)

        out = subp.call('ps xao pid,ppid,command | grep "nginx[:]" | tr -s " "')[0]
        masters = [map(int, line.strip().split()[:2]) for line in out if 'nginx: master process' in line]
        assert_that(masters, has_length(1))
        master_pid, master_ppid = masters[0]
        assert_that(master_ppid, equal_to(supervisor_pid))

        worker_pids = []

        workers = [map(int, line.strip().split()[:2]) for line in out if 'nginx: worker process' in line]
        for worker_pid, worker_ppid in workers:
            worker_pids.append(worker_pid)
            assert_that(worker_ppid, equal_to(master_pid))

        container = NginxManager()
        nginxes = container._find_all()
        assert_that(nginxes, has_length(1))

        definition, data = nginxes.pop(0)
        assert_that(data, has_key('pid'))
        assert_that(data, has_key('workers'))

        assert_that(master_pid, equal_to(data['pid']))
        assert_that(worker_pids, equal_to(data['workers']))
