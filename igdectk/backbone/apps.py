# -*- coding: utf-8; -*-
#
# @file __init__.py
# @brief Django Backbone application main.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2016-02-03
# @copyright Copyright (c) 2016 INRA
# @license MIT (see LICENSE file)
# @details

from igdectk.packager.apphelpers import PackagerApplicationMain


class IgdecTkBackbone(PackagerApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])
