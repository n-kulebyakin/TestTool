# =========================================
# ==____________Command_reader___________==
# =========================================

import re
from copy import deepcopy

WORD_PATTERN = r'(?:[\w.-]|".*")+'


def get_line_data(line):
    """
    Строка разбивается на слова в соответствии с шаблоном
    и исключаются закомментированные строки
    """
    match = re.findall(WORD_PATTERN, line)
    if match and "." != match[0][0]:
        return match


def cos_analyse(command_data, out_data):
    """
    Информация о количестве подключений АРМ
    и разграничении зон ответственности
    """
    for line in command_data:
        line = get_line_data(line)

        if line:
            if line[0] in ('End', 'Components', 'Commands'):
                return line[0]
            areas = dict(zip(line[2::2], line[3::2]))
            out_data['COS'][line[0]] = {
                'cos_name': line[1],
                'areas': areas
            }


def save_current_component(current_component, current_section):
    """
    Сохраняем текущий компонент в общее хранилище
    в соответствии с именем объекта и типом компонента
    """
    com_type = current_component["Command"]
    obj = current_component['Parameters']

    # Выбираем параметр для сохранения, если компонент
    # без дополнительных параметров, вставляем пустой
    obj = obj[0] if obj else ""

    # Если тип компонента уже есть в общем хранилище
    # и если для объекта уже присутствуют компоненты
    # добавляем к предыдущим,
    # если нет создаём новую запись
    if com_type in current_section:
        if obj in current_section[com_type]:
            current_section[com_type][obj].append(deepcopy(current_component))
            return
        current_section[com_type][obj] = [deepcopy(current_component), ]
        return
    current_section[com_type] = {obj: []}
    current_section[com_type][obj].append(deepcopy(current_component))


def components_analyse(command_data, out_data):
    """
    Функция анализа компонентов
    """

    # Шаблон структуры данных объекта
    current_component_temp = {
        "Command": "",
        "Route": "",
        "Parameters": [],
        "Areas": [],
        "Shared": "",
        "Pretest": [],
        "Manoeuvres": [],
    }

    # Выбор секции для сохранении данных
    current_section = out_data['Components']
    current_component = deepcopy(current_component_temp)
    current_sub_section = None
    for line_num, line in enumerate(command_data):
        line = get_line_data(line)

        if line:
            if line[0] in ('End', 'Commands', 'Component'):
                # Если далее следует новый компонент или
                # другой раздел и компонент не пустой
                # сохраняем его в общее хранилище
                if current_component['Command']:
                    save_current_component(current_component, current_section)

                # Если далее следует не новый компонент,
                # завершаем анализ
                if line[0] != 'Component':
                    return line[0]

                current_sub_section = 'Header'
                current_component = deepcopy(current_component_temp)

                continue

            # Выбор текущего раздела компонента
            if line[0] == 'Main':
                current_sub_section = 'Main'
            elif current_sub_section == 'Header':

                # Если это заголовок, выбираем необходимые данные
                current_component['Command'] = line[1]
                current_component['Route'] = line[0]
                # Заголовок компонента может быть различным.
                # С/без параметров и зон ответственности.
                # Выбираем параметры и зоны исходя из того,
                # что параметры не могут быть числом, а зоны строкой
                route_parameters = [x for x in line[2:-1] if not x.isdigit()]
                areas = [x for x in line[2:-1] if x.isdigit()]

                current_component['Parameters'] = route_parameters
                current_component['Areas'] = areas
                # Последний параметр обязательный
                current_component['Shared'] = line[-1]
                current_sub_section = 'Pretest'
            elif current_sub_section == 'Pretest':
                current_component['Pretest'] = deepcopy(line)
            else:
                current_component['Manoeuvres'].append(deepcopy(line))


def commands_analyse(command_data, out_data):
    # TODO: Добавить разбор составных компонентов
    pass


def command_data_parser(command_data):
    """
    Функция получения данных о командах и компонентах.
    Позволяет получить информацию о зарегистрированных
    командах, компонентах, зонах распределения и
    ответственностей
    """
    current_section = 'Header'
    out_data = {
        'Header': {},
        'Components': {},
        'Commands': {},
        'COS': {},
        'Site_product_name': '',
    }

    for line_num, line in enumerate(command_data):
        line = get_line_data(line)

        if not line:
            # Если строка пустая или закомментированная
            continue

        if line == ['COS', 'interface']:
            current_section = 'COS'

        # Обработка заголовка файла и сохранение
        if current_section == 'Header':
            out_data['Header'][line[0]] = line[1:]
            if line[0] == 'Site_product_name':
                out_data['Site_product_name'] = line[1]
            continue

        # Вызов обработчиков в соответствии с каждой секцией
        if current_section == 'COS':
            current_section = cos_analyse(command_data, out_data)
        if current_section == 'Components':
            current_section = components_analyse(command_data, out_data)

        if current_section == 'Commands':
            commands_analyse(command_data, out_data)
            break

    return out_data


if __name__ == "__main__":
    command_data_path = 'X:/projects/mosgd/MCD/mcd_3/moskva_kazanskaya/eqv/ipu2/ILS2_MCD3_KAZANSKY2-ELCUR/ILS2_MCD3_KAZANSKY2/implementation/input/data/Command_table'
    with open(command_data_path) as int_data:
        parsed_data = command_data_parser(int_data)
        for component in parsed_data['Components']['UPM']['SIC']:
            print(component)
        # print(parsed_data['Components']['UPM']['SIC'])
