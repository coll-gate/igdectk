# -*- coding: utf-8; -*-
#
# @file appsettings.py
# @brief JQuery sub-module/Django-application settings.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-07-09
# @copyright Copyright (c) 2017 INRA
# @license MIT (see LICENSE file)
# @details

APP_VERBOSE_NAME = "igdectk.jquery"

APP_SETTINGS_MODEL = None

APP_VERSION = (1, 0, 4)

DEFAULT_PROPERTIES = {
    'jquery': {'js': 'jquery.min.js', 'css': '', 'default_version': '2.1.4', 'versions': ('2.1.4', '3.2.1')},
    'ui': {
        'js': 'jquery-ui.min.js', 'css': 'ui-%(theme)s/jquery-ui.min.css', 'img': '%(filename)s', 'default_version': '1.10.4', 'versions': ('1.10.4', '1.12.1'), 'default_theme': 'lightness', 'themes': ('lightness',),
        '.datepicker-fr': {'js': 'i18n/datepicker-fr.js', 'css': '', 'default_version': '1.10.4', 'versions': ('1.10.4', '1.12.1'), 'default_theme': ''}
    },
    'fancytree': {
        'js': 'jquery.fancytree.min.js', 'css': 'skin-%(theme)s/ui.fancytree.min.css', 'default_version': '2.18.0', 'versions': ('2.12.0', '2.13.0', '2.18.0'), 'default_theme': 'bootstrap', 'themes': ('bootstrap',),
        '.glyph': {'js': 'jquery.fancytree.glyph.min.js', 'css': '', 'default_version': '2.18.0', 'versions': ('2.12.0', '2.13.0', '2.18.0'), 'default_theme': ''},
        '.filter': {'js': 'jquery.fancytree.filter.min.js', 'css': '', 'default_version': '2.18.0', 'versions': ('2.18.0',), 'default_theme': ''}
    },
    'select2': {
        'js': 'select2.min.js', 'css': 'select2.css', 'default_version': '3.5.4', 'versions': ('3.5.1', '3.5.4', '4.0.3', '4.0.4'),
        '.bootstrap': {'js': '', 'css': 'select2-bootstrap.css', 'default_version': '3.5.4', 'versions': ('3.5.1', '3.5.4', '4.0.3', '4.0.4')},
        '.fr': {'js': 'i18n/fr.js', 'css': '', 'default_version': '4.0.4', 'versions': ('4.0.3', '4.0.4')},
        '.en': {'js': 'i18n/en.js', 'css': '', 'default_version': '4.0.4', 'versions': ('4.0.3', '4.0.4')},
    },
    'colpick': {'js': 'colpick.js', 'css': 'colpick.css', 'default_version': '1.0.0', 'versions': ('1.0.0',)},
    'numeric': {'js': 'jquery.numeric.js', 'css': '', 'default_version': '1.4.1', 'versions': ('1.4.1',)},
    'igdectk': {
        'js': 'igdectk.js', 'css': '', 'default_version': '1.0.0', 'versions': ('1.0.0',),
        '.csrf': {'js': 'csrf.js', 'css': '', 'default_version': '1.0.0', 'versions': ('1.0.0', '2.0.0')},
        '.validator': {'js': 'validator.js', 'css': '', 'default_version': '1.0.0', 'versions': ('1.0.0', '2.0.0')},
    },
}
