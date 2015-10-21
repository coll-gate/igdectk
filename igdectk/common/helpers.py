# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
    Usefull common helpers.
"""

import json
import validictory

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


def def_request(method, format, parameters=(), content=()):
    """
    Check the method of the request, and then the list of parameters.
    If the format is incorrect or a parameter is missing raise a ViewException
    Html or Json depending of the format.

    If it pass the test, the function will contains two news parameters :
        - method : from the decorator
        - format : from the decorator

    Parameters
    ----------
    method: string
        'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'

    format: string
        'JSON' or 'HTML', defines the format of the http response.

    parameters: list
        A list of strings or an empty list, containing the names of the
        mandatory parameters requested in the URL.

    content: list
        A list of strings or an empty list, containing the names of the
        mandatory parameters requested in the body.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            request = args[0]

            # add the parameters to the request
            request.format = format
            request.parameters = parameters

            # check request method
            if request.method != method:
                raise ViewExceptionRest(method + " is excepted", 400)

            # check for the existence of the parameters into the encoded URL
            for p in parameters:
                if p not in request.GET:
                    raise ViewExceptionRest("Missing parameter " + p, 400)

            # check for the existence of the values into the encoded body
            data = request.data if hasattr(request, 'data') else request.POST

            if type(content) == tuple:
                for p in content:
                    if p not in data:
                        raise ViewExceptionRest("Missing parameter " + p, 400)
            elif type(content) == dict and request.format.upper() == "JSON":
                # or do a data validation
                validictory.validate(data, content)

            # call the function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def def_auth_request(
        method, format,
        parameters=(), content=(),
        fallback=None):
    """
    Check the method of the request, then is the user is authenticated and finaly,
    the list of parameters.
    If the format is incorrect or a parameter is missing raise a ViewException
    Html or Json depending of the format.

    If it pass the test, the function will contains two news parameters :
        - method : from the decorator
        - format : from the decorator

    Parameters
    ----------
    method: string
        'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'

    format: string
        'JSON' or 'HTML', defines the format of the http response.

    parameters: list
        A list of strings or an empty list, containing the names of the
        mandatory parameters requested in the URL.

    content: list
        A list of strings or an empty list, containing the names of the
        mandatory parameters requested in the body.

    fallback: function
        None or a function object that will be called if the user
        is not authenticated.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            request = args[0]

            # add the parameters to the request
            request.format = format
            request.parameters = parameters

            # check request method
            if request.method != method:
                raise ViewExceptionRest(method + " is excepted", 400)

            # check for user authentication
            if not request.user.is_authenticated():
                if fallback:
                    fallback()
                raise ViewExceptionRest("Unauthorized", 401)

            # check for the existence of the parameters into the encoded URL
            for p in parameters:
                if p not in request.GET:
                    raise ViewExceptionRest("Missing parameter " + p, 400)

            # check for the existence of the values into the encoded body
            data = request.data if hasattr(request, 'data') else request.POST

            if type(content) == tuple:
                for p in content:
                    if p not in data:
                        raise ViewExceptionRest("Missing parameter " + p, 400)
            elif type(content) == dict and request.format.upper() == "JSON":
                # or do a data validation
                validictory.validate(data, content)

            # call the function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def def_admin_request(
        method, format,
        parameters=(), content=(),
        fallback=None):
    """
    Check the method of the request, then is the user is authenticated super-user
    and finaly, the list of parameters.
    If the format is incorrect or a parameter is missing raise a ViewException
    Html or Json depending of the format.

    If it pass the test, the function will contains two news parameters :
        - method : from the decorator
        - format : from the decorator

    Parameters
    ----------
    method: string
        'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'

    format: string
        'JSON' or 'HTML', defines the format of the http response.

    parameters: list
        A list of strings or an empty list, containing the names of the
        mandatory parameters requested in the URL.

    content: list
        A list of strings or an empty list, containing the names of the
        mandatory parameters requested in the body.

    fallback: function
        None or a function object that will be called if the user
        is not authenticated.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            request = args[0]

            # add the parameters to the request
            request.format = format
            request.parameters = parameters

            # check request method
            if request.method != method:
                raise ViewExceptionRest(method + " is excepted", 400)

            # check for super-user authentication
            if not request.user.is_authenticated() or not request.user.is_superuser:
                if fallback:
                    fallback()
                raise ViewExceptionRest("Unauthorized", 401)

            # check for the existence of the parameters into the encoded URL
            for p in parameters:
                if p not in request.GET:
                    raise ViewExceptionRest("Missing parameter " + p, 400)

            # check for the existence of the values into the encoded body
            data = request.data if hasattr(request, 'data') else request.POST

            if type(content) == tuple:
                for p in content:
                    if p not in data:
                        raise ViewExceptionRest("Missing parameter " + p, 400)
            elif type(content) == dict and request.format.upper() == "JSON":
                # or do a data validation
                validictory.validate(data, content)

            # call the function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def rest_handler(func):
    """
    Helper to define a url handler for differents methods.
    """
    def wrapper(request, **kwargs):
        # call the function
        if request.META['CONTENT_TYPE'].startswith('application/json') and request.body:
            data = json.loads(request.body.decode())
        else:
            data = request.POST

        request.data = data

        result = func(request, **kwargs)

        if not result:
            raise ViewExceptionRest('Unavaible', 404)
        else:
            return result

    return wrapper


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
