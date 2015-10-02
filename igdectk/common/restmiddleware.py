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

__title__ = 'Inra Unit Tools Common'
__copyright__ = "Copyright (c) 2015 INRA UMR1095 GDEC"
__organisation__ = "INRA"
__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"
__license__ = 'Private'

logger = logging.getLogger(__name__)


class ViewExceptionRest(Exception):
    pass


class HttpResponseUnauthorized(http.HttpResponse):
    status_code = 401


class InraUnitToolsRestMiddleware(object):

    def process_request(self, request):
        # defines a default request format to HTML
        request.format = 'HTML'
        request.parameters = ()

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

            return http.HttpResponse(jsondata, content_type="application/json")

        # HTML format
        elif request.format == 'HTML':
            types = {
                400: http.HttpResponseBadRequest,
                401: HttpResponseUnauthorized,
                404: http.HttpResponseNotFound,
                500: http.HttpResponseServerError,
            }
            response_type = types.get(code, http.HttpResponse)

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
