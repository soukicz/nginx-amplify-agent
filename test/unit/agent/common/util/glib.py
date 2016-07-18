# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase, disabled_test

import amplify.agent.common.util.glib as glib


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class GlibTestCase(BaseTestCase):
    def test_overall(self):
        excludes = [
            'access-frontend-*.log',
            'receiver1-*.log',
            'frontend2.log',
            '/var/log/nginx/frontend/*',
            '/var/log/naas/'
        ]

        file_paths = [
            '/var/log/nginx/frontend/asdf.log',  # exclude 4
            '/var/log/nginx/frontend/frontend3.log',  # exclude 4
            '/var/log/blank.log',
            '/var/log/frontend2.log',  # exclude 3
            '/var/receiver1-2012.log',  # exclude 2
            '/var/log/naas/blah.log',  # exclude 5
            'access-frontend-asf.log'  # exclude 1
        ]

        results = file_paths
        for exclude_pathname in excludes:
            for match in glib.glib(file_paths, exclude_pathname):
                results.remove(match)

        assert_that(results, has_length(1))
        assert_that(results[0], equal_to('/var/log/blank.log'))

# TODO: Add more tests for individual instances and edge cases.
