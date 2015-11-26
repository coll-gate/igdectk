# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Advanced CSRF middleware for django.
"""

from __future__ import unicode_literals

from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_text
from django.utils.http import same_origin

from django.middleware.csrf import *
from django.middleware.csrf import _sanitize_token, _get_new_csrf_key  # , _get_failure_view

from igdectk.rest.restmiddleware import IGdecTkRestMiddleware

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"


class CsrfViewMiddleware(object):

    """
    Middleware that requires a present and correct csrfmiddlewaretoken
    for POST/PUT/DELETE requests that have a CSRF cookie, and sets an outgoing
    CSRF cookie.
    This middleware should be used in conjunction with the csrf_token template
    tag.
    The CSRF cookie rotate after it was consumed. That mean the client side must
    takes care to always sending the latest value of the cookie.
    """
    # The _accept and _reject methods currently only exist for the sake of the
    # requires_csrf_token decorator.

    def _accept(self, request):
        # Avoid checking the request twice by adding a custom attribute to
        # request.  This will be relevant when both decorator and middleware
        # are used.
        request.csrf_processing_done = True
        return None

    def _reject(self, request, reason):
        logger.warning(
            'Forbidden (%s): %s', reason, request.path,
            extra={
                'status_code': 403,
                'request': request,
            }
        )

        # it is not defined at this level
        request.format = request.header.prefered_type

        return IGdecTkRestMiddleware.format_response(request, reason, 403)
        # return _get_failure_view()(request, reason=reason)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(request, 'csrf_processing_done', False):
            return None

        try:
            csrf_token = _sanitize_token(
                request.COOKIES[settings.CSRF_COOKIE_NAME])
            # Use same token next time
            request.META['CSRF_COOKIE'] = csrf_token
        except KeyError:
            csrf_token = None
            # Generate token and store it in the request, so it's
            # available to the view.
            request.META["CSRF_COOKIE"] = _get_new_csrf_key()

        # Wait until request.META["CSRF_COOKIE"] has been manipulated before
        # bailing out, so that get_token still works
        if getattr(callback, 'csrf_exempt', False):
            return None

        # Assume that anything not defined as 'safe' by RFC2616 needs protection
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            if getattr(request, '_dont_enforce_csrf_checks', False):
                # Mechanism to turn off CSRF checks for test suite.
                # It comes after the creation of CSRF cookies, so that
                # everything else continues to work exactly the same
                # (e.g. cookies are sent, etc.), but before any
                # branches that call reject().
                return self._accept(request)

            if request.is_secure():
                # Suppose user visits http://example.com/
                # An active network attacker (man-in-the-middle, MITM) sends a
                # POST form that targets https://example.com/detonate-bomb/ and
                # submits it via JavaScript.
                #
                # The attacker will need to provide a CSRF cookie and token, but
                # that's no problem for a MITM and the session-independent
                # nonce we're using. So the MITM can circumvent the CSRF
                # protection. This is true for any HTTP connection, but anyone
                # using HTTPS expects better! For this reason, for
                # https://example.com/ we need additional protection that treats
                # http://example.com/ as completely untrusted. Under HTTPS,
                # Barth et al. found that the Referer header is missing for
                # same-domain requests in only about 0.2% of cases or less, so
                # we can use strict Referer checking.
                referer = force_text(
                    request.META.get('HTTP_REFERER'),
                    strings_only=True,
                    errors='replace'
                )
                if referer is None:
                    return self._reject(request, REASON_NO_REFERER)

                # Note that request.get_host() includes the port.
                good_referer = 'https://%s/' % request.get_host()
                if not same_origin(referer, good_referer):
                    reason = REASON_BAD_REFERER % (referer, good_referer)
                    return self._reject(request, reason)

            if csrf_token is None:
                # No CSRF cookie. For POST requests, we insist on a CSRF cookie,
                # and in this way we can avoid all CSRF attacks, including login
                # CSRF.
                return self._reject(request, REASON_NO_CSRF_COOKIE)

            # Check non-cookie token for match.
            request_csrf_token = ""
            if request.method in ("POST", "PUT", "DELETE", "PATCH"):
                try:
                    request_csrf_token = request.POST.get('csrfmiddlewaretoken', '')
                except IOError:
                    # Handle a broken connection before we've completed reading
                    # the POST data. process_view shouldn't raise any
                    # exceptions, so we'll ignore and serve the user a 403
                    # (assuming they're still listening, which they probably
                    # aren't because of the error).
                    pass

            if request_csrf_token == "":
                # Fall back to X-CSRFToken, to make things easier for AJAX,
                # and possible for PUT/DELETE.
                request_csrf_token = request.META.get(
                    getattr(settings, 'CSRF_HEADER_NAME') if hasattr(settings, 'CSRF_HEADER_NAME') else 'HTTP_X_CSRFTOKEN',
                    '')

            if not constant_time_compare(request_csrf_token, csrf_token):
                return self._reject(request, REASON_BAD_TOKEN)

            # rotating token
            rotate_token(request)

        return self._accept(request)

    def process_response(self, request, response):
        if getattr(response, 'csrf_processing_done', False):
            return response

        # If CSRF_COOKIE is unset, then CsrfViewMiddleware.process_view was
        # never called, probably because a request middleware returned a response
        # (for example, contrib.auth redirecting to a login page).
        if request.META.get("CSRF_COOKIE") is None:
            return response

        if not request.META.get("CSRF_COOKIE_USED", False):
            return response

        # Set the CSRF cookie even if it's already set, so we renew
        # the expiry timer.
        response.set_cookie(settings.CSRF_COOKIE_NAME,
                            request.META["CSRF_COOKIE"],
                            max_age=getattr(settings, 'CSRF_COOKIE_AGE') if hasattr(settings, 'CSRF_COOKIE_AGE') else 31449600,
                            domain=settings.CSRF_COOKIE_DOMAIN,
                            path=settings.CSRF_COOKIE_PATH,
                            secure=settings.CSRF_COOKIE_SECURE,
                            httponly=settings.CSRF_COOKIE_HTTPONLY
                            )
        # Content varies with the CSRF cookie, so set the Vary header.
        patch_vary_headers(response, ('Cookie',))
        response.csrf_processing_done = True
        return response
