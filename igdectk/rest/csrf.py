# -*- coding: utf-8; -*-
#
# @file csrf.py
# @brief Advanced CSRF middleware for django..
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-04-13
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details

from __future__ import unicode_literals

import logging
import re

from urllib.parse import urlparse

import django

from django.conf import settings
from django.utils.crypto import get_random_string
from django.middleware import csrf
from django.utils.cache import patch_vary_headers
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_text
from django.utils import http
from django.utils.http import is_same_domain

from igdectk.rest.restmiddleware import RestMiddleware

"""
This version make the CSRF token rotate, but since Django 1.10 this is no longer necessary because
it is renforced with a salt and regenerated each non read requests with a better security.

Also, the problem using this version with Django 1.10 is because of get_token method that is took
from django.middleware.csrf and not from this source. Causing a trouble writing an invalid token
in form using the {% csrf_token %} macro. So there is a workaround line replacing the get_token function
but this is not very clean.
"""

logger = logging.getLogger('django.request')


if django.VERSION[0] <= 1 and django.VERSION[1] <= 9:
    CSRF_KEY_LENGTH = 32

    def _get_new_csrf_key():
        return get_random_string(CSRF_KEY_LENGTH)


    def _sanitize_token(token):
        # Allow only alphanum
        if len(token) > CSRF_KEY_LENGTH:
            return _get_new_csrf_key()
        token = re.sub('[^a-zA-Z0-9]+', '', force_text(token))
        if token == "":
            # In case the cookie has been truncated to nothing at some point.
            return _get_new_csrf_key()
        return token


    def get_token(request):
        """
        Returns the CSRF token required for a POST form. The token is an
        alphanumeric value. A new token is created if one is not already set.

        A side effect of calling this function is to make the csrf_protect
        decorator and the CsrfViewMiddleware add a CSRF cookie and a 'Vary: Cookie'
        header to the outgoing response.  For this reason, you may need to use this
        function lazily, as is done by the csrf context processor.
        """
        if "CSRF_COOKIE" not in request.META:
            request.META["CSRF_COOKIE"] = _get_new_csrf_key()
        request.META["CSRF_COOKIE_USED"] = True
        return request.META["CSRF_COOKIE"]

    # workaround: override of the get_token method
    django.middleware.csrf.get_token = get_token

    def rotate_token(request):
        """
        Changes the CSRF token in use for a request - should be done on login
        for security purposes.
        """
        request.META.update({
            "CSRF_COOKIE_USED": True,
            "CSRF_COOKIE": _get_new_csrf_key(),
        })


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

        def __init__(self, get_response=None):
            self.get_response = get_response

        def __call__(self, request):
            response = self.get_response(request)
            response = self.process_response(request, response)

            return response

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
            request.format = request.header.preferred_type

            return RestMiddleware.format_response(request, reason, 403)

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
                        return self._reject(request, csrf.REASON_NO_REFERER)

                    # django <= 1.8
                    if getattr(http, 'same_origin'):
                        # Note that request.get_host() includes the port.
                        good_referer = 'https://%s/' % request.get_host()
                        if not http.same_origin(referer, good_referer):
                            reason = csrf.REASON_BAD_REFERER % (referer, good_referer)
                            return self._reject(request, reason)
                    else:
                        # django >= 1.9
                        referer = urlparse(referer)

                        # Make sure we have a valid URL for Referer.
                        if '' in (referer.scheme, referer.netloc):
                            return self._reject(request, csrf.REASON_MALFORMED_REFERER)

                        # Ensure that our Referer is also secure.
                        if referer.scheme != 'https':
                            return self._reject(request, csrf.REASON_INSECURE_REFERER)

                        # If there isn't a CSRF_COOKIE_DOMAIN, assume we need an exact
                        # match on host:port. If not, obey the cookie rules.
                        if settings.CSRF_COOKIE_DOMAIN is None:
                            # request.get_host() includes the port.
                            good_referer = request.get_host()
                        else:
                            good_referer = settings.CSRF_COOKIE_DOMAIN
                            server_port = request.META['SERVER_PORT']
                            if server_port not in ('443', '80'):
                                good_referer = '%s:%s' % (good_referer, server_port)

                        # Here we generate a list of all acceptable HTTP referers,
                        # including the current host since that has been validated
                        # upstream.
                        good_hosts = list(settings.CSRF_TRUSTED_ORIGINS)
                        good_hosts.append(good_referer)

                        if not any(is_same_domain(referer.netloc, host) for host in good_hosts):
                            reason = csrf.REASON_BAD_REFERER % referer.geturl()
                            return self._reject(request, reason)

                if csrf_token is None:
                    # No CSRF cookie. For POST requests, we insist on a CSRF cookie,
                    # and in this way we can avoid all CSRF attacks, including login
                    # CSRF.
                    return self._reject(request, csrf.REASON_NO_CSRF_COOKIE)

                # Check non-cookie token for match.
                request_csrf_token = ""
                if request.method in ("POST", "PUT", "PATCH"):  # DELETE has no body
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
                    return self._reject(request, csrf.REASON_BAD_TOKEN)

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
                                max_age=settings.CSRF_COOKIE_AGE,
                                domain=settings.CSRF_COOKIE_DOMAIN,
                                path=settings.CSRF_COOKIE_PATH,
                                secure=settings.CSRF_COOKIE_SECURE,
                                httponly=settings.CSRF_COOKIE_HTTPONLY
                                )
            # Content varies with the CSRF cookie, so set the Vary header.
            patch_vary_headers(response, ('Cookie',))
            response.csrf_processing_done = True
            return response
else:
    import django.middleware.csrf

    class CsrfViewMiddleware(csrf.CsrfViewMiddleware):
        def __init__(self, get_response=None):
            super(CsrfViewMiddleware, self).__init__(get_response)

        def _reject(self, request, reason):
            logger.warning(
                'Forbidden (%s): %s', reason, request.path,
                extra={
                    'status_code': 403,
                    'request': request,
                }
            )

            # it is not defined at this level
            request.format = request.header.preferred_type

            return RestMiddleware.format_response(request, reason, 403)
