# =========================================
# ==___________Int_data_reader___________==
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


def leg_analyse(line, current_obj):
    """
    Информация о соседних объектах и их соединении
    собирается для каждого вывода объекта
    """
    current_obj['legs'][line[0]] = {
        "neighbour": line[1],
        "neighbour_leg": line[2],
    }


def individ_analyse(line, current_obj):
    """
    Все индивидуализации расположенные в строке
    собираются в пары ИМЯ:ЗНАЧЕНИЕ
    """
    i_data = dict(zip(line[::2], line[1::2]))
    current_obj["individualizations"].update(i_data)


def ofw_analyse(line, current_obj):
    """
    Информация передаваемая методом 'свободного монтажа'
    с одного приказа может передаваться на несколько объектов
    вся информация суммируется для каждого приказа
    """
    if line[0] in current_obj["ofw"]:
        current_obj["ofw"][line[0]]["ipu"] += line[1:]
    else:
        current_obj["ofw"][line[0]] = {"ipu": line[1:], "value": ""}


def order_analyse(line, current_obj):
    """
    Информация передаваемая на контроллеры
    """
    current_obj["orders"][line[0]] = {"ipu": line[1], "value": ""}


def status_analyse(line, current_obj):
    """
    Информация получаемая от контроллеров
    """
    current_obj["status"][line[0]] = {"ipu": line[1], "value": ""}


def indication_analyse(line, current_obj):
    """
    Информация передаваемая на АРМ
    """
    current_obj["indication"][line[0]] = line[1]


def automaton_analyse(line, current_obj):
    """
    Дополнительные параметры автокоманд
    """
    if line[0] in current_obj["command"]:
        current_obj["command"][line[0]][line[1]] = line[2:]
    else:
        current_obj["command"][line[0]] = {line[1]: line[2:]}


def telegram_analyse(line, current_obj):
    """
    Телеграммы обмена данными с соседними ЦП
    """
    current_obj["ITI"].append(line)


def connection_check_analyse(line, current_obj):
    """
    Индикация наличия соединений с соседними ЦП
    """
    current_obj["Check"].append(line)


def log_objects_analyse(interlocking_data, out_data):
    """
    Функция анализа информации объекта и записи
    в итоговый словарь
    """

    # Шаблон структуры данных объекта
    current_object_temp = {
        "Name": '',
        "Type": '',
        "legs": {},
        "individualizations": {},
        "orders": {},
        "status": {},
        "indication": {},
        "ITI": [],
        "ofw": {},
        "incoming": {},
        "telegram": [],
        "command": {},
        "Check": [],
    }

    # Функции анализа атрибутов объекта
    # собраны для удобства вызова
    analyse_func = {
        'Leg': leg_analyse,
        'Individ': individ_analyse,
        'Ofw': ofw_analyse,
        'Order': order_analyse,
        'Status': status_analyse,
        'Indication': indication_analyse,
        'Command': automaton_analyse,
        'Telegram': telegram_analyse,
        'Check': connection_check_analyse,
    }
    current_section = out_data['Logical_objects']

    current_object = deepcopy(current_object_temp)
    current_sub_section = None
    for line_num, line in enumerate(interlocking_data):
        line = get_line_data(line)

        if line:
            if line[0] in ('End', 'COS', 'IPU', 'External'):
                # Если раздел объекта закончен и предыдущий объект
                # не пустой, то сохранением его данные
                if current_object['Name']:
                    current_section[current_object['Name']] = deepcopy(current_object)
                # Если далее следует не новый объект, то завершаем анализ
                if line[0] != 'External':
                    return line[0]

                # Обнуляем текущую информацию об объекте
                current_object = deepcopy(current_object_temp)
                current_object['Name'] = line[2]
                current_object['Type'] = line[4]
                continue

            # Выбор подраздела объекта по заголовку
            if line[0] == 'Leg':
                current_sub_section = 'Leg'
            elif line[0] == 'Individualizations':
                current_sub_section = 'Individ'
            elif line[0] == 'Order':
                # Заголовки одинаковые, но информация различается
                # для передачи в контроллеры и в другие объекты
                if current_sub_section != 'Ofw':
                    current_sub_section = 'Ofw'
                else:
                    current_sub_section = 'Order'
            elif line[0] == 'Status':
                current_sub_section = 'Status'
            elif line[0] == 'Indication':
                current_sub_section = 'Indication'
            elif line[0] == 'Command':
                current_sub_section = 'Command'
            elif line[0] == 'Telegram':
                current_sub_section = 'Telegram'
            elif line[0] == 'Check':
                current_sub_section = 'Check'
            else:
                # Обработка строки в соответствии с текущей подсекцией
                current_func = analyse_func[current_sub_section]
                current_func(line, current_object)


