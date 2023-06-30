from copy import deepcopy


def line_replacer(line, param="intData"):
    line = line.replace("\r", "").replace("\t", " ").replace("\n", "")
    if param == "intData":
        while line.count("  "):
            line = line.replace("  ", " ")
    else:
        line = line.replace(" ", "")
    if (
            len(line) < 2
            or line[0] == "."
            or line.count("General data")
            or line.count("Logical objects")
            or line.count("COSinterface")
            or line.count("Components")
            or line.count("Areaauthority")
            or line.count("ETHERNET port")
            or line.count("COS connection")
    ):
        return False
    else:
        return line


# =========================================
# ==_________Command_table_reader________==
# =========================================


def add_temp_component(parsed_data, current_obj):
    if current_obj["Command"] in parsed_data["Components"].keys():
        if (
                current_obj["Parameters"][0]
                not in parsed_data["Components"][current_obj["Command"]].keys()
        ):

            parsed_data["Components"][current_obj["Command"]][
                current_obj["Parameters"][0]
            ] = [
                deepcopy(current_obj),
            ]
        else:

            parsed_data["Components"][current_obj["Command"]][
                current_obj["Parameters"][0]
            ].append(deepcopy(current_obj))
    else:
        parsed_data["Components"][current_obj["Command"]] = {
            current_obj["Parameters"][0]: [
                deepcopy(current_obj),
            ]
        }

    parsed_data["Seq"].append(
        (deepcopy(current_obj["Command"]), deepcopy(current_obj["Parameters"]))
    )
    current_obj["Command"] = ""
    current_obj["Maneuvres"][:] = []


def component_parser(line, key, parsed_data, current_obj):
    line = line_replacer(line, "comTable")
    if not line:
        return
    line = [x for x in line.split("|")]
    if line[0] == "Component" or line[0] == "Commands":
        add_temp_component(parsed_data, current_obj)
        current_obj = {
            "Command": "",
            "Route": "",
            "Parameters": [],
            "Areas": [],
            "Shared": "",
            "Pretest": [],
            "Maneuvres": [],
        }
        key[0] = line[0]
        if line[0] == "Commands":
            return True
    elif not current_obj["Command"]:
        current_obj["Route"] = line[2]
        current_obj["Command"] = line[3]
        current_obj["Parameters"] = line[5:-5]
        current_obj["Areas"] = line[-4]
        current_obj["Shared"] = line[-3]
        key[0] = "Pretest"
        return False
    elif key[0] == "Pretest":
        current_obj["Pretest"] = line[2:-2]
        key[0] = "Maneuvres"
    elif key[0] == "Maneuvres" and line[0] != "Mainobjects":
        current_obj["Maneuvres"].append(
            [line[2], line[3], line[4], "", line[-5], line[-4], line[-3]]
        )


def add_current_command(parsed_data, current_command):
    if current_command["Command"] in parsed_data["Commands"].keys():
        if (
                current_command["Parameters"][0]
                not in parsed_data["Commands"][current_command["Command"]].keys()
        ):
            parsed_data["Commands"][current_command["Command"]][
                current_command["Parameters"][0]
            ] = [
                deepcopy(current_command),
            ]
        else:
            parsed_data["Commands"][current_command["Command"]][
                current_command["Parameters"][0]
            ].append(deepcopy(current_command))
    else:
        parsed_data["Commands"][current_command["Command"]] = {
            current_command["Parameters"][0]: [
                deepcopy(current_command),
            ]
        }
    current_command["Command"] = ""
    current_command["Route"][:] = []
    current_command["Parameters"][:] = []


def command_parser(line, key, parsed_data, current_command):
    line = line_replacer(line, "comTable")
    if not line:
        return
    line = [x for x in line.split("|")]
    if line[0] == "Endofcommandtable" or line[0] == "Command":
        add_current_command(parsed_data, current_command)
        if line[0] == "Endofcommandtable":
            key[0] = "End"
            return True
    elif not current_command["Command"]:
        current_command["Command"] = line[2]
        current_command["Parameters"] = line[4:]
    else:
        current_command["Route"].append([line[2]] + line[4:])


def command_table_parser(command_table):
    parsed_data = {
        "Components": {},
        "COS_interface": {},
        "Commands": {},
        "Seq": [],
    }
    line_counter = -1
    key = ["COS_interface"]
    current_component = {
        "Command": "",
        "Route": "",
        "Parameters": [],
        "Areas": [],
        "Shared": "",
        "Pretest": [],
        "Maneuvres": [],
    }
    tempCommand = {"Command": "", "Parameters": [], "Route": []}
    for line in command_table:
        line_counter += 1
        line = line_replacer(line, "comTable")
        if not line:
            continue
        if ":" in line:
            line = line.split(":")
            parsed_data[line[0]] = line[1][1:-1]
            continue
        line = [x for x in line.split("|") if x]
        if line[0] == "Endofcommandtable":
            if tempCommand["Route"]:
                command_parser(line, key, parsed_data, tempCommand)
            break
        if key[0] == "Component" or line[0] == "Component":
            for line in command_table:
                line_counter += 1
                if component_parser(line, key, parsed_data, current_component):
                    break
        elif key == ["COS_interface"]:
            areas = line[2].split(",")
            areas = {
                x[0: x.find("(")]: x[x.find("(") + 1: x.find(")")]
                for x in areas
            }
            parsed_data["COS_interface"][line[0]] = {
                "name": line[1],
                "areas": areas,
            }
        elif key == ["Commands"]:
            for line in command_table:
                line_counter += 1
                if command_parser(line, key, parsed_data, tempCommand):
                    break
    return parsed_data


# =========================================
# ==______Interlocking_data_reader_______==
# =========================================

