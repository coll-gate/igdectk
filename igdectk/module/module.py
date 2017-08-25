# -*- coding: utf-8; -*-
#
# @file module.py
# @brief Module object.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2016-02-03
# @copyright Copyright (c) 2016 INRA
# @license MIT (see LICENSE file)
# @details

from django.core.exceptions import ImproperlyConfigured

from .menu import MenuEntryBase, MenuSeparator, MenuEntry
from . import AUTH_TYPE, AUTH_ANY


class ModuleException(ImproperlyConfigured):
    """
    Base exception for module registration and definition.
    """

    pass


class ModuleMenu(object):
    """
    A merge-able menu for a module. It contains ordered menu entries.
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

    def dump(self):
        entries = []

        for entry in self.entries:
            e = {
                'name': entry.name,
                'order': entry.order,
                'auth': AUTH_TYPE[entry.auth][2].split('-')[1]
            }

            if isinstance(entry, MenuEntry):
                e['type'] = 'entry'
                e['icon'] = entry.icon.value
                e['label'] = str(entry.label)
                e['url'] = entry.url
            elif isinstance(entry, MenuSeparator):
                e['type'] = 'separator'
            else:
                continue

            entries.append(e)

        return {
            'name': self.name,
            'label': str(self.label),
            'order': self.order,
            'auth': self.auth_class().split('-')[1],
            'entries': entries
        }


class Module(object):
    """
    The module itself that must be registered into the ModuleManager singleton.
    """

    def __init__(self, name, verbose_name="", base_url=""):
        # module name
        self.name = name

        # module verbose name
        self.verbose_name = verbose_name

        # list of registered menus
        self.menus = []

        # prefix for URLs
        self.base_url = base_url

        # client side module (default is True)
        self.client_export = True

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

        # an exception is raised if a module doesn't exists
        from importlib import import_module
        for module in modules:
            import_module("%s.%s" % (self.name, module))

        RestHandler.register_urls()

    def has_client(self):
        return self.client_export
