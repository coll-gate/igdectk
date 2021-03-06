# -*- coding: utf-8; -*-
#
# @file manager.py
# @brief Module manager with template context definition.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2016-02-03
# @copyright Copyright (c) 2016 INRA
# @license MIT (see LICENSE file)
# @details

from .module import Module, ModuleException, ModuleMenu


class ModuleManager(object):

    """
    Module manager. Each module must be registered
    before to be used correctly (menu...).
    """

    def __init__(self):
        self._modules = []
        self._menus = []

    def register_module(self, module):
        """
        Register a module and its menu.
        :param module: A valid module instance
        """
        self.register_menu(module)

    def register_menu(self, module):
        """
        Register the menu for a specific module.
        :param module: A valid Module instance
        """
        if not isinstance(module, Module):
            raise ModuleException('Must be a Module')

        if module not in self._modules:
            self._modules.append(module)

        if module.menus:
            for menu in module.menus:
                src = None

                # search for an existing menu with the same label
                for m in self._menus:
                    if m.label == menu.label:
                        src = m
                        break

                # not found, then duplicate the menu from module
                if not src:
                    src = ModuleMenu(menu.name, menu.label, menu.order, menu.auth)

                    # insert sorted the menu into the global menu
                    i = 0
                    for mm in self._menus:
                        if mm.order <= src.order:
                            i += 1
                        else:
                            break
                    self._menus.insert(i, src)

                # finally merge any entries of the current menu into the existing one (global)
                for entry in menu.entries:
                    src.add_entry(entry)

    @property
    def menus(self):
        """
        Get the ordered array of menus of any registered modules.
        :return: An array of ModuleMenu
        """
        return self._menus

    @property
    def modules(self):
        """
        Get the list of installed and initialized modules.
        :return: An array of Module
        """
        return self._modules

    def get_module(self, module_name):
        """
        Get a specific module according to its unique name.
        :param module_name: string
        :return: A module or raise BadValue exception if not found
        """
        for module in self._modules:
            if module.name == module_name:
                return module

        raise ValueError("Invalid module name: " + module_name)

"""
Module manager singleton.
"""
module_manager = ModuleManager()
