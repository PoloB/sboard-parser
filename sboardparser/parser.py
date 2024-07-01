"""
Parser for Storyboard Pro .sboard xml file.
The SBoardParser class will let you build a hierarchy of objects from the
given sboard file path.
"""

from __future__ import annotations

import abc
import os
from typing import Iterator
from typing import Optional
from typing import Tuple
from xml.etree import cElementTree


def _get_timeline(
    scene_node: cElementTree.Element,
) -> cElementTree.Element:
    assert scene_node.attrib["name"] != "Top"

    # Shot timeline is described in the column with type=0
    columns = scene_node.find("columns")
    assert columns is not None
    return next(c for c in columns.findall("column") if c.attrib["type"] == "0")


def _get_timeline_range(
    timeline_node: cElementTree.Element, uid: str
) -> Tuple[int, int]:
    warp_seq = next(
        ws for ws in timeline_node.iter("warpSeq") if ws.attrib["id"] == uid
    )

    exposure = warp_seq.attrib["exposures"]
    ex_split = exposure.split("-")

    if len(ex_split) == 1:
        return int(exposure), int(exposure)

    return int(ex_split[0]), int(ex_split[1])


class _SBoardNode:
    """Abstract class for all Story Board Pro objects derived from a given
    xml node of the .sboard file."""

    __metaclass__ = abc.ABCMeta

    def __init__(self, xml_node):
        self.__xml_node = xml_node

    @property
    def xml_node(self) -> cElementTree.Element:
        """Returns the root xml node for this given object."""
        return self.__xml_node


class SBoardAudioClip(_SBoardNode):
    """A Storyboard pro audio clip."""

    def __init__(self, xml_node: cElementTree.Element, track: SBoardAudioTrack):
        # /projects/scenes/scene[@name='Top']/columns/column[@type='1']/soundSequence
        super(SBoardAudioClip, self).__init__(xml_node)
        self.__track = track

    @property
    def file_name(self) -> str:
        """Returns the file name of the media of this clip."""
        return self.xml_node.attrib["name"]

    @property
    def path(self) -> str:
        """Returns the full path of the file used relative to the .sboard file."""
        return "./audio/{}".format(self.file_name)

    @property
    def clip_range(self) -> Tuple[float, float]:
        """Returns the clip range of the audio track in seconds."""
        return float(self.xml_node.attrib["clippingTimeStart"]), float(
            self.xml_node.attrib["clippingTimeStop"]
        )

    @property
    def timeline_range(self) -> Tuple[int, int]:
        """Returns the timeline range of the audio track."""
        return int(self.xml_node.attrib["startFrame"]), int(
            self.xml_node.attrib["stopFrame"]
        )

    @property
    def length(self) -> int:
        """Returns the number of frames of the clip."""
        timeline_range = self.timeline_range
        return timeline_range[1] - timeline_range[0]

    @property
    def track(self) -> SBoardAudioTrack:
        """Returns the track of the clip."""
        return self.__track


class SBoardVideoClip(_SBoardNode):
    """A Storyboard Pro Video Clip."""

    def __init__(self, xml_node: cElementTree.Element, track: SBoardVideoTrack):
        # /project/scenes/scene
        super(SBoardVideoClip, self).__init__(xml_node)
        self.__track = track

    @property
    def track(self) -> SBoardVideoTrack:
        """Returns the track of the clip."""
        return self.__track

    @property
    def uid(self) -> str:
        """Returns the unique identifier of the scene."""
        return self.xml_node.attrib["id"]

    @property
    def timeline_range(self) -> Tuple[int, int]:
        """Returns the range of the scene within the project timeline."""
        project = self.__track.timeline.project
        top_node = project.xml_node.find("./scenes/scene[@name='Top']")
        assert top_node is not None
        return _get_timeline_range(top_node, self.uid)

    @property
    def clip_range(self) -> Tuple[int, int]:
        """Returns the frame range of the scene. This is the window of the
        scene used in the project timeline.

        Returns:
            tuple(int, int)
        """

        project = self.__track.timeline.project
        top_node = project.xml_node.find("./scenes/scene[@name='Top']")
        assert top_node is not None
        warp_sequences = top_node.iter("warpSeq")

        warp_seq = next(ws for ws in warp_sequences if ws.attrib["id"] == self.uid)

        return int(warp_seq.attrib["start"]), int(warp_seq.attrib["end"])

    @property
    def length(self) -> int:
        """Returns the number of frames of the clip."""
        return int(self.xml_node.attrib["nbframes"])

    @property
    def path(self) -> str:
        """Returns the full path of the clip file used relative to the .sboard file."""
        return self.element.path

    @property
    def element(self) -> SBoardLibraryElement:
        """Returns the path to the video clip."""
        # Get the movieSeqExp or elementSeq node
        mov = self.xml_node.find("./columns/column[@type='0']")
        assert mov is not None
        mov = next(m for m in mov)

        # Get in /projects/elements/ and find the element matching the mov
        project = self.__track.timeline.project

        cat_id = mov.attrib["id"]
        element_name = mov.attrib["val"]

        # Get the element in the library
        cat = next(cat for cat in project.library.categories if cat.uid == cat_id)

        return next(element for element in cat.elements if element.name == element_name)