def cos_objects_analyse(interlocking_data, out_data):
    """
    Функция анализа индикационных объектов
    """
    for line in interlocking_data:
        line = get_line_data(line)
        if line:
            if line[0] == 'End':
                return line[0]

            out_data['COS_objects'][line[0]] = {
                "Type": line[1],
                "Number": line[2],
            }


def ipu_objects_analyse(interlocking_data, out_data):
    """
    Функция анализа объектов контроллеров
    """
    for line in interlocking_data:
        line = get_line_data(line)

        if line:
            if line[0] in ('End', 'COS',):
                return line[0]

            out_data['IPU_objects'][line[0]] = {
                "Yard": line[1],
                "Type": line[2],
                "COS": line[3],
                "Consists": line[4:],
            }


def add_cfw(out_data, obj_name, ils_id=""):
    """
    Функция добавления информации о входящих данных
    получаемых в объекте от приказов свободного монтажа
    """
    # При наличии нескольких централизаций получаем
    # номер необходимой
    if "-" in obj_name:
        ils_id = obj_name.split("-")[-1]
    # Для всех направлений приказа добавляем информацию
    # об объекте передачи в объект приёма
    for ofw in out_data[obj_name]["ofw"]:
        for log_obj, check in zip(
                out_data[obj_name]["ofw"][ofw]["ipu"][::2],
                out_data[obj_name]["ofw"][ofw]["ipu"][1::2],
        ):
            if ils_id:
                log_obj = log_obj + "-" + ils_id
            out_data[log_obj]["status"][check] = {
                "value": 0,
                "ipu": obj_name + "." + ofw,
            }


def ofw_cfw_mapping(out_data):
    """
    Функция обвязки приказ - статус для свободного монтажа
    """
    # Собираем все объекты в которых есть нужные приказы
    objects_with_ofw = [
        _
        for _ in out_data["Logical_objects"]
        if out_data["Logical_objects"][_]["ofw"]
    ]

    for log_obj in objects_with_ofw:
        add_cfw(out_data["Logical_objects"], log_obj)


def interlocking_data_parser(interlocking_data):
    """
    Функция получения данных объектов из файла станции.
    Позволяет получить топологию и экземпляры используемых
    объектов.
    Обработка исключений отсутствует, т.к. файл с некорректной
    структурой распознается на более ранних этапах тестирования.
    """
    current_section = 'Header'
    out_data = {
        'Header': {},
        'Logical_objects': {},
        'IPU_objects': {},
        'COS_objects': {},
        'Site_product_name': '',
    }
    for line_num, line in enumerate(interlocking_data):

        line = get_line_data(line)

        if not line:
            # Если строка пустая или закомментированная
            continue

        # Если строка обозначает начало нового раздела
        # изменяем значение на него
        if line == ['Logical', 'objects']:
            current_section = 'Logical'

        if current_section == 'Header':
            out_data['Header'][line[0]] = line[1:]
            if line[0] == 'Site_product_name':
                out_data['Site_product_name'] = line[1]
            continue
        # В соответствии с разделом вызывается функция обработчик
        # Каждая функция закончив работу возвращает тип следующего раздела
        if current_section == 'Logical':
            current_section = log_objects_analyse(interlocking_data, out_data)
        if current_section == 'IPU':
            current_section = ipu_objects_analyse(interlocking_data, out_data)
            ofw_cfw_mapping(out_data)
        if current_section == 'COS':
            cos_objects_analyse(interlocking_data, out_data)
            # COS раздел является последним значащим,
            # обработка файла останавливается
            break
    return out_data


if __name__ == "__main__":
    int_data_path = 'X:/projects/mosgd/MMK/serebryanyi_bor/eqv/ipu7/ILS2_RF_SBO-RB2CUR/ILS2_RF_SBO/implementation/input/data/Interlocking_data'
    with open(int_data_path) as int_data:
        parsed_data = interlocking_data_parser(int_data)
        print(parsed_data['Header'])
        print(parsed_data['Logical_objects'])
