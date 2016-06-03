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
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect

import igdectk.xmlio

from .restmiddleware import ViewExceptionRest

from igdectk.rest import Format, Method
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


class RestForm(object):

    """
    Rest handler to register a form with GET and POST method and HTML format.

    :ivar django.forms.Form form_class: Django formular class.
    :ivar str form_template: Complete name of the template used to render the formular.
    :ivar str form_template_name: Name of the template form variable. Default is 'form'.
    :ivar boolean auth: True if the user must be authenticated. Default False.
    :ivar boolean admin: True if the user must be a super-user. Default False.
    :ivar boolean redirect: If True, when form POST success the client is redirected to :attr:`success`
        location.
    :ivar str success: If :attr:`redirect` is True success defines the location URL to the redirection
        when form POST success.
        If False, success defines the template name to render.
    """

    form_class = None
    form_template = ''
    form_template_name = 'form'

    auth = False
    admin = False

    redirect = True
    success = '/'

    @classmethod
    def get(cls, request, form):
        """
        Method to override when it is necessary to perform initialization
        on the form before sending it to the client.

        It is permit to raise an exception here.
        """
        pass

    @classmethod
    def valid_form(cls, request, form):
        """
        Method to override to use the result of the form, when it pass
        the django form validation tests. For example updating a model.

        If False is returned the form page is returned to the client.

        It is permit to raise an exception here.
        """
        pass

    @classmethod
    def invalid_form(cls, request, form):
        """
        Method to override to use the result of the form, when it failed
        to pass the django form validation tests. For example highlight
        some fields, display an error message..

        It is permit to raise an exception here.
        """
        pass

    @classmethod
    def _register_form(cls, handler):
        # target conditions
        conditions = RestHandler._make_conditions(Format.HTML, (), {})

        # register the 'get' wrapper
        def wrapper_get(*args, **kwargs):
            request = args[0]

            # check for user authentication
            if cls.auth and not request.user.is_authenticated():
                raise ViewExceptionRest("Unauthorized", 401)

            # check for super-user authentication
            if cls.admin and not request.user.is_superuser:
                raise ViewExceptionRest("Forbidden", 403)

            form = cls.form_class()
            cls.get(request, form)

            return render(request, cls.form_template, {cls.form_template_name: form})

        wrapper_get.target_name = handler.__module__ + '.' + handler.__qualname__
        handler._register_wrapper(wrapper_get, Method.GET, Format.HTML, (), (), conditions)

        # register the 'post' wrapper
        def wrapper_post(*args, **kwargs):
            request = args[0]
            form = cls.form_class(request.POST)

            if form.is_valid():
                result = cls.valid_form(request, form)

                # valid form returns False meaning an invalid form processing
                if result is not None and result is False:
                    cls.invalid_form(request, form)
                    return render(request, cls.form_template, {cls.form_template_name: form})

                # success redirect to a dynamic location
                elif result is not None and isinstance(result, str):
                    return redirect(result)

                # success redirect to the default static location
                if cls.redirect:
                    return redirect(cls.success)
                else:
                    return render(request, cls.redirect, {})
            else:
                # invalid form
                cls.invalid_form(request, form)
                return render(request, cls.form_template, {cls.form_template_name: form})

        wrapper_post.target_name = handler.__module__ + '.' + handler.__qualname__
        handler._register_wrapper(wrapper_post, Method.POST, Format.HTML, (), (), conditions)


class RestHandlerMeta(type):

    """
    Metaclass for :class:`RestHandler` used to automatize the registration of
    the handler.
    """

    def __init__(cls, name, base, d):
        type.__init__(cls, name, base, d)

        # register only when inheritance (not base)
        if cls.__name__ is not 'RestHandler':
            cls._register(base, cls.regex, cls.name, cls.app_name, urls='urls')