class SBoardAudioTrack(_SBoardNode):
    """A Storyboard Pro audio track"""

    def __init__(self, xml_node: cElementTree.Element, timeline: SBoardTimeline):
        # /projects/scenes/scene[@name='Top']/columns/column[@type='1']
        super(SBoardAudioTrack, self).__init__(xml_node)
        self.__timeline = timeline

    @property
    def name(self) -> str:
        """Returns the name of the audio track."""
        return self.xml_node.attrib["name"]

    @property
    def clips(self) -> Iterator[SBoardAudioClip]:
        """Generator f all the clips in the track."""
        return (
            SBoardAudioClip(node, self)
            for node in self.xml_node.findall("./soundSequence")
        )

    @property
    def timeline(self) -> SBoardTimeline:
        """Returns the timeline of the track."""
        return self.__timeline

    def is_enabled(self) -> bool:
        """Returns True if the track is enabled, False otherwise."""
        return not self.xml_node.attrib["disabled"] == "true"


class SBoardVideoTrack(_SBoardNode):
    """A Storyboard Pro video track"""

    def __init__(self, xml_node: cElementTree.Element, timeline: SBoardTimeline):
        # /projects/scenes/scene[@name=Top]/rootgroup/nodelist/module
        super(SBoardVideoTrack, self).__init__(xml_node)
        self.__timeline = timeline

    @property
    def uid(self) -> str:
        """Returns the unique identifier of the video track."""
        node = self.xml_node.find("./attrs/drawing/element")
        assert node is not None
        return node.attrib["col"]

    @property
    def name(self) -> str:
        """Returns the name of the video track."""
        return self.xml_node.attrib["name"]

    @property
    def clips(self) -> Iterator[SBoardVideoClip]:
        """Returns an iterator of all the clips in order."""
        column = self.__timeline.xml_node.find(
            "./columns/column[@name='{}']" "".format(self.uid)
        )
        assert column is not None
        uids = [node.attrib["id"] for node in column.findall("./warpSeq")]

        # Get all the clips
        video_clips = {
            video_clip.attrib["id"]: video_clip
            for video_clip in self.__timeline.project.xml_node.findall("./scenes/scene")
            if video_clip.attrib["id"] in uids
        }
        return (SBoardVideoClip(video_clips[uid], self) for uid in uids)

    @property
    def timeline(self) -> SBoardTimeline:
        """Returns the timeline of the track."""
        return self.__timeline

    def is_enabled(self) -> bool:
        """Returns True if the track is enabled, False otherwise."""
        # Look in the options, if the disabled tag is not here, the track is on.
        disabled = self.xml_node.find("./options/disabled[@val='true']")

        if disabled is None:
            return True

        return False


