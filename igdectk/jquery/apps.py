# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Django Jquery application main
"""

from igdectk.common.apphelpers import ApplicationMain

from django.core.exceptions import ImproperlyConfigured
from .appsettings import PROPERTIES


def check_library_version(default, config):
    # check if the default version is available for this library
    default_version = config.get('default_version')
    if default_version:
        if default_version not in default.get('versions', ()):
            return False
        else:
            # replace default version
            default['default_version'] = default_version

    return True


def check_library_theme(default, config):
    # check if the default theme is available for this library
    default_theme = config.get('default_theme')
    if default_theme:
        if default_theme not in default.get('themes', ()):
            return False
        else:
            # replace default theme
            default['default_theme'] = default_theme

    return True


class IgdecTkJquery(ApplicationMain):
    name = '.'.join(__name__.split('.')[0:-1])

    def ready(self):
        super().ready()

        # check the settings provided at project level
        for libname, library in PROPERTIES.items():
            # get the configuration for the library
            lib = self.get_setting(libname)
            sublibname = None

            # if we have a specific configuration for library
            if lib:
                if not check_library_version(library, lib):
                    fq_libname = libname if not sublibname else libname + sublibname
                    raise ImproperlyConfigured('Invalid default version for %s' % (fq_libname))

                if not check_library_theme(library, lib):
                    fq_libname = libname if not sublibname else libname + sublibname
                    raise ImproperlyConfigured('Invalid default theme for %s' % (fq_libname))

                # find for sub-libraries
                for key, sublib in lib.items():
                    # sub-libraries keys starts with a dot '.'
                    if key.startswith('.'):
                        # check if the sub-library exists into this packager
                        sublibrary = library.get(key)
                        if sublibrary:
                            if not check_library_version(sublibrary, sublib):
                                fq_libname = libname if not key else libname + key
                                raise ImproperlyConfigured('Invalid default version for %s' % (fq_libname))

                            if not check_library_theme(sublibrary, sublib):
                                fq_libname = libname if not key else libname + key
                                raise ImproperlyConfigured('Invalid default theme for %s' % (fq_libname))
                        else:
                            raise ImproperlyConfigured('Invalid sub-library %s for %s' % (sublibname, libname))
