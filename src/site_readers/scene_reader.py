# =========================================
# ==_____________Scene_reader____________==
# =========================================

import xml.dom.minidom


def get_x_y_data(node_data):
    """
    Функция преобразования координаты
    полученной из файла
    """

    # Файлы могут содержатm разные разделители
    # целой и дробной части, по этому
    # отрезаем дробную часть в любом случае
    if "," in node_data:
        node_data = node_data.split(",")[0]
    else:
        node_data = node_data.split(",")[0]
    return int(node_data)


def read_scene_data(file_path):
    """
    Функция получения данных о расположении
    объектов
    """

    # По умолчанию выставляем высоту и ширину
    # отображаемой сцены
    max_x = 1000
    max_y = 1000

    logical_objects = {}

    doc = xml.dom.minidom.parse(file_path)
    node = doc.documentElement

    rem_1 = node.getElementsByTagName("ScriptGraphicObject")

    for node in rem_1:
        # Из строки собираем данные и преобразуем в словарь
        node_items = dict(node.attributes.items())
        obj_name = node_items["object_name"]

        # Добавляем имя объекта в общее хранилище
        logical_objects[obj_name] = {}

        # Получаем координаты и сохраняем их
        coord_x = get_x_y_data(node_items["x"])
        coord_y = get_x_y_data(node_items["y"])

        logical_objects[obj_name]["x"] = coord_x
        logical_objects[obj_name]["y"] = coord_y

        # Если текущие координаты выходят за пределы
        # размеров сцены, увеличиваем её значения
        if coord_x > max_x:
            max_x = coord_x + 1000
        if coord_y > max_y:
            max_y = coord_y + 500

        # Сохраняем значения матрицы трансформации
        for attr in ("m11", "m12", "m21", "m22"):
            logical_objects[obj_name][attr] = int(float(node_items[attr][0:8]))

    # Если файл был сохранён специальной программой,
    # то он МОЖЕТ хранить данные о необходимом размере сцены
    rem_2 = None
    if file_path.endswith('LogicScene.xml'):
        rem_2 = node.getElementsByTagName("config")

    if rem_2:
        rem_1 = rem_2[0].getElementsByTagName("scene")
        node_items = dict(rem_1[0].attributes.items())
        # Выбираем данные размера и сохраняем их
        logical_objects["sceneWidth"] = int(node_items["fieldWidth"])
        logical_objects["sceneHeight"] = int(node_items["fieldHeight"])

    else:
        # Если данных о размере сцены в
        # исходных данных нет, то записываем
        # расчётные
        logical_objects["sceneWidth"] = max_x
        logical_objects["sceneHeight"] = max_y

    return logical_objects
