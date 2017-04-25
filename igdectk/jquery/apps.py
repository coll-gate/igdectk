# -*- coding: utf-8; -*-
#
# @file apps.py
# @brief Django Jquery application main
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-07-09
# @copyright Copyright (c) 2017 INRA
# @license MIT (see LICENSE file)
# @details

from igdectk.packager.apphelpers import PackagerApplicationMain


class IgdecTkJquery(PackagerApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])
