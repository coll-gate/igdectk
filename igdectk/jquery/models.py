# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
JQuery common models
"""

from django.db import models


class Settings(models.Model):
    param_name = models.CharField(max_length=127)
    value = models.CharField(max_length=1024)
