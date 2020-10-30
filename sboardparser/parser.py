"""
Parser for Storyboard Pro .sboard xml file.
The SBoardParser class will let you build a hierarchy of objects from the
given sboard file path.
"""

import abc
from xml.etree import cElementTree


def _get_timeline(scene_node):
    # Shot timeline is described in the column with type=0
    columns = scene_node.find('columns')
    return next(c for c in columns.findall("column")
                if c.attrib['type'] == "0")


def _get_timeline_range(timeline_node, uid):
    warp_seq = next(ws for ws in timeline_node.findall("warpSeq")
                    if ws.attrib['id'] == uid)

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
    def xml_node(self):
        """Returns the root xml node for this given object.

        Returns:

        """
        return self.__xml_node


class SBoardLayer(_SBoardNode):
    """A layer group"""

    def __init__(self, xml_node, panel):
        # /projects/scenes/scene/rootgroup/nodeslist/module
        super(SBoardLayer, self).__init__(xml_node)
        self.__panel = panel

    @property
    def panel(self):
        """Returns the panel of the layer.

        Returns:
            SBoardPanel
        """
        return self.__panel

    @property
    def name(self):
        """Returns the name of the layer group.

        Returns:
            str
        """
        return self.xml_node.attrib["name"]

    @property
    def element(self):
        """Returns the element for this layer.

        Returns:
            SBoardElement
        """

        draw_node = self.xml_node.find('./attrs/drawing/element')
        column_name = draw_node.attrib['col']

        column_node = self.__panel.xml_node.find("./columns/column[@name='{}']"
                                                 "".format(column_name))
        element_id = column_node.attrib['id']

        return next(element for element in self.__panel.project.elements
                    if element.uid == element_id)

    def layer_iter(self, groups=False, recursive=False):
        """Generator of all the sub layers contained in the layer.

        Args:
            groups (bool, optional): iter groups
            recursive (bool, optional): iter layer recursively

        Yields:
            SBoardLayer
        """

        if self.xml_node.attrib['type'] == "READ":
            return

        modules = self.__panel.xml_node.findall("./rootgroup/nodeslist/module")
        layers_by_name = {module.attrib['name']: module for module in modules}
        group_name = self.xml_node.attrib['name']

        for link in self.__panel.xml_node.findall(
                "./rootgroup/linkedlist/link"):

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

    def is_group(self):
        """Returns True if the layer is a group.

        Returns:
            bool
        """
        return self.xml_node.attrib['type'] == 'PEG'


