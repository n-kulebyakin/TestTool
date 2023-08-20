# =========================================
# ==____________Config_reader____________==
# =========================================

import os
import re
from copy import deepcopy
from pathlib import Path

HEADER_PATTERN = r'(?:[\w.-]|".*")+'
BODY_PATTERN = r'[\w.\-\~\;>]+'
ADAPT_PATH = os.environ.get('ADAPT_PATH', 'E:/')

PRODUCT_TYPES = ('File', 'Directory',)


def get_line_data(line, word_pattern):
    """
    Строка разбивается на слова в соответствии
    с переданным шаблоном
    и исключаются закомментированные строки
    """
    match = re.findall(word_pattern, line)
    if match and '.' != match[0][0]:
        return match


def get_header_line_data(line):
    """
    Получение информации из строки заголовка
    """
    return get_line_data(line, HEADER_PATTERN)


def get_obj_line_data(line):
    """
    Получение информации из строки тела файла
    """
    return get_line_data(line, BODY_PATTERN)


def get_product_path(line, config_path):
    """
    Получение пути абсолютного до файла
    """
    if not line or line[-1] == '~':
        return config_path
    return os.path.join(config_path, *line[2:])


def get_name_and_version(obj_name):
    """
    Получение имени и версии файла,
    если файл замещает старую версию,
    то выбираем информацию и старую версию
    """
    version = '0'
    old_version = ''

    if '-' in obj_name:
        obj_name, version = obj_name.rsplit('-', maxsplit=1)
    if '>' in version:
        old_version, version = version.split('>')
    return obj_name, version, old_version


def product_save(current_data, out_data, current_path):
    """
    Сохранение информации об объекте в общее хранилище
    """
    if not current_data:
        return
    temp_product = {'Name': '', 'Type': '', 'Identity': '', 'Key': [],
                    'version': '', 'old_version': '', 'Path': '', }
    # Если директория раздела reference,
    # то объекты из этой директории являются
    # ссылками на подпродукты
    if current_path.endswith('reference'):
        name, version, old_version = get_name_and_version(current_data[-1])
        out_data['Products'][name] = {'Name': name, 'version': version,
                                      'old_version': old_version}
        return

    # Если объектом является стандартный файл или директория,
    # собираем данные в словарь КЛЮЧ:ЗНАЧЕНИЕ
    product_data = dict(zip(current_data[::2], current_data[1::2]))
    # Записываем значения в соответствующие поля
    for key, value in product_data.items():
        if key in PRODUCT_TYPES:
            temp_product['Type'] = key
            name, version, old_version = get_name_and_version(value)
            temp_product['Name'] = name
            temp_product['version'] = version
            temp_product['old_version'] = old_version
            continue
        # Для всех полей кроме типа и названия возможно присвоение
        # нескольких значений перечисленных через точку с запятой
        temp_product[key] = value.split(';')
    temp_product['Path'] = current_path
    # Сохраняем объект в соответствующий раздел
    if temp_product['Type'] == 'File':
        out_data['Files'].append(deepcopy(temp_product))
        return
    out_data['Directories'].append(deepcopy(temp_product))


