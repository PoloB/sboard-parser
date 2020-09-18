
"""
"""

import os
from unittest import TestCase

from sboardparser import parse


SAMPLE_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "samples")


class SBoardParserTest(TestCase):

    def test_empty_project(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "empty_project.sboard")
        parse(test_path)

    def test_01(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_01.sboard")
        parse(test_path)

    def test_02(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_01.sboard")
        parse(test_path)
