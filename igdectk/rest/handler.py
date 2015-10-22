# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
    Easy manage RESTfull urls and views according
    to the HTTP method and content format.
"""

import json
import validictory

import logging

from django.apps import apps
from django.conf.urls import url

from .restmiddleware import ViewExceptionRest

__date__ = "2015-10-15"
__author__ = "Frédéric Scherma"

logger = logging.getLogger(__name__)


class RestRegistrationException(Exception):

    """
    Occurs during registration of a handler or a method
    into a REST handler.
    """

    pass


class RestHandlerMeta(type):

    def __init__(cls, name, base, d):
        type.__init__(cls, name, base, d)

        # register only when inheritance (not base)
        if cls.__name__ is not 'RestHandler':
            cls._register(cls.regex, cls.name, cls.application, urls='urls')


class RestHandler(object, metaclass=RestHandlerMeta):

    """
    Manage RESTfull API with autogenenation and registration of urls.
    """

    regex = r"^$"
    name = ''
    application = None
    methods = []

    unprocessed_handlers = []  # intermediary list of handles to register
    handlers = []              # list of registered handlers (by register_urls)

    @classmethod
    def _register(cls, regex, name, application=None, urls='urls'):
        """
        Internaly called by RestHandlerMeta on class definition
        in way to create a new entry into the list of managed handlers.
        This list is finally manually inserted into each application urlpatterns
        classing register_urls.
        """
        cls.regex = regex
        cls.name = name
        cls.methods = {}

        if application:
            cls.appname = application
        else:
            cls.appname = cls.__module__.split('.')[0]

        cls.application = apps.get_app_config(cls.appname)

        # application urls
        cls.urlsname = urls if urls else 'urls'

        try:
            cls.urls = __import__(
                '%s.%s' % (cls.application.module.__name__, cls.urlsname),
                fromlist=['*'])
        except ImportError:
            raise

        RestHandler.unprocessed_handlers.append(cls)

    @classmethod
    def _interceptor(cls, request, **kwargs):
        methods = cls.methods.get(request.method)

        if methods:
            if request.META['CONTENT_TYPE'].startswith('application/json') and request.body:
                data = json.loads(request.body.decode())
            else:
                data = request.POST

            # check for the existence of the parameters into the encoded URL
            for p in request.parameters:
                if p not in request.GET:
                    raise ViewExceptionRest("Missing parameter " + p, 400)

            request.data = data

            # constrained by GET parameters method
            if type(methods) is list:
                sub = None
                fallback = None

                for submethod in methods:
                    sub = submethod

                    # fallback method is the one having no conditions
                    if not submethod[4]:
                        fallback = sub
                        continue

                    for condition in submethod[4]:
                        # compare key
                        if condition[0] not in request.GET:
                            sub = None
                            break

                        # compare value
                        if condition[1] != request.GET[condition[0]]:
                            sub = None
                            break

                    # we have our method
                    if sub:
                        break

                if sub:
                    method = sub
                else:
                    method = fallback
            else:
                method = methods

            if method:
                result = method[0](request, **kwargs)

                if not result:
                    raise ViewExceptionRest(
                        'No results for %s %s' % (request.path, request.method), 404)
                else:
                    return result

        # when no view is defined for the method, there is no decorator
        # to apply the format, so we have to look what client ask for
        if request.META['CONTENT_TYPE'].startswith('application/json'):
            request.format = 'JSON'
        elif request.META['CONTENT_TYPE'].startswith('application/xml'):
            request.format = 'HTML'  # 'XML' TODO HTML for the moment
        else:
            request.format = 'HTML'

        raise ViewExceptionRest(
            'Undefined view for %s %s' % (request.path, request.method), 404)

    @staticmethod
    def register_urls():
        """
        This method must be called once time in the urls.py
        """
        for handler in RestHandler.unprocessed_handlers:
            handler.urls.urlpatterns.append(
                url(handler.regex, handler._interceptor, name=handler.name))

            # append to registered handlers
            handler.handlers.append(handler)

        # Empty list of unprocessed handlers
        RestHandler.unprocessed_handlers = []

    @classmethod
    def _register_wrapper(cls, wrapper, method, format, parameters, content, conditions):
        # register the wrapper
        if cls.methods.get(method):
            # look for an existing empty conditions wrapper for this method
            if not conditions:
                methods = cls.methods[method]

                for m in methods:
                    if not m.conditions:
                        raise RestRegistrationException(
                            "Only one empty conditions wrapper is allowed per method of a REST handler")

            if type(cls.methods[method]) is list:
                cls.methods[method].append(
                    (wrapper, format, parameters, content, conditions))
            else:
                cls.methods[method] = [
                    cls.methods[method],
                    (wrapper, format, parameters, content, conditions)
                ]
        else:
            cls.methods[method] = (wrapper, format, parameters, content, conditions)

    @classmethod
    def def_request(cls, method, format, parameters=(), content=(), **kwargs):
        """
        Request function register and wrapper for non auth requests.

        Check the list of mandatory URL parameters.

        Check the list of mandatory content Form/JSON parameters, or validate the
        content using validictory format.

        If the format is incorrect or a parameter is missing raise a ViewException
        HTML or JSON depending of the format.

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

        conditions: string
            The next parameters if theirs names starts with a 'url__' will
            be used as condition expression for the url parameters.

            For example, having url__action='save' mean that the url must
            contains the parameter action with the value 'save'.

            This is useful to have many action for a same HTTP method.
            It is possible to have many 'url__' conditions.

        Notes
        -----

            Only once free of conditions method per handler can be registered.
            Otherwise a :any:`RestRegistrationException` exception is raised.
        """
        # create a decorator for the function
        def decorator(func):
            def wrapper(*args, **kwargs):
                request = args[0]

                # add the parameters to the request
                request.format = format
                request.parameters = parameters

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

            # parse the url__ conditions
            conditions = []

            for argn, argv in kwargs.items():
                if argn.startswith('url__'):
                    conditions.append((argn[5:], argv))

            # register the wrapper
            cls._register_wrapper(wrapper, method, format, parameters, content, conditions)

            return wrapper

        return decorator

    @classmethod
    def def_auth_request(cls, method, format, parameters=(), content=(), fallback=None, **kwargs):
        """
        Same as :meth:`def_request` but in addition the user must be authenticated.

        Parameters
        ----------

        fallback: func
            Optional callback function called in case the user is not authenticated.
        """
        # create a decorator for the function
        def decorator(func):
            def wrapper(*args, **kwargs):
                request = args[0]

                # add the parameters to the request
                request.format = format
                request.parameters = parameters

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

            # parse the url__ conditions
            conditions = []

            for argn, argv in kwargs.items():
                if argn.startswith('url__'):
                    conditions.append((argn[5:], argv))

            # register the wrapper
            cls._register_wrapper(wrapper, method, format, parameters, content, conditions)

            return wrapper

        return decorator

    @classmethod
    def def_admin_request(cls, method, format, parameters=(), content=(), fallback=None, **kwargs):
        """
        Same as :meth:`def_request` but in addition the user must be authenticated
        and superuser.

        Parameters
        ----------

        fallback: func
            Optional callback function called in case the user is not authenticated.
        """
        # create a decorator for the function
        def decorator(func):
            def wrapper(*args, **kwargs):
                request = args[0]

                # add the parameters to the request
                request.format = format
                request.parameters = parameters

                # check for user authentication
                if not request.user.is_authenticated():
                    if fallback:
                        fallback()
                    raise ViewExceptionRest("Unauthorized", 401)

                # check for super-user authentication
                if not request.user.is_superuser:
                    if fallback:
                        fallback()
                    raise ViewExceptionRest("Forbidden", 403)

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

            # parse the url__ conditions
            conditions = []

            for argn, argv in kwargs.items():
                if argn.startswith('url__'):
                    conditions.append((argn[5:], argv))

            # register the wrapper
            cls._register_wrapper(wrapper, method, format, parameters, content, conditions)

            return wrapper

        return decorator


def inline_rest_handler(regex, name, application=None, version='1.0'):
    class InlineRestHandler(RestHandler):
        version = version
        regex = regex
        name = name
        application = application

    return InlineRestHandler
