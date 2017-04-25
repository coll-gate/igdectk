# -*- coding: utf-8; -*-
#
# @file decoder.py
# @brief Simplest XML decoder.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2015-03-10
# @copyright Copyright (c) 2015 INRA
# @license MIT (see LICENSE file)
# @details

import xml.etree.cElementTree as etree


class Decoder:

    """
    Simplest XML to object decoder.
    """

    def __init__(self):
        self.obj = {}  # the processed object

    def decode(self, data):
        """
        processes XML data structure into Python object
        """
        tree = etree.fromstring(data)

        self.obj = {tree.tag: self._node(tree)}
        return self.obj

    def _node(self, node):
        content = {}

        # attributes
        for item in node.items():
            content[item[0]] = item[1]

        done = set()

        # children
        for child in node.getchildren():
            siblings = node.findall(child.tag)

            if len(siblings) > 1:
                done.add(child.tag)
                elts = []

                for s in siblings:
                    elts.append(self._node(s))

                content[child.tag] = elts
            elif child.tag not in done:
                content[child.tag] = self._node(child)

        if not node.getchildren() and node.text:
            content = node.text

        return content
