# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 INRA UMR1095 GDEC

"""
Backbone sub-module/Django-application settings
"""

APP_VERBOSE_NAME = "igdectk.backbone"

APP_SETTINGS_MODEL = None

APP_VERSION = (1, 0, 0)

DEFAULT_PROPERTIES = {
    'underscore': {'js': 'underscore-min.js', 'css': '', 'default_version': '1.8.3', 'versions': ('1.8.3',)},
    'backbone': {'js': 'backbone-min.js', 'css': '', 'default_version': '1.3.2', 'versions': ('1.3.2',)},
    'marionette': {'js': 'backbone.marionette.min.js', 'css': '', 'default_version': '2.4.5', 'versions': ('2.4.5',)},
}
