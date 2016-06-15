# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 INRA UMR1095 GDEC

"""
module sub-package init.
"""

AUTH_ANY = 0
AUTH_GUEST = 1
AUTH_USER = 2
AUTH_STAFF = 3
AUTH_SUPER_USER = 4

AUTH_TYPE = (
    (0, AUTH_ANY, "auth-any"),
    (1, AUTH_GUEST, "auth-guest"),
    (2, AUTH_USER, "auth-user"),
    (3, AUTH_STAFF, "auth-staff"),
    (4, AUTH_SUPER_USER, "auth-superuser"),
)