def path_analyse(last_line, config_data, file_path):
    """
    Функция анализа разделов PATH конфигурации
    """
    out_data = {'Files': [], 'Products': {}, 'Directories': [], }

    # Получаем абсолютный путь, до каталога
    # содержащего конфигурационный путь
    # от этого пути стояться все остальные в файле
    current_path = config_path = str(Path(file_path).parent.absolute())

    # Если текущий путь раздела не является исходным
    # то получаем его абсолютный путь
    line = get_obj_line_data(last_line)
    if line:
        current_path = get_product_path(line[-1], config_path)
    current_data = []

    for line in config_data:
        line = get_obj_line_data(line)
        if not line:
            continue
        if line[0] == 'Checksum_A':
            # Если тело конфигурационного файла закончено
            # сохраняем последний объект
            product_save(current_data, out_data, current_path)
            return out_data
        if line[0] == 'Path':
            # Если строка является началом нового раздела PATH,
            # то сохраняем текущий продукт, получаем новый
            # абсолютный путь и очищаем текущий продукты
            product_save(current_data, out_data, current_path)
            current_path = get_product_path(line, config_path)
            current_data.clear()
        elif line[0] == '->':
            # Обрабатываем спецсимвол '->' обозначающий
            # перенос строки внутри конфигурационного файла
            # добавляем строку к информации о текущем объекте
            # исключая символ переноса
            current_data += line[1:]
        elif not current_data:
            # Если текущий объект пуст, записываем в него информацию
            current_data = line
        else:
            # Если это новый объект внутри одного раздела PATH,
            # то сохраняем предыдущий и записываем в текущий
            # информацию из строки
            product_save(current_data, out_data, current_path)
            current_data = line


def header_analyse(config_data):
    """
    Функция анализа заголовка файла
    """
    out_data = {}
    for source_line in config_data:
        line = get_header_line_data(source_line)
        if not line:
            continue
        # Если строка является началом раздела PATH
        # завершаем анализ заголовка и возвращаем
        # исходную строку
        if line[0] == 'Path':
            return source_line, out_data
        out_data[line[0]] = line[-1]
    # Если файл закончился, а раздел PATH
    # так и не наёмен, возвращаем вместо исходной
    # строки объект None
    return None, out_data


def get_path_to_product(product_data, adapt_path=ADAPT_PATH):
    """
    Функция получения абсолютного пути
    до конфигурационного файла подпродукта
    """
    product = product_data['Name'] + '-' + product_data['version']
    product_path = os.path.join(adapt_path, product_data['Name'], product,
                                product_data['Name'], 'ConfigInfo.CI')
    if os.path.exists(product_path):
        return product_path


def config_parser(file_path):
    """
    Функция анализа содержимого конфигурационного
    файла продукта без подгрузки
    конфигураций подпродуктов
    """
    out_data = {}

    with open(file_path) as config_data:
        last_line, header = header_analyse(config_data)
        out_data['Header'] = header
        if last_line:
            products = path_analyse(last_line, config_data, file_path)
            out_data.update(deepcopy(products))
    return out_data


def config_reader(file_path, adapt_path=ADAPT_PATH):
    """
    Функция сбора информации конфигурации продукта,
    включая все подпродукты на которые он ссылается
    """
    # Получаем информацию о продукте
    product_config = config_parser(file_path)

    # Для каждого подпродукта собираем информацию
    # о нём и добавляем в общую структуру
    for sub_prod in product_config.get('Products', []):

        # Получаем абсолютный пути до подпродукта
        path_to_sub = get_path_to_product(product_config['Products'][sub_prod])
        # Если подпродукт не найден, переходим к следующему
        if not path_to_sub:
            continue

        sub_data = config_reader(path_to_sub, adapt_path)
        product_config['Files'] += sub_data['Files']
        product_config['Directories'] += sub_data['Directories']

    return product_config


def get_file_with_key(config_information, key):
    """
    Функция получения файла/директории по ключу
    из конфигурационной информации проекта
    """

    # Для исключения проверки вхождения в список
    # ключей обёрнуто в перехват исключения
    try:
        # Для всех файлов и папок проверяем соответствие
        # требуемому ключу
        # Нахождение ключа в начале списка указывает
        # на его актуальную версию
        files = config_information.get('Files', [])
        directories = config_information.get('Directories', [])
        files_and_directories = files + directories
        for proj_file in files_and_directories:
            if key in proj_file.get('Key'):
                return proj_file
    except TypeError:
        return


def get_path_to_key(config_information, key):
    """
    Функция получения абсолютного пути до
    файла/директории по ключу включая
    сам файл/директорию
    """
    key_data = get_file_with_key(config_information, key)
    if key_data:
        path_to_key = os.path.join(key_data['Path'], key_data['Name'])
        return path_to_key
