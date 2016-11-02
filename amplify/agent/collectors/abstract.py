# -*- coding: utf-8 -*-
import time

from abc import abstractproperty
from collections import defaultdict
from threading import current_thread
from gevent import queue, GreenletExit

from amplify.agent.common.context import context

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class AbstractCollector(object):
    """
    Abstract data collector
    Runs in a thread and collects specific data
    """
    short_name = None

    zero_counters = tuple()

    def __init__(self, object=None, interval=None):
        self.object = object
        self.in_container = self.object.in_container
        self.interval = interval
        self.previous_counters = defaultdict(dict)  # for deltas
        self.current_counters = defaultdict(int)  # for aggregating
        self.current_latest = defaultdict(int)
        self.methods = set()

        # stamp store organized by type - metric_name - stamp
        self.current_stamps = defaultdict(lambda: defaultdict(time.time))

    def init_counters(self, counters=None):
        """
        Helper function for sending 0 values when no data is found.

        :param counters: Iterable String values of names of counters to init as 0 (default is self.zero_counters)
        """
        counters = counters or self.zero_counters
        for counter in counters:
            self.object.statsd.incr(counter, value=0)

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

    def register(self, *methods):
        """
        Register methods for collecting
        """
        self.methods.update(methods)

    def _collect(self):
        """
        Wrapper for actual collect process.  Handles memory reporting before and after collect process.
        """
        start_time = time.time()
        try:
            self.collect()
        finally:
            end_time = time.time()
            context.log.debug('%s collect in %.3f' % (self.object.definition_hash, end_time - start_time))

    def _sleep(self):
        time.sleep(self.interval)

    def collect(self, *args, **kwargs):
        if self.zero_counters:
            self.init_counters()

        for method in self.methods:
            try:
                method(*args, **kwargs)
            except Exception as e:
                self.handle_exception(method, e)

    def handle_exception(self, method, exception):
        context.log.error('%s failed to collect: %s raised %s%s' % (
            self.short_name,  method.__name__, exception.__class__.__name__,
            ' (in container)' if self.in_container else ''
        ))
        context.log.debug('additional info:', exc_info=True)

    def increment_counters(self):
        """
        Increment counter method that takes the "current_values" dictionary of metric name - value pairs increments
        statsd appropriately based on previous values.
        """
        for metric_name, value in self.current_counters.iteritems():
            prev_stamp, prev_value = self.previous_counters.get(metric_name, (None, None))
            stamp, value = self.current_stamps['counters'][metric_name], self.current_counters[metric_name]

            if isinstance(prev_value, (int, float, long)) and prev_stamp:
                value_delta = value - prev_value
                if value_delta >= 0:
                    # Only increment our statsd client and send data to backend if calculated value is non-negative.
                    self.object.statsd.incr(metric_name, value_delta, stamp=stamp)

            # Re-base the calculation for next collect
            self.previous_counters[metric_name] = (stamp, value)

        # reset counter stores
        self.current_counters = defaultdict(int)
        if self.current_stamps['counters']:
            del self.current_stamps['counters']

    def aggregate_counters(self, counted_vars, stamp=None):
        """
        Aggregate several counter metrics from multiple places and store their sums in a metric_name-value store.

        :param counted_vars: Dict Metric_name - Value dict
        :param stamp: Int Timestamp of Plus collect
        """
        for metric_name, value in counted_vars.iteritems():
            self.current_counters[metric_name] += value
            if stamp:
                self.current_stamps['counters'][metric_name] = stamp

    def finalize_latest(self):
        """
        Go through stored latest variables and send them to the object statsd.
        """
        for metric_name, value in self.current_latest.iteritems():
            stamp = self.current_stamps['latest'][metric_name]
            self.object.statsd.latest(metric_name, value, stamp)

        # reset latest store
        self.current_latest = defaultdict(int)
        if self.current_stamps['latest']:
            del self.current_stamps['latest']

    def aggregate_latest(self, latest_vars, stamp=None):
        """
        Aggregate several latest metrics from multiple places and store the final value in a metric_name-value store.

        :param latest_vars: Dict Metric_name - Value dict
        :param stamp: Int Timestamp of collect
        """
        for metric_name in latest_vars:
            self.current_latest[metric_name] += 1
            if stamp:
                self.current_stamps['latest'][metric_name] = stamp


class AbstractMetaCollector(AbstractCollector):
    default_meta = abstractproperty()

    def __init__(self, **kwargs):
        super(AbstractMetaCollector, self).__init__(**kwargs)
        self.meta = {}

    def collect(self, *args):
        self.meta.update(self.default_meta)
        super(AbstractMetaCollector, self).collect(*args)
        self.object.metad.meta(self.meta)


class AbstractMetricsCollector(AbstractCollector):
    pass
