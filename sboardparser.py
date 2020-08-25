
"""
"""


import collections
import keyword
import xml.etree.ElementTree as ET


__author__ = "Paul-Emile Buteau"
__maintainer__ = "Paul-Emile Buteau"


def namedtuple_with_defaults(typename, field_names, default_values=()):
    T = collections.namedtuple(typename, field_names)
    T.__new__.__defaults__ = (None,) * len(T._fields)
    if isinstance(default_values, collections.abc.Mapping):
        prototype = T(**default_values)
    else:
        prototype = T(*default_values)
    T.__new__.__defaults__ = tuple(prototype)
    return T


class SBoardParser(object):
    """Parser of Storyboard Pro .sboard files."""

    xml_version = "1.0"

    def __init__(self, sboard_path):
        self.__sboard_path = sboard_path

    def parse(self):
        attr_by_class = collections.defaultdict(set)
        unspecialized_names = {'column'}

        change_of_name = collections.defaultdict(dict)

        def xml_to_dict(xml_tree_element, parent=None):

            key_ = xml_tree_element.tag

            if key_ in unspecialized_names:
                key_ = parent + "_" + key_

            is_list = len(set(a.tag for a in xml_tree_element)) == 1 \
                and not xml_tree_element.attrib

            if is_list:

                object_list = []

                for a in xml_tree_element:

                    akey = a.tag

                    if akey in unspecialized_names:
                        akey = parent + "_" + akey

                    object_list.append({akey: xml_to_dict(a, parent)})

                return object_list

            # Craft all children data
            data_dict = {a.tag: xml_to_dict(a, key_) for a in xml_tree_element}
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

            cls = namedtuple_with_defaults(cls_name, " ".join(attrs))
            cls_by_name[key] = cls

        return craft_obj_hierarchy_from_dict(root.tag, full_dict)
