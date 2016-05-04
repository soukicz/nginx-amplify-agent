# -*- coding: utf-8 -*-
import abc
import hashlib
import time

from collections import defaultdict
from threading import current_thread
from gevent import queue, GreenletExit

from amplify.agent.data.eventd import EventdClient
from amplify.agent.data.metad import MetadClient
from amplify.agent.data.statsd import StatsdClient

from amplify.agent.data.configd import ConfigdClient
from amplify.agent.common.context import context
from amplify.agent.common.util.threads import spawn

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class AbstractObject(object):
    """
    Abstract object. Supervisor for collectors and data client bucket.
    """

    # TODO: Refactor our agent objects to be more inline with our backend representations of the same.
    type = 'common'

    def __init__(self, data=None, **kwargs):
        self.id = None
        self.data = data if data else kwargs

        self.intervals = context.app_config['containers'].get(self.type, {}).get('poll_intervals', {'default': 10})
        self.running = False
        self.need_restart = False
        self.init_time = int(time.time())

        self.threads = []
        self.collectors = []
        self.filters = []
        self.queue = queue.Queue()

        # data clients
        self.statsd = StatsdClient(object=self, interval=max(self.intervals.values()))
        self.eventd = EventdClient(object=self)
        self.metad = MetadClient(object=self)
        self.configd = ConfigdClient(object=self)
        self.clients = {
            'meta': self.metad,
            'metrics': self.statsd,
            'events': self.eventd,
            'configs': self.configd,
        }  # This is a client mapping to aid with lookup during flush by Bridge.

        self.definition_hash_cache = None
        self.local_id_cache = None

    @abc.abstractproperty
    def definition(self):
        return {'id': self.id, 'type': self.type}

    @property
    def definition_hash(self):
        if not self.definition_hash_cache:
            definition_string = str(map(lambda x: u'%s:%s' % (x, self.definition[x]), sorted(self.definition.keys())))
            self.definition_hash_cache = hashlib.sha256(definition_string).hexdigest()
        return self.definition_hash_cache

    @staticmethod
    def hash(definition):
        definition_string = str(map(lambda x: u'%s:%s' % (x, definition[x]), sorted(definition.keys())))
        result = hashlib.sha256(definition_string).hexdigest()
        return result

    @property
    def local_id_args(self):
        """
        Class specific local_id_args for local_id hash.  Should be overridden by objects that utilize local_id's.
        (Optional for system/root objects)
        """
        return tuple()

    @property
    def local_id(self):
        # TODO: Refactor Nginx object to use this style local_id property.
        if not self.local_id_cache and len(self.local_id_args) == 3:
            self.local_id_cache = hashlib.sha256(
                '%s_%s_%s' % (self.local_id_args[0], self.local_id_args[1], self.local_id_args[2])
            ).hexdigest()
        return self.local_id_cache

    @staticmethod
    def hash_local(*args):
        if len(args) == 3:
            return hashlib.sha256('%s_%s_%s' % (args[0], args[1], args[2])).hexdigest()

    def start(self):
        """
        Starts all of the object's collector threads
        """
        if not self.running:
            context.log.debug('starting object "%s" %s' % (self.type, self.definition_hash))
            for collector in self.collectors:
                self.threads.append(spawn(collector.run))
            self.running = True

    def stop(self):
        context.log.debug('halting object "%s" %s' % (self.type, self.definition_hash))
        # Kill raises errors with gevent.
        # for thread in self.threads:
        #     thread.kill()
        self.running = False
        context.log.debug('stopped object "%s" %s ' % (self.type, self.definition_hash))

    def flush(self, clients=None):
        """
        Object flush method.  Since the object is what has the bins, it should be responsible for managing them.

        :param clients: List of Strings (names of the bins to flush.
        :return: Dict Flush contents for each named bin.  Structure of each is determined by the bin itself.
        """
        results = {}

        if clients:  # Flush the bins requested.
            if len(clients) != 1:
                for name in clients:
                    if name in self.clients:
                        results[name] = self.clients[name].flush()
            else:
                results = self.clients[clients[0]].flush()
        else:  # Flush all the bins for the object
            for name, client in self.clients.iteritems():
                results[name] = client.flush()

        return results


class AbstractCollector(object):
    """
    Abstract data collector
    Runs in a thread and collects specific data
    """
    short_name = None

    def __init__(self, object=None, interval=None):
        self.object = object
        self.interval = interval
        self.previous_values = defaultdict(dict)  # for deltas

    def run(self):
        """
        Common collector cycle

        1. Collect data
        2. Sleep
        3. Stop if object stopped
        """
        # TODO: Standardize this with Managers.
        current_thread().name = self.short_name
        context.setup_thread_id()

        try:
            while True:
                context.inc_action_id()
                if self.object.running:
                    self._collect()
                    self._sleep()
                else:
                    break

            raise GreenletExit  # Since kill signals won't work, we raise it ourselves.
        except GreenletExit:
            context.log.debug(
                '%s collector for %s received exit signal' % (self.__class__.__name__, self.object.definition_hash)
            )
        except:
            context.log.error(
                '%s collector run failed' % self.object.definition_hash,
                exc_info=True
            )
            raise

    def _collect(self):
        """
        Wrapper for actual collect process.  Handles memory reporting before and after collect process.
        """
        start_time = time.time()
        try:
            self.collect()
        except:
            raise
        finally:
            end_time = time.time()
            context.log.debug('%s collect in %.3f' % (self.object.definition_hash, end_time - start_time))

    def _sleep(self):
        time.sleep(self.interval)

    @abc.abstractmethod
    def collect(self):
        """
        Real collect method
        Override it
        """
        pass

    def increment_counters(self, counted_vars, stamp):
        """
        Increment counter method that takes a dictionary of metric name - value pairs increments statsd appropriately
        based on previous values.

        :param counted_vars: Dict Metric name - value pairs
        :param stamp: Int Timestamp of Plus collect
        """
        for metric_name, value in counted_vars.iteritems():
            prev_stamp, prev_value = self.previous_values.get(metric_name, [None, None])

            if prev_stamp:
                value_delta = value - prev_value
                self.object.statsd.incr(metric_name, value_delta, stamp=stamp)

            self.previous_values[metric_name] = [stamp, value]
