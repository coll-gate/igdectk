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

import igdectk.xml

from .restmiddleware import ViewExceptionRest
from igdectk.common.helpers import *

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
            cls._register(cls.regex, cls.name, cls.app_name, urls='urls')


class RestHandler(object, metaclass=RestHandlerMeta):

    """
    Manage RESTfull API with autogenenation and registration of urls.
    """

    regex = r"^$"
    name = ''
    app_name = None
    application = None
    methods = []

    unprocessed_handlers = []  # intermediary list of handles to register
    handlers = []              # list of registered handlers (by register_urls)

    @classmethod
    def _register(cls, regex, name, app_name=None, urls='urls'):
        """
        Internaly called by RestHandlerMeta on class definition
        in way to create a new entry into the list of managed handlers.
        This list is finally manually inserted into each application urlpatterns
        classing register_urls.
        """
        cls.regex = regex
        cls.name = name
        cls.methods = {}

        if app_name:
            cls.app_name = app_name
        else:
            cls.app_name = cls.__module__.split('.')[0]

        cls.application = apps.get_app_config(cls.app_name)

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
            if request.header.content_type[0] == 'application/json' and request.body:
                data = json.loads(request.body.decode())
            elif request.header.content_type[0] == 'application/xml' and request.body:
                data = igdectk.xml.loads(request.body.decode())
            elif request.header.content_type[0] == 'multipart/form-data':
                data = request.POST  # Form POST encoded
            else:
                data = request.POST  # Form POST encoded

            # check for the existence of the parameters into the encoded URL
            for p in request.parameters:
                if p not in request.GET:
                    raise ViewExceptionRest("Missing parameter " + p, 400)

            request.data = data

            # conditionned selection of the handler
            sub = None
            fallback = None

            for submethod in methods:
                sub = submethod

                # fallback method is the one having only the accept condition
                if len(submethod[4]) == 1 and submethod[4][0][2] is 'accept':
                    fallback = sub
                    continue

                for condition in submethod[4]:
                    # key/value URL parameters (must be equal)
                    if condition[2] == 'eq':
                        # compare key
                        if condition[0] not in request.GET:
                            sub = None
                            break

                        # and value
                        if condition[1] != request.GET[condition[0]]:
                            sub = None
                            break
                    # key in URL (just contains)
                    elif condition[2] == 'has':
                        # compare key
                        if condition[0] not in request.GET:
                            sub = None
                            break
                    # or HTTP_ACCEPT (must be equal)
                    elif condition[2] == 'accept':
                        # accept any
                        if request.header.accepted_types != ['*/*']:
                            # compare content
                            if condition[0] not in request.header.accepted_types:
                                sub = None
                                break

                # we have our method
                if sub:
                    break

            if sub:
                method = sub
            else:
                method = fallback

            if method:
                result = method[0](request, **kwargs)

                if not result:
                    raise ViewExceptionRest(
                        'No results for %s %s' % (request.path, request.method), 404)
                else:
                    return result

        # when no view is defined for the method, there is no decorator
        # to apply the format, so we have to look what client ask for
        request.format = request.header.prefered_type(True)

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
        """
        Internaly register a wrapper for a specific method and conditions.
        """
        # register the wrapper
        if cls.methods.get(method):
            # look for an existing empty conditions wrapper for this method
            if not conditions:
                methods = cls.methods[method]
                failed = False

                for m in methods:
                    if not m[4]:
                        failed = True

                if failed:
                    raise RestRegistrationException(
                        "Only one empty conditions wrapper is allowed per method of a REST handler")

            cls.methods[method].append((wrapper, format, parameters, content, conditions))
        else:
            cls.methods[method] = [(wrapper, format, parameters, content, conditions)]

    @staticmethod
    def _make_conditions(format, kwargs):
        """
        For requests decorator submethod creating the conditions
        for a specific method, using optionals arguments dictionnary.
        This conditions list is a parameter for :meth:`_register_wrapper`.
        """
        # parse the url__ conditions
        conditions = []

        for argn, argv in kwargs.items():
            # url constraint for a key having value equality
            if argn.startswith('url__'):
                conditions.append((argn[5:], argv, 'eq'))
            # url constraint presence of a key
            elif argn == 'url_contains':
                for a in argv:
                    conditions.append((a, '', 'has'))

        # HTTP_ACCEPT must respect the format value
        if format.upper() == 'JSON':
            accept = 'application/json'
        elif format.upper() == 'XML':
            accept = 'application/xml'
        elif format.upper() == 'HTML':
            accept = 'text/html'
        else:
            raise RestRegistrationException('%s is not a supported accept format' % argv)

        conditions.append((accept, '', 'accept'))

        return conditions

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

        accept: string
            Specify a request method accepting only to returns a specific format.
            Must be 'JSON', 'XML', 'HTML' or None.

        conditions: string
            The next parameters if theirs names starts with a 'url__' will
            be used as condition expression for the url parameters.

            For example, having url__action='save' mean that the url must
            contains the parameter action with the value 'save'.

            This is useful to have many action for a same HTTP method.
            It is possible to have many 'url__' conditions.

        url_contains: tuple
            Tuple of URL parameters that identify this handler.

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

            # target conditions
            conditions = RestHandler._make_conditions(format, kwargs)

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

            # target conditions
            conditions = RestHandler._make_conditions(format, kwargs)

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

            # target conditions
            conditions = RestHandler._make_conditions(format, kwargs)

            # register the wrapper
            cls._register_wrapper(wrapper, method, format, parameters, content, conditions)

            return wrapper

        return decorator


