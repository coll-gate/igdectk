# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 INRA UMR1095 GDEC

"""
Module menu objects.
"""

from django.core.urlresolvers import reverse

from . import AUTH_TYPE, AUTH_ANY


class MenuEntryBase(object):

    """
    Base class for any menu entry.
    """

    def __init__(self, name, order=-1, auth=AUTH_ANY):
        self.name = name
        self.order = order
        self.auth = auth

    def __eq__(self, other):
        return self.order == other.order

    def __lt__(self, other):
        return self.order < other.order

    def auth_class(self):
        return AUTH_TYPE[self.auth][2]


class MenuEntry(MenuEntryBase):

    """
    Labeled menu entry.
    """

    def __init__(self, name, label, url, icon=None, order=-1, auth=AUTH_ANY):
        super(MenuEntry, self).__init__(name, order, auth)

        self.label = label
        self.url = reverse(url) if ':' in url else url
        self.icon = icon


class MenuSeparator(MenuEntryBase):

    """
    Menu separator without label neither url.
    """

    def __init__(self, order=-1, auth=AUTH_ANY):
        super(MenuSeparator, self).__init__(None, order, auth)