class SBoardLayer(_SBoardNode):
    """A layer group"""

    def __init__(self, xml_node: cElementTree.Element, panel: SBoardPanel):
        # /projects/scenes/scene[@name='panel']/rootgroup/nodeslist/module
        super(SBoardLayer, self).__init__(xml_node)
        self.__panel = panel

    @property
    def panel(self) -> SBoardPanel:
        """Returns the panel of the layer."""
        return self.__panel

    @property
    def name(self) -> str:
        """Returns the name of the layer group."""
        return self.xml_node.attrib["name"]

    @property
    def element(self) -> Optional[SBoardLibraryElement]:
        """Returns the library element for this layer."""
        draw_node = self.xml_node.find("./attrs/drawing/element")
        assert draw_node is not None

        column_name = draw_node.attrib["col"]

        column_node = self.__panel.xml_node.find(
            "./columns/column[@name='{}']/elementSeq".format(column_name)
        )

        if column_node is None:
            return None

        element_cat_id = column_node.attrib["id"]
        element_name = column_node.attrib["val"]

        # Search directly in category
        project = self.__panel.project
        project_node = project.xml_node
        cat_path = "./elements/element[@id='{}']".format(element_cat_id)
        category_node = project_node.find(cat_path)
        assert category_node is not None

        element_path = "./drawings/dwg[@name='{}']".format(element_name)
        element_node = category_node.find(element_path)
        assert element_node is not None

        cat = SBoardLibraryCategory(category_node, project.library)
        return SBoardLibraryElement(element_node, cat)

    def layer_iter(
        self, groups: bool = False, recursive: bool = False
    ) -> Iterator[SBoardLayer]:
        """Returns an iterator of all the sub layers contained in the layer.

        Args:
            groups: If True, also yield layers in groups
            recursive: If True, iterate layer recursively
        """
        if self.xml_node.attrib["type"] == "READ":
            return

        modules = self.__panel.xml_node.findall("./rootgroup/nodeslist/module")
        layers_by_name = {module.attrib["name"]: module for module in modules}
        group_name = self.xml_node.attrib["name"]

        for link in self.__panel.xml_node.findall("./rootgroup/linkedlist/link"):

            if link.attrib["out"] != group_name:
                continue

            layer = SBoardLayer(layers_by_name[link.attrib["in"]], self.__panel)

            if layer.is_group():

                if groups:
                    yield layer

                if recursive:
                    for child in layer.layer_iter(groups, recursive):
                        yield child
            else:
                yield layer

    def is_group(self) -> bool:
        """Returns True if the layer is a group."""
        return self.xml_node.attrib["type"] == "PEG"


class SBoardPanel(_SBoardNode):
    """Representation of a Story Board Pro Panel."""

    def __init__(self, xml_node: cElementTree.Element, scene: SBoardScene):
        # /projects/elements/scene
        super(SBoardPanel, self).__init__(xml_node)
        self.__scene = scene  # /project/scenes/scene

    @property
    def project(self) -> SBoardProject:
        """Returns the project of the panel."""
        return self.__scene.project

    @property
    def uid(self) -> str:
        """Returns the unique identifier of the panel."""
        return self.xml_node.attrib["id"]

    @property
    def number(self) -> int:
        """Returns the number of the panel."""
        for k, panel in enumerate(self.__scene.panels):
            if panel.uid == self.uid:
                return k + 1
        assert False

    @property
    def scene(self) -> SBoardScene:
        """Returns the scene in which the panel belongs."""
        return self.__scene

    @property
    def clip_range(self) -> Tuple[int, int]:
        """Returns the frame range of the panel."""
        timeline = _get_timeline(self.__scene.xml_node)

        warp_seq = next(ws for ws in timeline if ws.attrib["id"] == self.uid)

        return int(warp_seq.attrib["start"]), int(warp_seq.attrib["end"])

    @property
    def length(self) -> int:
        """Returns the number of frames of the panel."""
        return int(self.xml_node.attrib["nbframes"])

    @property
    def scene_range(self) -> Tuple[int, int]:
        """Returns the frame range of the panel relative to the scene."""
        # Get the panel within the timeline of the scene
        timeline = _get_timeline(self.__scene.xml_node)
        return _get_timeline_range(timeline, self.uid)

    @property
    def timeline_range(self) -> Tuple[int, int]:
        """Returns the range within the global timeline."""
        # Get the timeline range of the scene
        scene_timeline_range = self.scene.timeline_range

        start = scene_timeline_range[0] + self.scene_range[0]
        end = start + self.length
        return start, end

    def layer_iter(self, groups=False, recursive=False) -> Iterator[SBoardLayer]:
        """Returns an iterator of all the root layers in the panel.

        Args:
            groups: If True, also yield layers in groups
            recursive: If True, iterate layer recursively
        """
        for module in self.xml_node.findall("./rootgroup/nodeslist/module"):

            layer = SBoardLayer(module, self)

            if layer.is_group():

                if groups:
                    yield layer

                if recursive:
                    for child in layer.layer_iter(groups, recursive):
                        yield child

            else:
                yield layer


