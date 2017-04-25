# -*- coding: utf-8; -*-
#
# @file __init__.py
# @brief module sub-package init.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2016-02-03
# @copyright Copyright (c) 2016 INRA
# @license MIT (see LICENSE file)
# @details

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
