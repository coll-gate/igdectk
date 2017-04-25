# -*- coding: utf-8; -*-
#
# @file __init__.py
# @brief Backbone sub-module/Django-application settings.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2016-02-03
# @copyright Copyright (c) 2016 INRA
# @license MIT (see LICENSE file)
# @details

APP_VERBOSE_NAME = "igdectk.backbone"

APP_SETTINGS_MODEL = None

APP_VERSION = (1, 0, 0)

DEFAULT_PROPERTIES = {
    'underscore': {'js': 'underscore-min.js', 'css': '', 'default_version': '1.8.3', 'versions': ('1.8.3',)},
    'backbone': {'js': 'backbone-min.js', 'css': '', 'default_version': '1.3.2', 'versions': ('1.3.2',)},
    'marionette': {'js': 'backbone.marionette.min.js', 'css': '', 'default_version': '2.4.5', 'versions': ('2.4.5',)},
}
