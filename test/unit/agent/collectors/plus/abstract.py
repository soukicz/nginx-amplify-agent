# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.object import PlusObject
from amplify.agent.collectors.plus.abstract import PlusStatusCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusStatusCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(PlusStatusCollectorTestCase, self).setup_method(method)
        context.plus_cache = None
        context._setup_plus_cache()

    def test_basic(self):
        plus_obj = PlusObject(local_name='test_obj', parent_local_id='nginx123', root_uuid='root123')
        # Do a quick override of plus_status_internal_url_cache
        plus_obj.plus_status_internal_url_cache = 'test_status'

        status_collector = PlusStatusCollector(object=plus_obj)
        assert_that(status_collector.last_collect, equal_to(None))
        data = status_collector.gather_data()

        assert_that(data, equal_to([]))

    def test_dummy_data(self):
        plus_obj = PlusObject(local_name='test_obj', parent_local_id='nginx123', root_uuid='root123')
        # Do a quick override of plus_status_internal_url_cache
        plus_obj.plus_status_internal_url_cache = 'test_status'

        # Insert some dummy data
        context.plus_cache.put('test_status', ({'pluss': {'test_obj': {}}}, 0))

        status_collector = PlusStatusCollector(object=plus_obj)
        assert_that(status_collector.last_collect, equal_to(None))
        data = status_collector.gather_data()

        assert_that(data, equal_to([({}, 0)]))
        assert_that(status_collector.last_collect, equal_to(0))

    def test_several_dummy_data(self):
        plus_obj = PlusObject(local_name='test_obj', parent_local_id='nginx123', root_uuid='root123')
        # Do a quick override of plus_status_internal_url_cache
        plus_obj.plus_status_internal_url_cache = 'test_status'

        # Insert some dummy data
        context.plus_cache.put('test_status', ({'pluss': {'test_obj': {}}}, 0))
        context.plus_cache.put('test_status', ({'pluss': {'test_obj': {'proper': 'data'}}}, 2))

        status_collector = PlusStatusCollector(object=plus_obj)
        data = status_collector.gather_data()

        assert_that(data, has_length(2))
        assert_that(data, equal_to([({}, 0), ({'proper': 'data'}, 2)]))
        assert_that(status_collector.last_collect, equal_to(2))

    def test_old_dummy_data(self):
        plus_obj = PlusObject(local_name='test_obj', parent_local_id='nginx123', root_uuid='root123')
        # Do a quick override of plus_status_internal_url_cache
        plus_obj.plus_status_internal_url_cache = 'test_status'

        # Insert some dummy data
        context.plus_cache.put('test_status', ({'pluss': {'test_obj': {}}}, 0))
        context.plus_cache.put('test_status', ({'pluss': {'test_obj': {'proper': 'data'}}}, 2))

        status_collector = PlusStatusCollector(object=plus_obj)
        status_collector.last_collect = 1  # Hard set timestamp
        data = status_collector.gather_data()

        assert_that(data, has_length(1))
        assert_that(data, equal_to([({'proper': 'data'}, 2)]))
        assert_that(status_collector.last_collect, equal_to(2))
