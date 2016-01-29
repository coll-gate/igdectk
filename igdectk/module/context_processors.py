# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 INRA UMR1095 GDEC

"""
Context processor to insert the module context to each view.
"""

from .manager import module_manager


def module(request):
    """
    Adds module context variables to the context.
    """
    return {
        'menus': module_manager.menus,
    }
