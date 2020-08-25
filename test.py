#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""
import os
from unittest import TestCase

from sboardparser import SBoardParser


__author__ = "Paul-Emile Buteau"
__maintainer__ = "Paul-Emile Buteau"
__email__ = "pebuteau@studiohari.com"


SAMPLE_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "test_samples")


class SBoardParserTest(TestCase):

    def test_empty_project(self):

        test_path = os.path.join(SAMPLE_DIRECTORY, "empty_project.sboard")

        p = SBoardParser(test_path)
        p.parse()

    def test_01(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_01.sboard")

        p = SBoardParser(test_path)
        p.parse()

    def test_02(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_01.sboard")

        p = SBoardParser(test_path)
        p.parse()