class SBoardScene(_SBoardNode):
    """A Storyboard Pro Scene has it is conceptually defined within StoryBoard
    Pro. A scene is a collection of panels (see SBoardPanel) which is then
    placed on the project timeline."""

    def __init__(self, xml_node: cElementTree.Element, project: SBoardProject):
        # /project/scenes/scene
        super(SBoardScene, self).__init__(xml_node)
        self.__project = project  # /project

    def __get_info(self) -> cElementTree.Element:
        """Returns the scene node info from the node metadata."""
        scene_info = self.xml_node.find("./metas/meta/sceneInfo")

        assert scene_info is not None, "No scene info found"
        return scene_info

    @property
    def project(self) -> SBoardProject:
        """Returns the project of the scene."""
        return self.__project

    @property
    def uid(self) -> str:
        """Returns the unique identifier of the scene."""
        return self.xml_node.attrib["id"]

    @property
    def name(self) -> str:
        """Returns the name of the scene."""
        return self.__get_info().attrib["name"]

    @property
    def timeline_range(self) -> Tuple[int, int]:
        """Returns the range of the scene within the project timeline."""
        top_node = self.__project.xml_node.find("./scenes/scene[@name='Top']")
        assert top_node is not None
        return _get_timeline_range(top_node, self.uid)

    @property
    def clip_range(self) -> Tuple[int, int]:
        """Returns the frame range of the scene. This is the window of the
        scene used in the project timeline.

        """
        top_node = self.__project.xml_node.find("./scenes/scene[@name='Top']")
        assert top_node is not None
        warp_sequences = top_node.iter("warpSeq")

        warp_seq = next(ws for ws in warp_sequences if ws.attrib["id"] == self.uid)

        return int(warp_seq.attrib["start"]), int(warp_seq.attrib["end"])

    @property
    def length(self) -> int:
        """Returns the number of frames of the scene."""
        return int(self.xml_node.attrib["nbframes"])

    @property
    def panels(self) -> Iterator[SBoardPanel]:
        """Returns an iterator of panels within the scene."""
        scene_iter = self.__project.xml_node.findall("./scenes/scene")

        all_panels_by_id = {
            panel.attrib["id"]: panel
            for panel in scene_iter
            if "panel" in panel.attrib["name"]
        }

        timeline = _get_timeline(self.xml_node)

        # Evaluate all the warp sequences
        for warp_seq in timeline.findall("warpSeq"):
            # Only get existing panels
            panel_id = warp_seq.attrib["id"]
            yield SBoardPanel(all_panels_by_id[panel_id], self)

    @property
    def sequence(self) -> Optional[SBoardSequence]:
        """Returns the sequence the scene belongs to or None if there is no sequence."""
        scene_info = self.xml_node.find("./metas/meta/sceneInfo")
        assert scene_info is not None
        sequence_name = scene_info.attrib["sequenceName"]

        if sequence_name == "":
            sequence_name = "0"

        return SBoardSequence(self.__project, sequence_name)


class SBoardSequence(object):
    """A Storyboard sequence. A sequence contains one or more scenes."""

    def __init__(self, project: SBoardProject, sequence_name: str):
        self.__project = project
        self.__sequence_name = sequence_name

    @property
    def project(self) -> SBoardProject:
        """Returns the project of this scene."""
        return self.__project

    @property
    def name(self) -> str:
        """Returns the name of the sequence."""
        return self.__sequence_name

    @property
    def scenes(self) -> Iterator[SBoardScene]:
        """Generator of all the scenes within the sequence."""

        for scene in self.__project.scenes:
            sequence = scene.sequence
            if not sequence:
                continue
            if sequence.name == self.name:
                yield scene


