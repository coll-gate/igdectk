# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
xml sub-package init.
"""

from .encoder import Encoder
from .decoder import Decoder


def dumps(obj):
    """
    Helper to dumps a Python object to an XML string.
    """
    return Encoder().encode(obj)


def loads(data):
    """
    Helper to loads an XML string into a Python object.
    """
    return Decoder().decode(data)
