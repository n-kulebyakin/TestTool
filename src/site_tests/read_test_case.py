import os
import xml.etree.cElementTree as ET

EVENT_DEF = {
    "execGoSeconds": "{0}/break seconds {1}\n{0}/go\n",
    "execGoCycles": "{0}/break after {1}\n{0}/go\n",
    "calcTraceOn": "{0}/display +\n",
    "ilsCheckpointSave": "{0}/save {1}\n",
    "ilsCheckpointRead": "{0}/queue clear\n{0}/open {1}.cp\n{0}/break steady\n{0}/go\n",
    "yardSetStatusTrySeconds": "{0}/yard {2} try_set {3}\n{0}/break seconds {1}\n{0}/go\n",
    "yardSetStatusTryCycles": "{0}/yard {2} try_set {3}\n{0}/break after {1}\n{0}/go\n",
    "yardSetStatusTry": "{0}/yard {1} try_set {2}\n{0}/break steady\n{0}/go\n",
    "yardSimLock": "{0}/persistent + {1}\n",
    "yardSimUnlock": "{0}/persistent - {1}\n",
}

EVENT_DEF_WITH_FREE_PARAMS = {
    "cosCmd": "{0}/pcmd {2}\n{0}/break steady\n{0}/go\n",
    "cosCmdSeconds": "{0}/pcmd {2}\n{0}/break seconds {1}\n{0}/go\n",
    "cosCmdCycles": "{0}/pcmd {2}\n{0}/break after {1}\n{0}/go\n",
}

NO_TRANSLATED_EVENTS = {
    "ilsInit": "",
    "ilsInitCurrent": "",
    "ilsLoad": "",
    "ilsLoadCurrent": "",
}


def parse_test_case(test_elem):
    out_events = []
    for event in test_elem.findall("./*/Event"):
        event = event.text
        if not event:
            continue
        event = event.strip().split(" ")
        if not event:
            continue
        if event[0] in EVENT_DEF:
            event_str = EVENT_DEF[event[0]].format(*event[1:])
        elif event[0] in EVENT_DEF_WITH_FREE_PARAMS:
            event = event[0:3] + [" ".join(event[3:])]
            event_str = EVENT_DEF_WITH_FREE_PARAMS[event[0]].format(*event[1:])
        elif event[0] in NO_TRANSLATED_EVENTS:
            continue
        else:
            print("Event not in EV_DEF " + " ".join(event))
            continue
        out_events += event_str.split("\n")
    return out_events


def read_test_file(path_to_file):
    test_cases = {}
    if path_to_file and os.path.exists(path_to_file):
        xml_tree = ET.ElementTree(file=path_to_file)
        root = xml_tree.getroot()

        for elem in root.findall("./Function/TestSuite/TestCase/Test"):
            test_events = parse_test_case(elem)
            test_id = elem.attrib["id"]
            test_cases[test_id] = test_events
    return test_cases

