# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Base class for packager templage node.
"""

import re

import django.template

from django.core.exceptions import ImproperlyConfigured


class Node(django.template.Node):

    """
    Base class for template node packager's.
    """

    VALIDATOR = re.compile(r'^([a-zA-Z0-9-]+)(\.[a-zA-Z0-9-]+){0,1}_([a-zA-Z0-9-]+)(\|[a-zA-Z0-9\-]+){0,1}(#[a-zA-Z0-9-_\.]+){0,1}$')

    @property
    def validator(self):
        return Node.VALIDATOR

    def get_default_version(self, libname, sublibname=None):
        raise ImproperlyConfigured('Missing get_default_version override')

    def get_default_theme(self, libname, sublibname=None):
        raise ImproperlyConfigured('Missing get_default_theme override')
