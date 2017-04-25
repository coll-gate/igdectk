# -*- coding: utf-8; -*-
#
# @file __init__.py
# @brief xml sub-package init.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-03-10
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details

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
