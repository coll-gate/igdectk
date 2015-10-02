import os
import logging

from django.conf import settings
from django.apps import AppConfig

from .evaluator import eval_expr

logger = logging.getLogger(__name__)


def startup(appconfig, logger):
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

    def ready(self):
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
            else self.name)

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
        """
        # get settings table from the application
        setting = self.settings_table.objects.filter(param_name=param_name)

        if len(setting) >= 1 and setting[0].value:
            return eval_expr(setting[0].value)
        else:
            return None
