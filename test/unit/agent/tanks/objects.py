# -*- coding: utf-8 -*-
from hamcrest import *
from test.base import BaseTestCase
from test.helpers import DummyObject

from amplify.agent.common.context import context
from amplify.agent.tanks.objects import ObjectsTank


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class ObjectTankTestCase(BaseTestCase):
    def setup_method(self, method):
        super(ObjectTankTestCase, self).setup_method(method)
        context.objects = None
        self.object_tank = ObjectsTank()

    def teardown_method(self, method):
        self.object_tank = None
        context.objects = ObjectsTank()
        super(ObjectTankTestCase, self).teardown_method(method)

    def test_init(self):
        assert_that(self.object_tank, is_not(equal_to(None)))

    def test_register(self):
        dummy_obj = DummyObject()

        self.object_tank.register(dummy_obj)
        assert_that(self.object_tank._ID_SEQUENCE, not_(equal_to(0)))

        assert_that(self.object_tank.objects, has_length(1))
        assert_that(self.object_tank.objects, has_key(1))
        registered_obj = self.object_tank.objects[1]

        assert_that(registered_obj, equal_to(dummy_obj))

        assert_that(self.object_tank.relations, has_length(1))
        assert_that(self.object_tank.objects_by_type, has_length(1))
        assert_that(self.object_tank.objects_by_type, has_key('dummy'))
        assert_that(self.object_tank.objects_by_type['dummy'], has_length(1))

    def test_register_multi(self):
        dummy_obj = DummyObject()
        dummy_obj_2 = DummyObject()

        obj_id_1 = self.object_tank.register(dummy_obj)
        obj_id_2 = self.object_tank.register(dummy_obj_2)

        assert_that(self.object_tank.objects, has_length(2))
        assert_that(self.object_tank.objects_by_type, has_length(1))
        assert_that(self.object_tank.objects_by_type, has_key('dummy'))
        for obj_id in (obj_id_1, obj_id_2):
            assert_that(self.object_tank.objects, has_key(obj_id))
            assert_that(self.object_tank.relations, has_key(obj_id))
            assert_that(self.object_tank.relations[obj_id], has_length(0))
            assert_that(self.object_tank.objects_by_type['dummy'], has_item(obj_id))

    def test_register_children(self):
        dummy_obj = DummyObject()
        dummy_child_1 = DummyObject()
        dummy_child_2 = DummyObject()

        parent_obj_id = self.object_tank.register(dummy_obj)
        child_obj_id_1 = self.object_tank.register(dummy_child_1, parent_id=parent_obj_id)
        child_obj_id_2 = self.object_tank.register(dummy_child_2, parent_id=parent_obj_id)

        assert_that(self.object_tank.objects, has_length(3))
        assert_that(self.object_tank.objects_by_type, has_length(1))
        assert_that(self.object_tank.objects_by_type, has_key('dummy'))
        for obj_id in (parent_obj_id, child_obj_id_1, child_obj_id_2):
            assert_that(self.object_tank.objects, has_key(obj_id))
            assert_that(self.object_tank.relations, has_key(obj_id))
            assert_that(self.object_tank.objects_by_type['dummy'], has_item(obj_id))

        assert_that(self.object_tank.relations[parent_obj_id], has_length(2))
        for obj_id in (child_obj_id_1, child_obj_id_2):
            assert_that(self.object_tank.relations[parent_obj_id], has_item(obj_id))

    def test_unregister(self):  # TODO: Do some more unregister tests.
        dummy_obj = DummyObject()

        self.object_tank.register(dummy_obj)
        assert_that(self.object_tank._ID_SEQUENCE, not_(equal_to(0)))

        assert_that(self.object_tank.objects, has_length(1))
        assert_that(self.object_tank.objects, has_key(1))
        registered_obj = self.object_tank.objects[1]

        assert_that(registered_obj, equal_to(dummy_obj))

        assert_that(self.object_tank.relations, has_length(1))
        assert_that(self.object_tank.objects_by_type, has_length(1))
        assert_that(self.object_tank.objects_by_type, has_key('dummy'))
        assert_that(self.object_tank.objects_by_type['dummy'], has_length(1))

        self.object_tank.unregister(obj_id=1)
        assert_that(self.object_tank._ID_SEQUENCE, not_(equal_to(0)))

        assert_that(self.object_tank.objects, has_length(0))

        assert_that(self.object_tank.relations, has_length(0))
        assert_that(self.object_tank.objects_by_type, has_length(1))  # We don't actually delete the empty list.
        assert_that(self.object_tank.objects_by_type, has_key('dummy'))
        assert_that(self.object_tank.objects_by_type['dummy'], has_length(0))

    def test_find_one(self):
        dummy_obj = DummyObject()

        self.object_tank.register(dummy_obj)
        assert_that(self.object_tank._ID_SEQUENCE, not_(equal_to(0)))

        assert_that(self.object_tank.objects, has_length(1))
        assert_that(self.object_tank.objects, has_key(1))
        found_obj = self.object_tank.find_one(obj_id=1)

        assert_that(found_obj, equal_to(dummy_obj))

    def test_find_all_single(self):
        dummy_obj = DummyObject()

        self.object_tank.register(dummy_obj)
        assert_that(self.object_tank._ID_SEQUENCE, not_(equal_to(0)))

        assert_that(self.object_tank.objects, has_length(1))
        assert_that(self.object_tank.objects, has_key(1))
        found_obj_list = self.object_tank.find_all(obj_id=1)

        assert_that(found_obj_list, equal_to([dummy_obj]))

    def test_find_all_single_with_children(self):
        dummy_obj = DummyObject()

        self.object_tank.register(dummy_obj)
        assert_that(self.object_tank._ID_SEQUENCE, not_(equal_to(0)))

        assert_that(self.object_tank.objects, has_length(1))
        assert_that(self.object_tank.objects, has_key(1))
        found_obj_list = self.object_tank.find_all(obj_id=1, children=True)

        assert_that(found_obj_list, equal_to([dummy_obj]))

    def test_find_all_single_by_type(self):
        dummy_obj = DummyObject()

        self.object_tank.register(dummy_obj)
        assert_that(self.object_tank._ID_SEQUENCE, not_(equal_to(0)))

        assert_that(self.object_tank.objects, has_length(1))
        assert_that(self.object_tank.objects, has_key(1))
        found_obj_list = self.object_tank.find_all(types=('dummy',))

        assert_that(found_obj_list, equal_to([dummy_obj]))

    def test_find_all_with_children(self):
        dummy_obj = DummyObject()
        dummy_child_1 = DummyObject()
        dummy_child_2 = DummyObject()

        parent_obj_id = self.object_tank.register(dummy_obj)
        child_obj_id_1 = self.object_tank.register(dummy_child_1, parent_id=parent_obj_id)
        child_obj_id_2 = self.object_tank.register(dummy_child_2, parent_id=parent_obj_id)
        found_obj_list = self.object_tank.find_all(obj_id=parent_obj_id, children=True)

        assert_that(found_obj_list, has_length(3))
        for obj in (dummy_obj, dummy_child_1, dummy_child_2):
            assert_that(found_obj_list, has_item(obj))

    def test_find_all_only_children(self):
        dummy_obj = DummyObject()
        dummy_child_1 = DummyObject()
        dummy_child_2 = DummyObject()

        parent_obj_id = self.object_tank.register(dummy_obj)
        child_obj_id_1 = self.object_tank.register(dummy_child_1, parent_id=parent_obj_id)
        child_obj_id_2 = self.object_tank.register(dummy_child_2, parent_id=parent_obj_id)
        found_obj_list = self.object_tank.find_all(parent_id=parent_obj_id)

        assert_that(found_obj_list, has_length(2))
        for obj in (dummy_child_1, dummy_child_2):
            assert_that(found_obj_list, has_item(obj))

    def test_tree_single(self):
        dummy_obj = DummyObject()

        obj_id = self.object_tank.register(dummy_obj)
        tree = self.object_tank.tree(obj_id)
        assert_that(tree, equal_to({'object': dummy_obj, 'children': []}))

    def test_tree_with_children(self):
        dummy_obj = DummyObject()
        dummy_child_1 = DummyObject()
        dummy_child_2 = DummyObject()

        parent_obj_id = self.object_tank.register(dummy_obj)
        child_obj_id_1 = self.object_tank.register(dummy_child_1, parent_id=parent_obj_id)
        child_obj_id_2 = self.object_tank.register(dummy_child_2, parent_id=parent_obj_id)
        tree = self.object_tank.tree(parent_obj_id)
        assert_that(tree, equal_to(
            {
                'object': dummy_obj,
                'children': [
                    {
                        'object': dummy_child_1,
                        'children': []
                    },
                    {
                        'object': dummy_child_2,
                        'children': []
                    }
                ]
            }
        ))

    def test_sub_tree(self):
        dummy_obj = DummyObject()
        dummy_child_1 = DummyObject()
        dummy_child_2 = DummyObject()

        parent_obj_id = self.object_tank.register(dummy_obj)
        child_obj_id_1 = self.object_tank.register(dummy_child_1, parent_id=parent_obj_id)
        child_obj_id_2 = self.object_tank.register(dummy_child_2, parent_id=parent_obj_id)
        tree = self.object_tank.tree(child_obj_id_1)
        assert_that(tree, equal_to(
            {
                'object': dummy_child_1,
                'children': []
            }
        ))

    def test_nested_tree(self):
        dummy_obj = DummyObject()
        dummy_child_1 = DummyObject()
        dummy_child_2 = DummyObject()

        parent_obj_id = self.object_tank.register(dummy_obj)
        child_obj_id_1 = self.object_tank.register(dummy_child_1, parent_id=parent_obj_id)
        child_obj_id_2 = self.object_tank.register(dummy_child_2, parent_id=child_obj_id_1)
        tree = self.object_tank.tree(parent_obj_id)
        assert_that(tree, equal_to(
            {
                'object': dummy_obj,
                'children': [
                    {
                        'object': dummy_child_1,
                        'children': [
                            {
                                'object': dummy_child_2,
                                'children': []
                            }
                        ]
                    }
                ]
            }
        ))
