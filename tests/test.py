
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

    def test_04(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test_04.sboard")
        project = sboardparser.parse(test_path)
        self._test_project(project)

    def test_sequence(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "sequence.sboard")
        project = sboardparser.parse(test_path)
        self._test_project(project)

    def test_3d(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "test3d.sboard")
        project = sboardparser.parse(test_path)
        self._test_project(project)

    def test_track(self):
        test_path = os.path.join(SAMPLE_DIRECTORY, "track.sboard")
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
                              sboardparser.parser.SBoardTimeline)
        self._test_timeline(project.timeline)

        # Test library
        library = project.library
        self.assertIsInstance(library, sboardparser.parser.SBoardLibrary)
        self._test_library(library)

        self.assertIsInstance(project.frame_rate, float)
        self.assertIsInstance(project.title, str)

    def _test_library(self, library):

        # Test categories
        cat_gen = library.categories
        self.assertIsInstance(cat_gen, types.GeneratorType)
        self.assertIsInstance(library.project,
                              sboardparser.parser.SBoardProject)

        element_gen = library.elements
        self.assertIsInstance(element_gen, types.GeneratorType)

        for element in element_gen:
            self.assertIsInstance(element,
                                  sboardparser.parser.SBoardLibraryElement)
            self._test_element(element)

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
        frame_range = scene.clip_range
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
        self.assertIsInstance(panel.number, int)
        self.assertIsInstance(panel.uid, str)

        # Test scene
        self.assertIsInstance(panel.scene, sboardparser.parser.SBoardScene)

        # Test project
        self.assertIsInstance(panel.project, sboardparser.parser.SBoardProject)

        # Test frame range
        frame_range = panel.clip_range
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

        # Test layers without groups
        layers_gen = panel.layer_iter()
        self.assertIsInstance(layers_gen, types.GeneratorType)

        for layer in layers_gen:
            self.assertIsInstance(layer, sboardparser.parser.SBoardLayer)
            self.assertFalse(layer.is_group())
            self._test_layer(layer)

        # Test all layers iter
        for layer in panel.layer_iter(groups=True, recursive=True):
            self.assertIsInstance(layer, sboardparser.parser.SBoardLayer)

            if not layer.is_group():
                self._test_layer_leaf(layer)

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

        v_tracks = timeline.video_tracks
        self.assertIsInstance(v_tracks, types.GeneratorType)

        for track in v_tracks:
            self.assertIsInstance(track, sboardparser.parser.SBoardVideoTrack)
            self._test_video_track(track)

        a_tracks = timeline.audio_tracks
        self.assertIsInstance(a_tracks, types.GeneratorType)

        for track in a_tracks:
            self.assertIsInstance(track, sboardparser.parser.SBoardAudioTrack)
            self._test_audio_track(track)

        for transition in timeline.transitions:
            self.assertIsInstance(transition, sboardparser.parser.SBoardTransition)
            self.assertEqual(transition.timeline, timeline)
            self._test_transition(transition)

        self.assertIsInstance(timeline.project, sboardparser.SBoardProject)

    def _test_video_track(self, track):
        self.assertIsInstance(track.uid, str)
        self.assertIsInstance(track.name, str)
        self.assertIsInstance(track.timeline,
                              sboardparser.parser.SBoardTimeline)
        self.assertIsInstance(track.is_enabled(), bool)
        clips = track.clips
        self.assertIsInstance(clips, types.GeneratorType)

        for clip in clips:
            self.assertIsInstance(clip, sboardparser.parser.SBoardVideoClip)
            self._test_video_clip(clip)

    def _test_audio_track(self, track):
        self.assertIsInstance(track.name, str)
        self.assertIsInstance(track.timeline,
                              sboardparser.parser.SBoardTimeline)
        self.assertIsInstance(track.is_enabled(), bool)
        clips = track.clips
        self.assertIsInstance(clips, types.GeneratorType)

        for clip in clips:
            self.assertIsInstance(clip, sboardparser.parser.SBoardAudioClip)
            self._test_audio_clip(clip)

    def _test_video_clip(self, clip):
        self.assertIsInstance(clip.uid, str)
        self.assertIsInstance(clip.timeline_range, tuple)
        self.assertIsInstance(clip.clip_range, tuple)
        self.assertIsInstance(clip.length, int)
        self.assertIsInstance(clip.path, str)
        self.assertIsInstance(clip.element,
                              sboardparser.parser.SBoardLibraryElement)
        self.assertIsInstance(clip.track,
                              sboardparser.parser.SBoardVideoTrack)

    def _test_audio_clip(self, clip):
        self.assertIsInstance(clip.file_name, str)
        self.assertIsInstance(clip.timeline_range, tuple)
        self.assertIsInstance(clip.clip_range, tuple)
        self.assertIsInstance(clip.length, int)
        self.assertIsInstance(clip.path, str)
        self.assertIsInstance(clip.track,
                              sboardparser.parser.SBoardAudioTrack)

    def _test_element(self, element):

        self.assertIsInstance(element.category,
                              sboardparser.parser.SBoardLibraryCategory)
        self.assertIsInstance(element.name, str)
        self.assertIsInstance(element.path, str)

    def _test_layer(self, layer):

        self.assertIsInstance(layer.name, str)
        self.assertIsInstance(layer.panel, sboardparser.parser.SBoardPanel)

        element = layer.element
        self.assertIsInstance(element,
                              (sboardparser.parser.SBoardLibraryElement,
                               type(None)))

        if element:
            self._test_element(element)

    def _test_layer_leaf(self, layer):

        self.assertEqual(0, len(list(layer.layer_iter())))

    def _test_transition(self, transition):
        self.assertIsInstance(transition.uid, str)
        self.assertIsInstance(transition.timeline_range, tuple)
        self.assertIsInstance(transition.type, str)


class SBoardTrackTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(SBoardTrackTest, self).__init__(*args, **kwargs)
        test_path = os.path.join(SAMPLE_DIRECTORY, "track.sboard")
        self.project = sboardparser.parse(test_path)

    def test_tracks(self):

        timeline = self.project.timeline

        audio_tracks = list(timeline.audio_tracks)
        video_tracks = list(timeline.video_tracks)

        # Check audio tracks
        self.assertEqual(2, len(audio_tracks))
        self.assertEqual("AudioTrack2", audio_tracks[0].name)
        self.assertEqual("AudioTrack1", audio_tracks[1].name)
        audio_clips1 = list(audio_tracks[0].clips)
        self.assertEqual(0, len(audio_clips1))
        audio_clips2 = list(audio_tracks[1].clips)
        self.assertEqual(2, len(audio_clips2))
        audio_clip21 = audio_clips2[0]
        audio_clip22 = audio_clips2[1]
        self.assertEqual("file_example_MP3_700KB.mp3",
                         audio_clip21.file_name)
        self.assertEqual((4.2083334922790527, 27.287981033325195),
                         audio_clip21.clip_range)
        self.assertEqual((146, 699), audio_clip21.timeline_range)
        self.assertEqual("file_example_MP3_700KB.mp3",
                         audio_clip22.file_name)
        self.assertEqual((0, 27.287981033325195),
                         audio_clip22.clip_range)
        self.assertEqual((775, 1429), audio_clip22.timeline_range)

        self.assertEqual(2, len(video_tracks))
        video_track = video_tracks[0]
        self.assertEqual("VideoTrack1", video_track.name)
        self.assertEqual("ATV-0A5A672AA5C01754", video_track.uid)
        video_clips = list(video_track.clips)
        self.assertEqual(5, len(video_clips))
        video_clip1 = video_clips[0]
        video_clip2 = video_clips[1]
        video_clip3 = video_clips[2]
        self.assertEqual("0a5a672aa5c0189f", video_clip1.uid)
        self.assertEqual("0a5a672aa5c04668", video_clip2.uid)
        self.assertEqual("0a5a672aa5c03a09", video_clip3.uid)
        self.assertEqual(1045, video_clip1.length)
        self.assertEqual(24, video_clip2.length)
        self.assertEqual(1045, video_clip3.length)
        self.assertEqual((1, 1045), video_clip1.timeline_range)
        self.assertEqual((1046, 1069), video_clip2.timeline_range)
        self.assertEqual((1203, 1491), video_clip3.timeline_range)
        self.assertEqual((1, 1045), video_clip1.clip_range)
        self.assertEqual((1, 24), video_clip2.clip_range)
        self.assertEqual((757, 1045), video_clip3.clip_range)
        element_video_clip1 = video_clip1.element
        element_video_clip2 = video_clip2.element
        element_video_clip3 = video_clip3.element
        self.assertEqual("2", element_video_clip1.category.uid)
        self.assertEqual("3", element_video_clip2.category.uid)
        self.assertEqual("2", element_video_clip3.category.uid)
        self.assertEqual("mp4", element_video_clip1.category.name)
        self.assertEqual("Shared", element_video_clip2.category.name)
        self.assertEqual("mp4", element_video_clip3.category.name)
