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

    """
    Base exception for module registration and definition.
    """

    pass


class ModuleMenu(object):

    """
    A mergable menu for a module. It contains ordered menu entries.
    """

    def __init__(self, name, label, order=-1, auth=AUTH_ANY):
        self.name = name
        self.label = label
        self.order = order
        self.auth = auth
        self.entries = []

    def __eq__(self, other):
        return self.order == other.order

    def __lt__(self, other):
        return self.order < other.order

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

    """
    The module itself that must be registered into the ModuleManager singleton.
    """

    def __init__(self, name, verbose_name="", base_url=""):
        self.name = name
        self.verbose_name = verbose_name
        self.menus = []
        self.base_url = base_url

    def merge_menu(self, org, menu):
        for entry in menu.entries:
            org.add_entry(entry)

    def add_menu(self, menu):
        """
        Add a new menu to this module. If the menu already exists
        it is merged with the previous one.
        :param menu: A valid module menu.
        """
        if not menu:
            return
        if not isinstance(menu, ModuleMenu):
            raise ModuleException('menu Must be a ModuleMenu')

        for m in self.menus:
            if m.name == menu.name:
                # merge menu on existing
                self.merge_menu(m, menu)
                return

        i = 0
        for m in self.menus:
            if m.order <= menu.order:
                i += 1
            else:
                break
        self.menus.insert(i, menu)

    def include_urls(self, modules=()):
        from igdectk.rest.handler import RestHandler
        RestHandler.include_main_url(self.name, self.base_url)

        __import__(self.name, fromlist=modules)

        RestHandler.register_urls()
