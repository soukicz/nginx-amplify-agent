# -*- coding: utf-8 -*-
import re
import time

import psutil

from amplify.agent.collectors.plus.util.cache import CACHE_COLLECT_INDEX
from amplify.agent.collectors.plus.util.upstream import UPSTREAM_COLLECT_INDEX
from amplify.agent.collectors.plus.util.status_zone import STATUS_ZONE_COLLECT_INDEX

from amplify.agent.common.context import context
from amplify.agent.common.errors import AmplifyParseException
from amplify.agent.common.util.ps import Process
from amplify.agent.data.eventd import WARNING
from amplify.agent.collectors.abstract import AbstractCollector

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard", "Arie van Luttikhuizen"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"

STUB_RE = re.compile(r'^Active connections: (?P<connections>\d+)\s+[\w ]+\n'
                     r'\s+(?P<accepts>\d+)'
                     r'\s+(?P<handled>\d+)'
                     r'\s+(?P<requests>\d+)'
                     r'\s+Reading:\s+(?P<reading>\d+)'
                     r'\s+Writing:\s+(?P<writing>\d+)'
                     r'\s+Waiting:\s+(?P<waiting>\d+)')


class CommonNginxMetricsCollector(AbstractCollector):

    short_name = 'common_nginx_metrics'

    def __init__(self, **kwargs):
        super(CommonNginxMetricsCollector, self).__init__(**kwargs)

        self.processes = [Process(pid) for pid in self.object.workers]
        self.zombies = set()

    def collect(self):
        for method in (
            self.workers_count,
            self.memory_info,
            self.workers_fds_count,
            self.workers_cpu,
            self.status
        ):
            try:
                method()
            except psutil.NoSuchProcess as e:
                exception_name = e.__class__.__name__
                pid = e.pid

                # Log exception
                context.log.warning(
                    'failed to collect metrics %s due to %s, object restart needed (PID: %s)' %
                    (method.__name__, exception_name, pid)
                )
                self.object.need_restart = True
            except Exception as e:
                exception_name = e.__class__.__name__

                # Fire event warning.
                self.object.eventd.event(
                    level=WARNING,
                    message="can't obtain worker process metrics (maybe permissions?)",
                    onetime=True
                )

                # Log exception
                context.log.error('failed to collect metrics %s due to %s' % (method.__name__, exception_name))
                context.log.debug('additional info:', exc_info=True)

    def workers_count(self):
        """nginx.workers.count"""
        self.object.statsd.gauge('nginx.workers.count', len(self.object.workers))

    def handle_zombie(self, pid):
        """
        removes pid from workers list
        :param pid: zombie pid
        """
        context.log.warning('zombie process %s found' % pid)
        self.zombies.add(pid)

    def memory_info(self):
        """
        memory info

        nginx.workers.mem.rss
        nginx.workers.mem.vms
        nginx.workers.mem.rss_pct
        """
        rss, vms, pct = 0, 0, 0.0
        for p in self.processes:
            if p.pid in self.zombies:
                continue
            try:
                mem_info = p.memory_info()
                rss += mem_info.rss
                vms += mem_info.vms
                pct += p.memory_percent()
            except psutil.ZombieProcess:
                self.handle_zombie(p.pid)

        self.object.statsd.gauge('nginx.workers.mem.rss', rss)
        self.object.statsd.gauge('nginx.workers.mem.vms', vms)
        self.object.statsd.gauge('nginx.workers.mem.rss_pct', pct)

    def workers_fds_count(self):
        """nginx.workers.fds_count"""
        fds = 0
        for p in self.processes:
            if p.pid in self.zombies:
                continue
            try:
                fds += p.num_fds()
            except psutil.ZombieProcess:
                self.handle_zombie(p.pid)
        self.object.statsd.incr('nginx.workers.fds_count', fds)

    def workers_cpu(self):
        """
        cpu

        nginx.workers.cpu.system
        nginx.workers.cpu.user
        """
        worker_user, worker_sys = 0.0, 0.0
        for p in self.processes:
            if p.pid in self.zombies:
                continue
            try:
                u, s = p.cpu_percent()
                worker_user += u
                worker_sys += s
            except psutil.ZombieProcess:
                self.handle_zombie(p.pid)
        self.object.statsd.gauge('nginx.workers.cpu.total', worker_user + worker_sys)
        self.object.statsd.gauge('nginx.workers.cpu.user', worker_user)
        self.object.statsd.gauge('nginx.workers.cpu.system', worker_sys)

    def status(self):
        """
        check if found extended status, collect "global" metrics from it
        don't look for stub_status
        if there's no extended status easily accessible, proceed with stub_status
        """
        if self.object.plus_status_enabled and self.object.plus_status_internal_url:
            self.plus_status()
        elif self.object.stub_status_enabled and self.object.stub_status_url:
            self.stub_status()
        else:
            return

    def stub_status(self):
        """
        stub status metrics

        nginx.http.conn.current = ss.active
        nginx.http.conn.active = ss.active - ss.waiting
        nginx.http.conn.idle = ss.waiting
        nginx.http.request.count = ss.requests ## counter
        nginx.http.request.reading = ss.reading
        nginx.http.request.writing = ss.writing
        nginx.http.conn.dropped = ss.accepts - ss.handled ## counter
        nginx.http.conn.accepted = ss.accepts ## counter
        """
        stub_body = ''
        stub = {}
        stub_time = int(time.time())

        # get stub status body
        try:
            stub_body = context.http_client.get(self.object.stub_status_url, timeout=1, json=False, log=False)
        except:
            context.log.error('failed to check stub_status url %s' % self.object.stub_status_url)
            context.log.debug('additional info', exc_info=True)
            stub_body = None

        if not stub_body:
            return

        # parse body
        try:
            gre = STUB_RE.match(stub_body)
            if not gre:
                raise AmplifyParseException(message='stub status %s' % stub_body)
            for field in ('connections', 'accepts', 'handled', 'requests', 'reading', 'writing', 'waiting'):
                stub[field] = int(gre.group(field))
        except:
            context.log.error('failed to parse stub_status body')
            raise

        # store some variables for further use
        stub['dropped'] = stub['accepts'] - stub['handled']

        # gauges
        self.object.statsd.gauge('nginx.http.conn.current', stub['connections'])
        self.object.statsd.gauge('nginx.http.conn.active', stub['connections'] - stub['waiting'])
        self.object.statsd.gauge('nginx.http.conn.idle', stub['waiting'])
        self.object.statsd.gauge('nginx.http.request.writing', stub['writing'])
        self.object.statsd.gauge('nginx.http.request.reading', stub['reading'])
        self.object.statsd.gauge('nginx.http.request.current', stub['reading'] + stub['writing'])

        # counters
        counted_vars = {
            'nginx.http.request.count': 'requests',
            'nginx.http.conn.accepted': 'accepts',
            'nginx.http.conn.dropped': 'dropped'
        }
        for metric_name, stub_name in counted_vars.iteritems():
            stamp, value = stub_time, stub[stub_name]
            prev_stamp, prev_value = self.previous_counters.get(metric_name, (None, None))

            if isinstance(prev_value, (int, float)) and prev_stamp and prev_stamp != stamp:
                value_delta = value - prev_value
                self.object.statsd.incr(metric_name, value_delta)

            self.previous_counters[metric_name] = [stamp, value]

    def plus_status(self):
        """
        plus status metrics

        nginx.http.conn.accepted = connections.accepted  ## counter
        nginx.http.conn.dropped = connections.dropped  ## counter
        nginx.http.conn.active = connections.active
        nginx.http.conn.current = connections.active + connections.idle
        nginx.http.conn.idle = connections.idle
        nginx.http.request.count = requests.total  ## counter
        nginx.http.request.current = requests.current
        """
        stamp = int(time.time())

        # get plus status body
        try:
            status = context.http_client.get(self.object.plus_status_internal_url, timeout=1, log=False)

            # Add the status payload to plus_cache so it can be parsed by other collectors (plus objects)
            context.plus_cache.put(self.object.plus_status_internal_url, (status, stamp))
        except:
            context.log.error('failed to check plus_status url %s' % self.object.plus_status_internal_url)
            context.log.debug('additional info', exc_info=True)
            status = None

        if not status:
            return

        connections = status.get('connections', {})
        requests = status.get('requests', {})

        # gauges

        self.object.statsd.gauge('nginx.http.conn.active', connections.get('active'))
        self.object.statsd.gauge('nginx.http.conn.idle', connections.get('idle'))
        self.object.statsd.gauge('nginx.http.conn.current', connections.get('active') + connections.get('idle'))
        self.object.statsd.gauge('nginx.http.request.current', requests.get('current'))

        # counters
        counted_vars = {
            'nginx.http.request.count': requests.get('total'),
            'nginx.http.conn.accepted': connections.get('accepted'),
            'nginx.http.conn.dropped': connections.get('dropped'),
        }
        self.aggregate_counters(counted_vars, stamp=stamp)

        # Aggregate plus metrics

        # Caches
        caches = status.get('caches', {})
        for cache in caches.values():
            for method in CACHE_COLLECT_INDEX:
                method(self, cache, stamp)

        # Status Zones
        zones = status.get('server_zones', {})
        for zone in zones.values():
            for method in STATUS_ZONE_COLLECT_INDEX:
                method(self, zone, stamp)

        # Upstreams
        upstreams = status.get('upstreams', {})
        for upstream in upstreams.values():
            # workaround for supporting old N+ format
            # http://nginx.org/en/docs/http/ngx_http_status_module.html#compatibility
            peers = upstream['peers'] if 'peers' in upstream else upstream

            for peer in peers:
                for method in UPSTREAM_COLLECT_INDEX:
                    method(self, peer, stamp)

        self.increment_counters()
        self.finalize_latest()


