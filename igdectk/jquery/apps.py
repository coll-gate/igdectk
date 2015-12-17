# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Django Jquery application main
"""

from igdectk.common.apphelpers import ApplicationMain


class IgdecTkJquery(ApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])

    def ready(self):
        super().ready()
