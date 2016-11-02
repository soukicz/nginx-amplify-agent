# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.collectors.nginx.meta import NginxMetaCollector
from amplify.agent.managers.nginx import NginxManager
from amplify.agent.objects.nginx.binary import _parse_arguments
from test.base import NginxCollectorTestCase, RealNginxTestCase, container_test

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Arie van Luttikhuizen"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class MetaParsersTestCase(NginxCollectorTestCase):

    def test_parse_arguments_1_4_6(self):
        raw_arguments = """ --with-cc-opt='-g -O2 -fstack-protector --param=ssp-buffer-size=4 -Wformat -Werror=format-security -D_FORTIFY_SOURCE=2' --with-ld-opt='-Wl,-Bsymbolic-functions -Wl,-z,relro' --prefix=/usr/share/nginx --conf-path=/etc/nginx/nginx.conf --http-log-path=/var/log/nginx/access.log --error-log-path=/var/log/nginx/error.log --lock-path=/var/lock/nginx.lock --pid-path=/run/nginx.pid --http-client-body-temp-path=/var/lib/nginx/body --http-fastcgi-temp-path=/var/lib/nginx/fastcgi --http-proxy-temp-path=/var/lib/nginx/proxy --http-scgi-temp-path=/var/lib/nginx/scgi --http-uwsgi-temp-path=/var/lib/nginx/uwsgi --with-debug --with-pcre-jit --with-ipv6 --with-http_ssl_module --with-http_stub_status_module --with-http_realip_module --with-http_addition_module --with-http_dav_module --with-http_geoip_module --with-http_gzip_static_module --with-http_image_filter_module --with-http_spdy_module --with-hroot"""
        arguments = _parse_arguments(raw_arguments)

        assert_that(arguments.keys(), contains_inanyorder(
            'with-http_realip_module', 'with-http_spdy_module', 'with-ipv6', 'prefix', 'pid-path',
            'with-http_ssl_module', 'http-log-path', 'with-http_gzip_static_module',
            'with-http_image_filter_module', 'with-http_addition_module', 'with-http_geoip_module',
            'with-http_dav_module', 'http-fastcgi-temp-path', 'http-proxy-temp-path', 'with-ld-opt',
            'conf-path', 'with-http_stub_status_module', 'http-client-body-temp-path', 'with-debug',
            'error-log-path', 'with-hroot', 'with-cc-opt', 'http-uwsgi-temp-path',
            'http-scgi-temp-path', 'with-pcre-jit', 'lock-path'
        ))

        assert_that(arguments, not_(has_key(contains_string('--'))))

    def test_parse_arguments_nginx_1_6_2(self):
        raw_arguments = """configure arguments: --with-cc-opt='-g -O2 -fPIE -fstack-protector-strong -Wformat -Werror=format-security -D_FORTIFY_SOURCE=2' --with-ld-opt='-Wl,-Bsymbolic-functions -fPIE -pie -Wl,-z,relro -Wl,-z,now' --prefix=/usr/share/nginx --conf-path=/etc/nginx/nginx.conf --http-log-path=/var/log/nginx/access.log --error-log-path=/var/log/nginx/error.log --lock-path=/var/lock/nginx.lock --pid-path=/run/nginx.pid --http-client-body-temp-path=/var/lib/nginx/body --http-fastcgi-temp-path=/var/lib/nginx/fastcgi --http-proxy-temp-path=/var/lib/nginx/proxy --http-scgi-temp-path=/var/lib/nginx/scgi --http-uwsgi-temp-path=/var/lib/nginx/uwsgi --with-debug --with-pcre-jit --with-ipv6 --with-http_ssl_module --with-http_stub_status_module --with-http_realip_module --with-http_auth_request_module --with-http_addition_module --with-http_dav_module --with-http_geoip_module --with-http_gzip_static_module --with-http_image_filter_module --with-http_spdy_module --with-http_sub_module --with-http_xslt_module --with-mail --with-mail_ssl_module"""
        arguments = _parse_arguments(raw_arguments)

        assert_that(arguments.keys(), contains_inanyorder(
            'with-http_realip_module', 'with-http_sub_module', 'with-http_auth_request_module', 'with-http_spdy_module',
            'with-ipv6', 'prefix', 'pid-path', 'with-http_ssl_module', 'http-log-path', 'with-http_gzip_static_module',
            'with-http_image_filter_module', 'with-http_addition_module', 'with-http_geoip_module',
            'with-http_dav_module', 'http-proxy-temp-path', 'with-ld-opt', 'conf-path', 'with-http_stub_status_module',
            'http-client-body-temp-path', 'with-debug', 'error-log-path', 'http-fastcgi-temp-path', 'with-cc-opt',
            'with-mail_ssl_module', 'http-uwsgi-temp-path', 'with-http_xslt_module', 'with-mail', 'http-scgi-temp-path',
            'with-pcre-jit', 'lock-path'
        ))

    def test_parse_arguments_compound_values(self):
        raw_arguments = """configure arguments: --with-cc-opt='-g -O2 -fstack-protector --param=ssp-buffer-size=4 -Wformat -Werror=format-security --example="quoted value in a quoted value"'"""
        arguments = _parse_arguments(raw_arguments)
        assert_that(arguments, has_entry('with-cc-opt', '\'-g -O2 -fstack-protector --param=ssp-buffer-size=4 -Wformat -Werror=format-security --example="quoted value in a quoted value"\''))

    def test_parse_arguments_add_modules(self):
        raw_arguments = """configure arguments: --build=nginx-plus-extras-r7-p1 --prefix=/etc/nginx --sbin-path=/usr/sbin/nginx --conf-path=/etc/nginx/nginx.conf --error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log --pid-path=/var/run/nginx.pid --lock-path=/var/run/nginx.lock --http-client-body-temp-path=/var/cache/nginx/client_temp --http-proxy-temp-path=/var/cache/nginx/proxy_temp --http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp --http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp --http-scgi-temp-path=/var/cache/nginx/scgi_temp --user=nginx --group=nginx --with-http_ssl_module --with-http_realip_module --with-http_addition_module --with-http_sub_module --with-http_dav_module --with-http_flv_module --with-http_mp4_module --with-http_f4f_module --with-http_hls_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_random_index_module --with-http_secure_link_module --with-http_session_log_module --with-http_stub_status_module --with-http_auth_request_module --with-mail --with-mail_ssl_module --with-threads --with-file-aio --with-http_spdy_module --with-ipv6 --with-stream --with-stream_ssl_module --with-http_perl_module --with-http_image_filter_module --with-http_geoip_module --with-http_xslt_module --add-module=extra/ngx_devel_kit-0.2.19 --add-module=extra/set-misc-nginx-module-0.29 --add-module=extra/lua-nginx-module-0.9.16 --add-module=extra/headers-more-nginx-module-0.26 --add-module=extra/passenger-5.0.15/ext/nginx --add-module=extra/nginx-rtmp-module-1.1.7 --with-cc-opt='-g -O2 -fstack-protector-strong -Wformat -Werror=format-security -Wp,-D_FORTIFY_SOURCE=2' --with-ld-opt='-Wl,-Bsymbolic-functions -Wl,-z,relro -Wl,--as-needed'"""
        arguments = _parse_arguments(raw_arguments)

        assert_that(arguments, has_key('add-module'))
        assert_that(arguments['add-module'], is_(list))
        assert_that(arguments['add-module'], contains_inanyorder(
            'extra/ngx_devel_kit-0.2.19',
            'extra/set-misc-nginx-module-0.29',
            'extra/lua-nginx-module-0.9.16',
            'extra/headers-more-nginx-module-0.26',
            'extra/passenger-5.0.15/ext/nginx',
            'extra/nginx-rtmp-module-1.1.7'
        ))

    def test_parse_arguments_1_9_11(self):
        raw_arguments = """configure arguments: --prefix=/etc/nginx --sbin-path=/usr/sbin/nginx --modules-path=%{_libdir}/nginx/modules --conf-path=/etc/nginx/nginx.conf --error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log --pid-path=/var/run/nginx.pid --lock-path=/var/run/nginx.lock --http-client-body-temp-path=/var/cache/nginx/client_temp --http-proxy-temp-path=/var/cache/nginx/proxy_temp --http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp --http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp --http-scgi-temp-path=/var/cache/nginx/scgi_temp --user=nginx --group=nginx --with-http_ssl_module --with-http_realip_module --with-http_sub_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_secure_link_module --with-http_stub_status_module --with-http_auth_request_module --with-threads --with-file-aio --with-http_v2_module --with-cc-opt='-g -O2 -fstack-protector --param=ssp-buffer-size=4 -Wformat -Werror=format-security' --with-ld-opt='-Wl,-Bsymbolic-functions -Wl,-z,relro' --add-module=/opt/build/nginx/modules/nginx-lua --add-module=/opt/build/nginx/modules/ngx_pagespeed --add-module=/opt/build/nginx/modules/nginx-headers-more"""
        arguments = _parse_arguments(raw_arguments)

        assert_that(arguments, not_(has_key('configure arguments:')))
        assert_that(arguments.keys(), contains_inanyorder(
            "prefix", "sbin-path", "modules-path", "conf-path", "error-log-path", "http-log-path", "pid-path",
            "lock-path", "http-client-body-temp-path", "http-proxy-temp-path", "http-fastcgi-temp-path",
            "http-uwsgi-temp-path", "http-scgi-temp-path", "user", "group", "with-http_ssl_module",
            "with-http_realip_module", "with-http_sub_module", "with-http_gunzip_module",
            "with-http_gzip_static_module", "with-http_secure_link_module", "with-http_stub_status_module",
            "with-http_auth_request_module", "with-threads", "with-file-aio", "with-http_v2_module", "with-cc-opt",
            "with-ld-opt", "add-module"
        ))

        assert_that(arguments, has_key('add-module'))
        assert_that(arguments['add-module'], contains_inanyorder(
            '/opt/build/nginx/modules/nginx-lua',
            '/opt/build/nginx/modules/ngx_pagespeed',
            '/opt/build/nginx/modules/nginx-headers-more'
        ))

