# -*- coding: utf-8 -*-
import xml.dom.minidom


def get_x_y_data(node_data):
    if "." in node_data:
        node_data = node_data.split(".")[0]
    else:
        node_data = node_data.split(",")[0]
    return int(node_data)


def read_scene_data(file):
    max_x = 1000
    max_y = 1000

    logical_objects = {}
    rem_2 = None

    doc = xml.dom.minidom.parse(file)
    node = doc.documentElement

    rem_1 = node.getElementsByTagName("ScriptGraphicObject")
    if file[-14:] == "LogicScene.xml":
        rem_2 = node.getElementsByTagName("config")

    for node in rem_1:
        node_items = dict(node.attributes.items())
        obj_name = node_items["object_name"]
        logical_objects[obj_name] = {}

        coord_x = get_x_y_data(node_items["x"])
        coord_y = get_x_y_data(node_items["y"])

        logical_objects[obj_name]["x"] = coord_x
        logical_objects[obj_name]["y"] = coord_y

        if coord_x > max_x:
            max_x = coord_x + 1000
        if coord_y > max_y:
            max_y = coord_y + 500

        for attr in ("m11", "m12", "m21", "m22"):
            logical_objects[obj_name][attr] = int(float(node_items[attr][0:8]))

    if rem_2:
        rem_1 = rem_2[0].getElementsByTagName("scene")
        node_items = dict(rem_1[0].attributes.items())

        logical_objects["sceneWidth"] = int(node_items["fieldWidth"])
        logical_objects["sceneHeight"] = int(node_items["fieldHeight"])

    else:
        logical_objects["sceneWidth"] = max_x
        logical_objects["sceneHeight"] = max_y

    return logical_objects
