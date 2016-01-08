# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Django Jquery application main
"""

from igdectk.packager.apphelpers import PackagerApplicationMain


class IgdecTkJquery(PackagerApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])
