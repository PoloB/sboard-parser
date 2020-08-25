
"""
"""


import collections
import keyword
import re
import xml.etree.ElementTree as ET

import cls_factory

__author__ = "Paul-Emile Buteau"
__maintainer__ = "Paul-Emile Buteau"


def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def namedtuple_with_defaults(typename, field_names, default_values=()):
    T = collections.namedtuple(typename, field_names)
    T.__new__.__defaults__ = (None,) * len(T._fields)
    if isinstance(default_values, collections.abc.Mapping):
        prototype = T(**default_values)
    else:
        prototype = T(*default_values)
    T.__new__.__defaults__ = tuple(prototype)
    return T


def get_class(class_name, field_names):

    cls = cls_factory.__dict__.get(class_name)

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
                return self.__data[field_name]

            return property(prop_)
        # Add the field to the known class
        setattr(cls, f, get_property(f))

    return cls


class SBoardParser(object):
    """Parser of Storyboard Pro .sboard files."""

    xml_version = "1.0"

    def __init__(self, sboard_path):
        self.__sboard_path = sboard_path

    def parse(self):
        """Returns the project parsed.

        Returns:
            SBoardProject
        """
        attr_by_class = collections.defaultdict(set)
        unspecialized_names = {'column'}

        change_of_name = collections.defaultdict(dict)

        def xml_to_dict(xml_tree_element, parent=None):

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

        def craf_obj_hierarchy_from_list(list_data):

            # If this is a list, we know this is a dictionary with a single key
            all_objects = []

            for d in list_data:
                name = list(d.keys())[0]
                d_data = list(d.values())[0]
                all_objects.append(craft_obj_hierarchy_from_dict(name, d_data))

            return all_objects

        def craft_obj_hierarchy_from_dict(name, data):

            # Craft the sub objects
            if isinstance(data, list):
                return craf_obj_hierarchy_from_list(data)

            obj_dict = {}

            for key_name, sub_data in data.items():
                if isinstance(sub_data, dict):
                    d = craft_obj_hierarchy_from_dict(key_name, sub_data)
                elif isinstance(sub_data, list):
                    d = craf_obj_hierarchy_from_list(sub_data)
                else:
                    d = sub_data

                obj_dict[key_name] = d

            if not obj_dict and name not in cls_by_name:
                return None

            return cls_by_name[name](**obj_dict)

        root = ET.parse(self.__sboard_path).getroot()
        full_dict = xml_to_dict(root)

        # Craft all the objects
        cls_by_name = {}

        for key, attrs in attr_by_class.items():
            cls_name = "SBoard" + "".join([k.capitalize()
                                           for k in key.split("_")])

            cls = get_class(cls_name, " ".join(attrs))
            cls_by_name[key] = cls

        obj = craft_obj_hierarchy_from_dict(root.tag, full_dict)
        assert isinstance(obj, cls_factory.SBoardProject), (type(obj), obj)

        return obj