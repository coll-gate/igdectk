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
from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib import messages
from django.core.urlresolvers import resolve
from django.apps import apps
from django.utils.translation.trans_real import parse_accept_lang_header

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"


logger = logging.getLogger(__name__)


class ViewExceptionRest(Exception):

    """
    Formated exception with message and code.

    Parameters
    ----------
    message: string
        Cause of the exception

    code: int
        HTTP error code
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

    Parameters
    ----------
    accept: string
        Accept string from HTTP header.

    Results
    -------
    : list(tuple)
        A list with pairs of (media_type, q_value), ordered by q values.
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
        self._accept_languages = None
        self._accepted_laguages_codes = None

    def _cache_http_accept(self):
        accept = parse_accept_header(self.request.META.get("HTTP_ACCEPT", ""))
        self._accept = accept
        self._accepted_types = [t[0] for t in accept]

    @property
    def accept(self):
        # not cached
        if not self._accept:
            self._cache_http_accept()
        return self._accept

    @property
    def accepted_types(self):
        # not cached
        if not self._accepted_types:
            self._cache_http_accept()
        return self._accepted_types

    def prefered_type(self, simplified=False):
        # not cached
        if not self._accepted_types:
            self._cache_http_accept()

        if simplified:
            return self._accepted_types[0].split('/')[1].upper() if self._accepted_types else 'HTML'
        else:
            return self._accepted_types[0] if self._accepted_types else 'text/html'

    def _cache_http_accept_language(self):
        accept_language = parse_accept_lang_header(self.request.META.get("HTTP_ACCEPT_LANGUAGE", ""))
        self._accept_language = accept_language
        self._accepted_language_codes = [t[0] for t in accept_language]

    @property
    def accept_language(self):
        # not cached
        if not self._accept_language:
            self._cache_http_accept_language()
        return self._accept_language

    @property
    def accepted_language_codes(self):
        # not cached
        if not self._accepted_language_codes:
            self._cache_http_accept_language()
        return self._accepted_language_codes

    @property
    def content_type(self):
        """
        Returns a pair with content type and a tuples of content settings.
        """
        content_type = parse_content_type(self.request.META.get("CONTENT_TYPE", ""))
        return content_type


class IGdecTkRestMiddleware(object):

    """
    Middleware that manages request format and catch views exceptions.
    It also manage the customized view errors (page if HTML else JSON).

    The middleware decorate the request with a format (HTML by default),
    and by a list of URL parameters.

    When a view is decorated by :class:`igdectk.helpers.def_request`,
    :class:`igdectk.helpers.def_auth_request` or by
    :class:`igdectk.helpers.def_admin_request`,
    the decorator can attach a data dict to the request object.
    """

    def process_request(self, request):
        # default request data format to HTML
        request.format = 'HTML'

        # an empty list of url parameters
        request.parameters = ()

        request.header = HttpHeader(request)

    def process_exception(self, request, exception):
        if isinstance(exception, ViewExceptionRest):
            message, code = exception.args
        elif isinstance(exception, http.Http404):
            message = exception.args[0]
            code = 404
        else:
            message = repr(exception)
            code = 500

            import traceback
            # write the traceback to the logger (should be redirected to console)
            logger.error(traceback.format_exc())

        # JSON format
        if request.format == 'JSON':
            jsondata = json.dumps({
                "result": "failed",
                "cause": message,
                "code": code})

            types = {
                400: http.HttpResponseBadRequest,
                401: HttpResponseUnauthorized,
                404: http.HttpResponseNotFound,
                500: http.HttpResponseServerError,
            }
            response_type = types.get(code, http.HttpResponse)

            return response_type(jsondata, content_type="application/json")

        # HTML format
        elif request.format == 'HTML':
            types = {
                400: http.HttpResponseBadRequest,
                401: HttpResponseUnauthorized,
                404: http.HttpResponseNotFound,
                500: http.HttpResponseServerError,
            }
            response_type = types.get(code, http.HttpResponse)

            # append a Boostrap message error
            messages.error(request, 'Http %i: %s' % (code, message))

            # render a default error page if it excepts
            try:
                # get HTTP_TEMPLATE_STRING from the app of the request
                app_name = resolve(request.path).app_name
                current_app = apps.get_app_config(app_name)
                http_template_string = current_app.http_template_string

                t = render_to_string(
                    http_template_string % (code,),
                    {'error': message},
                    context_instance=RequestContext(request))
            except Exception:
                return response_type('Http %i: %s' % (code, message),
                                     RequestContext(request))

            return response_type(t)
