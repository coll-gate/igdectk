# -*- coding: utf-8; -*-
#
# @file context_processors.py
# @brief Context processor to insert the module context to each view.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2016-02-03
# @copyright Copyright (c) 2016 INRA
# @license MIT (see LICENSE file)
# @details

from .manager import module_manager


def module(request):
    """
    Adds module context variables to the context.
    """
    return {
        'menus': module_manager.menus,
    }
