# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
ldap authentication backend for django.
"""

from __future__ import unicode_literals

import ldap3

from django.conf import settings
from django.contrib.auth import get_user_model
# from django.contrib.auth.models import Permission
from django.contrib.auth.backends import ModelBackend

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"


class LdapAuthenticationBackend(ModelBackend):

    """
        Authenticates against settings.AUTH_USER_MODEL and LDAP.
    """

    def authenticate(self, username=None, password=None, **kwargs):
        user_dn = settings.LDAPS['default']['USER_DN'] % (
            username)

        UserModel = get_user_model()

        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        # is user in DB
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            options = settings.LDAPS['default'].get('OPTIONS', {})

            # auto creation of non registred users
            if options.get('auto_add_user', True):
                email = ''

                get_email = options.get('get_email', False)
                get_state = options.get('get_state', False)

                if get_email or get_state:
                    email_fields = options.get('email_fields', [])
                    state_fields = options.get('state_fields', {})
                    search_filter = options.get('search_filter', '()')

                    # process an LDAP query for the uid
                    srv = ldap3.Server(settings.LDAPS['default']['HOST'])
                    conn = ldap3.Connection(srv, auto_bind=True, client_strategy=ldap3.SYNC)

                    attributes = ['uid']

                    if get_email:
                        attributes.extend(email_fields)

                    if get_state:
                        attributes.extend(state_fields.keys())
                        active_user = False
                    else:
                        active_user = True

                    conn.search(user_dn, search_filter, ldap3.SUBTREE, attributes=attributes)

                    for r in conn.response:
                        if 'attributes' not in r:
                            continue

                        attrs = r['attributes']

                        if 'uid' not in attrs:
                            continue

                        for stk, stv in state_fields.items():
                            if stk in attrs and attrs[stk][0] and attrs[stk][0] == stv:
                                active_user = True
                                break

                        for ef in email_fields:
                            if ef in attrs and attrs[ef][0]:
                                email = attrs[ef][0]
                                break

                    if active_user:
                        user = UserModel.objects.create_user(username, email, '')
                    else:
                        return None
                else:
                    user = UserModel.objects.create_user(username, '', '')
            else:
                # Run the default password hasher once to reduce the timing
                # difference between an existing and a non-existing user (#20760).
                UserModel().set_password(password)
                return None

        if user.is_staff:
            if user.check_password(password):
                # user.backend = __name__ + '.LdapAuthenticationBackend'
                return user

        # try to bind account
        try:
            srv = ldap3.Server(settings.LDAPS['default']['HOST'])
            conn = ldap3.Connection(
                srv,
                authentication=ldap3.AUTH_SIMPLE,
                user=user_dn,
                password=password,
                check_names=True,
                lazy=False,
                client_strategy=ldap3.STRATEGY_SYNC,
                raise_exceptions=True)

            conn.open()
            conn.bind()
        except ldap3.core.exceptions.LDAPInvalidCredentialsResult:
            return None
        except Exception:
            return None

        return user

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
