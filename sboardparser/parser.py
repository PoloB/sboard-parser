
"""
Parser for Storyboard Pro .sboard xml file.
The SBoardParser class will let you build a hierarchy of objects from the
given sboard file path.
The classes used to represent object from the xml hierarchy are either created
using the class templates found in the cls_template module or created at runtime.
"""


import collections
import keyword
import re
import xml.etree.ElementTree as ET

from sboardparser import cls_template

__author__ = "Paul-Emile Buteau"
__maintainer__ = "Paul-Emile Buteau"


def camel_to_snake(name):
    """Convert camel case to snake case.

    Args:
        name (str)

    Returns:
          str
    """
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def namedtuple_with_defaults(typename, field_names, default_values=()):
    """Returns a new class built with namedtuple but with default arguments to
    None.

    Args:
        typename (str): name of the class to create
        field_names (str): field names of the class
        default_values (tuple): default values to give to fields

    Returns:
        class
    """
    T = collections.namedtuple(typename, field_names)
    T.__new__.__defaults__ = (None,) * len(T._fields)
    if isinstance(default_values, collections.abc.Mapping):
        prototype = T(**default_values)
    else:
        prototype = T(*default_values)
    T.__new__.__defaults__ = tuple(prototype)
    return T


def get_class(class_name, field_names):
    """Returns a class from the given class name with the given fields.
    This function first look in the cls_template module to find a template for
    the given class name. If it can't be found, the class is built using the
    namedtuple_with_defaults factory function.
    If some fields are missing from the class found in cls_template, they will
    be added dynamically at runtime.

    Args:
        class_name (str): name of the class to create
        field_names (str): field names of the class

    Returns:
        class
    """
    cls = cls_template.__dict__.get(class_name)

    if not cls:
        return namedtuple_with_defaults(class_name, field_names)

    # Compare known class fields with requested ones
    requested_fields = set(field_names.split(" "))
    known_fields = set(dir(cls))

    field_diff = requested_fields.difference(known_fields)

    if not field_diff:
        return cls

    # There are unsatisfied fields
    print("Known class {} does not support the following fields: {}"
          "".format(class_name, ", ".join(field_diff)))

    # Create a copy of the class
    # cls_copy = type(cls.__name__ + "Extended", (cls,), dict(cls.__dict__))

    for f in field_diff:

        def get_property(field_name):
            def prop_(self):
                return self._data[field_name]

            return property(prop_)
        # Add the field to the known class
        setattr(cls, f, get_property(f))

    return cls


class SBoardParser(object):
    """Parser of Storyboard Pro .sboard files."""

    def __init__(self, content):

        # This is the content of the sboard file. It is never modified
        self.__original_content = content
        self.__root_node = None
        self.__parse()

    @classmethod
    def from_file(cls, sboard_path):
        """Returns a parser initialized from the given file path.

        Args:
            sboard_path (str): path to the Toon Boom Storyboard Pro sboard file

        Returns:
            SBoardParser
        """
        with open(sboard_path, "r") as f:
            content = f.read()

        return cls(content)

    def __parse(self):
        """Returns the SBoardProject parsed from the Storyboard Pro path.
        The whole hierarchy of object is built on this call.

        Returns:
            SBoardProject
        """
        attr_by_class = collections.defaultdict(set)
        unspecialized_names = {'column'}

        change_of_name = collections.defaultdict(dict)

        def xml_to_dict(xml_tree_element, parent=None):
            """Recursive function that takes the given xml ElementTree and
            create a dict from it.

            Args:
                xml_tree_element (ElementTree): node of the xml tree to
                    convert to dict.
                parent (str, None): name of the parent. Being used to build
                    key of dictionary which have vague names

            Returns:
                dict
            """

            key_ = camel_to_snake(xml_tree_element.tag)

            if key_ in unspecialized_names:
                key_ = parent + "_" + key_

            is_list = len(set(a.tag for a in xml_tree_element)) == 1 \
                and not xml_tree_element.attrib

            if is_list:

                object_list = []

                for a in xml_tree_element:

                    akey = camel_to_snake(a.tag)

                    if akey in unspecialized_names:
                        akey = parent + "_" + akey

                    object_list.append({akey: xml_to_dict(a, parent)})

                return object_list

            # Craft all children data
            data_dict = {camel_to_snake(a.tag): xml_to_dict(a, key_)
                         for a in xml_tree_element}
            data_dict.update(xml_tree_element.attrib)

            # Make sure we are not using python keyword names
            for k in list(data_dict.keys()):
                if not keyword.iskeyword(k):
                    continue

                # Replace the name
                v = data_dict.pop(k)
                new_name = key_ + "_" + k
                data_dict[new_name] = v

                # Store the change of name so it is possible to rewrite the
                # xml back
                change_of_name[k][new_name] = k

            # Register the attributes of the tree element
            for k in data_dict.keys():
                attr_by_class[key_].add(k)

            return data_dict

        def craft_obj_hierarchy_from_list(list_data):
            """Build list of objects for the given list of dict.

            Args:
                list_data (list[dict])

            Returns:
                list[object]
            """

            # If this is a list, we know this is a dictionary with a single key
            all_objects = []

            for d in list_data:
                name = list(d.keys())[0]
                d_data = list(d.values())[0]
                all_objects.append(craft_obj_hierarchy_from_dict(name, d_data))

            return all_objects

        def craft_obj_hierarchy_from_dict(name, data):
            """Returns the root of the object hierarchy built from the given
            data.

            Args:
                name (str): key name of the object
                data (dict): content of the object

            Returns:
                obj
            """

            # Craft the sub objects
            if isinstance(data, list):
                return craft_obj_hierarchy_from_list(data)

            obj_dict = {}

            for key_name, sub_data in data.items():
                if isinstance(sub_data, dict):
                    d = craft_obj_hierarchy_from_dict(key_name, sub_data)
                elif isinstance(sub_data, list):
                    d = craft_obj_hierarchy_from_list(sub_data)
                else:
                    d = sub_data

                obj_dict[key_name] = d

            if not obj_dict and name not in cls_by_name:
                return None

            return cls_by_name[name](**obj_dict)

        root = ET.fromstring(self.__original_content)
        full_dict = xml_to_dict(root)

        # Craft all the objects
        cls_by_name = {}

        for key, attrs in attr_by_class.items():
            cls_name = "SBoard" + "".join([k.capitalize()
                                           for k in key.split("_")])

            cls = get_class(cls_name, " ".join(attrs))
            cls_by_name[key] = cls

        obj = craft_obj_hierarchy_from_dict(root.tag, full_dict)
        assert isinstance(obj, cls_template.SBoardProject), (type(obj), obj)

        self.__root_node = obj

    @property
    def root(self):
        return self.__root_node