class InlineRestHandler(object):

    def __init__(self, regex, name, app_name=None, version='1.0'):
        self.regex = regex
        self.name = name
        self.app_name = app_name
        self.version = version


def def_inline_request(inline_handler, method, format, parameters=(), content=(), **kwargs):
    """
    Check the method of the request, and then the list of parameters.
    If the format is incorrect or a parameter is missing raise a ViewException
    Html or Json depending of the format.

    If it pass the test, the function will contains two news parameters :
        - method : from the decorator
        - format : from the decorator

    Parameters
    ----------
    inline_handler: InlineRestHandler
        Inline version of the RestHandler class definition.

    method: string
        'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'

    format: string
        'JSON', 'HTML' or 'XML' defines the format of the HTTP response.

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

        # get the default application name from decorated function
        if inline_handler.app_name:
            _app_name = inline_handler.app_name
        else:
            _app_name = func.__module__.split('.')[0]

        class InlineRestHandler(RestHandler):
            version = inline_handler.version
            regex = inline_handler.regex
            name = inline_handler.name
            app_name = _app_name

        # target conditions
        conditions = RestHandler._make_conditions(format, kwargs)

        # register the wrapper
        InlineRestHandler._register_wrapper(wrapper, method, format, parameters, content, conditions)

        return wrapper

    return decorator


def def_inline_auth_request(inline_handler, method, format, parameters=(), content=(), fallback=None, **kwargs):
    """
    Same as :func:`def_inline_request` but in addition the user must be authenticated.

    Parameters
    ----------

    fallback: func
        Optional callback function called in case the user is not authenticated.
    """
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

        # get the default application name from decorated function
        if inline_handler.app_name:
            _app_name = inline_handler.app_name
        else:
            _app_name = func.__module__.split('.')[0]

        class InlineRestHandler(RestHandler):
            version = inline_handler.version
            regex = inline_handler.regex
            name = inline_handler.name
            app_name = _app_name

        # target conditions
        conditions = RestHandler._make_conditions(format, kwargs)

        # register the wrapper
        InlineRestHandler._register_wrapper(wrapper, method, format, parameters, content, conditions)

        return wrapper

    return decorator


def def_inline_admin_request(inline_handler, method, format, parameters=(), content=(), fallback=None, **kwargs):
    """
    Same as :meth:`def_inline_request` but in addition the user must be authenticated.

    Parameters
    ----------

    fallback: func
        Optional callback function called in case the user is not authenticated.
    """
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

        # get the default application name from decorated function
        if inline_handler.app_name:
            _app_name = inline_handler.app_name
        else:
            _app_name = func.__module__.split('.')[0]

        class InlineRestHandler(RestHandler):
            version = inline_handler.version
            regex = inline_handler.regex
            name = inline_handler.name
            app_name = _app_name

        # target conditions
        conditions = RestHandler._make_conditions(format, kwargs)

        # register the wrapper
        InlineRestHandler._register_wrapper(wrapper, method, format, parameters, content, conditions)

        return wrapper

    return decorator
