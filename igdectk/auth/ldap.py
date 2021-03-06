# -*- coding: utf-8; -*-
#
# @file ldap.py
# @brief LDAP authentication backend for django.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-04-13
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details

from __future__ import unicode_literals

import ldap3

from django.conf import settings
from django.contrib.auth import get_user_model
# from django.contrib.auth.models import Permission
from django.contrib.auth.backends import ModelBackend


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
        :param str 'BASE_DN': Base domain name as a string.
        :param dict 'OPTIONS': Set of options:
        :param str 'username_attr': Name of the attribute of the username (default is "uid")
        :param boolean 'auto_add_user': True means users that does not exists into
            the user table are automatically created. The next parameters are relevant
            if this setting is True.
        :param str 'search_filter': LDAP search filter is a list wrapped by parenthesis,
            containing pairs of fields name and value separate by a equal sign (=), and each
            pair are separate by a comma (,).
        :param list(str) 'email_attrs': List of candidates, in order of priority,
            containing an email adress. Or not defined if email field is not wanted.
        :param dict(str|str) 'state_fields': Defines a dict of candidates, in order of priority,
            containing the user status (active, or not) and its value. In others words,
            the key contains a name of attribute, and its value is the value meaning
            the account is in its active state.
            Or None if status field should be not checked.
        :param list(str) 'firstname_attrs': List of candidates, in order of priority,
            containing a first name. Or not defined if first name field is not wanted.
        :param list(str) 'lastname_attrs': List of candidates, in order of priority,
            containing a last name. Or not defined if last name field is not wanted.

        If state fields return a disabled account, then the authentication returns None.
        If email fields returns empty email then the newly created account will have an empty email.
    """

    def authenticate(self, username=None, password=None, **kwargs):
        base_dn = settings.LDAPS['default']['BASE_DN']

        UserModel = get_user_model()

        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        # is user in DB
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            options = settings.LDAPS['default'].get('OPTIONS', {})

            # auto creation of non registered users
            if options.get('auto_add_user', True):
                email = ''
                firstname = ''
                lastname = ''

                state_attrs = options.get('state_attrs', {})
                email_attrs = options.get('email_attrs', [])
                firstname_attrs = options.get('firstname_attrs', [])
                lastname_attrs = options.get('lastname_attrs', [])
                search_filter = options.get('search_filter', '()')
                username_attr = options.get('username_attr', 'uid')

                search_filters = [x for x in search_filter.lstrip('(').rstrip(')').split(',') if x != ""]
                search_filters.append('%s=%s' % (username_attr, username))
                search_filter = '(%s)' % ','.join(search_filters)

                # process an LDAP query for the uid
                srv = ldap3.Server(settings.LDAPS['default']['HOST'])
                conn = ldap3.Connection(srv, auto_bind=True, client_strategy=ldap3.SYNC)

                attributes = [username_attr]

                if email_attrs:
                    attributes.extend(email_attrs)

                if firstname_attrs:
                    attributes.extend(firstname_attrs)

                if lastname_attrs:
                    attributes.extend(lastname_attrs)

                if state_attrs:
                    attributes.extend(state_attrs.keys())
                    active_user = False
                else:
                    active_user = True

                conn.search(base_dn, search_filter, ldap3.SUBTREE, attributes=attributes)

                for r in conn.response:
                    if 'attributes' not in r:
                        continue

                    attrs = r['attributes']

                    if username_attr not in attrs:
                        continue

                    for stk, stv in state_attrs.items():
                        if stk in attrs and attrs[stk][0] and attrs[stk][0] == stv:
                            active_user = True
                            break

                    for f in email_attrs:
                        if f in attrs and attrs[f][0]:
                            email = attrs[f][0]
                            break

                    for f in firstname_attrs:
                        if f in attrs and attrs[f][0]:
                            firstname = attrs[f][0]
                            break

                    for f in lastname_attrs:
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

            options = settings.LDAPS['default'].get('OPTIONS', {})
            username_attr = options.get('username_attr', 'uid')
            search_filter = options.get('search_filter', '()')

            search_filters = [x for x in search_filter.lstrip('(').rstrip(')').split(',') if x != ""]
            search_filters.append('%s=%s' % (username_attr, username))
            search_filter = '(%s)' % ','.join(search_filters)

            conn = ldap3.Connection(srv, auto_bind=True, client_strategy=ldap3.SYNC)
            conn.search(base_dn, search_filter, ldap3.SUBTREE, attributes=[username_attr])

            if len(conn.response) != 1:
                return None

            conn = ldap3.Connection(
                srv,
                authentication=ldap3.SIMPLE,
                user=conn.response[0]['dn'],
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
