# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Usefull common responses.
"""

import json

from datetime import date, datetime

from django.core import serializers
from django.http import HttpResponse
from django.db.models.query import QuerySet
from django.db import models

import decimal
import igdectk.xmlio

from igdectk.rest import Format

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
        elif isinstance(obj, models.Model):
            return serializers.serialize('python', [obj])[0]
        elif isinstance(obj, date):
            return str(obj)
        elif isinstance(obj, datetime):
            return str(obj)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)  # TODO as str or as float because of the double precision ?
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
    if request.format == Format.JSON:
        encoded = json.dumps(data, cls=ComplexEncoder)
        return HttpResponse(encoded, content_type=Format.JSON.content_type)
    elif request.format == Format.HTML:
        return HttpResponse(data)
    elif request.format == Format.XML:
        encoded = igdectk.xmlio.dumps(data)
        return HttpResponse(encoded, content_type=Format.XML.content_type)
    elif request.format == Format.TEXT:
        return HttpResponse(data, content_type=Format.TEXT.content_type)
    else:
        return None
