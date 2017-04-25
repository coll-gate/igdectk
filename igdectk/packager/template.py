# -*- coding: utf-8; -*-
#
# @file template.py
# @brief Base class for packager templage node.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2014-06-03
# @copyright Copyright (c) 2014 INRA
# @license MIT (see LICENSE file)
# @details

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

        :param str libname: Valid library name
        :param str sublibname: Optional sub-library name (empty string or None if not)
        :param str version: Queried valid version string as 'x.y.z' format.

        :return: True if the version exists.
        :rtype: boolean
        """
        return False

    def get_default_version(self, libname, sublibname=None):
        """
        Get the default version string for the specific library and optionnaly sub-library.

        :param str libname: Valid library name
        :param str sublibname: Optional sub-library name (empty string or None if not)

        :return: Default version string as 'x.y.z' format.
        :rtype: str
        """
        raise ImproperlyConfigured('Missing get_default_version override')

    def has_theme(self, libname, sublibname, theme):
        """
        Check if for a specific library and optionnaly sub-library
        is defined a specific theme.

        :param str libname: Valid library name
        :param str sublibname: Optional sub-library name (empty string or None if not)
        :param str theme: Queried valid theme string.

        :return: True if the version exists.
        :rtype: boolean
        """
        raise ImproperlyConfigured('Missing get_default_theme override')

    def get_default_theme(self, libname, sublibname=None):
        """
        Get the default theme string for the specific library and optionnaly sub-library.

        :param str libname: Valid library name
        :param str sublibname: Optional sub-library name (empty string or None if not)

        :return: Default theme string or None.
        :rtype: str
        """
        return False
