# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Bootstrap sub-module/Django-application settings
"""

APP_VERBOSE_NAME = "igdectk.bootstrap"

APP_SETTINGS_MODEL = None

APP_VERSION = (1, 0, 3)

DEFAULT_PROPERTIES = {
    'bootstrap': {'js': 'bootstrap.min.js', 'css': ('bootstrap.min.css', 'bootstrap-theme.min.css'), 'default_version': '3.3.6', 'versions': ('3.3.6',)},
    'contextmenu': {'js': 'bootstrap-contextmenu.js', 'css': '', 'default_version': '0.2.0', 'versions': ('0.2.0',)},
    'igdectk': {
        '.alert': {'js': 'alert.js', 'css': '', 'default_version': '1.0.0', 'versions': ('1.0.0', '2.0.0')},
        '.helper': {'js': 'helper.js', 'css': 'helper.css', 'default_version': '1.0.0', 'versions': ('1.0.0', '2.0.0')},
    },
    'select': {'js': 'bootstrap-select.min.js', 'css': 'bootstrap-select.min.css', 'default_version': '1.10.0', 'versions': ('1.10.0',)}
}
