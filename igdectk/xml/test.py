# -*- coding: utf-8; -*-
#
# Copyright (c) 2015 INRA UMR1095 GDEC

"""
xml sub-package unit tests.
"""

import unittest

from .decoder import Decoder
from .encoder import Encoder

xml1 = """
<encspot test="true">
  <file>
   <Name>some filename.mp3</Name>
   <Encoder>Gogo (after 3.0)</Encoder>
   <Bitrate>131</Bitrate>
  </file>
  <file>
   <Name>another filename.mp3</Name>
   <Encoder>iTunes</Encoder>
   <Bitrate>128</Bitrate>
  </file>
</encspot>
"""

xml1_obj = {'encspot': {
    'test': 'true',
    'file': [{
        'Bitrate': '131',
        'Encoder': 'Gogo (after 3.0)',
        'Name': 'some filename.mp3'},
        {'Bitrate': '128', 'Encoder': 'iTunes', 'Name': 'another filename.mp3'}
    ]}
}

xml2 = """
<family name="The Andersson's" size="4">
    <children total-age="62">
      <child name="Tom" sex="male"/>
      <child name="Betty" sex="female">
      <grandchildren>
        <grandchild name="herbert" sex="male"/>
        <grandchild name="lisa" sex="female"/>
      </grandchildren>
      </child>
    </children>
    </family>
"""

xml2_obj = {'family': {'children': {
    'child': [
        {'name': 'Tom', 'sex': 'male'},
        {'name': 'Betty', 'sex': 'female', 'grandchildren': {
            'grandchild': [
                {'name': 'herbert', 'sex': 'male'},
                {'name': 'lisa', 'sex': 'female'}]
        }}],
    'total-age': '62'},
    'name': "The Andersson's",
    'size': '4'}
}


class TestXmlDecoder(unittest.TestCase):

    def test_decoder_xml1(self):
        decoder = Decoder()
        result = decoder.decode(xml1)
        self.assertEqual(result, xml1_obj)

    def test_decoder_xml2(self):
        decoder = Decoder()
        result = decoder.decode(xml2)
        self.assertEqual(result, xml2_obj)

    def test_encoder_xml1(self):
        # the XML element are never in the same order because of dict (into Encoder)
        # we decode the encoded and compare object
        encoder = Encoder()
        decoder = Decoder()
        result = decoder.decode(encoder.encode(xml1_obj))
        self.assertEqual(result, xml1_obj)

    def test_encoder_xml2(self):
        # the XML element are never in the same order because of dict (into Encoder)
        # we decode the encoded and compare object
        encoder = Encoder()
        decoder = Decoder()
        result = decoder.decode(encoder.encode(xml2_obj))
        self.assertEqual(result, xml2_obj)

if __name__ == '__main__':
    unittest.main()