class RestHandler(object, metaclass=RestHandlerMeta):

    """
    Manage RESTfull API with autogenenation and registration of urls.

    :ivar str regex: Python regular expression of the URL. It is combined with its parent
        handler regex when using inheritance of handlers.

    :ivar str name: Qualified name of the URL to be used into reverse URL and templates.
        It is possible to omit it and use :attr:`suffix` when using inheritance.

    :ivar str suffix: When inherit of a parent handler (excepted RestHandler base class),
        and if :attr:`name` is empty or None, suffix is added to the URL name
        of its parent. It is useful to avoid the rewriting of the complete path name.
        There is no need to add a separator before.

    :ivar str name_separator: Separator used between each word into the URL name. Default is '-'.

    :ivar str app_name: Application name. If None it is detect from the module where the
        class is defined.
    """

    regex = ''
    name = ''
    name_separator = '-'
    suffix = ''
    app_name = None
    application = None
    # classname_prefix = 'Rest'
    methods = {}

    unprocessed_handlers = []  # intermediary list of handles to register
    handlers = {}              # list of registered handlers (by register_urls)

    @classmethod
    def _register(cls, base, regex, name, app_name=None, urls='urls'):
        """
        Internaly called by RestHandlerMeta on class definition
        in way to create a new entry into the list of managed handlers.
        This list is finally manually inserted into each application urlpatterns
        calling register_urls.
        """
        # inheritance of the class name prefix
        # cls.classname_prefix = base[-1].classname_prefix if base[-1].classname_prefix else 'Rest'
        # last_name = cls.__name__.lstrip(base[-1].__name__).lower()

        # regex is compound of its parent regex + himself OR only himself if no parent
        cls.regex = base[-1].regex.rstrip('$') + regex.lstrip('^') if base[-1].regex else regex

        # name is compound of its parent name + suffix OR only name
        if cls.suffix:
            if base[-1] is RestHandler:
                raise RestRegistrationException('Suffix can only be defined on inherited rest handlers')
            cls.name = base[-1].name + cls.name_separator + cls.suffix

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

        if RestForm in base:
            cls._register_form(cls)

        RestHandler.unprocessed_handlers.append(cls)

    @classmethod
    def _interceptor(cls, request, **kwargs):
        methods = cls.methods.get(request.method)

        if methods:
            # decode the incoming data (json, xml, form-data, multipart/form-data)
            if request.header.content_format == Format.JSON and request.body:
                data = json.loads(request.body.decode())
            elif request.header.content_format == Format.XML and request.body:
                data = igdectk.xmlio.loads(request.body.decode())
            elif request.header.content_format == Format.MULTIPART:
                data = request.POST  # Form POST encoded
            else:
                data = request.POST  # Form POST encoded

            request.data = data

            # conditioned selection of the handler
            sub = None
            fallback = None

            for submethod in methods:
                sub = submethod

                # fallback method is the one having only the accept condition
                if len(submethod[4]) == 1 and submethod[4][0][2] is 'accept':
                    if request.header.accepted_types != ['*/*']:
                        # compare accept
                        if submethod[4][0][0] == request.header.accepted_types:
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
                            # compare accept
                            if condition[0] not in request.header.accepted_types:
                                sub = None
                                break

                # we have our candidat
                if sub:
                    break

            # if no candidat, try to use fallback
            if sub:
                method = sub
            else:
                method = fallback

            if method:
                # call the request function by calling its decorator wrapper
                result = method[0](request, **kwargs)

                if not result:
                    raise ViewExceptionRest(
                        'No results for %s %s' % (request.path, request.method), 404)
                else:
                    return result

        # when no view is defined for the method, there is no decorator
        # to apply the format, so we have to look what client ask for
        request.format = request.header.prefered_type

        raise ViewExceptionRest(
            'Undefined view for %s %s' % (request.path, request.method), 404)

    @staticmethod
    def register_urls():
        """
        This method must be called once time in the urls.py
        """
        for handler in RestHandler.unprocessed_handlers:
            if handler.regex in RestHandler.handlers:
                raise RestRegistrationException(
                    "Duplicate entry for %s('%s') with '%s'" % (handler.__name__, handler.name, handler.regex))

            handler.urls.urlpatterns.append(
                url(handler.regex, handler._interceptor, name=handler.name))

            # append to registered handlers dict
            RestHandler.handlers[handler.regex] = handler

        # Empty list of unprocessed handlers
        RestHandler.unprocessed_handlers = []

    @classmethod
    def include_main_url(cls, app_name=None, url_prefix=""):
        from django.conf.urls import include, url
        import urls

        if app_name:
            name = app_name
        else:
            name = cls.__module__.split('.')[0]

        pattern = r'^%s%s/' % (url_prefix, "")  # name)

        urls.urlpatterns += url(
                     pattern,
                     include('%s.urls' % name,
                             namespace=name,
                             app_name=name)),

    @classmethod
    def _register_wrapper(cls, wrapper, method, format, parameters, content, conditions):
        """
        Internaly register a wrapper for a specific method and conditions.
        """
        # look for an existing similar entry
        if method.name in cls.methods:
            methods = cls.methods[method.name]

            for m in methods:
                if len(m[4]) == len(conditions):
                    count = 0

                    for condition in conditions:
                        if condition in m[4]:
                            count += 1

                    if count == len(conditions):
                        raise RestRegistrationException(
                            "Duplicate entry for %s with %s" % (cls.__name__, wrapper.target_name))

            cls.methods[method.name].append((wrapper, format, parameters, content, conditions))
        else:
            cls.methods[method.name] = [(wrapper, format, parameters, content, conditions)]

    @staticmethod
    def _make_conditions(format, parameters, kwargs):
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

        # url constraint presence of a parameter
        for param in parameters:
            conditions.append((param, '', 'has'))

        # HTTP_ACCEPT must respect the format value
        conditions.append((format.accept, '', 'accept'))

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
            * method : from the decorator
            * format : from the decorator

        :param igdectk.rest.Method method: One of the Method value (GET, POST...) define the accepted method.
        :param igdectk.rest.Format format: One of the Format value (JSON, HTML...) defines the format of the http response,
            and the accepted value from HTTP_ACCEPT.
        :param list parameters: A list of strings or an empty list, containing the names of the
            mandatory parameters requested in the URL.
        :param list(str) list: A list of strings or an empty list, containing the names of the
            mandatory parameters requested in the body.
        :param string conditions: The next parameters if theirs names starts with a 'url__' will
            be used as condition expression for the url parameters.

            For example, having url__action='save' mean that the url must
            contains the parameter action with the value 'save'.

            This is useful to have many action for a same HTTP method.
            It is possible to have many 'url__' conditions.


        .. note::

            Only a single free of conditions method per handler can be registered.
            Otherwise a :exc:`RestRegistrationException` exception is raised.
        """
        # create a decorator for the function
        def decorator(func):
            def wrapper(*args, **kwargs):
                request = args[0]

                # add the parameters to the request
                request.format = format
                request.parameters = parameters

                # check for the existence of the values into the encoded body
                data = request.data if hasattr(request, 'data') else request.POST

                if type(content) == tuple:
                    for p in content:
                        if p not in data:
                            raise ViewExceptionRest("Missing parameter " + p, 400)
                elif type(content) == dict and request.header.content_type[0] == Format.JSON.content_type:
                    # or do a data validation
                    validictory.validate(data, content)

                # call the function
                return func(*args, **kwargs)

            # target conditions
            conditions = RestHandler._make_conditions(format, parameters, kwargs)

            # register the wrapper
            wrapper.target_name = func.__module__ + '.' + func.__qualname__
            cls._register_wrapper(wrapper, method, format, parameters, content, conditions)

            return wrapper

        return decorator

    @classmethod
    def def_auth_request(cls, method, format, parameters=(), content=(), fallback=None, perms=None, staff=None, **kwargs):
        """
        Same as :meth:`def_request` but in addition the user must be authenticated.

        :param func fallback: Optional callback function called in case the user is not authenticated.
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
                        return fallback(request)
                    raise ViewExceptionRest("Authenticated users only", 401)

                if staff and (not request.user.is_staff and not request.user.is_superuser):
                    if fallback:
                        return fallback(request)
                    raise PermissionDenied("Superuser and staff only")

                # simple permissions check
                if perms:
                    for k, v in perms.items():
                        if not request.user.has_perm(k):
                            raise PermissionDenied(v)

                # check for the existence of the values into the encoded body
                data = request.data if hasattr(request, 'data') else request.POST

                if type(content) == tuple:
                    # simple existence of a parameter into the body (dict and flat model)
                    for p in content:
                        if p not in data:
                            raise ViewExceptionRest("Missing parameter " + p, 400)
                elif type(content) == dict and request.header.content_format == Format.JSON:
                    # or do a data validation for JSON content (dict and tree model)
                    validictory.validate(data, content)

                # call the function
                return func(*args, **kwargs)

            # target conditions
            conditions = RestHandler._make_conditions(format, parameters, kwargs)

            # register the wrapper
            wrapper.target_name = func.__module__ + '.' + func.__qualname__
            cls._register_wrapper(wrapper, method, format, parameters, content, conditions)

            return wrapper

        return decorator

    @classmethod
    def def_admin_request(cls, method, format, parameters=(), content=(), fallback=None, **kwargs):
        """
        Same as :meth:`def_request` but in addition the user must be authenticated
        and superuser.

        :param func fallback: Optional callback function called in case the user is not authenticated.
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
                        return fallback(request)
                    raise ViewExceptionRest("Authenticated users only", 401)

                # check for super-user authentication
                if not request.user.is_superuser:
                    if fallback:
                        return fallback(request)
                    raise PermissionDenied("Superuser only")

                # check for the existence of the values into the encoded body
                data = request.data if hasattr(request, 'data') else request.POST

                if type(content) == tuple:
                    # simple existence of a parameter into the body (dict and flat model)
                    for p in content:
                        if p not in data:
                            raise ViewExceptionRest("Missing parameter " + p, 400)
                elif type(content) == dict and request.header.content_format == Format.JSON:
                    # or do a data validation for JSON content (dict and tree model)
                    validictory.validate(data, content)

                # call the function
                return func(*args, **kwargs)

            # target conditions
            conditions = RestHandler._make_conditions(format, parameters, kwargs)

            # register the wrapper
            wrapper.target_name = func.__module__ + '.' + func.__qualname__
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
    Request function register and wrapper for non auth requests.

    Check the list of mandatory URL parameters.

    Check the list of mandatory content Form/JSON parameters, or validate the
    content using validictory format.

    If the format is incorrect or a parameter is missing raise a ViewException
    HTML or JSON depending of the format.

    If it pass the test, the function will contains two news parameters :
        * method : from the decorator
        * format : from the decorator

    :param igdectk.rest.Method method: One of the Method value (GET, POST...) define the accepted method.
    :param igdectk.rest.Format format: One of the Format value (JSON, HTML...) defines the format of the http response,
        and the accepted value from HTTP_ACCEPT.
    :param list parameters: A list of strings or an empty list, containing the names of the
        mandatory parameters requested in the URL.
    :param list(str) list: A list of strings or an empty list, containing the names of the
        mandatory parameters requested in the body.
    :param string conditions: The next parameters if theirs names starts with a 'url__' will
        be used as condition expression for the url parameters.

        For example, having url__action='save' mean that the url must
        contains the parameter action with the value 'save'.

        This is useful to have many action for a same HTTP method.
        It is possible to have many 'url__' conditions.


    .. note::

        Only a single free of conditions method per handler can be registered.
        Otherwise a :exc:`RestRegistrationException` exception is raised.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            request = args[0]

            # add the parameters to the request
            request.format = format
            request.parameters = parameters

            # check for the existence of the values into the encoded body
            data = request.data if hasattr(request, 'data') else request.POST

            if type(content) == tuple:
                # simple existence of a parameter into the body (dict and flat model)
                for p in content:
                    if p not in data:
                        raise ViewExceptionRest("Missing parameter " + p, 400)
            elif type(content) == dict and request.header.content_format == Format.JSON:
                # or do a data validation for JSON content (dict and tree model)
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
        conditions = RestHandler._make_conditions(format, parameters, kwargs)

        # register the wrapper
        wrapper.target_name = func.__module__ + '.' + func.__qualname__
        InlineRestHandler._register_wrapper(wrapper, method, format, parameters, content, conditions)

        return wrapper

    return decorator


def def_inline_auth_request(inline_handler, method, format, parameters=(), content=(), fallback=None, perms=None, staff=None, **kwargs):
    """
    Same as :func:`def_inline_request` but in addition the user must be authenticated.

    :param func fallback: Optional callback function called in case the user is not authenticated.
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
                    return fallback(request)
                raise ViewExceptionRest("Authenticated users only", 401)

            if staff and (not request.user.is_staff and not request.user.is_superuser):
                if fallback:
                    return fallback(request)
                raise PermissionDenied("Superuser and staff only")

            # simple permissions check
            if perms:
                for k, v in perms.items():
                    if not request.user.has_perm(k):
                        raise PermissionDenied(v)

            # check for the existence of the values into the encoded body
            data = request.data if hasattr(request, 'data') else request.POST

            if type(content) == tuple:
                # simple existence of a parameter into the body (dict and flat model)
                for p in content:
                    if p not in data:
                        raise ViewExceptionRest("Missing parameter " + p, 400)
            elif type(content) == dict and request.header.content_format == Format.JSON:
                # or do a data validation for JSON content (dict and tree model)
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
        conditions = RestHandler._make_conditions(format, parameters, kwargs)

        # register the wrapper
        wrapper.target_name = func.__module__ + '.' + func.__qualname__
        InlineRestHandler._register_wrapper(wrapper, method, format, parameters, content, conditions)

        return wrapper

    return decorator


def def_inline_admin_request(inline_handler, method, format, parameters=(), content=(), fallback=None, **kwargs):
    """
    Same as :meth:`def_inline_request` but in addition the user must be authenticated.

    :param func fallback: Optional callback function called in case the user is not authenticated.
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
                    return fallback(request)
                raise ViewExceptionRest("Authenticated users only", 401)

            # check for super-user authentication
            if not request.user.is_superuser:
                if fallback:
                    return fallback(request)
                raise PermissionDenied("Superuser only")

            # check for the existence of the values into the encoded body
            data = request.data if hasattr(request, 'data') else request.POST

            if type(content) == tuple:
                # simple existence of a parameter into the body (dict and flat model)
                for p in content:
                    if p not in data:
                        raise ViewExceptionRest("Missing parameter " + p, 400)
            elif type(content) == dict and request.header.content_format == Format.JSON:
                # or do a data validation for JSON content (dict and tree model)
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
        conditions = RestHandler._make_conditions(format, parameters, kwargs)

        # register the wrapper
        wrapper.target_name = func.__module__ + '.' + func.__qualname__
        InlineRestHandler._register_wrapper(wrapper, method, format, parameters, content, conditions)

        return wrapper

    return decorator
