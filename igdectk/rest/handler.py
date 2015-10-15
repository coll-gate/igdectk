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


class RestHandler(object):

    """
    Manage RESTfull API with autogenenation and registration of urls.
    """

    handlers = []

    @classmethod
    def register(cls, regex, name, application=None, urls='urls'):
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

        RestHandler.handlers.append(cls)

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
                        if condition[0] not in request.GET:
                            sub = None
                            break

                            if condition[1] != request.GET[condition[0]]:
                                sub = None
                                break

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
        TODO
        """
        for handler in RestHandler.handlers:
            handler.urls.urlpatterns.append(
                url(handler.regex, handler._interceptor, name=handler.name))

    @classmethod
    def def_request(cls, method, format, parameters=(), content=(), **kwargs):
        """
        TODO
        """
        # create a decorator for the function
        def decorator(func):
            def wrapper(*args, **kwargs):
                request = args[0]

                # add the parameters to the request
                request.format = format
                request.parameters = parameters

                # check request method (should never fail here because of the
                # _interceptor)
                if request.method != method:
                    raise ViewExceptionRest(method + " is excepted", 400)

                # check for the existence of the parameters into the encoded URL
                for p in parameters:
                    if p not in request.GET:
                        raise ViewExceptionRest("Missing parameter " + p, 400)

                # check for the existence of the values into the encoded body
                data = request.data if hasattr(request, 'data') else request.POST
                print(content)
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

            # TODO is fallback always works ?
            # we should avoid the possibility to register many zero conditions
            # for the same method type

            # register the wrapper
            if cls.methods.get(method):
                cls.methods[method] = [
                    cls.methods[method],
                    (wrapper, format, parameters, content, conditions)
                ]
            else:
                cls.methods[method] = (wrapper, format, parameters, content, conditions)
            return wrapper

        return decorator
