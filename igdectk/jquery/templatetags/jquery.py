# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
JQuery Django integrator with template tag.
"""

from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateSyntaxError, Variable, Library
from django.contrib.staticfiles.templatetags.staticfiles import static

from igdectk.common import evaluator
from igdectk.packager.template import Node

from .. import appsettings

register = Library()


@register.tag
def jquery(parser, token):
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

    DEFAULT_JQUERY_VERSION = '2.1.4'
    DEFAULT_JQUERY_UI_VERSION = '1.10.4'
    DEFAULT_FANCYTREE_VERSION = '2.12.0'  # ISSUE with 2.13.0 and glyph+bootstrap theme
    DEFAULT_SELECT2_VERSION = '3.5.1'
    DEFAULT_COLPICK_VERSION = '1.0.0'
    DEFAULT_NUMERIC_VERSION = '1.4.1'

    PROPERTIES = {
        'jquery': {'js': 'jquery.min.js', 'css': '', 'default_version': '2.1.4', 'versions': ('2.1.4',)},
        'ui': {'js': 'jquery-ui.min.js', 'css': 'ui-%(theme)s/jquery-ui.min.css', 'img': '%(filename)s', 'default_version': '1.10.4', 'versions': ('1.10.4',), 'default_theme': 'lightness', 'themes': ('lightness',)},
        'fancytree': {
            'js': 'jquery.fancytree.min.js', 'css': 'skin-%(theme)s/ui.fancytree.min.css', 'default_version': '2.12.0', 'versions': ('2.12.0',), 'default_theme': 'bootstrap', 'themes': ('bootstrap',),
            '.glyph': {'js': 'jquery.fancytree.glyph.min.js', 'css': '', 'default_version': '2.12.0', 'versions': ('2.12.0',), 'default_theme': ''}
        },
        'select2': {'js': 'select2.min.js', 'css': 'select2.css', 'default_version': '3.5.1', 'versions': ('3.5.1',)},
        'colpick': {'js': 'colpick.js', 'css': 'colpick.css', 'default_version': '1.0.0', 'versions': ('1.0.0',)},
        'numeric': {'js': 'jquery.numeric.js', 'css': '', 'default_version': '1.4.1', 'versions': ('1.4.1',)}
    }

    CACHE = {}

    def get_default_version(self, libname, sublibname=None):
        library = TemplateAppValue.PROPERTIES.get(libname)
        if not library:
            raise ImproperlyConfigured('Missing library')

        # sublib
        if sublibname:
            library = library.get(sublibname)

        if not library:
            raise ImproperlyConfigured('Missing sub-library')

        default = library.get('default_version')

        if default:
            return default

        raise ImproperlyConfigured('Missing default_version')

    def get_default_theme(self, libname, sublibname=None):
        library = TemplateAppValue.PROPERTIES.get(libname)
        if not library:
            raise ImproperlyConfigured('Missing library')

        # sublib
        if sublibname:
            library = library.get(sublibname)

        if not library:
            raise ImproperlyConfigured('Missing sub-library')

        return library.get('default_theme', None)

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
                result += self.wrap(module, 'jquery/%s/%s/%s/%s' % (module, libname, version, rc))
        else:
            rc = resources % {'theme': (theme[1:] if theme else prop.get('default_theme', '')), 'filename': (filename[1:] if filename else '')}
            result = self.wrap(module, 'jquery/%s/%s/%s/%s' % (module, libname, version, rc))

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
