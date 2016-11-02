# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.common.context import context
from test.base import BaseTestCase
from test.fixtures.defaults import *

__author__ = "Arie van Luttikhuizen"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"]
__license__ = ""
__maintainer__ = "Arie van Luttikhuizen"
__email__ = "arie@nginx.com"


class ContextTestCase(BaseTestCase):
    def test_uuid(self):
        assert_that(context.app_config['credentials'], has_entry('imagename', none()))
        assert_that(context.app_config['credentials'], has_entry('hostname', DEFAULT_HOST))
        assert_that(context.app_config['credentials'], has_entry('api_key', DEFAULT_API_KEY))
        assert_that(context.app_config['credentials'], has_entry('uuid', DEFAULT_UUID))
        assert_that(context.uuid, equal_to(DEFAULT_UUID))


class ContextContainerTestCase(BaseTestCase):

    def setup_method(self, method):
        super(ContextContainerTestCase, self).setup_method(method)
        context.app_config['credentials']['imagename'] = 'DockerTest'
        context.setup(app='test', app_config=context.app_config)

    def teardown_method(self, method):
        context.app_config['credentials']['imagename'] = None
        context.app_config['credentials']['uuid'] = DEFAULT_UUID
        context.setup(app='test', app_config=context.app_config)

    def test_uuid(self):
        assert_that(context.app_config['credentials'], has_entry('imagename', 'DockerTest'))
        assert_that(context.app_config['credentials'], has_entry('api_key', DEFAULT_API_KEY))
        assert_that(context.app_config['credentials'], has_entry('uuid', 'container-DockerTest'))
        assert_that(context.uuid, equal_to('container-DockerTest'))
