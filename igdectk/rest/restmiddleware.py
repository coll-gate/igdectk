# -*- coding: utf-8; -*-
#
# @file restmiddleware.py
# @brief REST django middleware.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-04-13
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details Middleware thats manage common view errors.
# The middleware decorate the request with a format (HTML by default), and by a list of URL parameters.
# When a view is decorated by def_request or def_auth_request,
# this modify the data attached to the request and the format.

import json
import logging
import threading

from django import http
from django.core.exceptions import *
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import resolve
from django.apps import apps
from django.utils.translation.trans_real import parse_accept_lang_header

from validictory import FieldValidationError

import igdectk.xmlio

from igdectk.rest.response import ComplexEncoder

from . import Format

logger = logging.getLogger(__name__)


class ViewExceptionRest(Exception):
    """
    Formatted exception with message and code.

    :param str message: Cause of the exception
    :param int code: HTTP error code
    """

    def __init__(self, message, code):
        super(Exception, self).__init__(message, code)
        self.code = code


class HttpResponseUnauthorized(http.HttpResponse):
    status_code = 401


def parse_content_type(content_type):
    parts = content_type.strip().split(";")
    media_type = parts.pop(0)
    media_params = []
    for part in parts:
        (key, value) = part.lstrip().split("=", 1)
        media_params.append((key, value))
    return (media_type, tuple(media_params))


def parse_accept_header(accept):
    """
    Parse the Accept header.

    :param str accept: Accept string from HTTP header.

    :return: A list with pairs of (media_type, q_value), ordered by q values.
    :rtype: list(tuple)
    """
    result = []
    for media_range in accept.split(","):
        parts = media_range.strip().split(";")
        media_type = parts.pop(0)
        media_params = []
        q = 1.0
        for part in parts:
            (key, value) = part.lstrip().split("=", 1)
            if key == "q":
                q = float(value)
            else:
                media_params.append((key, value))
        result.append((media_type, tuple(media_params), q))
    result.sort(key=lambda x: -x[2])
    return result


class HttpHeader(object):

    """
    HTTP header parser with cache.
    """

    def __init__(self, request):
        self.request = request

        # HTTP_ACCEPT
        self._accept = None
        self._accepted_types = None

        # HTTP_ACCEPT_LANGUAGE
        self._accept_language = None
        self._accepted_language_codes = None

        # CONTENT_TYPE
        self._content_type = None
        self._content_format = None

    def _cache_http_accept(self):
        accept = parse_accept_header(self.request.META.get("HTTP_ACCEPT", ""))
        self._accept = accept
        self._accepted_types = [t[0] for t in accept]

    @property
    def accept(self):
        """
        Returns the HTTP_ACCEPT list of pairs (media_type, q_value).
        This list is cached the first time.
        """
        # not cached
        if not self._accept:
            self._cache_http_accept()
        return self._accept

    @property
    def accepted_types(self):
        """
        Sames as :ref:`accept` but returns only the media_type.
        This list is cached the first time.
        """
        # not cached
        if not self._accepted_types:
            self._cache_http_accept()
        return self._accepted_types

    @property
    def preferred_type(self):
        """
        Get the preferred media_type as Format enum.
        """
        # not cached
        if not self._accepted_types:
            self._cache_http_accept()

        if not self._accepted_types:
            return Format.HTML

        if self._accepted_types[0] == Format.JSON.content_type:
            return Format.JSON
        elif self._accepted_types[0] == Format.XML.content_type:
            return Format.XML
        elif self._accepted_types[0] == Format.HTML.content_type:
            return Format.HTML
        elif self._accepted_types[0] == Format.MULTIPART.content_type:
            return Format.MULTIPART
        elif self._accepted_types[0] == Format.TEXT.content_type:
            return Format.TEXT
        else:
            return Format.TEXT

    def _cache_http_accept_language(self):
        accept_language = parse_accept_lang_header(self.request.META.get("HTTP_ACCEPT_LANGUAGE", ""))
        self._accept_language = accept_language
        self._accepted_language_codes = [t[0] for t in accept_language]

    @property
    def accept_language(self):
        """
        Returns the HTTP_ACCEPT_LANGUAGE as a list of pairs.
        This list is cached the first time.
        """
        # not cached
        if not self._accept_language:
            self._cache_http_accept_language()
        return self._accept_language

    @property
    def accepted_language_codes(self):
        """
        Sames as :ref:`accept_language` but returns only the languages codes.
        This list is cached the first time.
        """
        # not cached
        if not self._accepted_laguage_codes:
            self._cache_http_accept_language()
        return self._accepted_laguage_codes

    @property
    def preferred_language_code(self):
        # not cached
        if not self._accepted_language_codes:
            self._cache_http_accept_language()
        if len(self._accepted_language_codes) > 0:
            return self._accepted_language_codes[0]
        else:
            return 'en_US'

    def _cache_content_type(self):
        self._content_type = parse_content_type(self.request.META.get("CONTENT_TYPE", ""))

        if self._content_type[0] == Format.JSON.content_type:
            self._content_format = Format.JSON
        elif self._content_type[0] == Format.XML.content_type:
            self._content_format = Format.XML
        elif self._content_type[0] == Format.HTML.content_type:
            self._content_format = Format.HTML
        elif self._content_type[0] == Format.MULTIPART.content_type:
            self._content_format = Format.MULTIPART
        elif self._content_type[0] == Format.TEXT.content_type:
            self._content_format = Format.TEXT
        else:
            self._content_format = Format.ANY

    @property
    def content_type(self):
        """
        Returns a pair with content type and a tuples of content settings.
        """
        if not self._content_type:
            self._cache_content_type()
        return self._content_type

    @property
    def content_format(self):
        """
        Returns a Format for the content type.
        """
        if not self._content_format:
            self._cache_content_type()
        return self._content_format


