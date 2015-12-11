# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
JQuery Django integrator with template tag.
"""

from django.template import TemplateSyntaxError, Variable, Node, Library
from django.contrib.staticfiles.templatetags.staticfiles import static

from igdectk.common import evaluator

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
        "version": lambda p: '.'.join([str(x) for x in appsettings.APP_VERSION]),
        "jquery_js": lambda p: "<script src='%s'></script>" % static(
            'jquery/js/jquery/%s/jquery.min.js' % (p if p else TemplateAppValue.DEFAULT_JQUERY_VERSION)),
        "jquery_version": lambda p: TemplateAppValue.DEFAULT_JQUERY_VERSION,  # default version

        "ui_js": lambda p: "<script src='%s'></script>" % static(
            'jquery/js/jquery-ui/%s/jquery-ui.min.js' % (p if p else TemplateAppValue.DEFAULT_JQUERY_UI_VERSION)),
        "ui_css": lambda p: '<link rel="stylesheet" href="%s" />' % static(
            'jquery/css/jquery-ui/%s/ui-lightness/jquery-ui.min.css' % (p if p else TemplateAppValue.DEFAULT_JQUERY_UI_VERSION)),
        "ui_version": lambda p: TemplateAppValue.DEFAULT_JQUERY_UI_VERSION,  # default version
        "ui_anim_basic_16x16": lambda p: '%s' % static(
            'jquery/img/jquery-ui/%s/ui-anim_basic_16x16.gif' % (p if p else TemplateAppValue.DEFAULT_JQUERY_UI_VERSION)),

        "fancytree_js": lambda p: "<script src='%s'></script>" % static(
            'jquery/js/fancytree/%s/jquery.fancytree.min.js' % (p if p else TemplateAppValue.DEFAULT_FANCYTREE_VERSION)),
        "fancytree_version": lambda p: TemplateAppValue.DEFAULT_FANCYTREE_VERSION,  # default version
        "fancytree_css": lambda p: '<link rel="stylesheet" href="%s" />' % static(
            'jquery/css/fancytree/%s/skin-bootstrap/ui.fancytree.min.css' % (p if p else TemplateAppValue.DEFAULT_FANCYTREE_VERSION)),

        "fancytree_glyph_js": lambda p: "<script src='%s'></script>" % static(
            'jquery/js/fancytree/%s/jquery.fancytree.glyph.min.js' % (p if p else TemplateAppValue.DEFAULT_FANCYTREE_VERSION)),

        "select2_js": lambda p: "<script src='%s'></script>" % static(
            'jquery/js/select2/%s/select2.min.js' % (p if p else TemplateAppValue.DEFAULT_SELECT2_VERSION)),
        "select2_version": lambda p: TemplateAppValue.DEFAULT_SELECT2_VERSION,  # default version
        "select2_css": lambda p: '<link rel="stylesheet" href="%s" />' % static(
            'jquery/css/select2/%s/select2.css' % (p if p else TemplateAppValue.DEFAULT_SELECT2_VERSION)),

        "colpick_js": lambda p: "<script src='%s'></script>" % static(
            'jquery/js/colpick/%s/colpick.js' % (p if p else TemplateAppValue.DEFAULT_COLPICK_VERSION)),
        "colpick_version": lambda p: TemplateAppValue.DEFAULT_COLPICK_VERSION,  # default version
        "colpick_css": lambda p: '<link rel="stylesheet" href="%s" />' % static(
            'jquery/css/colpick/%s/colpick.css' % (p if p else TemplateAppValue.DEFAULT_COLPICK_VERSION)),

        "numeric_js": lambda p: "<script src='%s'></script>" % static(
            'jquery/js/numeric/%s/jquery.numeric.js' % (p if p else TemplateAppValue.DEFAULT_NUMERIC_VERSION)),
        "numeric_version": lambda p: TemplateAppValue.DEFAULT_NUMERIC_VERSION,  # default version
    }

    def foo():
        return ""

    def __init__(self, settingsvar, param, asvar):
        self.arg = Variable(settingsvar)
        self.param = param
        self.asvar = asvar

    def render(self, context):
        arg_repr = str(self.arg)

        # lookup into PROPERTIES with a parameter (general version string number)
        ret_val = TemplateAppValue.PROPERTIES.get(arg_repr, TemplateAppValue.foo)(self.param)
        if not ret_val:
            # lookup for appsettings
            ret_val = getattr(appsettings, arg_repr, "")

        if self.asvar:
            context[self.asvar] = ret_val
            return ''
        else:
            return ret_val