class SBoardTimeline(_SBoardNode):
    """Represents the timeline of the project."""

    def __init__(self, xml_node: cElementTree.Element, project: SBoardProject):
        # /projects/scenes/scene[@name='Top']
        super(SBoardTimeline, self).__init__(xml_node)
        self.__project = project

    @property
    def length(self) -> int:
        """Returns the number of frames in the timeline."""
        return int(self.xml_node.attrib["nbframes"])

    @property
    def uid(self) -> str:
        """Returns the unique identifier of the timeline."""
        return self.xml_node.attrib["id"]

    @property
    def project(self) -> SBoardProject:
        """Returns the project of the timeline."""
        return self.__project

    @property
    def audio_tracks(self) -> Iterator[SBoardAudioTrack]:
        """Returns an iterator of all the audio tracks of the timeline.

        Tracks are generated in the same order as they appear in the project.
        """
        audio_tracks = self.xml_node.findall("./columns/column[@type='1']")
        return (SBoardAudioTrack(node, self) for node in audio_tracks)

    @property
    def video_tracks(self) -> Iterator[SBoardVideoTrack]:
        """Returns an iterator of all the video tracks of the timeline.

        Tracks are generated in the same order as they appear in the project.
        """
        # To get video tracks, we must  find the module which is not TopLayer
        # ./rootgroup/nodeslist
        modules = self.xml_node.findall("./rootgroup/nodeslist/module")

        return (
            SBoardVideoTrack(module, self)
            for module in modules
            if module.attrib["name"] != "TopLayer"
        )

    @property
    def scenes(self) -> Iterator[SBoardScene]:
        """Returns an iterator of the scene within the timeline.

        The scenes are generated in the same order as they appear in the
        timeline.
        """
        project_scenes_by_id = {s.uid: s for s in self.__project.scenes}

        # Parse the warpSequences in the timeline node
        warp_sequences = self.xml_node.iter("warpSeq")

        for warp_seq in warp_sequences:

            scene = project_scenes_by_id.get(warp_seq.attrib["id"], None)

            # Check if it is a scene
            if scene is None:
                continue

            yield scene

    @property
    def panels(self) -> Iterator[SBoardPanel]:
        """Returns an iterator of the panels within the timeline.

        The panels are generated in the same order as they appear in the timeline.
        """
        for scene in self.scenes:

            # We already get panels in order, just yield them
            for panel in scene.panels:
                yield panel

    @property
    def transitions(self) -> Iterator[SBoardTransition]:
        """Returns an iterator of the transitions within the timeline.
        Transitions are returned in the same order as they appear in the timeline.

        """

        # Parse the warpSequences in the timeline node
        warp_sequences = self.xml_node.iter("transitionSeq")

        for warp_seq in warp_sequences:
            yield SBoardTransition(warp_seq, self)


class SBoardTransition(_SBoardNode):
    """A Storyboard Pro Transition has it is conceptually defined within StoryBoard
    Pro. A transition is a moment over scene in a timeline."""

    def __init__(self, xml_node: cElementTree.Element, timeline: SBoardTimeline):
        # /project/scenes/scene[@name='Top']
        super(SBoardTransition, self).__init__(xml_node)
        self.__timeline = timeline  # /project/scenes/scene

    @property
    def timeline(self) -> SBoardTimeline:
        """Returns the timeline of the scene."""
        return self.__timeline

    @property
    def uid(self) -> str:
        """Returns the unique identifier of the transition."""
        return self.xml_node.attrib["id"]

    @property
    def timeline_range(self) -> Tuple[int, int]:
        """Returns the unique identifier of the transition."""

        exp = [int(x) for x in self.xml_node.attrib["exposures"].split("-", maxsplit=1)]
        return exp[0], exp[1]

    @property
    def type(self) -> str:
        """Returns the unique type of the transition."""
        return self.xml_node.attrib["type"]


class SBoardLibraryElement(_SBoardNode):
    """Storyboard Pro library element. Represents a file used within the project"""

    def __init__(self, xml_node: cElementTree.Element, category: SBoardLibraryCategory):
        # /projects/elements/element/drawings/dwg
        super(SBoardLibraryElement, self).__init__(xml_node)
        self.__category = category

    @property
    def category(self) -> SBoardLibraryCategory:
        """Returns the SBoardLibraryCategory of this element."""
        return self.__category

    @property
    def name(self) -> str:
        """Returns the name of the element."""
        return self.xml_node.attrib["name"]

    @property
    def path(self) -> str:
        """Returns the path of the file relative to the project .sboard file."""
        file_name = "{}.{}".format(self.name, self.__category.extension)
        return os.path.join(
            ".", self.__category.root_folder, self.__category.folder, file_name
        )


