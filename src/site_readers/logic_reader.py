# =========================================
# ==____________Logic_reader_____________==
# =========================================

import re
from copy import deepcopy

WORD_PATTERN = r'[#!\w,\-]+'


def get_line_data(line):
    """
    Строка разбивается на слова в соответствии с шаблоном
    и исключаются закомментированные строки
    """
    match = re.findall(WORD_PATTERN, line)
    # Комментарии обозначаются
    # восклицательным знаком в начале строки
    if match and "!" != match[0][0]:
        return match


def line_iteration(input_data):
    """
    Функция итерации по исходным данным.
    Возвращает информацию является
    ли строка концом раздела
    и значение самой строки
    """
    for line in input_data:
        line = get_line_data(line)

        if line:
            if line[0][0] == '#' and line[0] != '#PROGRAM':
                # Если строка содержит значащие данные
                # и обозначает начало нового раздела
                return True, line
            # Возвращаем данные,
            # строка продолжение раздела
            return False, line

    # Если структура файла не корректна
    # и он закончился раньше времени
    # возвращаемся из функции
    return True, None


def all_section_lines(func):
    """
    Декоратор предназначенный для итерации
    по файлу до первой значащей строки
    """

    def wrapped(*args, **kwargs):
        # Получаем первую значащую строку
        input_data = args[0]
        is_end, line = line_iteration(input_data)
        # Пока не дойдём до конца раздела
        # или файла
        while not is_end:
            # Вызываем исходную функцию с новыми данными
            func(*args, line=line)
            # Получаем данные новой строки
            is_end, line = line_iteration(input_data)
        # Если раздел закончился, возвращаем
        # полученную строку для последующего
        # анализа
        return line

    return wrapped


@all_section_lines
def header_analyse(*args, **kwargs):
    """
    Функция анализа заголовка файла
    """
    out_data = args[1]
    line = kwargs['line']
    out_data['Header'][line[0]] = line[1]


@all_section_lines
def global_data_analyse(*args, **kwargs):
    # input_data, out_data, section
    """
    Функция анализа информации объявленной глобально
    """

    section = args[2]
    out_data = args[1]

    # Каждый объявленный параметр уникальный,
    # по этому просто сохраняем в список
    out_data[section].append(kwargs['line'])


def global_param_analyse(input_data, out_data):
    """
    Функция анализа глобальных параметров
    """
    global_data_analyse(input_data, out_data, 'PAR')


def global_var_analyse(input_data, out_data):
    """
    Функция анализа глобальных переменных
    """
    global_data_analyse(input_data, out_data, 'GLOBVAR')


@all_section_lines
def const_analyse(*args, **kwargs):
    """
    Функция анализа констант
    """
    out_data = args[1]
    line = kwargs['line']
    out_data['CONST'][line[0]] = line[1]


@all_section_lines
def obj_types_analyse(*args, **kwargs):
    """
    Функция анализа объявления типов объектов
    """
    out_data = args[1]
    line = kwargs['line']

    out_data['OBJ'][line[0]] = {
        'Name': line[0],
        'num_legs': line[1],
        # Номер объекта соответствует порядку
        # пересчёта в ПО, графа представляет
        # собой тип и порядковый номер
        # через запятую, сохраняем только номер
        'obj_num': line[-1].split(',')[-1]
    }


def get_value_range(value_range):
    """
    Функция получения возможных значений
    """

    # Так как допустимые значения перечисляются
    # как по порядку через запятую, так и диапазоном
    # через дефис, приводим всё к
    # единому формату значений
    values = value_range.split(",")
    out_values = []
    for value in values:
        if '-' in value:
            value = value.split("-")
            # Получаем значения в диапазоне
            # и добавляем ко всем остальным
            new_values = range(int(value[0]), int(value[-1]) + 1)
            out_values += [str(_) for _ in new_values]
        else:
            out_values.append(value)
    return out_values


@all_section_lines
def global_inout_analyse(*args, **kwargs):
    """
    Функция анализа каналов передачи данных
    между объектами
    """
    out_data = args[1]
    line = kwargs['line']

    value_range = get_value_range(line[2])
    # У объекта может быть несколько однотипных
    # каналов для связи с разными объектами,
    # Сохраняем данные в соотвествии
    out_data['CHANNELS'][line[0]] = {
        'Name': line[0],
        'Type': line[1],
        'values': value_range,
    }


@all_section_lines
def obj_g_var_analyse(*args, **kwargs):
    """
    Функция анализа объявления
    глобальных переменных
    внутри объекта
    """
    # TODO: При наличии проекта с глобальными
    #       переменными добавить корректную обработку

    out_data = args[1]
    out_data['#GVAR'] = kwargs['line'][0]


@all_section_lines
def obj_var_analyse(*args, **kwargs):
    """
    Функция анализа объявления
    переменных внутри объекта
    """
    # TODO: При наличии проекта с внутренними
    #       переменными добавить корректную обработку
    out_data = args[1]
    out_data['#VAR'] = kwargs['line'][0]


def obj_channel_analyse(line, obj_data):
    """
    Функция анализа объявления каналов связи
    внутри объекта
    """
    # Если канал не объявлен в объекте
    # ранее, то добавляем его
    if line[0] not in obj_data['#INOUT']:
        obj_data['#INOUT'][line[0]] = {}
    # Сохраняем информацию о канале
    # указывая его номер в качестве ключа
    obj_data['#INOUT'][line[0]][line[1]] = {
        'init': line[2],
        'priority': line[3],
    }


