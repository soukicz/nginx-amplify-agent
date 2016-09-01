# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.objects.plus.object import PlusObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PlusObjectTestCase(BaseTestCase):
    def test_basic(self):
        plus_obj = PlusObject(local_name='test_obj', parent_local_id='nginx123', root_uuid='root123')

        assert_that(plus_obj, not_(equal_to(None)))
        assert_that(plus_obj.definition, equal_to(
            {'type': 'nginx_plus', 'local_id': plus_obj.local_id, 'root_uuid': 'root123'}
        ))
        assert_that(plus_obj.definition_hash, has_length(64))
        assert_that(plus_obj.hash(plus_obj.definition), equal_to(plus_obj.definition_hash))
        assert_that(plus_obj.local_id_args, has_length(3))
        assert_that(plus_obj.local_id, has_length(64))
        assert_that(
            plus_obj.hash_local(
                plus_obj.local_id_args[0],
                plus_obj.local_id_args[1],
                plus_obj.local_id_args[2]
            ),
            equal_to(plus_obj.local_id)
        )
        assert_that(plus_obj.collectors, has_length(1))
