# -*- coding: utf-8; -*-
#
# Copyright (c) 2014 INRA UMR1095 GDEC

"""
Allow to parse Django templates and to find what are the used custom tag and theirs values.
This is especialy used to detect for the packager in way to auto initialize the list of installed
packages and which version even at css templates level.
"""

import os
import re

from django.conf import settings
from django.template import Lexer, Parser

import igdectk.packager.template

from .exception import UnsupportedPackagerConfiguration


VALIDATOR = re.compile(r'^([a-zA-Z0-9-]+)(\.[a-zA-Z0-9-]+){0,1}_([a-zA-Z0-9-]+)(\|[a-zA-Z0-9\-]+){0,1}(#[a-zA-Z0-9-_\.]+){0,1}$')


def compile_string(template_string, origin):
    "Compiles template_string into NodeList ready for rendering"
    if settings.TEMPLATE_DEBUG:
        from django.template.debug import DebugLexer, DebugParser
        lexer_class, parser_class = DebugLexer, DebugParser
    else:
        lexer_class, parser_class = Lexer, Parser
    lexer = lexer_class(template_string, origin)
    parser = parser_class(lexer.tokenize())
    return parser.parse()


def get_apps_list():
    return getattr(settings, 'INSTALLED_APPS', ())


def get_templates_list(application):
    result = []

    app_module = __import__(application, fromlist=['*'])

    app_abspath = app_module.__path__[0]

    tpl_path = os.path.join(app_abspath, 'templates', application.split('.')[-1])

    # found template dir for this app
    if os.path.isdir(tpl_path):
        for f in os.listdir(tpl_path):
            if f.endswith('.html'):
                result.append(os.path.join(tpl_path, f))

    return result


def introspect_node(node, results):
    module = node.__module__.split('.')
    module_name = None

    is_next = False

    for m in module:
        if is_next:
            module_name = m
            break

        if m == 'templatetags':
            is_next = True

    if module_name:
        if module_name not in results:
            results[module_name] = []

        matches = VALIDATOR.match(node.arg.var)

        libname = matches.group(1)
        sublibname = matches.group(2)
        module = matches.group(3)
        theme = matches.group(4)
        # filename = matches.group(5)

        lib = None

        fq_libname = libname if not sublibname else libname + sublibname

        for library in results[module_name]:
            if library[0] == fq_libname:
                lib = library

        # specific version in param
        if node.param:
            version_v = node.param

            if not node.has_version(libname, sublibname, version_v):
                raise UnsupportedPackagerConfiguration("Unsupported specific version %s for %s" % (version_v, fq_libname))
        else:
            version_v = node.get_default_version(libname, sublibname)

        # specific theme
        if theme:
            theme_v = theme.lstrip('|')

            if not node.has_theme(libname, sublibname, theme_v):
                raise UnsupportedPackagerConfiguration("Unsupported specific theme %s for %s" % (theme_v, fq_libname))
        else:
            theme_v = node.get_default_theme(libname, sublibname)

        if not lib:
            lib = [fq_libname, [], []]
            results[module_name].append(lib)

        if lib:
            if version_v not in lib[1]:
                lib[1].append(version_v,)

            if theme_v and theme_v not in lib[2]:
                lib[2].append(theme_v,)


def get_installed_packages():
    """
    Automatically create the list of installed packages, library and sub-library used
    for default or specific versions and themes.
    """
    apps = get_apps_list()
    templates = []
    results = {}

    for app in apps:
        templates = get_templates_list(app)

        for tpl in templates:
            f = open(tpl, 'rU')
            root = compile_string(f.read(), None)

            for node in root.get_nodes_by_type(igdectk.packager.template.Node):
                introspect_node(node, results)

    return results
