# -*- coding: utf-8 -*-
import copy

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


class NginxConfigCollector(AbstractCollector):
    short_name = 'nginx_config'

    def __init__(self, **kwargs):
        super(NginxConfigCollector, self).__init__(**kwargs)

        self.previous_files = {}
        self.previous_directories = {}
        self.previous_checksum = None

    def collect(self):
        try:
            config = self.object.config

            # check if config is changed (changes are: new files/certs, new mtimes)
            config_files, config_dirs = config.collect_structure(include_ssl_certs=self.object.upload_ssl)
            if config_files == self.previous_files and config_dirs == self.previous_directories:
                return

            # parse config tree
            config.full_parse()

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

            if self.previous_checksum:
                # config changed, so we need to restart the object
                self.object.need_restart = True
            else:
                # otherwise run test
                if self.object.run_config_test and config.total_size() < 20*1024*1024:  # 20 MB
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

            self.previous_checksum = checksum
            self.previous_files = copy.copy(config_files)
            self.previous_directories = copy.copy(config_dirs)
        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.error('failed to collect due to %s' % exception_name)
            context.log.debug('additional info:', exc_info=True)

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
