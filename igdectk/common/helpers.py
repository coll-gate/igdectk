# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Usefull common helpers.
"""

from django.apps import apps

from igdectk.rest.restmiddleware import ViewExceptionRest

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"


def get_setting(app_name, param_name):
    """
    Get a setting value.

    :param str app_name: Name of the django application
    :param str param_name: Name of the settings parameters key

    :return: Returns the asked value
    :rtype: any

    :raise ViewExceptionRest: If not found
    """
    return apps.get_app_config(app_name).get_setting(param_name)


def int_arg(v):
    """
    Check if v is an integer.

    :param int|any v: Potential integer to check

    :return: True if success
    :rtype: boolean
    """
    try:
        return int(v)
    except:
        raise ViewExceptionRest(
            'Invalid argument format. %s must be an integer.' %
            (repr(v),),
            400
        )


def bool_arg(v):
    """
    Check if v is a boolean string (true|false).

    :param string: Potential boolean to check

    :return: True or False
    :rtype: boolean
    """
    try:
        val = str(v)
        if val == 'true':
            return True
        elif val == 'false':
            return False
        else:
            raise
    except:
        raise ViewExceptionRest(
            'Invalid argument format. %s must be a boolean string (true|false).' %
            (repr(v),),
            400
        )


def rint_arg(v, r):
    """
    Check if v is an integer into a specific range r.

    :param int|any v: Potential integer to check
    :param list(int,int) r: 2 integers list (min and max inclusive of the range)

    :return: True if success
    :rtype: boolean
    """
    try:
        value = int(v)
    except:
        raise ViewExceptionRest(
            'Invalid argument format. %s must be an integer.' %
            (repr(v),),
            400
        )

    if value < r[0] or value > r[1]:
        raise ViewExceptionRest(
            'Invalid argument value. %s is out of the range %s.' %
            (repr(v), repr(r)),
            400
        )

    return value
