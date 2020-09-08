#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""
import os
from unittest import TestCase

from sboardparser import parse


__author__ = "Paul-Emile Buteau"
__maintainer__ = "Paul-Emile Buteau"
__email__ = "pebuteau@studiohari.com"


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

    def test_additional_properties(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "empty_project.sboard")
        parser = parse(test_path)

        project_root = parser.root

        self.assertIsInstance(project_root.scenes[0].start_frame, int)
        self.assertIsInstance(project_root.scenes[0].end_frame, int)
        self.assertEqual(1, project_root.scenes[0].start_frame)
        print(project_root.scenes[0].end_frame)
