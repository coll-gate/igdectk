# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Django Bootstrap application main
"""

from igdectk.packager.apphelpers import PackagerApplicationMain


class IgdecTkBootstrap(PackagerApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])