class SBoardLibraryCategory(_SBoardNode):
    """A category of files in the library"""

    # If lower names are in this dict, the associated extension is used.
    # Otherwise, the name of the category is used
    EXTENSION_BY_LOW_NAME = {
        "draw": "tvg",
        "fbxmodels": "fbx",
        "abcmodels": "abc",
    }

    def __init__(self, xml_node: cElementTree.Element, library: SBoardLibrary):
        # /projects/elements/element
        super(SBoardLibraryCategory, self).__init__(xml_node)
        self.__library = library

    @property
    def uid(self) -> str:
        """Returns the unique identifier of the library category.

        This id may vary across project. Do not rely on this id to compare
        categories between different projects.
        """
        return self.xml_node.attrib["id"]

    @property
    def name(self) -> str:
        """Returns the name of the library category.

        This name may vary across project. Do not rely on this name to compare
        categories between different projects.
        """
        return self.xml_node.attrib["elementName"]

    @property
    def root_folder(self) -> str:
        """Returns the root folder of the library category."""
        return self.xml_node.attrib["rootFolder"]

    @property
    def folder(self) -> str:
        """Returns the folder of the library category."""
        return self.xml_node.attrib["elementFolder"]

    @property
    def extension(self) -> str:
        """Returns the extension for this category."""
        return self.EXTENSION_BY_LOW_NAME.get(self.name, self.name)

    @property
    def elements(self) -> Iterator[SBoardLibraryElement]:
        """Returns an iterator of all the elements for this category."""
        for node in self.xml_node.findall("./drawings/dwg"):
            yield SBoardLibraryElement(node, self)


class SBoardLibrary(_SBoardNode):
    """Storyboard Pro library that stores all the references to the files
    used in the project. Note that audio files are not stored in the library
    folder."""

    def __init__(self, xml_node: cElementTree.Element, project: SBoardProject):
        # /projects/elements
        super(SBoardLibrary, self).__init__(xml_node)
        self.__project = project

    @property
    def project(self) -> SBoardProject:
        """Returns the project of the library"""
        return self.__project

    @property
    def categories(self) -> Iterator[SBoardLibraryCategory]:
        """Returns an iterator of all the categories in the library."""
        for node in self.xml_node.findall("./element"):
            yield SBoardLibraryCategory(node, self)

    @property
    def elements(self) -> Iterator[SBoardLibraryElement]:
        """Returns an iterator of all the elements in the library."""
        for cat in self.categories:
            for element in cat.elements:
                yield element


class SBoardProject(_SBoardNode):
    """A StoryBoard Pro project abstraction built usually from a .sboard file
    (see from_file class method). It basically wraps the xml content of the
    .sboard file to provides a more intuitive way of accessing components of a
    project than just parsing directly the xml content."""

    @classmethod
    def from_file(cls, sboard_path) -> SBoardProject:
        """Returns a SBoardProject from the given path."""
        return cls(cElementTree.parse(sboard_path))

    @property
    def sequences(self) -> Iterator[SBoardSequence]:
        """Returns an iterator of the sequences in the project."""
        # Check that there are sequences
        for meta in self.xml_node.findall("./metas/meta[@name='sequenceExists']"):
            node = meta.find("bool")
            assert node is not None
            if node.attrib["value"] != "true":
                return

        # Get all the sequences
        sequence_names = set([])

        for scene in self.scenes:
            seq = scene.sequence
            if not seq:
                continue
            seq_name = seq.name

            if seq_name in sequence_names:
                continue

            sequence_names.add(seq_name)
            yield seq

    @property
    def scenes(self) -> Iterator[SBoardScene]:
        """Returns an iterator of scenes within the project."""
        for scene in self.xml_node.findall("./scenes/scene[@name]"):

            if "shot" not in scene.attrib["name"]:
                continue

            yield SBoardScene(scene, self)

    @property
    def timeline(self) -> SBoardTimeline:
        """Returns the SBoardTimeline of the project."""
        # Get the number of frames in the top node
        top_node = self.xml_node.find("./scenes/scene[@name='Top']")
        assert top_node is not None
        return SBoardTimeline(top_node, self)

    @property
    def frame_rate(self) -> float:
        """Returns the frame rate of the project"""
        node = self.xml_node.find("./options/framerate")
        assert node is not None
        return float(node.attrib["val"])

    @property
    def title(self) -> str:
        """Returns the title of the project."""
        node = self.xml_node.find("./metas/meta[@name='projectTitle']/string")
        assert node is not None
        return node.attrib["value"]

    @property
    def library(self) -> SBoardLibrary:
        """Returns the library of the project."""
        node = self.xml_node.find("elements")
        assert node is not None
        return SBoardLibrary(node, self)
