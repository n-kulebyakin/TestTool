def log_file_parser(lines):
    variables = {}
    lines = [line.split(':')[1].strip().split(' ') for line in lines
             if line and line[0] == '!']

    for line in lines:
        temp = line[0].split('.')
        if line.count('=>'):
            temp2 = line[2].split('.')
            obj = temp2[0]
            variable = temp2[1]
            temp2 = line[3].split('(')
            new_value = temp2[0]
            old_value = temp2[1][:-1]
        else:
            obj = temp[0]
            variable = temp[1]
            temp = line[2].split('(')
            new_value = temp[0]
            old_value = temp[1][:-1]
            if obj not in variables:
                variables[obj] = {variable: {'value': new_value,
                                             'old_value': old_value}}
            else:
                variables[obj][variable] = {'value': new_value,
                                            'old_value': old_value}
        if line.count('=>'):
            if obj not in variables:
                variables[obj] = {variable: {'value': new_value,
                                             'old_value': old_value}}
            else:
                variables[obj][variable] = {'value': new_value,
                                            'old_value': old_value}
            obj, variable = line[0].split('.')
            if obj not in variables:
                variables[obj] = {variable: {'valueOUT': new_value,
                                             'old_valueOUT': old_value}}
            else:
                if variable not in variables[obj]:
                    variables[obj][variable] = {'valueOUT': new_value,
                                                'old_valueOUT': old_value}
                else:
                    variables[obj][variable]['valueOUT'] = new_value
                    variables[obj][variable]['old_valueOUT'] = old_value
    return (variables)


def object_variable_parser(lines, obj=''):
    variables = {}
    for line in lines:
        line = line.replace('\n', '').replace(' = ', '=').strip().split(' ')
        line = [x for x in line if x.count('=')]
        for variable in line:
            if variable[0] == '\\':
                variable = variable[2:]
            value = variable.split('=')[1]
            variable = variable.split('=')[0]
            if variable.count('.'):
                obj = variable.split('.')[0]
                variable = variable.split('.')[-1]
            if variable.count('('):
                in_value, out_value = value.split(',')
                if obj not in variables:
                    variables[obj] = {variable: {'valueOUT': out_value,
                                                 'value': in_value}}
                else:
                    variables[obj][variable] = {'valueOUT': out_value,
                                                'value': in_value}
            else:
                if obj not in variables:
                    variables[obj] = {variable: {'value': value}}
                else:
                    variables[obj][variable] = {'value': value}
    return variables