def add_current_object(parsed_data, current_object, line):
    if "Name" not in current_object:
        return
    parsed_data["Logical_objects"][current_object["Name"]] = deepcopy(current_object)

    current_object.clear()
    if line[0] == "External":
        current_object["Name"] = line[2]
        current_object["Type"] = line[4]
        current_object["legs"] = {}
        current_object["individualizations"] = {}
        current_object["orders"] = {}
        current_object["status"] = {}
        current_object["orders"] = {}
        current_object["indication"] = {}
        current_object["command"] = {}
        current_object["telegram"] = {}
        current_object["ITI"] = []
        current_object["ofw"] = {}
        current_object["Check"] = []
        current_object["incoming"] = []


def add_free_wired_checks(parsed_data, object_name, ils_id=""):
    if "-" in object_name:
        ils_id = object_name.split("-")[-1]
    for ofw in parsed_data[object_name]["ofw"]:
        for logicalObject, logicalCheck in zip(
                parsed_data[object_name]["ofw"][ofw]["ipu"][::2],
                parsed_data[object_name]["ofw"][ofw]["ipu"][1::2],
        ):
            if ils_id:
                logicalObject = logicalObject + "-" + ils_id
            parsed_data[logicalObject]["status"][logicalCheck] = {
                "value": 0,
                "ipu": object_name + "." + ofw,
            }


def attributes_parser(line, key, parsed_data, temp_object):
    line = line_replacer(line)
    if not line:
        return
    line = line.replace(" = ", "=").replace(" =", "=").replace("= ", "=")
    line = [x for x in line.split(" ") if x]
    if line[0] in (
            "Order",
            "Status",
            "Indication",
            "External",
            "IPU",
            "Individualizations",
            "End",
            "Telegram",
            "Check",
            "Command",
    ):
        key[0] = line[0]
        if line[0] == "External" or line[0] == "IPU" or line[0] == "End":
            add_current_object(parsed_data, temp_object, line)
            if line[0] == "External":
                key[0] = "Leg:"
            return

    elif key[0] == "Leg:" and line[0] != "Leg:" or key[0] == "External":
        temp_object["legs"][line[0]] = {
            "neighbour": line[1],
            "neigbourLeg": line[2],
        }
    elif key == ["Individualizations"]:
        for ibit in line:
            name, value = ibit.split("=")
            temp_object["individualizations"][name] = value
    elif key == ["Order"]:
        if line.count("|"):
            return
        if len(line) > 2:
            if line[0] in temp_object["ofw"]:
                temp_object["ofw"][line[0]]["ipu"] += line[1:]
            else:
                temp_object["ofw"][line[0]] = {"ipu": line[1:], "value": ""}
        else:
            temp_object["orders"][line[0]] = {"ipu": line[1], "value": ""}
    elif key == ["Status"]:
        temp_object["status"][line[0]] = {"ipu": line[1], "value": ""}
    elif key == ["Indication"]:
        temp_object["indication"][line[0]] = line[1]
    elif key == ["Command"]:
        if line[0] in temp_object["command"]:
            temp_object["command"][line[0]][line[1]] = line[2:]
        else:
            temp_object["command"][line[0]] = {line[1]: line[2:]}
    elif key == ["Telegram"]:
        temp_object["ITI"].append(line)
    elif key == ["Check"]:
        temp_object["Check"].append(line)

    return


def interlocking_data_parser(interlocking_data):
    line_counter = 0
    parsed_data = {
        "Site Version": [],
        "Logical_objects": {},
        "IPU_objects": {},
        "COS_objects": {},
        "Seq": [],
    }
    current_object = {}
    key = ["Name", ]
    for line in interlocking_data:
        line_counter += 1
        line = line_replacer(line)
        if not line:
            continue

        elif (
                line.count(":")
                and line.count("External") == 0
                and line.count("Leg:") == 0
        ):
            line = line.split(":")
            if line[0].lstrip().rstrip() == "Site Version":
                parsed_data["Site Version"].append(line[-1].lstrip())
            else:
                parsed_data[line[0].lstrip()] = (
                    line[1].lstrip().replace(""", "")
                )
            continue
        if key[0] not in ("Name", "COS", "IPU") and not line.count("Leg:"):
            attributes_parser(line, key, parsed_data, current_object)
            continue
        line = [x for x in line.split(" ") if x]
        if line[0] in ("COS", "IPU"):
            key[0] = line[0]
            continue
        elif line[0] == "End":
            break
        elif key[0] == "IPU":
            parsed_data["IPU_objects"][line[0]] = {
                "Yard": line[1],
                "Type": line[2],
                "COS": line[3],
                "Consists": line[4:],
            }
        elif key[0] == "COS":
            parsed_data["COS_objects"][line[0]] = {
                "Type": line[1],
                "Number": line[2],
            }
        elif (
                "Name" not in current_object
                and key[0] not in ("COS", "End", "IPU", "Leg:")
                or line.count("External")
                and key[0] != "Name"
        ):
            current_object = {
                "Name": line[2],
                "Type": line[4],
                "legs": {},
                "individualizations": {},
                "orders": {},
                "status": {},
                "indication": {},
                "ITI": [],
                "ofw": {},
                "incoming": {},
                "telegram": {},
                "Check": [],
                "command": {},
            }
            key[0] = "Leg:"
        else:
            for line in interlocking_data:
                line_counter += 1
                if attributes_parser(line, key, parsed_data, current_object):
                    break
    objects_with_ofw = [
        x
        for x in parsed_data["Logical_objects"]
        if parsed_data["Logical_objects"][x]["ofw"]
    ]
    for logical_object in objects_with_ofw:
        add_free_wired_checks(parsed_data["Logical_objects"], logical_object)
    return parsed_data
