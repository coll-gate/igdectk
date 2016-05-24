# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 INRA UMR1095 GDEC

"""
Django Backbone application main
"""

from igdectk.packager.apphelpers import PackagerApplicationMain


class IgdecTkBackbone(PackagerApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])
