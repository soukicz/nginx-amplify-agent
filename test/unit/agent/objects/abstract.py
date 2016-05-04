# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.objects.abstract import AbstractObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class AbstractObjectTestCase(BaseTestCase):
    def test_basic(self):
        abstract_obj = AbstractObject()

        assert_that(abstract_obj, not_(equal_to(None)))
        assert_that(abstract_obj.definition, equal_to({'id': None, 'type': 'common'}))
        assert_that(abstract_obj.definition_hash, has_length(64))
        assert_that(abstract_obj.hash(abstract_obj.definition), equal_to(abstract_obj.definition_hash))
        assert_that(abstract_obj.hash_local(1,2,3), has_length(64))
        assert_that(abstract_obj.local_id, equal_to(None))
