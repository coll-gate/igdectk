# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
LDAP authentication backend for django.
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

        Here is the list of LDAP settings and options
        ---------------------------------------------

        The Django settings must contain a dict named LDAPS like :

        .. code-block:: python

            LDAPS = {
                'default': {
                    'HOST': "ldap.hostname",
                    'USER_DN': "uid=%s, ou=..., dc=..., ...",
                    'OPTIONS': {
                        'auto_add_user': boolean,
                        'search_filter': "(field=value,...)",
                        'email_fields': ['field1', ...] or None,
                        'state_fields': {'field1': 'active_state', ...: ..., ...} or None,
                        'firstname_fields': ['field1', ...] or None,
                        'lastname_fields': ['field1', ...] or None,
                    }
                },
            }


        :param dict 'default': Used by this backend. Any others entry are ignored.
        :param str 'HOST': LDAP hostname (with port if necessary).
        :param str 'USER_DN': User domain name as a string. The parameter representing
            the user identifier must be equal to '%s' because this field is completed by the username
            coming from the authentication method.
        :param dict 'OPTIONS': Set of options:
        :param boolean 'auto_add_user': True means users that does not exists into
            the user table are automaticaly created. The next parameters are relavant
            if this setting is True.
        :param str 'search_filter': LDAP search filter is a list wrapped by parenthesis,
            containing pairs of fields name and value separate by a equal sign (=), and each
            pair are separate by a comma (,).
        :param list(str) 'email_fields': List of candidats, in order of priority,
            containing an email adresse. Or not defined if email field is not wanted.
        :param dict(str|str) 'state_fields': Defines a dict of candidats, in order of priority,
            containing the user status (active, or not) and its value. In others words,
            the key contains a name of attribute, and its value is the value meaning
            the account is in its active state.
            Or None if status field should be not checked.
        :param list(str) 'firstname_fields': List of candidats, in order of priority,
            containing a first name. Or not defined if first name field is not wanted.
        :param list(str) 'lastname_fields': List of candidats, in order of priority,
            containing a last name. Or not defined if last name field is not wanted.

        If state fields return a disabled account, then the authentication returns None.
        If email fields returns empty email then the newly created account will have an empty email.
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
                firstname = ''
                lastname = ''

                state_fields = options.get('state_fields', {})
                email_fields = options.get('email_fields', [])
                firstname_fields = options.get('firstname_fields', [])
                lastname_fields = options.get('lastname_fields', [])
                search_filter = options.get('search_filter', '()')

                # process an LDAP query for the uid
                srv = ldap3.Server(settings.LDAPS['default']['HOST'])
                conn = ldap3.Connection(srv, auto_bind=True, client_strategy=ldap3.SYNC)

                attributes = ['uid']

                if email_fields:
                    attributes.extend(email_fields)

                if firstname_fields:
                    attributes.extend(firstname_fields)

                if lastname_fields:
                    attributes.extend(lastname_fields)

                if state_fields:
                    attributes.extend(state_fields.keys())
                    active_user = False
                else:
                    active_user = True

                if len(attributes) > 1:
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

                        for f in email_fields:
                            if f in attrs and attrs[f][0]:
                                email = attrs[f][0]
                                break

                        for f in firstname_fields:
                            if f in attrs and attrs[f][0]:
                                firstname = attrs[f][0]
                                break

                        for f in lastname_fields:
                            if f in attrs and attrs[f][0]:
                                lastname = attrs[f][0]
                                break

                if active_user:
                    user = UserModel.objects.create_user(
                        username, email, '', first_name=firstname, last_name=lastname)
                else:
                    return None
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
                authentication=ldap3.SIMPLE,
                user=user_dn,
                password=password,
                check_names=True,
                lazy=False,
                client_strategy=ldap3.SYNC,
                raise_exceptions=True)

            conn.open()
            conn.bind()
        except ldap3.core.exceptions.LDAPInvalidCredentialsResult:
            return None
        except ldap3.core.exceptions.LDAPException:
            return None

        return user

    def get_user(self, user_id):
        """
        If the user does not exists into the DB but exists into the LDAP,
        this method will returns None. Only the authenticate method automaticaly
        create the user from LDAP into the DB.
        """
        UserModel = get_user_model()
        try:
            return UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
