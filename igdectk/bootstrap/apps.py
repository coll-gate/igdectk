# -*- coding: utf-8; -*-
#
# @file apps.py
# @brief Django Bootstrap application main.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-04-13
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details

from igdectk.packager.apphelpers import PackagerApplicationMain


class IgdecTkBootstrap(PackagerApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])
