# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
    Simplest XML encoder.
"""

from datetime import date, datetime

from django.core import serializers
from django.db.models.query import QuerySet
from django.db.models import Model


class Encoder():

    """
    Simplest XML encoder.

    TODO improve it
    """

    def __init__(self):
        self.data = ""  # where we store the processed XML string

    def encode(self, obj, name=None):
        """
        processes Python data structure into XML string
        needs name if obj is a List
        """
        if obj is None:
            return ""

        if isinstance(obj, dict):
            self.data = self._PyDict2XML(obj)
        elif isinstance(obj, list):
            # we need name for List object
            self.data = self._PyList2XML(obj, name)
        elif isinstance(obj, QuerySet):
            pass
        elif isinstance(obj, Model):
            self.data = serializers.serialize('python', [obj])[0]
        elif isinstance(obj, date):
            self.data = str(obj)
        elif isinstance(obj, datetime):
            self.data = str(obj)
        else:
            self.data = "<%(n)s>%(o)s</%(n)s>" % {'n': name, 'o': str(obj)}

        return self.data

    def _PyDict2XML(self, obj, name=None):
        '''
        process Python Dict objects
        They can store XML attributes and/or children
        '''
        tagStr = ""      # XML string for this level
        attributes = {}  # attribute key/value pairs
        attr_str = ""    # attribute string of this level
        child_str = ""   # XML string of this level's children

        for k, v in obj.items():

            if isinstance(v, dict):
                # child tags, with attributes
                child_str += self._PyDict2XML(v, k)

            elif isinstance(v, list):
                # child tags, list of children
                child_str += self._PyList2XML(v, k)

            else:
                # tag could have many attributes, let's save until later
                attributes.update({k: v})

        if name is None:
            return child_str

        # create XML string for attributes
        for k, v in attributes.items():
            attr_str += " %s=\"%s\"" % (k, v)

        # let's assemble our tag string
        if child_str == "":
            tagStr += "<%(n)s%(a)s />" % {'n': name, 'a': attr_str}
        else:
            tagStr += "<%(n)s%(a)s>%(c)s</%(n)s>" % {'n': name, 'a': attr_str, 'c': child_str}

        return tagStr

    def _PyList2XML(self, obj, name=None):
        """
        process Python List objects
        They have no attributes, just children
        Lists only hold Dicts or Strings
        """
        tagStr = ""    # XML string for this level
        child_str = ""  # XML string of children

        for child_obj in obj:
            if isinstance(child_obj, dict):
                # here's some Magic
                # we're assuming that List parent has a plural name of child:
                # eg, persons > person, so cut off last char
                # name-wise, only really works for one level, however
                # in practice, this is probably ok
                child_str += self._PyDict2XML(child_obj, name[:-1])
            else:
                if isinstance(child_obj, list):
                    for string in child_obj:
                        child_str += string
                else:
                    child_str += str(child_obj) + ' '

        child_str = child_str.rstrip()

        if name is None:
            return child_str

        tagStr += "<%(n)s>%(c)s</%(n)s>" % {'n': name, 'c': child_str}

        return tagStr
