# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Helper for enum choice to uses for a database field.
"""

from enum import Enum


class IntegerChoice(int):

    def __new__(cls, value, label=""):
        instance = super(IntegerChoice, cls).__new__(cls, value)
        instance._label = label

        return instance

    @property
    def value(self):
        return self

    @property
    def label(self):
        return self._label

    @property
    def pair(self):
        return self, self._label


class StringChoice(str):

    def __new__(cls, value, label):
        instance = super(StringChoice, cls).__new__(cls, value)
        instance._label = label

        return instance

    @property
    def value(self):
        return self

    @property
    def label(self):
        return self._label

    @property
    def pair(self):
        return self, self._label


class ChoiceEnum(Enum):

    @classmethod
    def choices(cls):
        choices = list()

        # Loop thru defined enums
        for item in cls:
            choices.append(item.value.pair)

        # return as tuple
        return tuple(choices)

    def __str__(self):
        return self.name

    def __int__(self):
        return self.value

    @property
    def label(self):
        return self.value.label
