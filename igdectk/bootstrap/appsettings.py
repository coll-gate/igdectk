# -*- coding: utf-8; -*-
#
# @file appsettings.py
# @brief Bootstrap sub-module/Django-application settings.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-04-13
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details

APP_VERBOSE_NAME = "igdectk.bootstrap"

APP_SETTINGS_MODEL = None

APP_VERSION = (1, 0, 4)

DEFAULT_PROPERTIES = {
    'bootstrap': {
        'js': 'bootstrap.min.js',
        'css': ('bootstrap.min.css', 'bootstrap-theme.min.css'),
        'fonts': (
            'glyphicons-halflings-regular.eot',
            'glyphicons-halflings-regular.svg',
            'glyphicons-halflings-regular.ttf',
            'glyphicons-halflings-regular.woff',
            'glyphicons-halflings-regular.woff2'),
        'default_version': '3.3.7',
        'versions': ('3.3.6', '3.3.7')
    },
    'contextmenu': {'js': 'bootstrap-contextmenu.js', 'css': '', 'default_version': '0.2.0', 'versions': ('0.2.0',)},
    'igdectk': {
        '.alert': {'js': 'alert.js', 'css': '', 'default_version': '1.0.0', 'versions': ('1.0.0', '2.0.0')},
        '.helper': {'js': 'helper.js', 'css': 'helper.css', 'default_version': '1.0.0', 'versions': ('1.0.0', '2.0.0')},
    },
    'select': {'js': 'bootstrap-select.min.js', 'css': 'bootstrap-select.min.css', 'default_version': '1.10.0', 'versions': ('1.10.0',)}
}
