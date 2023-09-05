import re

WORD_LOG_PATTERN = r'[!\w]+'
WORD_SIM_PATTERN = r'[\w(),.]+'


def object_variable_parser(lines, obj_name, pattern=WORD_SIM_PATTERN):
    """
    Функция анализа информации переменных объекта,
    полученных напрямую от имитатора
    """
    # Добавляем запрошенный объект в хранилище
    out_data = {obj_name: {}}
    for line in lines:
        # Перебираем все полученные строки
        # разбиваем на пары переменная - значение
        match = re.findall(pattern, line)
        for variable, value in zip(match[::2], match[1::2]):
            # Проверяем наличие названия нового объекта
            # в значении переменной
            if '.' in variable:
                obj_name, variable = variable.split('.')
            if ',' in value:
                # Для значений каналов передачи данных
                # разделяем значения на входящее и
                # исходящее
                in_value, out_value = value.split(",")
                out_data[obj_name][variable] = {'value': in_value,
                                                'value_out': out_value}
            else:
                out_data[obj_name][variable] = {'value': value}

    return out_data


def get_lines(input_data, pattern=WORD_LOG_PATTERN):
    """
    Функция генератор для чтения лог файла
    """

    # По строчно проходим по файлу,
    # если строка содержит
    # информацию о переменных и не является
    # предварительными пересчётами
    # возвращаем её

    for line in input_data:
        match = re.findall(pattern, line)
        if match and match[0] == '!' and 'P' not in match:
            yield match


def log_data_parser(input_data):
    """
    Функция анализа лог файла
    """
    out_data = {}

    for line in get_lines(input_data):
        if not line:
            continue

        # Если названия станции нет в хранилище,
        # то добавляем его
        if line[1] not in out_data:
            out_data[line[1]] = {}
        # Если переменной нет на станции,
        # то добавляем её
        if line[4] not in out_data[line[1]]:
            out_data[line[1]][line[4]] = {}
        # Если строка содержит информацию о
        # канале передачи данных, то обрабатываем
        # её отдельно
        if line[-1] == 'channel':
            # Каналов передачи может быть несколько,
            # определяем нужный
            channel_name = f'{line[5]}({line[6]})'

            value = {'value_out': line[10], 'old_value_out': line[11]}
            out_data[line[1]][line[4]][channel_name] = value
        else:
            value = {'value': line[6], 'old_value': line[7]}
            out_data[line[1]][line[4]][line[5]] = value
    return out_data
