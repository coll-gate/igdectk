# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Useful Python logger formatter for VT100 compatibles terminals
"""

import logging
import copy
import sys


class ColoredFormatter(logging.Formatter):

    _level_colors = {
        "DEBUG": "\033[22;37m",
        "INFO": "\033[01;32m",
        "WARNING": "\033[22;35m",
        "ERROR": "\033[22;31m",
        "CRITICAL": "\033[01;31m"
    }

    def __init__(self, fmt=None, datefmt=None, style='%'):
        self.apply = True if sys.platform in ["linux", "macosx", "unix"] else False
        super(ColoredFormatter, self).__init__(fmt, datefmt, style)

    def format(self, record):
        if self.apply:
            _record = copy.copy(record)

            if _record.levelname in ColoredFormatter._level_colors:
                _record.levelname = "%s%s\033[0;0m" % (ColoredFormatter._level_colors[record.levelname], record.levelname)
                _record.name = "\033[37m%s\033[0;0m" % record.name
                _record.msg = "\033[32m%s\033[0;0m" % record.msg

            return logging.Formatter.format(self, _record)
        else:
            return logging.Formatter.format(self, record)