class RestMiddleware(object):
    """
    Middleware that manages request format and catch views exceptions.
    It also manage the customized view errors (page if HTML else JSON).

    The middleware decorate the request with a format (HTML by default),
    and by a list of URL parameters.

    When a view is decorated by :meth:`igdectk.rest.handler.RestHandler.def_request`,
    :meth:`igdectk.rest.handler.RestHandler.def_auth_request` or by
    :meth:`igdectk.rest.handler.RestHandler.def_admin_request`,
    the decorator can attach a data dict to the request object.
    """

    TYPES = {
        400: http.HttpResponseBadRequest,
        401: HttpResponseUnauthorized,
        403: http.HttpResponseForbidden,
        404: http.HttpResponseNotFound,
        500: http.HttpResponseServerError,
    }

    thread_local = threading.local()

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        try:
            response = self.get_response(request)
        except BaseException as e:
            response = self.process_exception(request, e)

        return response

    @staticmethod
    def format_response(request, message, code, error=""):
        """
        Helper to format a response related to the format and parameters
        defined into the request, a message, and an HTTP code.

        :param RequestContext request: Django request object.
        :param str message: Message constant string.
        :param int code: HTTP code.

        :return: An HTTP response object.
        :rtype: HttpResponse
        """
        response_type = RestMiddleware.TYPES.get(code, http.HttpResponse)

        result = {
            "result": "failed",
            "cause": message,
            "code": code,
            "error": error
        }

        # JSON format
        if request.format == Format.JSON:
            data = json.dumps(result, cls=ComplexEncoder)

        # HTML format
        elif request.format == Format.HTML:
            # append a Bootstrap message error
            messages.error(request, 'Http %i: %s' % (code, message))

            # render a default error page if it excepts
            try:
                # get HTTP_TEMPLATE_STRING from the app of the request
                app_name = resolve(request.path).app_name
                current_app = apps.get_app_config(app_name)
                http_template_string = current_app.http_template_string

                data = render_to_string(
                    http_template_string % (code,),
                    result,
                    request=request)
            except Exception:
                return response_type('Http %i: %s' % (code, message), RequestContext(request))

            return response_type(data)

        # XML format
        elif request.format == Format.XML:
            data = igdectk.xmlio.dumps(result)

        # TEXT format
        elif request.format == Format.TEXT:
            data = "result: %(result)s\ncause: %(cause)s\ncode: %(code)i" % result

        # ANY others formats
        else:
            data = "result: %(result)s\ncause: %(cause)s\ncode: %(code)i" % result

        return response_type(data, content_type=request.format.content_type)

    def process_request(self, request):
        # default request data format to HTML
        request.format = Format.HTML

        # an empty list of url parameters
        request.parameters = ()

        request.header = HttpHeader(request)

        # initialize thread local current request information
        RestMiddleware.thread_local.current_user = request.user
        RestMiddleware.thread_local.current_remote_addr = request.META.get('REMOTE_ADDR', '')

    def process_exception(self, request, exception):
        if isinstance(exception, ViewExceptionRest):
            cause, code = exception.args
            error = "view_exception"
        elif isinstance(exception, ValueError):
            cause = exception.args[0]
            code = 400
            error = "value_error" if len(exception.args) < 2 else exception.args[1]
        elif isinstance(exception, SuspiciousOperation):
            cause = exception.args[0]
            code = 400
            error = "suspicious_operation" if len(exception.args) < 2 else exception.args[1]
        elif isinstance(exception, PermissionDenied):
            cause = exception.args[0]
            code = 403
            error = "permission_denied" if len(exception.args) < 2 else exception.args[1]
        elif isinstance(exception, http.Http404):
            cause = exception.args[0]
            code = 404
            error = "http404" if len(exception.args) < 2 else exception.args[1]
        elif isinstance(exception, ObjectDoesNotExist):
            cause = exception.args[0]
            code = 404
            error = "object_does_not_exists" if len(exception.args) < 2 else exception.args[1]
        elif isinstance(exception, MultipleObjectsReturned):
            cause = exception.args[0]
            code = 404
            error = "multiple_objects_returned" if len(exception.args) < 2 else exception.args[1]
        elif isinstance(exception, FieldValidationError):
            cause = exception.args[0]
            code = 400
            error = "field_validation_error" if len(exception.args) < 2 else exception.args[1]
        elif isinstance(exception, ValidationError):
            cause = exception.messages
            code = 400
            error = "field_validation_error" if len(exception.args) < 2 else exception.args[1]
        else:
            cause = repr(exception)
            code = 500
            error = "internal_error" if len(exception.args) < 2 else exception.args[1]

            import traceback
            # write the traceback to the logger (should be redirected to console)
            logger.error(traceback.format_exc())

        return RestMiddleware.format_response(request, cause, code, error)

    @staticmethod
    def current_user():
        tl = RestMiddleware.thread_local
        if hasattr(tl, 'current_user'):
            return tl.current_user
        else:
            return None

    @staticmethod
    def current_remote_addr():
        tl = RestMiddleware.thread_local
        if hasattr(tl, 'current_remote_addr'):
            return tl.current_remote_addr
        else:
            return ''
