# -*- coding: utf-8 -*-

def read_logic(input_file=None):
    with open(input_file) as input_data:
        lines = input_data.read().replace(';', '').replace('\r', '').split('\n')
        logic_data = {}
        key = ''
        object_key = ''

        for counter, line in enumerate(lines):
            if len(line) < 2 or line[0] == '!':
                continue
            if line[0:8] == '#PROGRAM':
                logic_data['#PROGRAM'] = line[9:-1]
            elif line in ('#PAR', '#CONST', '#OBJ', '#GLOBVAR',
                          '#INOUT', '#GVAR', '#OWN', '#EQU', '#IN', '#OUT'):
                key = line
                if line in ('#PAR', '#GLOBVAR'):
                    logic_data[key] = []
                elif line in ('#CONST', '#OBJ', '#INOUT', '#OWN', '#IN', '#OUT'):
                    if object_key:
                        logic_data[object_key][key] = {}
                    else:
                        logic_data[key] = {}
                elif line in ('#GVAR', '#EQU'):
                    logic_data[object_key][line] = []
            elif line[0] != '#':
                if key == '#PAR':
                    logic_data[key].append(line)
                elif key == '#CONST':
                    const, value = line.split(':')
                    logic_data[key][const] = value
                elif key == '#OBJ':
                    tempData, objNum = line.split(',')
                    name, numLegs, obj_type = tempData.split(':')
                    logic_data[key][name] = {
                        'numLegs': numLegs,
                        'type': obj_type,
                        'objNum': objNum
                    }
                elif key == '#INOUT':
                    line = line.split(':')
                    if object_key:
                        logic_data[object_key][key][line[0]] = {
                            'init': line[1], 'priority': line[2]}
                    else:
                        logic_data[key][line[0]] = {
                            'type': line[1], 'values': line[2]}
                elif key in ('#GVAR', '#EQU'):
                    logic_data[object_key][key].append(line)
                elif key == '#OWN':
                    line = line.split(':')
                    logic_data[object_key][key][line[0]] = {
                        'type': line[1],
                        'values': line[2],
                        'init': line[3],
                        'priority': line[4],
                    }
                elif key in ('#IN', '#OUT'):
                    line = line.split(':')
                    if line[4].count(',') and key == '#IN':
                        sub_type = line[4].split(',')[0]
                        sub_num = line[4].split(',')[-1]
                        logic_data[object_key][key][line[0]] = {
                            'type': line[1],
                            'value': line[2],
                            'init': line[3],
                            'subType': sub_type,
                            'subTypeNum': sub_num,
                        }
                    elif key == '#IN':
                        logic_data[object_key][key][line[0]] = {
                            'type': line[1],
                            'value': line[2],
                            'init': line[3],
                            'subType': line[4],
                        }
                    elif line[4].count(',') == 2:
                        sub_type = line[4].split(',')[0]
                        sub_num = line[4].split(',')[1]
                        min_max = line[4].split(',')[-1]
                        logic_data[object_key][key][line[0]] = {
                            'type': line[1],
                            'value': line[2],
                            'init': line[3],
                            'subType': sub_type,
                            'subTypeNum': sub_num,
                            'minMax': min_max,
                        }
                    elif line[4].count(','):
                        sub_type = line[4].split(',')[0]
                        sub_num = line[4].split(',')[-1]
                        logic_data[object_key][key][line[0]] = {
                            'type': line[1],
                            'value': line[2],
                            'init': line[3],
                            'subType': sub_type,
                            'subTypeNum': sub_num,
                        }
                    else:
                        logic_data[object_key][key][line[0]] = {
                            'type': line[1],
                            'value': line[2],
                            'init': line[3],
                            'subType': line[4],
                        }

            elif '#OBJ' in logic_data and line[1:] in logic_data['#OBJ']:
                logic_data[line[1:]] = {}
                key = line[1:]
                object_key = key
        return logic_data


def get_default_value(i_bit, obj_type, logic_data):
    if i_bit in get_ibit_list(obj_type, logic_data):
        return logic_data[obj_type]['#IN'][i_bit]['init']
    else:
        return -1


def get_value_range(value_range):
    values = value_range.split(',')
    temp = []
    for value in values:
        if value.count('-'):
            value = value.split('-')
            for val in range(int(value[0]), int(value[-1]) + 1):
                temp.append(str(val))
        else:
            temp.append(value)
    return temp


def get_data_from_logic(obj_type, data_type, logic_data, sub_type=None, sub_type_num=None):
    if obj_type not in logic_data or data_type not in logic_data[obj_type]:
        return []

    params = logic_data[obj_type][data_type]

    if sub_type and sub_type_num:
        params = [x for x in params
                             if params[x]['subType'].startswith(sub_type)
                             and params[x]['subTypeNum'].startswith(sub_type_num)]
    elif sub_type_num:
        params = [x for x in params
                  if params[x]['subTypeNum'].startswith(sub_type_num)]
    else:
        params = [x for x in params
                  if params[x]['subType'].startswith(sub_type)]

    return params


def get_ibit_list(obj_type, logic_data):
    return get_data_from_logic(obj_type, '#IN', logic_data, sub_type='STATIC')


def get_checks(obj_type, logic_data):
    return get_data_from_logic(obj_type, '#IN', logic_data, sub_type='CHECK', sub_type_num='CHC')


def get_ofw(obj_type, logic_data):
    return get_data_from_logic(obj_type, '#OUT', logic_data, sub_type_num='CTFW')


def get_orders(obj_type, logic_data):
    return get_data_from_logic(obj_type, '#OUT', logic_data, sub_type_num='CTRL')


def getStatus(obj_type, logic_data):
    return get_data_from_logic(obj_type, '#OUT', logic_data, sub_type_num='STAS')


def get_logical_type_names(logic_data):
    return logic_data['#OBJ'].keys()
