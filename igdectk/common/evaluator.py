# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
Python expression safe evaluator, supporting basic mathematics and
booleans operators.
"""

import ast
import operator as op

__date__ = "2015-04-13"
__author__ = "Frédéric Scherma"


# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}


def _eval(node_or_string):
    # if isinstance(node, ast.Num):  # <number>
    #     return node.n
    # elif isinstance(node, ast.Str):  # <string>
    #     return node.s
    # elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
    #     return operators[type(node.op)](_eval(node.left), _eval(node.right))
    # elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
    #     return operators[type(node.op)](_eval(node.operand))
    # else:
    #     raise TypeError(node)
    if isinstance(node_or_string, str):
        node_or_string = ast.parse(node_or_string, mode='eval')
    if isinstance(node_or_string, ast.Expression):
        node_or_string = node_or_string.body

    def _convert(node):
        if isinstance(node, (ast.Str, ast.Bytes)):
            return node.s
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Tuple):
            return tuple(map(_convert, node.elts))
        elif isinstance(node, ast.List):
            return list(map(_convert, node.elts))
        elif isinstance(node, ast.Set):
            return set(map(_convert, node.elts))
        elif isinstance(node, ast.Dict):
            return dict((_convert(k), _convert(v)) for k, v
                        in zip(node.keys, node.values))
        elif isinstance(node, ast.NameConstant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](_eval(node.operand))
        else:
            raise TypeError(node)
    return _convert(node_or_string)


def eval_expr(expr):
    """
    Evaluate a Python expression safely. Support unaries and binaries
    operators, string, numeric, tuple, list, dict, set.

    Parameters
    ----------
    expr: string
        Literal expression to Evaluate

    Raises
    ------
    TypeError:
        If a type of the expression is not supported or the expression
        contains an error.

    Returns
    -------
    :any
        According to the expression, return an object of its type.
    """
    return _eval(ast.parse(expr, mode='eval').body)
