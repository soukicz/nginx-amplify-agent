# -*- coding: utf-8 -*-
import time

from amplify.agent.collectors.nginx.accesslog import NginxAccessLogsCollector
from amplify.agent.collectors.nginx.config import NginxConfigCollector
from amplify.agent.collectors.nginx.errorlog import NginxErrorLogsCollector
from amplify.agent.collectors.nginx.metrics import NginxMetricsCollector

from amplify.agent.common.context import context
from amplify.agent.common.util import host, http, net
from amplify.agent.data.eventd import INFO
from amplify.agent.objects.abstract import AbstractObject
from amplify.agent.objects.nginx.binary import nginx_v
from amplify.agent.objects.nginx.config.config import NginxConfig
from amplify.agent.objects.nginx.filters import Filter
from amplify.agent.pipelines.syslog import SyslogTail
from amplify.agent.pipelines.file import FileTail


__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class NginxObject(AbstractObject):
    type = 'nginx'

    def __init__(self, **kwargs):
        super(NginxObject, self).__init__(**kwargs)

        # Have to override intervals here because new container sub objects.
        self.intervals = context.app_config['containers'].get('nginx', {}).get('poll_intervals', {'default': 10})

        self.root_uuid = self.data.get(
            'root_uuid') or context.objects.root_object.uuid if context.objects.root_object else None
        self.local_id_cache = self.data['local_id']  # Assigned by manager
        self.pid = self.data['pid']
        self.version = self.data['version']
        self.workers = self.data['workers']
        self.prefix = self.data['prefix']
        self.bin_path = self.data['bin_path']
        self.conf_path = self.data['conf_path']

        # agent config
        default_config = context.app_config['containers']['nginx']
        self.upload_config = self.data.get('upload_config') or default_config.get('upload_config', False)
        self.run_config_test = self.data.get('run_test') or default_config.get('run_test', False)
        self.upload_ssl = self.data.get('upload_ssl') or default_config.get('upload_ssl', False)

        # nginx -V data
        self.parsed_v = nginx_v(self.bin_path)

        # filters
        self.filters = [Filter(**raw_filter) for raw_filter in self.data.get('filters') or []]

        # nginx config
        if 'config_data' in self.data:
            self.config = self.data['config_data']['config']
            self._restore_config_collector(self.data['config_data']['previous'])
        else:
            self.config = NginxConfig(self.conf_path, prefix=self.prefix, binary=self.bin_path)
            self._setup_config_collector()

        # plus status
        self.plus_status_external_url, self.plus_status_internal_url = self.get_alive_plus_status_urls()
        self.plus_status_enabled = True if (self.plus_status_external_url or self.plus_status_internal_url) else False

        # stub status
        self.stub_status_url = self.get_alive_stub_status_url()
        self.stub_status_enabled = True if self.stub_status_url else False

        self.processes = []

        self._setup_meta_collector()
        self._setup_metrics_collector()
        self._setup_access_logs()
        self._setup_error_logs()

    @property
    def definition(self):
        # Type is hard coded so it is not different from ContainerNginxObject.
        return {'type': 'nginx', 'local_id': self.local_id, 'root_uuid': self.root_uuid}

    def get_alive_stub_status_url(self):
        """
        Tries to get alive stub_status url
        Records some events about it
        :return:
        """
        urls_to_check = self.config.stub_status_urls

        if 'stub_status' in context.app_config.get('nginx', {}):
            predefined_uri = context.app_config['nginx']['stub_status']
            urls_to_check.append(http.resolve_uri(predefined_uri))

        stub_status_url = self.__get_alive_status(urls_to_check)
        if stub_status_url:
            # Send stub detected event
            self.eventd.event(
                level=INFO,
                message='nginx stub_status detected, %s' % stub_status_url
            )
        else:
            self.eventd.event(
                level=INFO,
                message='nginx stub_status not found in nginx config'
            )
        return stub_status_url

    def get_alive_plus_status_urls(self):
        """
        Tries to get alive plus urls
        There are two types of plus status urls: internal and external
        - internal are for the agent and usually they have the localhost ip in address
        - external are for the browsers and usually they have a normal server name

        Returns a tuple of str or Nones - (external_url, internal_url)

        Even if external status url is not responding (cannot be accesible from the host)
        we should return it to show in our UI

        :return: (str or None, str or None)
        """
        internal_urls = self.config.plus_status_internal_urls
        external_urls = self.config.plus_status_external_urls

        if 'plus_status' in context.app_config.get('nginx', {}):
            predefined_uri = context.app_config['nginx']['plus_status']
            internal_urls.append(http.resolve_uri(predefined_uri))

        internal_status_url = self.__get_alive_status(internal_urls, json=True)
        if internal_status_url:
            self.eventd.event(
                level=INFO,
                message='nginx internal plus_status detected, %s' % internal_status_url
            )

        external_status_url = self.__get_alive_status(external_urls, json=True)
        if len(self.config.plus_status_external_urls) > 0:
            if not external_status_url:
                external_status_url = 'http://%s' % self.config.plus_status_external_urls[0]

            self.eventd.event(
                level=INFO,
                message='nginx external plus_status detected, %s' % external_status_url
            )

        return external_status_url, internal_status_url

    def __get_alive_status(self, url_list, json=False):
        """
        Tries to find alive status url
        Returns first alive url or None if all founded urls are not responding

        :param url_list: [] of urls
        :param json: bool - will try to encode json if True
        :return: None or str
        """
        for url in url_list:
            for proto in ('http://', 'https://'):
                full_url = '%s%s' % (proto, url) if not url.startswith('http') else url
                try:
                    status_response = context.http_client.get(full_url, timeout=0.5, json=json, log=False)
                    if status_response:
                        if json or 'Active connections' in status_response:
                            return full_url
                    else:
                        context.log.debug('bad response from stub/plus status url %s' % full_url)
                except:
                    context.log.debug('bad response from stub/plus status url %s' % full_url)
        return None

    def __setup_pipeline(self, name):
        """
        Sets up a pipeline/tail object for a collector based on "filename".

        :param name: Str
        :return: Pipeline
        """
        tail = None
        try:
            if name.startswith('syslog'):
                address_bucket = name.split(',', 1)[0]
                host, port, address = net.ipv4_address(
                    address=address_bucket.split('=')[1], full_format=True, silent=True
                )
                # Right now we assume AFNET address/port...e.g. no support for unix sockets

                if address in context.listeners:
                    port = int(port)  # socket requires integer port
                    tail = SyslogTail(address=(host, port))
            else:
                tail = FileTail(name)
        except Exception as e:
            context.log.error(
                'failed to initialize pipeline for "%s" due to %s (maybe has no rights?)' % (name, e.__class__.__name__)
            )
            context.log.debug('additional info:', exc_info=True)

        return tail

    def _setup_meta_collector(self):
        collector_cls = self._import_collector_class('nginx', 'meta')
        self.collectors.append(
            collector_cls(object=self, interval=self.intervals['meta'])
        )

    def _setup_metrics_collector(self):
        collector_cls = self._import_collector_class('nginx', 'metrics')
        self.collectors.append(
            collector_cls(object=self, interval=self.intervals['metrics'])
        )

    def _setup_config_collector(self):
        collector = NginxConfigCollector(object=self, interval=self.intervals['configs'])
        try:
            start_time = time.time()
            collector.collect()  # run parse on startup
        finally:
            end_time = time.time()
            context.log.debug(
                '%s config parse on startup in %.3f' % (self.definition_hash, end_time - start_time)
            )
        self.collectors.append(collector)

    def _restore_config_collector(self, previous):
        collector = NginxConfigCollector(object=self, interval=self.intervals['configs'], previous=previous)
        context.log.debug(
            '%s restored previous config collector' % self.definition_hash
        )
        self.collectors.append(collector)

    def _setup_access_logs(self):
        # access logs
        for log_description, format_name in self.config.access_logs.iteritems():
            log_format = self.config.log_formats.get(format_name)
            tail = self.__setup_pipeline(log_description)

            if tail:
                self.collectors.append(
                    NginxAccessLogsCollector(
                        object=self,
                        interval=self.intervals['logs'],
                        log_format=log_format,
                        tail=tail
                    )
                )

                # Send access log discovery event.
                self.eventd.event(level=INFO, message='nginx access log %s found' % log_description)

    def _setup_error_logs(self):
        # error logs
        for log_description, log_level in self.config.error_logs.iteritems():
            tail = self.__setup_pipeline(log_description)

            if tail:
                self.collectors.append(
                    NginxErrorLogsCollector(
                        object=self,
                        interval=self.intervals['logs'],
                        level=log_level,
                        tail=tail
                    )
                )

                # Send error log discovery event.
                self.eventd.event(level=INFO, message='nginx error log %s found' % log_description)


class ContainerNginxObject(NginxObject):
    type = 'container_nginx'
