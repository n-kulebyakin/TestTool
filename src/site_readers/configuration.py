import os
import re

WORD_PATTERN = r'(?:[\w^.-:-~{}>])+'
PRODUCT_TYPES = ('File',
                 'Directory',
                 'Component',
                 'Replacement',
                 'Resource',
                 'Semiproduct',
                 'Subcomponent',
                 'Subproduct')

ADAPT_PATH = 'X:/eqv/adapt/'


def line_analyse(line):
    return re.findall(WORD_PATTERN, line)


def save_path(temp_product, out_data):
    product_data = [x for x in temp_product if x in PRODUCT_TYPES]
    if not product_data:
        temp_product.clear()
        return
    product_name = temp_product[product_data[0]]

    if '-' in product_name:
        product_version = product_name.split('-')[-1]
        product_name = product_name.split('-')[0]
    else:
        product_version = '0'
    out_data[product_name] = {'version': product_version}
    for key in temp_product:
        out_data[product_name][key] = temp_product[key]
    temp_product.clear()


def read_config_info(file_path, adapt_path=ADAPT_PATH):
    out_data = {}
    with open(file_path) as input_file:
        path_to_ils = file_path[0:file_path.rfind('/')]
        for line in input_file:
            line = line_analyse(line)
            if not line:
                continue
            if line[0] != '.' and 'Path:' in line:
                path = line[1][2:]
                temp_component = {}
                for line in input_file:
                    line = line_analyse(line)
                    if not line or line[0] in ('{', '.', ''):
                        continue
                    elif line[0] in ('}', 'Checksum_A:', 'Checksum_B:'):
                        if temp_component:
                            temp_component['Path'] = path_to_ils + '/' + path
                            save_path(temp_component, out_data)
                        break
                    else:

                        if line[0] != '->' and temp_component:
                            temp_component['Path'] = path_to_ils + '/' + path
                            save_path(temp_component, out_data)
                        for key in [x for x in line if x.count(':')]:
                            if key != line[-1]:
                                temp_component[key[:-1]] = line[line.index(key) + 1]
            elif line[0] == '.':
                continue
            elif len(line) == 2:
                out_data[line[0]] = line[1]

    target_keys = [x for x in out_data
                   if 'Path' in out_data[x]
                   and out_data[x]['Path'].count('reference')]
    for key in target_keys:
        component = (adapt_path + key + '/' + key + '-' +
                     out_data[key]['version'] + '/' + key + '/ConfigInfo.CI')
        if os.path.exists(component):
            temp_data = read_config_info(component)
            temp_data.update(out_data)
            out_data = temp_data
    return out_data


def get_file_with_key(config_data, key):
    for file in config_data:
        if 'Key' in config_data[file]:
            if key in config_data[file]['Key'].split(';'):
                return file


if __name__ == "__main__":
    test_path = ('X:/projects/mosgd/MMK/serebryanyi_bor/eqv' +
                 '/ipu7/ILS2_RF_SBO-4M2CUR/ILS2_RF_SBO/ConfigInfo.CI')
    configInfoOfProject = read_config_info(test_path)
    for key in ('CommandTable', 'IntData', 'ILL_STERNOL_FILE', 'CBI'):
        print(get_file_with_key(configInfoOfProject, key))
    print(configInfoOfProject.keys())
