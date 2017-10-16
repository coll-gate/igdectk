# -*- coding: utf-8; -*-
#
# @file customglyph.py
# @brief Compatibility with others glyphs enums.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2017-10-16
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details


class CustomGlyph(object):

    def __init__(self, prefix, name, opts=None):
        self._prefix = prefix
        self._name = name
        self._opts = opts

    @property
    def value(self):
        if type(self._name) is tuple or type(self._name) is list:
            return " ".join("%s-%s" % (self._prefix, self._name))
        else:
            return "%s-%s" % (self._prefix, self._name)

    @property
    def opts(self):
        if self._opts is None:
            return

        if type(self._opts) is tuple or type(self._opts) is list:
            return " ".join("%s-%s" % (self._prefix, self._opts))
        else:
            return "%s-%s" % (self._prefix, self._opts)

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class FaGlyph(CustomGlyph):
    """
    Font awesome glyphicons.
    Helper to add glyphicons from font awesome into the menu.
    @todo Stacked icons doesn't looks good in menu because of an additional useless left offset.
    @todo Stocked icons options need more complexes compositions. How to ?
    """

    FA_FW = "fa-fw"
    FA_LG = "fa-lg"
    FA_2X = "fa-2x"
    FA_3X = "fa-3x"
    FA_4X = "fa-4x"
    FA_5X = "fa-5x"

    def __init__(self, name, stack=False, rotate=False, pulse=False, opts=None):
        super().__init__('fa', name, opts=opts)

        self._stack = stack
        self._rotate = rotate
        self._pulse = pulse

    @property
    def html(self):
        if self._stack:
            if self._opts:
                classes = 'fa-stack ' + self.opts
            else:
                classes = 'fa-stack'

            result = '<span class="%s">' % classes

            if type(self._name) is tuple or type(self._name) is list:
                for i in self._name:
                    result += '<i class="fa fa-%s fa-stack-1x"></i>' % i
            else:
                result += '<i class="fa fa-%s fa-stack-1x"></i>' % self._name

            result += '</span>'
            return result
        else:
            lopts = ""

            if self._rotate:
                lopts = 'fa-spin'
            elif self._pulse:
                lopts = 'fa-pulse'

            if self._opts:
                lopts += self.opts

            if lopts:
                return '<i class="fa %s %s"></i>' % (self.value, lopts)
            else:
                return '<i class="fa %s"></i>' % self.value
