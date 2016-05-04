# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.context import context
from amplify.agent.objects.plus.abstract import PlusObject
from amplify.agent.objects.plus.collectors.meta.common import PlusObjectMetaCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusMetaCollectorTestCase(BaseTestCase):
    def setup_method(self, method):
        super(PlusMetaCollectorTestCase, self).setup_method(method)
        self.plus_obj = PlusObject(local_name='test_obj', parent_local_id='nginx123', root_uuid='root123')

    def teardown_method(self, method):
        self.plus_obj = None
        super(PlusMetaCollectorTestCase, self).teardown_method(method)

    def test_meta_collect(self):
        meta_collector = PlusObjectMetaCollector(object=self.plus_obj)
        meta_collector.collect()

        meta = self.plus_obj.metad.current
        assert_that(meta, not_none())

        assert_that(meta, equal_to(
            {
                'type': 'nginx_plus',
                'local_name': 'test_obj',
                'local_id': 'a9b8f9caa98ee30806a4a7c17ba393330059317600d768e4c81b2d585f7b9a6a',
                'root_uuid': 'root123',
                'hostname': context.hostname,
                'version': None,  # Version will fail because this test is done in a vacuum without parent nginx
                'warnings': []
            }
        ))