class SBoardPanel(_SBoardNode):
    """Representation of a Story Board Pro Panel."""

    def __init__(self, xml_node, scene):
        super(SBoardPanel, self).__init__(xml_node)
        self.__scene = scene  # /project/scenes/scene

    @property
    def project(self):
        """Returns the project for this node.

        Returns:
            SBoardProject
        """
        return self.__scene.project

    @property
    def uid(self):
        """Returns the unique identifier of the panel.

        Returns:
            str
        """
        return self.xml_node.attrib['id']

    @property
    def number(self):
        """Returns the number of the panel.

        Returns:
            str
        """
        for k, panel in enumerate(self.__scene.panels):
            if panel.uid == self.uid:
                return k + 1

    @property
    def scene(self):
        """Returns the scene in which the panel belongs.

        Returns:
            SBoardScene
        """
        return self.__scene

    @property
    def frame_range(self):
        """Returns the frame range of the panel.

        Returns:
            tuple(int, int)
        """
        timeline = _get_timeline(self.__scene.xml_node)

        warp_seq = next(ws for ws in timeline
                        if ws.attrib['id'] == self.uid)

        return int(warp_seq.attrib["start"]), int(warp_seq.attrib["end"])

    @property
    def length(self):
        """Returns the number of frames of the panel.

        Returns:
            int
        """
        return int(self.xml_node.attrib["nbframes"])

    @property
    def scene_range(self):
        """Returns the frame range of the panel relative to the scene.

        Returns:
            tuple(int, int)
        """
        # Get the panel within the timeline of the scene
        timeline = _get_timeline(self.__scene.xml_node)
        return _get_timeline_range(timeline, self.uid)

    @property
    def timeline_range(self):
        """Returns the range within the global timeline.

        Returns:
            tuple(int, int)
        """
        # Get the timeline range of the scene
        scene_timeline_range = self.scene.timeline_range

        start = scene_timeline_range[0] + self.scene_range[0]
        end = start + self.length
        return start, end

    def layer_iter(self, groups=False, recursive=False):
        """Generator of all the root layers in the panel.

        Args:
            groups (bool, optional): iter layer groups
            recursive (bool, optional): recursively iter in group

        Yields:
            SBoardLayer
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

    def __init__(self, xml_node, project):
        # /project/scenes/scene
        super(SBoardScene, self).__init__(xml_node)
        self.__project = project  # /project

    def __get_info(self):
        """Returns the scene node info from from the node metadata"""

        scene_info = self.xml_node.find('./metas/meta/sceneInfo')

        assert scene_info is not None, "No scene info found"
        return scene_info

    @property
    def project(self):
        """Returns the project of the scene.

        Returns:
            SBoardProject
        """
        return self.__project

    @property
    def uid(self):
        """Returns the unique identifier of the scene.

        Returns:
            str
        """
        return self.xml_node.attrib["id"]

    @property
    def name(self):
        """Returns the name of the scene.

        Returns:
            str
        """
        return self.__get_info().attrib["name"]

    @property
    def timeline_range(self):
        """Returns the range of the scene within the project timeline.

        Returns:
            tuple(int, int)
        """

        top_node = self.__project.xml_node.find("./scenes/scene[@name='Top']")

        # Get the panel within the timeline of the scene
        timeline = _get_timeline(top_node)
        return _get_timeline_range(timeline, self.uid)

    @property
    def frame_range(self):
        """Returns the frame range of the scene. This is the window of the
        scene used in the project timeline.

        Returns:
            tuple(int, int)
        """

        top_node = self.__project.xml_node.find("./scenes/scene[@name='Top']")
        timeline = _get_timeline(top_node)

        warp_seq = next(ws for ws in timeline
                        if ws.attrib['id'] == self.uid)

        return int(warp_seq.attrib["start"]), int(warp_seq.attrib["end"])

    @property
    def length(self):
        """Returns the number of frames of the scene.

        Returns:
            int
        """
        return int(self.xml_node.attrib["nbframes"])

    @property
    def panels(self):
        """Returns a generator of panels within the scene.

        Yields:
            SBoardPanel
        """
        scene_iter = self.__project.xml_node.findall('./scenes/scene')

        all_panels_by_id = {panel.attrib['id']: panel
                            for panel in scene_iter
                            if 'panel' in panel.attrib['name']}

        timeline = _get_timeline(self.xml_node)

        # Evaluate all the warp sequences
        for warp_seq in timeline.findall('warpSeq'):
            # Only get existing panels
            panel_id = warp_seq.attrib["id"]
            yield SBoardPanel(all_panels_by_id[panel_id], self)

    @property
    def sequence(self):
        """Returns the sequence the scene belongs to or None if there is no
        sequence.

        Returns:
            SBoardSequence or None
        """

        scene_info = self.xml_node.find('./metas/meta/sceneInfo')
        return SBoardSequence(self.__project, scene_info.attrib['sequenceName'])


class SBoardProjectTimeline(_SBoardNode):
    """Represents the timeline of the project."""

    def __init__(self, xml_node, project):
        super(SBoardProjectTimeline, self).__init__(xml_node)
        self.__project = project

    @property
    def length(self):
        """Returns the number of frames in the timeline.

        Returns:
            int
        """
        return int(self.xml_node.attrib["nbframes"])

    @property
    def uid(self):
        """Returns the unique identifier of the timeline.

        Returns:
            str
        """
        return self.xml_node.attrib["id"]

    @property
    def project(self):
        """Returns the project of the timeline.

        Returns:
            SBoardProject
        """
        return self.__project

    @property
    def scenes(self):
        """Returns a generator of the scene within the timeline.
        The scenes are generated in the same order as they appear in the
        timeline.

        Yields:
            SBoardScene
        """

        project_scenes_by_id = {s.uid: s for s in self.__project.scenes}

        # Parse the warpSequences in the timeline node
        warp_sequences = self.xml_node.iter("warpSeq")

        for warp_seq in warp_sequences:
            scene = project_scenes_by_id.get(warp_seq.attrib["id"], None)

            assert scene is not None

            yield scene

    @property
    def panels(self):
        """Returns a generator of the panels within the timeline.
        The panels are generated in the same order as they appear in the
        timeline.

        Yields:
            SBoardPanel
        """
        for scene in self.scenes:

            # We already get panels in order, just yield them
            for panel in scene.panels:
                yield panel


class SBoardSequence(object):
    """A Storyboard sequence. A sequence contains one or more scenes."""

    def __init__(self, project, sequence_name):
        self.__project = project
        self.__sequence_name = sequence_name

    @property
    def project(self):
        """Returns the project of this scene.

        Returns:
            SBoardProject
        """
        return self.__project

    @property
    def name(self):
        """Returns the name of the sequence.

        Returns:
            int
        """
        return self.__sequence_name

    @property
    def scenes(self):
        """Generator of all the scenes within the sequence.

        Yields:
            SBoardScene
        """

        for scene in self.__project.scenes:

            if scene.sequence.name == self.name:
                yield scene


class SBoardDrawing(_SBoardNode):
    """A piece of drawing"""

    def __init__(self, xml_node, element):
        super(SBoardDrawing, self).__init__(xml_node)
        self.__element = element

    @property
    def name(self):
        """Returns the name of the drawing.

        Returns:
            str
        """
        return self.xml_node.attrib['name']

    @property
    def scale_factor(self):
        """Returns the scale factor of the drawing.

        Returns:
            float
        """
        return float(self.xml_node.attrib['scaleFactor'])


class SBoardElement(_SBoardNode):
    """A Storyboard element"""

    def __init__(self, xml_node, project):
        super(SBoardElement, self).__init__(xml_node)
        self.__project = project

    @property
    def uid(self):
        """Returns the unique identifier of the board element.

        Returns:
            str
        """
        return self.xml_node.attrib['id']

    @property
    def type(self):
        """Returns the type of element.

        Returns:
            str
        """
        return self.xml_node.attrib['elementName']

    @property
    def drawings(self):
        """Generator of drawings that constitute the element.

        Yields:
            SBoardDrawing
        """
        for drawing in self.xml_node.iter("dwg"):
            yield SBoardDrawing(drawing, self)


class SBoardProject(_SBoardNode):
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
    def sequences(self):
        """Generator of the sequences in the project.

        Yields:
            SBoardSequence
        """
        # Check that there are sequences
        for meta in self.xml_node.findall(
                "./metas/meta[@name='sequenceExists']"):

            if meta.find("bool").attrib["value"] != "true":
                return

        # Get all the sequences
        sequence_names = set([])

        for scene in self.scenes:
            seq = scene.sequence
            seq_name = seq.name

            if seq_name in sequence_names:
                continue

            sequence_names.add(seq_name)
            yield seq

    @property
    def scenes(self):
        """Generator of scenes within the project.

        Yields:
            SBoardScene
        """
        for scene in self.xml_node.findall("./scenes/scene[@name]"):

            if 'shot' not in scene.attrib['name']:
                continue

            yield SBoardScene(scene, self)

    @property
    def elements(self):
        """Generator of all elements in the project.

        Yields:
            SBoardElement
        """
        for element in self.xml_node.findall("./elements/element"):
            yield SBoardElement(element, self)

    @property
    def timeline(self):
        """Returns the SBoardTimeline of the project.

        Returns:
            SBoardProjectTimeline
        """
        # Get the number of frames in the top node
        top_node = self.xml_node.find("./scenes/scene[@name='Top']")
        return SBoardProjectTimeline(top_node, self)

    @property
    def frame_rate(self):
        """Returns the frame rate of the project

        Returns:
            float
        """
        return float(self.xml_node.find('./options/framerate').attrib['val'])
