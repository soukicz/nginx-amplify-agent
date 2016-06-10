# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.common.util import ssl
from test.base import BaseTestCase

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class SSLAnalysisTestCase(BaseTestCase):

    def test_issuer_with_apostrophe(self):
        """
        Old regex method test.
        """
        result = {}
        line = "issuer= /C=US/O=Let's Encrypt/CN=Let's Encrypt Authority X1"

        for regex in ssl.ssl_regexs:
            match_obj = regex.match(line)
            if match_obj:
                result.update(match_obj.groupdict())

        assert_that(result, has_key('organization'))
        assert_that(result['organization'], equal_to("Let's Encrypt"))
        assert_that(result, has_key('common_name'))
        assert_that(result['common_name'], equal_to("Let's Encrypt Authority X1"))

    def test_structured_parse(self):
        result = {}
        line = "subject= CN=another.domain.com,OU=Domain Control Validated"

        output = line[8:]  # trim "subject=" or "Subject:" from output
        factors = output.split(',')  # split output into distinct groups
        for factor in factors:
            key, value = factor.split('=', 1)  # only split on the first equal sign
            key = key.lstrip().upper()  # remove leading spaces (if any) and capitalize (if lowercase)
            if key in ssl.ssl_subject_map:
                result[ssl.ssl_subject_map[key]] = value

        assert_that(result, has_key('common_name'))
        assert_that(result['common_name'], equal_to('another.domain.com'))
        assert_that(result, has_key('unit'))
        assert_that(result['unit'], equal_to('Domain Control Validated'))

    def test_complicated_common_name(self):
        result = {}
        line = "Subject: C=RU, ST=SPb, L=SPb, O=Fake Org, OU=D, CN=*.fake.domain.ru/emailAddress=fake@email.cc"

        output = line[8:]  # trim "subject=" or "Subject:" from output
        factors = output.split(',')  # split output into distinct groups
        for factor in factors:
            key, value = factor.split('=', 1)  # only split on the first equal sign
            key = key.lstrip().upper()  # remove leading spaces (if any) and capitalize (if lowercase)
            if key in ssl.ssl_subject_map:
                result[ssl.ssl_subject_map[key]] = value

        assert_that(result, has_length(6))

        assert_that(result, has_key('common_name'))
        assert_that(result['common_name'], equal_to('*.fake.domain.ru/emailAddress=fake@email.cc'))
        assert_that(result, has_key('unit'))
        assert_that(result['unit'], equal_to('D'))
        assert_that(result, has_key('organization'))
        assert_that(result['organization'], equal_to('Fake Org'))
