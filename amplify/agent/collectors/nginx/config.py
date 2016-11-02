# -*- coding: utf-8 -*-
import time

from amplify.agent.data.eventd import CRITICAL, WARNING, INFO
from amplify.agent.collectors.abstract import AbstractCollector

from amplify.agent.common.context import context
from amplify.agent.objects.nginx.config.config import NginxConfig

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"

MAX_SIZE_FOR_TEST = 20 * 1024 * 1024 # 20 MB
DEFAULT_PARSE_DELAY = 60.0

class NginxConfigCollector(AbstractCollector):
    short_name = 'nginx_config'

    def __init__(self, previous=None, **kwargs):
        super(NginxConfigCollector, self).__init__(**kwargs)

        self.previous = previous or {
            'files': {},
            'directories': {},
            'checksum': None
        }

        self.parse_delay = context.app_config['containers'].get('nginx', {}).get('parse_delay', DEFAULT_PARSE_DELAY)

        self.register(
            self.parse_config
        )

    def parse_config(self, no_delay=False):
        """
        Parses the NGINX configuration file.

        Will not run if:
            a) it hasn't been long enough since the last time it parsed (unless `no_delay` is True)
            b) the configuration files/directories from the last parse haven't changed

        :param no_delay: bool - ignore delay times for this run (useful for testing)
        """
        config = self.object.config

        # don't parse config if it hasn't been long enough since last parse
        if not no_delay and time.time() < config.wait_until:
            return

        files, directories = config.collect_structure(include_ssl_certs=self.object.upload_ssl)

        # check if config is changed (changes are: new files/certs, new mtimes)
        if files == self.previous['files'] and directories == self.previous['directories']:
            return

        self.previous['files'] = files
        self.previous['directories'] = directories

        # parse config tree
        start_time = time.time()
        try:
            config.full_parse()
        finally:
            elapsed_time = time.time() - start_time
            delay = 0 if no_delay else max(elapsed_time * 2, self.parse_delay)
            config.wait_until = start_time + delay

        # Send event for parsing nginx config.
        # Use config.parser.filename to account for default value defined in NginxConfigParser.
        self.object.eventd.event(
            level=INFO,
            message='nginx config parsed, read from %s' % config.filename,
        )
        for error in config.parser_errors:
            self.object.eventd.event(level=WARNING, message=error)

        # run ssl checks
        if self.object.upload_ssl:
            config.run_ssl_analysis()
        else:
            context.log.info('ssl analysis skipped due to users settings')

        # run upload
        checksum = config.checksum()
        if self.object.upload_config:
            self.upload(config, checksum)

        # config changed, so we need to restart the object
        if self.previous['checksum']:
            self.object.need_restart = True

        # otherwise run test
        elif self.object.run_config_test and config.total_size() < MAX_SIZE_FOR_TEST:
            run_time = config.run_test()

            # send event for testing nginx config
            if config.test_errors:
                self.object.eventd.event(level=WARNING, message='nginx config test failed')
            else:
                self.object.eventd.event(level=INFO, message='nginx config tested ok')

            for error in config.test_errors:
                self.object.eventd.event(level=CRITICAL, message=error)

            # stop -t if it took too long
            if run_time > context.app_config['containers']['nginx']['max_test_duration']:
                context.app_config['containers']['nginx']['run_test'] = False
                context.app_config.mark_unchangeable('run_test')
                self.object.eventd.event(
                    level=WARNING,
                    message='%s -t -c %s took %s seconds, disabled until agent restart' % (
                        config.binary, config.filename, run_time
                    )
                )
                self.object.run_config_test = False

        self.previous['checksum'] = checksum

    def handle_exception(self, method, exception):
        super(NginxConfigCollector, self).handle_exception(method, exception)
        self.object.eventd.event(
            level=INFO,
            message='nginx config parser failed, path %s' % self.object.conf_path,
            onetime=True
        )

    def upload(self, config, checksum):
        payload = {
            'root': config.filename,
            'index': config.index,
            'tree': config.tree,
            'directory_map': config.directory_map,
            'files': config.files,
            'directories': config.directories,
            'ssl_certificates': config.ssl_certificates,
            'access_logs': config.access_logs,
            'error_logs': config.error_logs,
            'errors': {
                'parser': len(config.parser_errors),
                'test': len(config.test_errors)
            }
        }
        self.object.configd.config(payload=payload, checksum=checksum)
