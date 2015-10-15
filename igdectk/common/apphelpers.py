# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Application startup process around django.apps.AppConfig.
"""

import os
import logging

from django.conf import settings
from django.apps import AppConfig

from .evaluator import eval_expr

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"

logger = logging.getLogger(__name__)


def startup(appconfig, logger):
    """
    Helper function called by :class:`ApplicationMain` on ready.

    It validates the settings for a specific application. If a setting
    is not found into the settings table of the application, the value entry
    is inserted.

    Later any other generic application startup processing will goes here.
    """
    logger.info("%s process %i started..." % (appconfig.verbose_name, os.getpid()))
    logger.info("> Looking for the model %s..." % (appconfig.settings_model,))

    # first we look for the settings table
    from django.db import connection

    module = __import__(
        '.'.join(appconfig.settings_model.split('.')[0:-1]),
        fromlist=[appconfig.settings_model.split('.')[-1]])

    appconfig.settings_table = getattr(module, appconfig.settings_model.split('.')[-1])
    appconfig.settings_table_name = appconfig.settings_table._meta.db_table

    logger.info("> Validate defaults settings...")

    if appconfig.settings_table_name in connection.introspection.table_names():
        # check or init default and mandatory settings
        for k in appconfig.default_settings:
            obj = appconfig.settings_table.objects.filter(param_name=k)
            if obj is None or not obj:
                obj = appconfig.settings_table()
                obj.param_name = k
                obj.value = appconfig.default_settings[k]
                obj.save()

                try:
                    value_str = str(appconfig.default_settings[k])
                except TypeError:
                    logger.fatal('Unable to eval %s' % (k,))
                    raise

                logger.info("    %s = %s (inserted with default)" % (k, value_str))

            elif obj[0].value is None or not obj[0].value:
                obj[0].value = appconfig.default_settings[k]
                obj[0].save()

                try:
                    value_str = str(obj[0].value)
                except TypeError:
                    logger.fatal('Unable to eval %s' % (obj[0].param_name,))
                    raise

                logger.info(
                    "    %s = %s (update to default)" % (
                        obj[0].param_name, value_str))
            else:
                try:
                    value_str = str(obj[0].value)
                except TypeError:
                    logger.fatal('Unable to eval %s' % (obj[0].param_name,))
                    raise

                logger.info("    %s = %s (found)" % (obj[0].param_name, value_str))

        logger.info("> All checks passes. Now running...")
    else:
        logger.warning('%s table does not exists' % (appconfig.settings_table_name,))


def get_app_db_settings(app_short_name):
    """
    It will look for the settings.APPLICATIONS dict that contains
    specifics parameters for each application.
    Each entry use the short name of the application.

    This settings are used to fill the database settings table for an
    application. Once the value exists into the database this is
    the database value that is taken en priority.

    Normaly should be reserved for internal usage only.

    Parameters
    ----------
    app_short_name: string
        Short name of the application to get the settings dict.

    Returns
    -------
    :dict
        The application settings to store into the database, or
        None if there is no settings for the application at settings
        level.
    """
    if hasattr(settings, 'APPLICATIONS'):
        applications = getattr(settings, 'APPLICATIONS')
    else:
        return None

    if app_short_name not in applications:
        return None

    if 'DB_DEFAULT_SETTINGS' not in applications[app_short_name]:
        return None

    return applications[app_short_name]['DB_DEFAULT_SETTINGS']


class ApplicationMain(AppConfig):

    """
    Advanced Django AppConfig.

    It looks for a module appsettings into the application folder.

    Some globals variables into appsettings are looked for :

    Parameters
    ----------
    name: string
        Application short name

    See also
    --------
    :attr:`igdectk.appsettings.APP_VERBOSE_NAME`
        A string containing the tong name of the application.
        Application short name is used if not founds.
    :attr:`igdectk.appsettings.APP_DB_DEFAULT_SETTINGS`
        A dict containing default settings to put into the settings table
        of the application. An empty dict if used if not founds.
    :attr:`igdectk.appsettings.APP_SETTINGS_MODEL`
        Object containing default settings table name.
        '<appname>_settings' is used if not founds.
    :attr:`igdectk.appsettings.HTTP_TEMPLATE_STRING`
        Compoundable string (containing a %s parameters) to build
        the path of the HTTP error pages (40x, 50x) template.
        '<appname>/%s.html' is used if not founds.
    :attr:`igdectk.appsettings.APP_VERSION`
        Application version as list.
        (0, 1) is defined if not founds.
    """

    def ready(self):
        """
        Called by Django application manager when the application is loaded.
        """

        # application settings
        self.appsettings = __import__(
            '%s.appsettings' % self.module.__name__, fromlist=['*'])

        # load the application settings
        self.verbose_name = (
            getattr(self.appsettings, 'APP_VERBOSE_NAME')
            if hasattr(self.appsettings, 'APP_VERBOSE_NAME')
            else self.name)

        self.default_settings = get_app_db_settings(self.name) or (
            getattr(self.appsettings, 'APP_DB_DEFAULT_SETTINGS')
            if hasattr(self.appsettings, 'APP_DB_DEFAULT_SETTINGS')
            else {})

        self.settings_model = (
            getattr(self.appsettings, 'APP_SETTINGS_MODEL')
            if hasattr(self.appsettings, 'APP_SETTINGS_MODEL')
            else self.name + '.models.Settings')

        self.http_template_string = (
            getattr(self.appsettings, 'HTTP_TEMPLATE_STRING')
            if hasattr(self.appsettings, 'HTTP_TEMPLATE_STRING')
            else self.name + '/%s.html')

        self.version = (
            getattr(self.appsettings, 'APP_VERSION')
            if hasattr(self.appsettings, 'APP_VERSION')
            else (0, 1))

        self.logger = logging.getLogger(self.name)

        startup(self, self.logger)

    def get_setting(self, param_name):
        """
        Get a setting value for this application or None if not exists.

        Parameters
        ----------
        param_name : string
            name of the settings parameters key

        Returns
        -------
        result: any
            returns the asked value or None if not founds.

        See also
        --------
        :func:`igdectk.helpers.get_setting`: to get settings from another application.
        """
        # get settings table from the application
        setting = self.settings_table.objects.filter(param_name=param_name)

        if len(setting) >= 1 and setting[0].value:
            return eval_expr(setting[0].value)
        else:
            return None
