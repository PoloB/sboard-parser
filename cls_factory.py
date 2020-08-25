#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
"""

__author__ = "Paul-Emile Buteau"
__maintainer__ = "Paul-Emile Buteau"


class SBoardProject(object):

    def __init__(self, **kwargs):
        self.__data = kwargs

    @property
    def build(self):
        return self.__data['build']

    @property
    def count(self):
        return self.__data['count']

    @property
    def elements(self):
        return self.__data.get('elements', [])

    @property
    def index(self):
        return self.__data['index']

    @property
    def metas(self):
        return self.__data['metas']

    @property
    def options(self):
        return self.__data['options']

    @property
    def scenes(self):
        return self.__data.get('scenes', [])

    @property
    def source(self):
        return self.__data['source']

    @property
    def symbols(self):
        return self.__data['symbols']

    @property
    def timeline(self):
        return self.__data['timeline']

    @property
    def timeline_markers(self):
        return self.__data['timeline_markers']

    @property
    def version(self):
        return self.__data['version']
