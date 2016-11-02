# -*- coding: utf-8 -*-
from amplify.agent.common.config.app import Config
from test.fixtures.defaults import *

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class TestingConfig(Config):
    filename = 'etc/agent.conf.testing'
    write_new = True

    config_changes = dict(
        daemon=dict(
            cpu_limit=1000.0,
            cpu_sleep=0.01
        ),
        cloud=dict(
            api_url=DEFAULT_API_URL,
            verify_ssl_cert=False,
        ),
        credentials=dict(
            uuid=DEFAULT_UUID,
            api_key=DEFAULT_API_KEY,
            hostname=DEFAULT_HOST
        ),
        containers=dict(
            system=dict(
                poll_intervals=dict(
                    discover=10.0,
                    meta=30.0,
                    metrics=20.0,
                    logs=10.0
                )
            ),
            nginx=dict(
                parse_delay=0,
                upload_config=True,
                run_test=True,
                max_test_duration=10.0,
                upload_ssl=True,
                poll_intervals=dict(
                    discover=10.0,
                    meta=30.0,
                    metrics=20.0,
                    logs=10.0,
                    configs=10.0,
                ),
            ),
            plus=dict(
                poll_intervals=dict(
                    discover=10.0,
                    meta=30.0,
                    metrics=20.0,
                )
            )
        )
    )