class NginxMetricsCollector(CommonNginxMetricsCollector):

    short_name = 'nginx_metrics'

    def __init__(self, **kwargs):
        super(CommonNginxMetricsCollector, self).__init__(**kwargs)

        self.processes = [Process(pid) for pid in self.object.workers]
        self.zombies = set()

    def collect(self):
        super(NginxMetricsCollector, self).collect()

        for method in (
                self.workers_rlimit_nofile,
                self.workers_io
        ):
            try:
                method()
            except psutil.NoSuchProcess as e:
                exception_name = e.__class__.__name__
                pid = e.pid

                # Log exception
                context.log.warning(
                    'failed to collect metrics %s due to %s, object restart needed (PID: %s)' %
                    (method.__name__, exception_name, pid)
                )
                self.object.need_restart = True
            except Exception as e:
                exception_name = e.__class__.__name__

                # Fire event warning.
                self.object.eventd.event(
                    level=WARNING,
                    message="can't obtain worker process metrics (maybe permissions?)",
                    onetime=True
                )

                # Log exception
                context.log.error('failed to collect metrics %s due to %s' % (method.__name__, exception_name))
                context.log.debug('additional info:', exc_info=True)

    def workers_rlimit_nofile(self):
        """
        nginx.workers.rlimit_nofile

        sum for all hard limits (second value of rlimit)
        """
        rlimit = 0
        for p in self.processes:
            if p.pid in self.zombies:
                continue
            try:
                rlimit += p.rlimit_nofile()
            except psutil.ZombieProcess:
                self.handle_zombie(p.pid)
        self.object.statsd.gauge('nginx.workers.rlimit_nofile', rlimit)

    def workers_io(self):
        """
        io

        nginx.workers.io.kbs_r
        nginx.workers.io.kbs_w
        """
        # collect raw data
        read, write = 0, 0
        for p in self.processes:
            if p.pid in self.zombies:
                continue
            try:
                io = p.io_counters()
                read += io.read_bytes
                write += io.write_bytes
            except psutil.ZombieProcess:
                self.handle_zombie(p.pid)
        current_stamp = int(time.time())

        # kilobytes!
        read /= 1024
        write /= 1024

        # get deltas and store metrics
        for metric_name, value in {'nginx.workers.io.kbs_r': read, 'nginx.workers.io.kbs_w': write}.iteritems():
            prev_stamp, prev_value = self.previous_counters.get(metric_name, (None, None))
            if isinstance(prev_value, (int, float)) and prev_stamp and prev_stamp != current_stamp:
                value_delta = value - prev_value
                self.object.statsd.incr(metric_name, value_delta)
            self.previous_counters[metric_name] = (current_stamp, value)


class ContainerNginxMetricsCollector(CommonNginxMetricsCollector):
    short_name = 'container_nginx_metrics'
