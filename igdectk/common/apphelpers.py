# -*- coding: utf-8; -*-
#
# @file apphelpers.py
# @brief Application startup process around django.apps.AppConfig.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-04-13
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details

import os
import sys
import logging

from importlib import import_module

from django.conf import settings
from django.apps import AppConfig

from igdectk.rest.restmiddleware import ViewExceptionRest

from .evaluator import eval_expr

logger = logging.getLogger(__name__)


def startup(appconfig, app_logger):
    """
    Helper function called by :class:`ApplicationMain` on ready.

    It validates the settings for a specific application. If a setting
    is not found into the settings table of the application, the value entry
    is inserted.

    Later any other generic application startup processing will goes here.
    """
    app_logger.info("'%s' application started into process %i..." % (appconfig.verbose_name, os.getpid()))

    if not appconfig.settings_model:
        appconfig.settings_table = None
        appconfig.settings_table_name = ''
        return

    app_logger.info("> Looking for the model settings '%s'..." % (appconfig.settings_model,))

    # first we look for the settings table
    from django.db import connection

    module_name, settings_class = appconfig.settings_model.rsplit('.', 1)
    module = import_module(module_name)

    appconfig.settings_table = getattr(module, settings_class)
    appconfig.settings_table_name = appconfig.settings_table._meta.db_table

    app_logger.info("> Validate defaults settings :")

    if appconfig.settings_table_name in connection.introspection.table_names():
        # check or init default and mandatory settings
        for k in appconfig.default_settings:
            obj = appconfig.settings_table.objects.filter(param_name=k)
            if obj is None or not obj:
                obj = appconfig.settings_table()
                obj.param_name = k
                obj.value = repr(appconfig.default_settings[k])
                obj.save()

                try:
                    value_str = str(appconfig.default_settings[k])
                except TypeError:
                    app_logger.fatal('Unable to eval %s' % (k,))
                    raise

                app_logger.info("    %s = %s (inserted with default)" % (k, value_str))

            elif obj[0].value is None or not obj[0].value:
                obj[0].value = repr(appconfig.default_settings[k])
                obj[0].save()

                try:
                    value_str = str(obj[0].value)
                except TypeError:
                    app_logger.fatal('Unable to eval %s' % (obj[0].param_name,))
                    raise

                app_logger.info(
                    "    %s = %s (update to default)" % (
                        obj[0].param_name, value_str))
            else:
                try:
                    value_str = str(obj[0].value)
                except TypeError:
                    app_logger.fatal('Unable to eval %s' % (obj[0].param_name,))
                    raise

                app_logger.info("    %s = %s (found)" % (obj[0].param_name, value_str))

        app_logger.info("> All checks passes. Now running...")
    else:
        # not yet configured
        appconfig.settings_table = None
        appconfig.settings_table_name = ''

        app_logger.warning("'%s' table does not exists (maybe you should apply the database migrations)" % (
            appconfig.settings_table_name,))


def get_app_db_settings(app_short_name):
    """
    It will look for the settings.APPLICATIONS dict that contains
    specifics parameters for each application.
    Each entry use the short name of the application.

    This settings are used to fill the database settings table for an
    application. Once the value exists into the database this is
    the database value that is taken en priority.

    Normally it should be reserved for internal usage only.

    :param str app_short_name: Short name of the application to get the settings dict.

    :return: The application settings to store into the database, or
        None if there is no settings for the application at settings
        level.
    :rtype: dict
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

    :param str name: Application short name

    .. seealso::

        :attr:`igdectk.appsettings.APP_VERBOSE_NAME`
            A string containing the tong name of the application.
            Application short name is used if not founds.

        :attr:`igdectk.appsettings.APP_DB_DEFAULT_SETTINGS`
            A dict containing default settings to put into the settings table
            of the application. An empty dict if used if not founds.

        :attr:`igdectk.appsettings.APP_SETTINGS_MODEL`
            Object containing default settings table name or None.
            '<appname>_settings' is used if not founds.

        :attr:`igdectk.appsettings.HTTP_TEMPLATE_STRING`
            Compoundable string (containing a %s parameters) to build
            the path of the HTTP error pages (40x, 50x) template.
            '<appname>/%s.html' is used if not founds.

        :attr:`igdectk.appsettings.APP_VERSION`
            Application version as list.
            (0, 1) is defined if not founds.
    """

    def __init__(self, app_name, app_module):
        super(ApplicationMain, self).__init__(app_name, app_module)

        self.appsettings = None
        self.verbose_name = self.name
        self.default_settings = {}
        self.settings_model = self.name + '.models.Settings'
        self.settings_table = None
        self.settings_table_name = ''
        self.http_template_string = self.name + '/%s.html'
        self.version = (0, 1)
        self.logger = logging.getLogger(self.name)

    def ready(self):
        """
        Called by Django application manager when the application is loaded.
        """

        # application settings
        self.appsettings = import_module('%s.appsettings' % self.module.__name__)

        # load the application settings
        self.verbose_name = (
            getattr(self.appsettings, 'APP_VERBOSE_NAME')
            if hasattr(self.appsettings, 'APP_VERBOSE_NAME')
            else self.name)

        self.default_settings = get_app_db_settings(self.name) or (
            getattr(self.appsettings, 'APP_DB_DEFAULT_SETTINGS')
            if hasattr(self.appsettings, 'APP_DB_DEFAULT_SETTINGS')
            else {})

        app_default_settings = (getattr(self.appsettings, 'APP_DB_DEFAULT_SETTINGS')
                                if hasattr(self.appsettings, 'APP_DB_DEFAULT_SETTINGS')
                                else {})

        # merge for missing default settings in global settings
        for param_name, value in app_default_settings.items():
            if param_name not in self.default_settings:
                self.default_settings[param_name] = value

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

        :param str param_name: Name of the settings parameters key

        :return: Returns the asked value or None if not founds.
        :rtype: any

        .. seealso::

            :func:`igdectk.helpers.get_setting`: to get settings from another application.
        """
        # get settings table from the application
        if not self.settings_table:
            # if not returns the settings from the project settings
            # if not returns it from the appsettings
            # else returns None
            return self.default_settings.get(param_name, None)

        # search for setting in DB
        setting = self.settings_table.objects.filter(param_name=param_name)

        # if found in DB eval it and returns, else fallback to the default value
        if len(setting) >= 1:
            return eval_expr(setting[0].value)
        # else:
        #     raise ViewExceptionRest('Bad configuration.', 500)

        return self.default_settings.get(param_name, None)

    def is_run_mode(self):
        command_list = ("init_fixtures", "migrate", "makemigrations", "help", "")

        for command in command_list:
            if command in sys.argv:
                return False

        return True

    def is_table_exists(self, table_name_or_model):
        from django.db import connection

        if type(table_name_or_model) == str:
            return table_name_or_model in connection.introspection.table_names()
        else:
            table_name = table_name_or_model._meta.db_table
            return table_name in connection.introspection.table_names()
