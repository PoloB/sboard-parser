
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
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_02.sboard")
        project = sboardparser.parse(test_path)
        self._test_project(project)

    def test_03(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_03.sboard")
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

        sequence_gen = project.sequences
        self.assertIsInstance(sequence_gen, types.GeneratorType)

        for sq in sequence_gen:
            self.assertIsInstance(sq, sboardparser.parser.SBoardSequence)
            self._test_sequence(sq)

        # Test timeline
        self.assertIsInstance(project.timeline,
                              sboardparser.parser.SBoardProjectTimeline)
        self._test_timeline(project.timeline)

        self.assertIsInstance(project.frame_rate, float)

    def _test_sequence(self, sequence):

        self.assertIsInstance(sequence.name, str)
        self.assertIsInstance(sequence.project,
                              sboardparser.parser.SBoardProject)

        for scene in sequence.scenes:
            self.assertIsInstance(scene, sboardparser.parser.SBoardScene)
            self._test_scene(scene)

    def _test_scene(self, scene):

        # Test name and id
        self.assertIsInstance(scene.name, str)
        self.assertIsInstance(scene.uid, str)

        # Test frame ranges
        frame_range = scene.frame_range
        self.assertIsInstance(frame_range, tuple)
        self.assertIsInstance(frame_range[0], int)
        self.assertIsInstance(frame_range[1], int)

        cut_range = scene.timeline_range
        self.assertIsInstance(cut_range, tuple)
        self.assertIsInstance(cut_range[0], int)
        self.assertIsInstance(cut_range[1], int)

        # Test length
        self.assertIsInstance(scene.length, int)

        # Test sequence
        self.assertIsInstance(scene.sequence,
                              (type(None), sboardparser.parser.SBoardSequence))

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
            panel_length_sum += p.length

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

        scene_range = panel.scene_range
        self.assertIsInstance(scene_range, tuple)
        self.assertIsInstance(scene_range[0], int)
        self.assertIsInstance(scene_range[1], int)

        timeline_range = panel.timeline_range
        self.assertIsInstance(timeline_range, tuple)
        self.assertIsInstance(timeline_range[0], int)
        self.assertIsInstance(timeline_range[1], int)

    def _test_timeline(self, timeline):

        self.assertIsInstance(timeline.uid, str)
        self.assertIsInstance(timeline.length, int)
        self.assertIsInstance(timeline.scenes, types.GeneratorType)

        scenes = list(timeline.scenes)
        self.assertGreaterEqual(len(scenes), 1)

        # Test scenes from timeline
        current_scene_start = 0

        for s in timeline.scenes:
            self.assertIsInstance(s, sboardparser.parser.SBoardScene)
            self.assertGreaterEqual(s.timeline_range[0], current_scene_start)
            current_scene_start = s.timeline_range[0]

        # Test panels from timeline
        current_panel_start = 0

        for p in timeline.panels:
            self.assertIsInstance(p, sboardparser.parser.SBoardPanel)
            self.assertGreaterEqual(p.timeline_range[0], current_panel_start)
            current_panel_start = p.timeline_range[0]

        self.assertIsInstance(timeline.project, sboardparser.SBoardProject)
