# -*- coding: utf-8 -*-
import copy
import pprint
import time
import gevent

from threading import current_thread
from random import randint
from requests.exceptions import HTTPError

from amplify.agent.common.cloud import CloudResponse, HTTP503Error
from amplify.agent.common.context import context
from amplify.agent.common.util.backoff import exponential_delay
from amplify.agent.common.errors import AmplifyCriticalException
from amplify.agent.common.util import loader
from amplify.agent.common.util.threads import spawn
from amplify.agent.managers.bridge import Bridge


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class Supervisor(object):
    """
    Agent supervisor

    Starts dedicated threads for each manager.
    """
    # TODO: Unify the manager init and supervision process (object managers vs. bridge)

    MANAGER_CLASS = '%sManager'
    MANAGER_MODULE = 'amplify.agent.managers.%s.%s'

    def __init__(self, foreground=False):
        # daemon specific
        self.stdin_path = '/dev/null'

        if foreground:
            self.stdout_path = '/dev/stdout'
            self.stderr_path = '/dev/stderr'
        else:
            self.stdout_path = '/dev/null'
            self.stderr_path = '/dev/null'

        self.pidfile_path = context.app_config['daemon']['pid']
        self.pidfile_timeout = 1

        # init
        self.object_managers = {}
        self.object_manager_order = ['system', 'nginx', 'plus']
        self.bridge = None
        self.bridge_object = None
        self.start_time = int(time.time())
        self.last_cloud_talk_time = 0
        self.cloud_talk_fails = 0
        self.cloud_talk_delay = 0
        self.is_running = True

    def init_object_managers(self):
        """
        Tries to load and create all object managers specified in config
        """
        object_managers_from_local_config = context.app_config['containers']

        for object_type in self.object_manager_order:
            try:
                object_manager_classname = self.MANAGER_CLASS % object_type.title()
                manager_class = loader.import_class(self.MANAGER_MODULE % (object_type, object_manager_classname))

                # copy object configs
                if object_type in self.object_managers:
                    object_configs = copy.copy(self.object_managers[object_type].object_configs)
                else:
                    object_configs = None

                self.object_managers[object_type] = manager_class(
                    object_configs=object_configs
                )
                context.log.debug('loaded "%s" object manager from %s' % (object_type, manager_class))
            except:
                context.log.error('failed to load %s object manager' % object_type, exc_info=True)

    def run(self):
        # get correct pid
        context.set_pid()

        # set thread name
        current_thread().name = 'supervisor'

        # get initial config from cloud
        self.talk_to_cloud(initial=True)

        # init object managers
        self.init_object_managers()

        if not self.object_managers:
            context.log.error('no object managers configured, stopping')
            return

        # run bridge manager
        self.bridge_object = Bridge()
        self.bridge = spawn(self.bridge_object.start)

        # main cycle
        while True:
            time.sleep(5.0)

            if not self.is_running:
                break

            try:
                context.inc_action_id()

                for object_manager_name in self.object_manager_order:
                    object_manager = self.object_managers[object_manager_name]
                    object_manager.run()

                try:
                    if context.objects.root_object:
                        if context.objects.root_object.definition and context.objects.root_object.definition_healthy:
                            context.inc_action_id()
                            self.talk_to_cloud(root_object=context.objects.root_object.definition)
                        else:
                            context.log.error('Problem with root object definition, agent stopping')
                            self.stop()
                    else:
                        pass
                        # context.default_log.debug('No root object defined during supervisor main run')
                except AmplifyCriticalException:
                    pass

                self.check_bridge()
            except OSError as e:
                if e.errno == 12:  # OSError errno 12 is a memory error (unable to allocate, out of memory, etc.)
                    context.log.error('OSError: [Errno %s] %s' % (e.errno, e.message), exc_info=True)
                    continue
                else:
                    raise e

    def stop(self):
        self.is_running = False

        if self.bridge_object:
            self.bridge_object.flush_metrics()

        for object_manager_name in reversed(self.object_manager_order):
            object_manager = self.object_managers[object_manager_name]
            object_manager.stop()

    def talk_to_cloud(self, root_object=None, force=False, initial=False):
        """
        Asks cloud for config, object configs, filters, etc
        Applies gathered data to objects and agent config

        :param root_object: {} definition dict of a top object
        :param force: bool will skip time check
        :param initial: bool first run
        """
        now = int(time.time())
        if not force and (
            now <= (
                self.last_cloud_talk_time +
                context.app_config['cloud']['talk_interval'] +
                self.cloud_talk_delay
            ) or
            now < context.backpressure_time
        ):
            return

        # talk to cloud
        try:
            # reset the cloud talk counter to avoid sending new requests every 5.0 seconds.
            self.last_cloud_talk_time = int(time.time())

            cloud_response = CloudResponse(
                context.http_client.post('agent/', data=root_object)
            )

            if self.cloud_talk_delay:
                self.cloud_talk_fails = 0
                self.cloud_talk_delay = 0
                context.log.debug('successful cloud connect, reset cloud talk delay')
        except Exception as e:
            if isinstance(e, HTTPError) and e.response.status_code == 503:
                backpressure_error = HTTP503Error(e)
                context.backpressure_time = int(time.time() + backpressure_error.delay)
                context.log.debug(
                    'back pressure delay %s added (next talk: %s)' % (
                        backpressure_error.delay,
                        context.backpressure_time
                    )
                )
            else:
                self.cloud_talk_fails += 1
                self.cloud_talk_delay = exponential_delay(self.cloud_talk_fails)
                context.log.debug(
                    'cloud talk delay set to %s (fails: %s)' % (self.cloud_talk_delay, self.cloud_talk_fails)
                )

            context.log.error('could not connect to cloud', exc_info=True)
            raise AmplifyCriticalException()

        # check agent version status
        if context.version_major <= float(cloud_response.versions.obsolete):
            context.log.error(
                'agent is obsolete - cloud will refuse updates until it is updated (version: %s, current: %s)' %
                (context.version_major, cloud_response.versions.current)
            )
            self.stop()
        elif context.version_major <= float(cloud_response.versions.old):
            context.log.warn(
                'agent is old - update is recommended (version: %s, current: %s)' %
                (context.version_major, cloud_response.versions.current)
            )

        # update special object configs and filters
        changed_object_managers = set()
        matched_object_configs = set()
        for obj in cloud_response.objects:
            object_manager = self.object_managers.get(obj.type)
            if not object_manager:
                continue

            if obj.id in object_manager.object_configs:
                matched_object_configs.add(obj.id)

            if object_manager.object_configs.get(obj.id, {}) != obj.config:
                context.log.info(
                    'object config has changed. now "%s" %s is running with: %s' %
                    (obj.type, obj.id, pprint.pformat(obj.config))
                )
                object_manager.object_configs[obj.id] = obj.config
                changed_object_managers.add(obj.type)
                matched_object_configs.add(obj.id)

        # purge obsoleted object configs
        for object_type, object_manager in self.object_managers.iteritems():
            for obj_id in object_manager.object_configs.keys():
                if obj_id not in matched_object_configs:
                    context.log.debug(
                        'object config has changed. now "%s" %s is running with default settings' %
                        (object_type, obj_id)
                    )
                    del object_manager.object_configs[obj_id]
                    changed_object_managers.add(object_type)

        # global config changes
        config_changed = context.app_config.apply(cloud_response.config)

        # perform restarts
        if config_changed or len(changed_object_managers) > 0:
            context.cloud_restart = True

            if self.bridge_object:
                self.bridge_object.flush_metrics()

            if config_changed:
                context.log.debug(
                    'app config has changed. now running with: %s' %
                    pprint.pformat(context.app_config.config)
                )

                context.http_client.update_cloud_url()

                if self.object_managers:
                    for object_manager_name in reversed(self.object_manager_order):
                        object_manager = self.object_managers[object_manager_name]
                        object_manager.stop()
            elif len(changed_object_managers) > 0:
                for obj_type in changed_object_managers:
                    self.object_managers[obj_type].stop()
            if not initial:
                self.init_object_managers()
            context.cloud_restart = False

    def check_bridge(self):
        """
        Check containers threads, restart if some failed
        """
        if self.bridge.ready and self.bridge.exception:
            context.log.debug('bridge exception: %s' % self.bridge.exception)
            self.bridge = gevent.spawn(Bridge().start)
