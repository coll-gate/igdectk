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
