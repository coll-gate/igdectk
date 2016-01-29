# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 INRA UMR1095 GDEC

"""
Module object.
"""

from django.core.exceptions import ImproperlyConfigured

from .menu import MenuEntryBase, MenuSeparator
from . import AUTH_TYPE, AUTH_ANY


class ModuleException(ImproperlyConfigured):
    pass


class ModuleMenu(object):

    def __init__(self, name, label, auth=AUTH_ANY):
        self.name = name
        self.label = label
        self.auth = auth
        self.entries = []

    def add_entry(self, entry):
        if entry:
            if not isinstance(entry, MenuEntryBase):
                raise ModuleException('entry Must be a ModuleMenuEntryBase')

            if entry.name:
                for e in self.entries:
                    if e.name == entry.name:
                        raise ModuleException('Menu entry %s is already defined' % entry.name)

            i = 0
            for e in self.entries:
                if e.order <= entry.order:
                    i += 1
                else:
                    break
            self.entries.insert(i, entry)
        else:
            self.entries.append(MenuSeparator())

    def auth_class(self):
        return AUTH_TYPE[self.auth][2]


class Module(object):

    def __init__(self, name, verbose_name=""):
        self.name = name
        self.verbose_name = verbose_name
        self.menus = []

    def add_menu(self, menu):
        if not menu:
            return
        if not isinstance(menu, ModuleMenu):
            raise ModuleException('menu Must be a ModuleMenu')

        for m in self.menus:
            if m.name == menu.name:
                raise ModuleException('Menu %s is already defined' % menu.name)

        self.menus.append(menu)
