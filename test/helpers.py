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


class DummyObject(AbstractObject):
    """
    Dummy object to be used in unit tests of which require/use objects.
    """
    type = 'dummy'

    def __init__(self, **kwargs):
        super(DummyObject, self).__init__(**kwargs)


class DummyRootObject(DummyObject):
    """
    Dummy root object...
    """
    type = 'system'


def collected_metric(matcher=None):
    return only_contains(
        instance_of(tuple),
        has_length(2),
        contains(greater_than(1476820876), matcher or anything())
    )
