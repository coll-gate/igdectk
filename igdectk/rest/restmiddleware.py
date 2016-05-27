# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Middleware thats manage common view errors.
The middleware decorate the request with a format (HTML by default),
and by a list of URL parameters.
When a view is decorated by def_request or def_auth_request,
this modify the data attached to the request and the format.
"""

import json
import logging

from django import http
from django.core.exceptions import *
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib import messages
from django.core.urlresolvers import resolve
from django.apps import apps
from django.utils.translation.trans_real import parse_accept_lang_header

import igdectk.xmlio

from . import Format

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"


logger = logging.getLogger(__name__)


class ViewExceptionRest(Exception):

    """
    Formated exception with message and code.

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
    def prefered_type(self):
        """
        Get the prefered media_type as Format enum.
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

    def prefered_language_code(self):
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


class IGdecTkRestMiddleware(object):

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

    @staticmethod
    def format_response(request, message, code):
        """
        Helper to format a response related to the format and parameters
        defined into the request, a message, and an HTTP code.

        :param RequestContext request: Django request object.
        :param str message: Message contant string.
        :param int code: HTTP code.

        :return: An HTTP response object.
        :rtype: HttpResponse
        """
        response_type = IGdecTkRestMiddleware.TYPES.get(code, http.HttpResponse)

        result = {
            "result": "failed",
            "cause": message,
            "code": code
        }

        # JSON format
        if request.format == Format.JSON:
            data = json.dumps(result)

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
                    context_instance=RequestContext(request))
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

    def process_exception(self, request, exception):
        if isinstance(exception, ViewExceptionRest):
            message, code = exception.args
        elif isinstance(exception, SuspiciousOperation):
            message = exception.args[0]
            code = 400
        elif isinstance(exception, PermissionDenied):
            message = exception.args[0]
            code = 403
        elif (isinstance(exception, http.Http404) or
              isinstance(exception, ObjectDoesNotExist) or
              isinstance(exception, MultipleObjectsReturned)):
            message = exception.args[0]
            code = 404
        else:
            message = repr(exception)
            code = 500

            import traceback
            # write the traceback to the logger (should be redirected to console)
            logger.error(traceback.format_exc())

        return IGdecTkRestMiddleware.format_response(request, message, code)
