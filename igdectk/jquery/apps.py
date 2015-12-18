# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Django Jquery application main
"""

from igdectk.common.apphelpers import ApplicationMain
from django.conf import settings


class IgdecTkJquery(ApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])

    def ready(self):
        packages = getattr(settings, 'INSTALLED_PACKAGES')
        if packages:
            if '__%PACKAGERS%__' not in packages:
                packages['__%PACKAGERS%__'] = ()

            packages['__%PACKAGERS%__'] = packages['__%PACKAGERS%__'] + ('jquery',)

        super().ready()
