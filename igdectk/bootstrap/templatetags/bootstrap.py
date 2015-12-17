# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Boostrap Django integrator with template tag.
"""

import re

from django.template import TemplateSyntaxError, Variable, Node, Library
from django.contrib.staticfiles.templatetags.staticfiles import static

from igdectk.common import evaluator

from .. import appsettings

register = Library()


@register.tag
def bootstrap(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one "
                                  "argument (settings constant to retrieve)" % bits[0])
    settingsvar = bits[1]
    settingsvar = settingsvar[1:-1] if settingsvar[0] == '"' else settingsvar
    param = ""
    asvar = None
    bits = bits[2:]

    if settingsvar.count('=') == 1:
        with_param = settingsvar.split('=')
        settingsvar = with_param[0]
        param = evaluator.eval_expr(with_param[1])

    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        raise TemplateSyntaxError("'%s' didn't recognise "
                                  "the arguments '%s'" % (__name__, ", ".join(bits)))

    return TemplateAppValue(settingsvar, param, asvar)


class TemplateAppValue(Node):

    VALIDATOR = re.compile(r'^([a-zA-Z0-9-]+)(\.[a-zA-Z0-9-]+){0,1}_([a-zA-Z0-9-]+)(\|[a-zA-Z0-9\-]+){0,1}(#[a-zA-Z0-9-_\.]+){0,1}$')

    PROPERTIES = {
        'bootstrap': {'js': 'bootstrap.min.js', 'css': ('bootstrap.min.css', 'bootstrap-theme.min.css'), 'default_version': '3.3.6', 'versions': ('3.3.6',)},
        'contextmenu': {'js': 'bootstrap-contextmenu.js', 'css': '', 'default_version': '0.2.0', 'versions': ('0.2.0',)},
    }

    CACHE = {}

    def wrap(self, module, content):
        if module == 'js':
            return '<script src="%s"></script>' % static(content)
        elif module == 'css':
            return '<link rel="stylesheet" href="%s" />' % static(content)
        else:
            return static(content)

    def get_property(self, args, param):
        # try with cache...
        cache = TemplateAppValue.CACHE.get(args + '=' + param)
        if cache:
            return cache

        # cache miss, generates the string
        matches = TemplateAppValue.VALIDATOR.match(args)

        if not matches:
            raise TemplateSyntaxError("invalid resource format for '%s'" % args)

        libname = matches.group(1)
        sublibname = matches.group(2)
        module = matches.group(3)
        theme = matches.group(4)
        filename = matches.group(5)

        if not libname:
            raise TemplateSyntaxError("missing library name for '%s'" % args)

        if not module:
            raise TemplateSyntaxError("missing module name for '%s'" % args)

        prop = TemplateAppValue.PROPERTIES.get(libname)
        if not prop:
            raise TemplateSyntaxError("undefined library '%s' for '%s'" % (libname, args))

        if sublibname:
            prop = prop.get(sublibname)
            if not prop:
                raise TemplateSyntaxError("undefined sub-library '%s' for '%s'" % (sublibname, args))

        default_version = prop.get('default_version')
        if not default_version:
            raise TemplateSyntaxError("undefined default version for '%s'" % args)

        version = param if param else default_version

        if version and version not in prop.get('versions', ''):
            raise TemplateSyntaxError("undefined version '%s' for '%s'" % (version, args))

        resources = prop.get(module)
        if not resources:
            raise TemplateSyntaxError("undefined module '%s' for '%s'" % (module, args))

        if theme and theme[1:] not in prop.get('themes', ''):
            raise TemplateSyntaxError("undefined theme '%s' for '%s'" % (theme[1:], args))

        result = ''

        if isinstance(resources, tuple):
            for resource in resources:
                rc = resource % {'theme': (theme[1:] if theme else prop.get('default_theme', '')), 'filename': (filename[1:] if filename else '')}
                result += self.wrap(module, 'bootstrap/%s/%s/%s/%s' % (module, libname, version, rc))
        else:
            rc = resources % {'theme': (theme[1:] if theme else prop.get('default_theme', '')), 'filename': (filename[1:] if filename else '')}
            result = self.wrap(module, 'bootstrap/%s/%s/%s/%s' % (module, libname, version, rc))

        # store in cache
        TemplateAppValue.CACHE[args + '=' + param] = result

        return result

    def __init__(self, settingsvar, param, asvar):
        self.arg = Variable(settingsvar)
        self.param = param
        self.asvar = asvar

    def render(self, context):
        args = str(self.arg)

        # lookup into PROPERTIES with a parameter (general version string number)
        if args == 'version':
            ret_val = '.'.join([str(x) for x in appsettings.APP_VERSION])
        else:
            ret_val = self.get_property(args, self.param)

        if not ret_val:
            # lookup for appsettings
            ret_val = getattr(appsettings, args, "")

        if self.asvar:
            context[self.asvar] = ret_val
            return ''
        else:
            return ret_val
