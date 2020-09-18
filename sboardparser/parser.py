"""
Parser for Storyboard Pro .sboard xml file.
The SBoardParser class will let you build a hierarchy of objects from the
given sboard file path.
"""


import abc
from collections import namedtuple
from xml.etree import cElementTree


def _get_timeline(scene_node):
    # Shot timeline is described in the column with type=0
    columns = scene_node.find('columns')
    return next(c for c in columns.findall("column")
                if c.attrib['type'] == "0")


SBoardFrameRange = namedtuple("SBoardFrameRange", "frame_in frame_out")


class SboardNode(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, xml_node):
        self.__xml_node = xml_node

    @property
    def xml_node(self):
        return self.__xml_node


class SBoardPanel(SboardNode):

    def __init__(self, xml_node, scene):
        super(SBoardPanel, self).__init__(xml_node)
        self.__scene = scene  # /project/scenes/scene

    def __get_info(self):
        """Returns the scene node info from from the node metadata"""
        # Get the scene info metadata
        panel_info = None

        for meta in self.xml_node.find('metas').findall('meta'):

            if meta.attrib['type'] != "panelInfo":
                continue

            panel_info = meta.find('panelInfo')
            break

        assert panel_info is not None, "No panel info found"
        return panel_info

    @property
    def id(self):
        return self.xml_node.attrib['id']

    @property
    def name(self):
        return self.__get_info().attrib["name"]

    @property
    def scene(self):
        return self.__scene

    @property
    def frame_range(self):

        timeline = _get_timeline(self.__scene.xml_node)

        warp_seq = next(ws for ws in timeline
                        if ws.attrib['id'] == self.id)

        return SBoardFrameRange(int(warp_seq.attrib["start"]),
                                int(warp_seq.attrib["end"]))

    @property
    def cut_range(self):
        # Get the panel within the timeline of the scene
        timeline = _get_timeline(self.__scene.xml_node)

        warp_seq = next(ws for ws in timeline.findall("warpSeq")
                        if ws.attrib['id'] == self.id)

        exposure = warp_seq.attrib["exposures"]
        ex_split = exposure.split("-")

        assert 0 < len(ex_split) < 3

        if len(ex_split) == 1:
            return SBoardFrameRange(int(exposure), int(exposure))

        return SBoardFrameRange(int(ex_split[0]), int(ex_split[1]))


class SBoardScene(SboardNode):
    """A Storyboard Pro Scene has it is conceptually defined within StoryBoard
     Pro. A scene is a collection of panels (see SBoardPanel) that can sit on
     the M"""

    def __init__(self, xml_node, project):
        super(SBoardScene, self).__init__(xml_node)
        self.__project = project  # /project

    def __get_info(self):
        """Returns the scene node info from from the node metadata"""
        # Get the scene info metadata
        scene_info = None

        for meta in self.xml_node.find('metas').findall('meta'):

            if meta.attrib['type'] != "sceneInfo":
                continue

            scene_info = meta.find('sceneInfo')
            break

        assert scene_info is not None, "No scene info found"
        return scene_info

    @property
    def id(self):
        return self.xml_node.attrib["id"]

    @property
    def name(self):
        return self.__get_info().attrib["name"]

    @property
    def cut_range(self):

        scene_iter = self.__project.xml_node.find('scenes').findall('scene')
        top_node = next(scene for scene in scene_iter
                        if scene.attrib['name'] == 'Top')
        timeline = _get_timeline(top_node)

        warp_seq = next(ws for ws in timeline.findall("warpSeq")
                        if ws.attrib['id'] == self.id)

        exposure = warp_seq.attrib["exposures"]
        ex_split = exposure.split("-")

        assert 0 < len(ex_split) < 3

        if len(ex_split) == 1:
            return SBoardFrameRange(int(exposure), int(exposure))

        return SBoardFrameRange(int(ex_split[0]), int(ex_split[1]))

    @property
    def frame_range(self):

        scene_iter = self.__project.xml_node.find('scenes').findall('scene')
        top_node = next(scene for scene in scene_iter
                        if scene.attrib['name'] == 'Top')
        timeline = _get_timeline(top_node)

        warp_seq = next(ws for ws in timeline
                        if ws.attrib['id'] == self.id)

        return SBoardFrameRange(int(warp_seq.attrib["start"]),
                                int(warp_seq.attrib["end"]))

    @property
    def panels(self):

        scene_iter = self.__project.xml_node.find('scenes').findall('scene')

        all_panels_by_id = {panel.attrib['id']: panel
                            for panel in scene_iter
                            if 'panel' in panel.attrib['name']}

        timeline = _get_timeline(self.xml_node)

        # Evaluate all the warp sequences
        for warp_seq in timeline.findall('warpSeq'):

            # Only get existing panels
            panel_id = warp_seq.attrib["id"]

            if panel_id not in all_panels_by_id:
                continue

            yield SBoardPanel(all_panels_by_id[panel_id], self)


class SBoardProject(SboardNode):
    """A StoryBoard Pro project abstraction built usually from a .sboard file
    (see from_file class method). It basically wraps the xml content of the
    .sboard file to provides a more intuitive way of accessing components of a
    project than just parsing directly the xml content."""

    @classmethod
    def from_file(cls, sboard_path):
        """Returns a SBoardProject from the given path.

        Returns:
            SBoardProject
        """
        return cls(cElementTree.parse(sboard_path))

    @property
    def scenes(self):
        """Generator of scenes within the project.

        Yields:
            SBoardScene
        """
        for scene in self.xml_node.find("scenes").findall("scene"):

            if "shot" in scene.attrib['name']:
                yield SBoardScene(scene, self)