def obj_own_analyse(line, obj_data):
    """
    Функция анализа объявления локальных
    переменных
    """
    obj_data['#OWN'][line[0]] = {
        'type': line[1],
        'values': line[2],
        'init': line[3],
        'priority': line[4],
    }


def obj_in_out_analyse(line, obj_data, key):
    """
    Функция анализа объявления входных
    и выходных переменных увязки
    с внешними устройствами
    """
    obj_data[key][line[0]] = {
        'type': line[1],
        'values': line[2],
        'init': line[3],
        'sub_type': line[4],
    }


def obj_in_analyse(line, obj_data):
    """
    Функция анализа объявления входных
    переменных увязки
    с внешними устройствами
    """
    obj_in_out_analyse(line, obj_data, '#IN')


def obj_out_analyse(line, obj_data):
    """
    Функция анализа объявления выходных
    переменных увязки
    с внешними устройствами
    """
    obj_in_out_analyse(line, obj_data, '#OUT')


def obj_equ_analyse(line, obj_data):
    """
    Функция анализа внутренних переменных
    """
    # TODO: Добавить разбор переменных
    #       со сбором информации о
    #       значении, условиях,
    #       влиянии на другие переменные
    #       используемые данные
    pass


def obj_analyse(input_data, out_data, obj_type):
    """
    Функция анализа объекта
    """

    # Объявлением структуру данных объекта
    obj_data = {
        'Type': obj_type,
        '#GVAR': [],
        '#INOUT': {},
        '#VAR': [],
        '#OWN': {},
        '#IN': {},
        '#OUT': {},
        '#EQU': {},
    }

    # Сохраняем функции обработчики в
    # соответствии с разделом
    analyse_func = {
        '#GVAR': obj_g_var_analyse,
        '#INOUT': obj_channel_analyse,
        '#VAR': obj_var_analyse,
        '#OWN': obj_own_analyse,
        '#IN': obj_in_analyse,
        '#OUT': obj_out_analyse,
        '#EQU': obj_equ_analyse,
    }

    sub_section = None
    for line in input_data:
        line = get_line_data(line)
        if line:
            # Если дошли до конца файла или до
            # следующего объекта сохраняем информацию
            # и выходим из функции
            if line == '#END' or line[0][1:] in out_data['OBJ']:
                out_data[obj_type[0][1:]] = deepcopy(obj_data)
                # Возвращаем из функции строку,
                # так как она может содержать имя
                # следующего объекта
                return line
            # Если встречается знак #,
            # то изменяем текущую подсекцию
            if line[0][0] == '#':
                sub_section = line[0]
                continue
            analyse_func[sub_section](line, obj_data)


def log_objs_analyse(input_data, out_data, last_line):
    """
    Функция поочерёдного анализа всех объектов
    """
    # Поочерёдно анализируем каждый объект
    # пока не достигнем конца файла
    while last_line and last_line != '#END':
        last_line = obj_analyse(input_data, out_data, last_line)


def logic_analyse(input_data):
    """
    Функция анализа данных логики
    """

    # Подготавливаем общую структуру данных
    out_data = {
        'Header': {},
        'PAR': [],
        'CONST': {},
        'OBJ': {},
        'CHANNELS': {},
        'GLOBVAR': [],

    }

    # Разделы файла жёстко закреплены.
    # При отсутствии данных внутри раздела
    # объявление самих разделов обязательно,
    # по этому по очереди анализируем каждый
    # раздел

    header_analyse(input_data, out_data)
    global_param_analyse(input_data, out_data)
    const_analyse(input_data, out_data)
    obj_types_analyse(input_data, out_data)
    global_var_analyse(input_data, out_data)
    last_line = global_inout_analyse(input_data, out_data)
    log_objs_analyse(input_data, out_data, last_line)

    return out_data


def read_logic(input_file):
    """
    Функция чтения файла логики с
    его последующим анализом
    """
    with open(input_file) as input_data:
        return logic_analyse(input_data)


def get_data_from_logic(obj_type, data_type, logic_data, sub_type):
    """
    Функция получения данных логического
    объекта из логики
    """

    # Если запрошенного типа нет в логике
    # либо нет нужного типа данных внутри
    # объекта возвращаем пустой список
    if obj_type not in logic_data or data_type not in logic_data[obj_type]:
        return []

    # Получаем все данные логического объекта
    params = logic_data[obj_type][data_type]

    # Выбираем данные соответствующего подтипа
    params = [
        x for x in params
        if params[x]["sub_type"].startswith(sub_type)
    ]

    return params


def get_ibits_list(obj_type, logic_data):
    """
    Функция получения списка индивидуализаций
    """
    return get_data_from_logic(obj_type, "#IN", logic_data, "STATIC")


def get_checks(obj_type, logic_data):
    """
    Функция получения списка интерфейсных входов
    """
    return get_data_from_logic(obj_type, "#IN", logic_data, "CHECK,CHC")


def get_ofw(obj_type, logic_data):
    """
    Функция получения списка приказов
    передачи информации между
    логическими объектами
    """
    return get_data_from_logic(obj_type, "#OUT", logic_data, "CONTROL,CTFW")


def get_orders(obj_type, logic_data):
    """
    Функция получения списка приказов
    на интерфейсные объекты
    """
    return get_data_from_logic(obj_type, "#OUT", logic_data, "CONTROL,CTRL")


def get_status(obj_type, logic_data):
    """
    Функция получения списка индикаций
    """
    return get_data_from_logic(obj_type, "#OUT", logic_data, "STATUS,STAS")


def get_logical_type_names(logic_data):
    """
    Функция получения списка логических типов
    """
    return list(logic_data["OBJ"].keys())
