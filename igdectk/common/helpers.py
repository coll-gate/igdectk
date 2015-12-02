# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Usefull common helpers.
"""

from django.apps import apps

from igdectk.rest.restmiddleware import ViewExceptionRest

from .evaluator import eval_expr

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"


def get_setting(app_name, param_name):
    """
    Get a setting value.

    Parameters
    ----------
    app_name: string
        name of the django application

    param_name: string
        name of the settings parameters key

    Returns
    -------
    result: any
        returns the asked value

    Raises
    ------
    ViewExceptionRest:
        if not found
    """

    # get settings table from the application
    settings_table = apps.get_app_config(app_name).settings_table

    setting = settings_table.objects.filter(param_name=param_name)

    if len(setting) >= 1 and setting[0].value:
        return eval_expr(setting[0].value)
    else:
        raise ViewExceptionRest('Bad configuration.', 500)


def int_arg(v):
    """
    Check if v is an integer.

    Parameters
    ----------
    v: int, any
        Potential integer to check

    Returns
    -------
    : boolean
        True if success
    """
    try:
        return int(v)
    except:
        raise ViewExceptionRest(
            'Invalid argument format. %s must be an integer.' %
            (repr(v),),
            400
        )


def rint_arg(v, r):
    """
    Check if v is an integer into a specific range r.

    Parameters
    ----------
    v: int or any
        Potential integer to check
    r: list
        2 integers list (min and max inclusive of the range)

    Returns
    -------
    : boolean
        True if success
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
