#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This module contains the class template used to represent the objects found in
a Storyboard Prod sboard xml file.
"""

__author__ = "Paul-Emile Buteau"
__maintainer__ = "Paul-Emile Buteau"


class _SBoardAbstractObject(object):

    def __init__(self, **kwargs):
        self._data = kwargs


class SBoardProject(_SBoardAbstractObject):
    """Top level object a StoryBoard Pro project."""

    @property
    def build(self):
        """Returns the number of the Storyboard Pro build used to create
        this project.

        Returns:
            str
        """
        return self._data['build']

    @property
    def elements(self):
        return self._data.get('elements', [])

    @property
    def metas(self):
        return self._data['metas']

    @property
    def options(self):
        return self._data['options']

    @property
    def scenes(self):
        """Returns the list of scenes of the project.

        Returns:
            list[SBoardScene]
        """
        return self._data.get('scenes', [])

    @property
    def source(self):
        """Returns the source of the project which consist of the StoryboardPro
        version, build number and build date.

        Returns:
            str
        """
        return self._data['source']

    @property
    def symbols(self):
        return self._data['symbols']

    @property
    def timeline(self):
        return self._data['timeline']

    @property
    def timeline_markers(self):
        return self._data['timeline_markers']

    @property
    def version(self):
        """Returns the version number of the Storyboard Pro used to craft the
        project.

        Returns:
            str
        """
        return self._data['version']


class SBoardScene(_SBoardAbstractObject):

    @property
    def id(self):
        """Returns the id of the scene.

        Returns:
            str
        """
        return self._data['id']

    @property
    def name(self):
        """Returns the scnee name.

        Returns:
            str
        """
        return self._data['name']

    @property
    def nbframes(self):
        """Returns the number of frames of the scene.

        Returns:
            str
        """
        return self._data['name']

    @property
    def columns(self):
        """Returns the column associated to this scene"""
        return self._data['columns']

    @property
    def start_frame(self):
        """Returns the start frame of the scene relative to the whole project.

        Returns:
            int
        """

        return int(self.columns[0].warp_sequences[0].exposures.split("-")[0])

    @property
    def end_frame(self):
        """Returns the start frame of the scene relative to the whole project.

        Returns:
            int
        """
        return int(self.columns[0].warp_sequences[0].exposures.split("-")[1])
