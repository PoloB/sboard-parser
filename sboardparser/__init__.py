
"""A parser for Toon Boom Story Board Pro .sboard files"""

from .parser import SBoardProject

parse = SBoardProject.from_file
