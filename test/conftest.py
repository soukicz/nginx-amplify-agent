# -*- coding: utf-8 -*-
import pytest

from amplify.agent.common.context import context

__author__ = "Arie van Luttikhuizen"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen"]
__license__ = ""
__maintainer__ = "Arie van Luttikhuizen"
__email__ = "arie@nginx.com"


@pytest.yield_fixture
def docker():
    """
    Use this fixture to test how the agent will act in a Docker container.
    """
    context.app_config['credentials']['imagename'] = 'DockerTest'
    yield
    context.app_config['credentials']['imagename'] = None
