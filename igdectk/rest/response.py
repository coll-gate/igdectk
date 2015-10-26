# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
    Usefull common responses.
"""

import json
import igdectk.xml

from datetime import date, datetime

from django.core import serializers
from django.http import HttpResponse
from django.db.models.query import QuerySet
from django.db.models import Model

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"


class ComplexEncoder(json.JSONEncoder):

    """
    Support standard json dumps plus serializers for django
    query set and model object.
    """

    def default(self, obj):
        if isinstance(obj, QuerySet):
            return serializers.serialize("python", obj)
        elif isinstance(obj, Model):
            return serializers.serialize('python', [obj])[0]
        elif isinstance(obj, date):
            return str(obj)
        elif isinstance(obj, datetime):
            return str(obj)
        else:
            # Let the base class default method raise the TypeError
            return json.JSONEncoder.default(self, obj)


def HttpResponseRest(request, data):
    """
    Return an Http response into the correct output format (JSON, XML or HTML),
    according of the request.format parameters.

    Format is automaticaly added when using the
    :class:`igdectk.rest.restmiddleware.IGdecTkRestMiddleware` and views decorators.
    """
    if request.format == 'JSON':
        jsondata = json.dumps(data, cls=ComplexEncoder)
        return HttpResponse(jsondata, content_type="application/json")
    elif request.format == 'HTML':
        return HttpResponse(data)
    elif request.format == 'XML':
        xmldata = igdectk.xml.dumps(data)
        return HttpResponse(xmldata)
