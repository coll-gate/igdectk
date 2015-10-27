# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
    Simplest XML encoder.
"""

from .encoder import Encoder


def dumps(obj):
    return Encoder().encode(obj)


def loads(data):
    raise Exception("Undefined loads...")
