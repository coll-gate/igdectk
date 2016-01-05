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

    def has_version(self, libname, sublibname, version):
        """
        Check if for a specific library and optionnaly sub-library
        is defined a specific version.

        Parameters
        ==========

        libname: string
            Valid library name

        sublibname: string
            Optional sub-library name (empty string or None if not)

        version: string
            Queried valid version string as 'x.y.z' format.

        Return
        ======

        : boolean
            True if the version exists.
        """
        return False

    def get_default_version(self, libname, sublibname=None):
        """
        Get the default version string for the specific library and optionnaly sub-library.

        Parameters
        ==========

        libname: string
            Valid library name

        sublibname: string
            Optional sub-library name (empty string or None if not)

        Return
        ======

        : string
            Default version string as 'x.y.z' format.
        """
        raise ImproperlyConfigured('Missing get_default_version override')

    def has_theme(self, libname, sublibname, theme):
        """
        Check if for a specific library and optionnaly sub-library
        is defined a specific theme.

        Parameters
        ==========

        libname: string
            Valid library name

        sublibname: string
            Optional sub-library name (empty string or None if not)

        theme: string
            Queried valid theme string.

        Return
        ======

        : boolean
            True if the version exists.
        """
        raise ImproperlyConfigured('Missing get_default_theme override')

    def get_default_theme(self, libname, sublibname=None):
        """
        Get the default theme string for the specific library and optionnaly sub-library.

        Parameters
        ==========

        libname: string
            Valid library name

        sublibname: string
            Optional sub-library name (empty string or None if not)

        Return
        ======

        : string
            Default theme string or None.
        """
        return False
