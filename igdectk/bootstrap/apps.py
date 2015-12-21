# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Django Bootstrap application main
"""

from igdectk.common.apphelpers import ApplicationMain


class IgdecTkBootstrap(ApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])
