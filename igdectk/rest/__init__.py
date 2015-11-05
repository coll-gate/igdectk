# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
rest sub-package init. Contains common enums.
"""

from enum import Enum


class Method(Enum):

    def __init__(self, code, safe):
        self.code = code
        self.safe = safe

    GET = (0, False)
    POST = (1, True)
    PUT = (2, True)
    DELETE = (3, True)
    PATCH = (4, False)
    OPTIONS = (5, False)
    HEAD = (6, False)


class Format(Enum):

    def __init__(self, code, accept, verbose):
        self.code = code
        self.accept = accept
        self.verbose = verbose

    ANY = (0, '*/*', '*/*')
    TEXT = (1, 'text/plain-text', 'text/plain-text; encoding=utf-8')
    HTML = (2, 'text/html', 'text/html; encoding=utf-8')
    JSON = (3, 'application/json', 'application/json; encoding=utf-8')
    XML = (4, 'application/xml', 'application/xml; encoding=utf-8')
    MULTIPART = (5, 'multipart/form-data', 'multipart/form-data')

    @property
    def content_type(self):
        return self.accept