class NginxMetaCollectorTestCase(RealNginxTestCase):

    def test_collect_meta(self):
        container = NginxManager()
        container._discover_objects()
        nginx_obj = container.objects.find_all(types=container.types)[0]

        collector = NginxMetaCollector(object=nginx_obj, interval=nginx_obj.intervals['meta'])
        assert_that(not_(collector.in_container))
        collector.collect()

        assert_that(nginx_obj.metad.current, contains_inanyorder(
            'type', 'local_id', 'root_uuid', 'running', 'stub_status_enabled', 'status_module_enabled', 'ssl',
            'stub_status_url', 'plus_status_url', 'version', 'plus', 'configure', 'packages', 'path',
            'built_from_source', 'parent_hostname', 'start_time', 'pid'
        ))

    @container_test
    def test_collect_meta_in_container(self):

        container = NginxManager()
        container._discover_objects()
        nginx_obj = container.objects.find_all(types=container.types)[0]

        collector = NginxMetaCollector(object=nginx_obj, interval=nginx_obj.intervals['meta'])
        assert_that(collector.in_container)
        collector.collect()

        assert_that(nginx_obj.metad.current, contains_inanyorder(
            'type', 'local_id', 'root_uuid', 'running', 'stub_status_enabled', 'status_module_enabled', 'ssl',
            'stub_status_url', 'plus_status_url', 'version', 'plus', 'configure', 'packages', 'path',
            'built_from_source', 'parent_hostname',
        ))
