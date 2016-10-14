# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Simplest XML encoder.
"""

import decimal
import uuid

from datetime import date, datetime

from django.core import serializers
from django.db.models.query import QuerySet
from django.utils import six
from django.db.models import Model
from django.utils.functional import Promise


class Encoder(object):

    """
    Simplest XML to object encoder.
    # TODO encoding/detection for unsupported characters into nodes and attributes names
    """

    def __init__(self):
        self.data = ""  # where we store the processed XML string

    def _Value2Xml(self, name, obj):
        if isinstance(obj, QuerySet):
            result = serializers.serialize('xml', obj)
        elif isinstance(obj, Model):
            result = serializers.serialize('xml', [obj])[0]
        elif isinstance(obj, date):
            result = obj.isoformat()
        elif isinstance(obj, datetime):
            result = obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            result = str(obj)
        elif isinstance(obj, Promise):
            result = six.text_type(obj)
        elif isinstance(obj, uuid.UUID):
            result = str(obj)
        elif hasattr(obj, "__dict__"):
            result = str(obj.__dict__)
        else:
            result = str(obj)

        return "<%(n)s>%(r)s</%(n)s>" % {'n': name, 'r': result}

    def _List2Xml(self, name, obj):
        result = ""

        for value in obj:
            if isinstance(value, dict):
                result += self._Dict2Xml(name, value)
            elif isinstance(value, list) or isinstance(value, tuple):
                result += self._List2Xml(name, value)
            else:
                result += self._Value2Xml(name, value)

        return result

    def _Dict2Xml(self, name, obj):
        """
        processes Python data structure into XML string
        needs name if obj is a List
        """
        result = ""
        attrs = ""
        simple = True

        for key, value in obj.items():
            if isinstance(value, dict):
                simple = False
                result += self._Dict2Xml(key, value)
            elif isinstance(value, list) or isinstance(value, tuple):
                simple = False
                result += self._List2Xml(key, value)
            elif isinstance(value, str) or isinstance(value, int) or isinstance(value, float):
                attrs += ' %s="%s"' % (key, str(value))
            else:
                simple = False
                result += self._Value2Xml(key, value)

        if name:
            if simple:
                return "<%s%s/>" % (name, attrs)
            else:
                return "<%s%s>%s</%s>" % (name, attrs, result, name)

        return result

    def encode(self, obj, root_node=None):
        if isinstance(obj, dict):
            self.data = self._Dict2Xml(None, obj)
        else:
            raise ValueError("Root object must be a dict")

        return self.data
