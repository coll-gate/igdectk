# -*- coding: utf-8; -*-
#
# @file evaluator.py
# @brief Useful common helpers.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-04-13
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details

from django.apps import apps

from igdectk.rest.restmiddleware import ViewExceptionRest


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
    :rtype: int
    """
    try:
        return int(v)
    except ValueError:
        raise ViewExceptionRest(
            'Invalid argument format. %s must be an integer.' %
            (repr(v),),
            400
        )


def bool_arg(v):
    """
    Check if v is a boolean string (true|false).

    :param str v : Potential boolean to check

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
            raise ValueError('Boolean value must be "true" or "false"')
    except ValueError:
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
    :rtype: int
    """
    try:
        value = int(v)
    except ValueError:
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
