# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 INRA UMR1095 GDEC

"""
Module manager with template context definition.
"""

from .module import Module, ModuleException


class ModuleManager(object):

    def __init__(self):
        self._menus = []

    def register_module(self, module):
        if not isinstance(module, Module):
            raise ModuleException('Must be a Module')

        if module.menus:
            for menu in module.menus:
                # TODO merge menus
                self._menus.append(menu)

    @property
    def menus(self):
        return self._menus

# singleton
module_manager = ModuleManager()
