# -*- coding: utf-8 -*-
import abc
import time

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

    def __init__(self, object=None, interval=None):
        self.object = object
        self.interval = interval
        self.previous_values = defaultdict(dict)  # for deltas
        self.current_values = defaultdict(int)  # for aggregating
        self.current_stamps = defaultdict(time.time)

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

    def increment_counters(self):
        """
        Increment counter method that takes the "current_values" dictionary of metric name - value pairs increments
        statsd appropriately based on previous values.
        """
        for metric_name, value in self.current_values.iteritems():
            prev_stamp, prev_value = self.previous_values.get(metric_name, (None, None))
            stamp, value = self.current_stamps[metric_name], self.current_values[metric_name]

            if isinstance(prev_value, (int, float)) and prev_stamp:
                value_delta = value - prev_value
                self.object.statsd.incr(metric_name, value_delta, stamp=stamp)

            self.previous_values[metric_name] = (stamp, value)

        # reset counter stores
        self.current_values = defaultdict(int)
        self.current_stamps = defaultdict(time.time)

    def aggregate_counters(self, counted_vars, stamp=None):
        """
        Aggregate several counter metrics from multiple places and store their sums in a metric_name-value store.

        :param counted_vars: Dict Metric_name - Value dict
        :param stamp: Int Timestamp of Plus collect
        """
        for metric_name, value in counted_vars.iteritems():
            self.current_values[metric_name] += value
            if stamp:
                self.current_stamps[metric_name] = stamp
