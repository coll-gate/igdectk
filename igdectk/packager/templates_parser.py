# -*- coding: utf-8; -*-
#
# @file template_parser.py
# @brief Base class for packager templage node.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2014-06-03
# @copyright Copyright (c) 2014 INRA
# @license MIT (see LICENSE file)
# @details Allow to parse Django templates and to find what are the used custom tag and theirs values.
# This is especially used to detect for the packager in way to auto initialize the list of installed packages and which
# version even at css templates level.

import os
import re

from importlib import import_module

from django.conf import settings
from django.template.base import Template

import igdectk.packager.template

from .exception import UnsupportedPackagerConfiguration


VALIDATOR = re.compile(r'^([a-zA-Z0-9-]+)(\.[a-zA-Z0-9-]+){0,1}_([a-zA-Z0-9-]+)(\|[a-zA-Z0-9\-]+){0,1}(#[a-zA-Z0-9-_\.]+){0,1}$')


def get_apps_list():
    return getattr(settings, 'INSTALLED_APPS', ())


def get_templates_list(application):
    result = []

    app_module = import_module(application)

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
                break

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

            # was a workaround in way to add the parent library
            # when only sublib are imported. but this is more easily
            # done in finders.py#l75 using a split on the library name
            # if sublibname:
            #     # can need parent lib for sublib and parent not specifically imported
            #     has_parent_lib = False
            #
            #     for library in results[module_name]:
            #         # when sublib and if parent lib is not imported in template
            #         # we have to add load it into the list of results
            #         if sublibname and library[0] == libname:
            #             print(module_name, libname, library)
            #             has_parent_lib = True
            #             break
            #
            #     if not has_parent_lib:
            #         parent_lib = [libname, [version_v], [theme_v]]
            #         results[module_name].append(parent_lib)

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
    results = {}

    for app in apps:
        templates = get_templates_list(app)

        for tpl in templates:
            f = open(tpl, 'rU')

            tpl = Template(f.read())
            root = tpl.compile_nodelist()

            for node in root.get_nodes_by_type(igdectk.packager.template.Node):
                introspect_node(node, results)

    return results
