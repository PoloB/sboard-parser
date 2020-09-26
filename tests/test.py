
"""
"""

import types

import os
from unittest import TestCase

import sboardparser


SAMPLE_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "samples")


class SBoardParserTest(TestCase):

    def test_empty_project(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "empty_project.sboard")
        project = sboardparser.parse(test_path)
        self._test_project(project)

    def test_01(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_01.sboard")
        project = sboardparser.parse(test_path)
        self._test_project(project)

    def test_02(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_01.sboard")
        project = sboardparser.parse(test_path)
        self._test_project(project)

    def _test_project(self, project):

        # Try to get the scenes from project
        scenes_gen = project.scenes
        self.assertIsInstance(scenes_gen, types.GeneratorType)

        for s in scenes_gen:
            self.assertIsInstance(s, sboardparser.parser.SBoardScene)

            # Test scene
            self._test_scene(s)

    def _test_scene(self, scene):

        # Test name and id
        self.assertIsInstance(scene.name, str)
        self.assertIsInstance(scene.uid, str)

        # Test frame ranges
        frame_range = scene.frame_range
        self.assertIsInstance(frame_range, tuple)
        self.assertIsInstance(frame_range[0], int)
        self.assertIsInstance(frame_range[1], int)

        cut_range = scene.cut_range
        self.assertIsInstance(cut_range, tuple)
        self.assertIsInstance(cut_range[0], int)
        self.assertIsInstance(cut_range[1], int)

        # Test length
        self.assertIsInstance(scene.length, int)

        # Test panels
        panels_gen = scene.panels
        self.assertIsInstance(panels_gen, types.GeneratorType)

        panel_length_sum = 0

        for p in panels_gen:
            self.assertIsInstance(p, sboardparser.parser.SBoardPanel)
            self._test_panel(p)

            # Test scene equality
            self.assertEqual(p.scene, scene)

            # Test range length
            panel_range = p.cut_range
            panel_length_sum += panel_range[1] - panel_range[0] + 1

        self.assertEqual(panel_length_sum, scene.length)

    def _test_panel(self, panel):

        # Test name and id
        self.assertIsInstance(panel.name, str)
        self.assertIsInstance(panel.uid, str)

        # Test scene
        self.assertIsInstance(panel.scene, sboardparser.parser.SBoardScene)

        # Test frame range
        frame_range = panel.frame_range
        self.assertIsInstance(frame_range, tuple)
        self.assertIsInstance(frame_range[0], int)
        self.assertIsInstance(frame_range[1], int)

        cut_range = panel.cut_range
        self.assertIsInstance(cut_range, tuple)
        self.assertIsInstance(cut_range[0], int)
        self.assertIsInstance(cut_range[1], int)
