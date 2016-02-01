# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
JQuery sub-module/Django-application settings
"""

APP_VERBOSE_NAME = "igdectk.jquery"

APP_SETTINGS_MODEL = None

APP_VERSION = (1, 0, 3)

DEFAULT_PROPERTIES = {
    'jquery': {'js': 'jquery.min.js', 'css': '', 'default_version': '2.1.4', 'versions': ('2.1.4',)},
    'ui': {'js': 'jquery-ui.min.js', 'css': 'ui-%(theme)s/jquery-ui.min.css', 'img': '%(filename)s', 'default_version': '1.10.4', 'versions': ('1.10.4',), 'default_theme': 'lightness', 'themes': ('lightness',)},
    'fancytree': {
        'js': 'jquery.fancytree.min.js', 'css': 'skin-%(theme)s/ui.fancytree.min.css', 'default_version': '2.12.0', 'versions': ('2.12.0', '2.13.0'), 'default_theme': 'bootstrap', 'themes': ('bootstrap',),
        '.glyph': {'js': 'jquery.fancytree.glyph.min.js', 'css': '', 'default_version': '2.12.0', 'versions': ('2.12.0', '2.13.0'), 'default_theme': ''}
    },
    'select2': {
        'js': 'select2.min.js', 'css': 'select2.css', 'default_version': '3.5.4', 'versions': ('3.5.1', '3.5.4'),
        '.bootstrap': {'js': '', 'css': 'select2-bootstrap.css', 'default_version': '3.5.4', 'versions': ('3.5.1', '3.5.4')},
    },
    'colpick': {'js': 'colpick.js', 'css': 'colpick.css', 'default_version': '1.0.0', 'versions': ('1.0.0',)},
    'numeric': {'js': 'jquery.numeric.js', 'css': '', 'default_version': '1.4.1', 'versions': ('1.4.1',)},
    'igdectk': {'js': 'igdectk.js', 'css': '', 'default_version': '1.0.0', 'versions': ('1.0.0',),
        '.csrf': {'js': 'csrf.js', 'css': '', 'default_version': '1.0.0', 'versions': ('1.0.0',)},
        '.datetime': {'js': 'datetime.js', 'css': '', 'default_version': '1.0.0', 'versions': ('1.0.0',)},
    },
}
