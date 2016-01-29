# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 INRA UMR1095 GDEC

"""
module sub-package init.
"""

AUTH_ANY = 0
AUTH_GUEST = 1
AUTH_USER = 2
AUTH_SUPER_USER = 3
AUTH_ADMIN = 4

AUTH_TYPE = (
    (0, AUTH_ANY, "auth_any"),
    (1, AUTH_GUEST, "auth_guest"),
    (2, AUTH_USER, "auth_user"),
    (3, AUTH_SUPER_USER, "auth_super_user"),
    (4, AUTH_ADMIN, "auth_admin"),
)
