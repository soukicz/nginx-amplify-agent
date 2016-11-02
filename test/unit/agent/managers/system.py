# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import RealNginxTestCase
from test.fixtures.defaults import DEFAULT_UUID, DEFAULT_HOST

from amplify.agent.common.context import context
from amplify.agent.managers.system import SystemManager


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class SystemManagerTestCase(RealNginxTestCase):
    def setup_method(self, method):
        super(SystemManagerTestCase, self).setup_method(method)
        context.objects = None
        context._setup_object_tank()

    def teardown_method(self, method):
        context.objects = None
        context._setup_object_tank()
        super(SystemManagerTestCase, self).teardown_method(method)

    def test_discover(self):
        system_manager = SystemManager()
        system_manager._discover_objects()
        assert_that(system_manager.objects.find_all(types=system_manager.types), has_length(1))

        # get the system object
        system_obj = system_manager.objects.find_all(types=system_manager.types)[0]

        assert_that(system_obj.type, equal_to('system'))
        assert_that(system_obj.uuid, equal_to(DEFAULT_UUID))
        assert_that(system_obj.hostname, equal_to(DEFAULT_HOST))


class ContainerSystemManagerTestCase(RealNginxTestCase):
    def setup_method(self, method):
        super(ContainerSystemManagerTestCase, self).setup_method(method)
        context.objects = None
        context._setup_object_tank()

        context.app_config['credentials']['imagename'] = 'DockerTest'
        context.app_config['credentials']['uuid'] = None
        context.setup(app='test', app_config=context.app_config)

    def teardown_method(self, method):
        context.app_config['credentials']['imagename'] = None
        context.app_config['credentials']['uuid'] = DEFAULT_UUID
        context.setup(app='test', app_config=context.app_config)

        context.objects = None
        context._setup_object_tank()
        super(ContainerSystemManagerTestCase, self).teardown_method(method)

    def test_discover(self):
        system_manager = SystemManager()
        system_manager._discover_objects()
        assert_that(system_manager.objects.find_all(types=system_manager.types), has_length(1))

        # get the system object
        system_obj = system_manager.objects.find_all(types=system_manager.types)[0]

        assert_that(system_obj.type, equal_to('container'))
        assert_that(system_obj.imagename, equal_to('DockerTest'))
        assert_that(system_obj.uuid, equal_to('container-DockerTest'))
