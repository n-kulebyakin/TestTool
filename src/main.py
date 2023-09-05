# -*- coding: utf-8 -*-
import os
import sys
from statistics import mean

from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QTransform
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QSplashScreen

from modeling_classes.window import SimWindow
from site_classes.color_dialog import OBJECT_COLORS, ObjectColorWindow
from site_classes.scene_objects import LogicalConnector
from site_classes.scene_objects import LogicalObject
from site_classes.window_objects import ImportSiteDataMixin
from site_classes.window_objects import MainWindow
from site_readers.log_reader import log_data_parser
from site_readers.log_reader import object_variable_parser

START_PICTURE = "static/start_screen.gif"


class SiteWindow(ImportSiteDataMixin, MainWindow):
    """
    Класс загрузки и отображения информации о
    проекте
    """
    _css_file = "static/style.css"

    def __init__(self):
        super().__init__()
        # Добавляем информацию о цветовой схеме
        # по умолчанию
        self.objects_colors = OBJECT_COLORS
        # Инициализируем словарь отображаемых объектов
        self._visual_objects = {}
        # Добавляем переменную для хранения имени
        # выделенного объекта
        self._selected_obj = None
        # Добавляем переменную для хранения информации
        # о том выбран ли новый объект и идёт обновление
        # информации о нём
        self._changing_object = False
        # Добавляем обработку выбора объекта
        # из дерева проекта
        pt = self.project_explorer.project_tree
        pt.itemClicked.connect(self.select_tree_item)
        pt.currentItemChanged.connect(self.select_tree_item)
        # Загружаем данные визуальных настроек программы
        # из CSS файла
        self.set_custom_styles(self._css_file)
        # Сохраняем окно изменения цветовой схемы
        # отображения объектов, что бы не создавать
        # его каждый раз
        self._color_window = ObjectColorWindow(self.objects_colors,
                                               self._visual_objects)

    def set_custom_styles(self, css_file):
        """
        Метод установки настройки отображения
        программы по css файлу
        """
        if os.path.exists(css_file):
            with open(css_file) as css_data:
                # Если файл присутствует, устанавливаем
                # информацию из него
                self.setStyleSheet(css_data.read())

    def create_objects_views(self):
        """
        Метод создания визуальных
        отображений объектов проекта
        """
        # Создаём пустой список в который будем
        # добавлять объекты без координат
        without_pos = []

        # Устанавливаем размены сцены
        self.view.scene.setSceneRect(0, -self._coordinates["sceneHeight"],
                                     self._coordinates["sceneWidth"] + 1000,
                                     self._coordinates["sceneHeight"])

        for deep, name in enumerate(self._logical_objects):
            log_data = self._logical_objects[name]
            # Для каждого логического объекта создаем
            # визуальное представление
            # Глубину задаём по порядковому номеру
            new_obj = LogicalObject(name, log_data, deep, self.view.scene,
                                    self.objects_colors,
                                    self.project_explorer.project_tree)

            if name in self._coordinates:
                # Если координаты объекта
                # заданы в проекте, считываем их
                obj_coordinate = self._coordinates[name]
                # Вместе с координатами есть информации
                # о размерах и ориентации
                # Создаём по данным матрицу трансформации
                matrix = QTransform(obj_coordinate["m11"],
                                    -obj_coordinate["m12"],
                                    obj_coordinate["m21"],
                                    -obj_coordinate["m22"],
                                    new_obj.size().width() / 2,
                                    new_obj.size().height() / 2)

                # Применяем матрицу трансформации
                # и перемещаем объект по координатам
                new_obj.apply_matrix(matrix)
                new_obj.move(obj_coordinate["x"], obj_coordinate["y"])
            else:
                # Если позиция неизвестна добавляем
                # имя объекта к остальным
                without_pos.append(name)
            # Добавляем новый объект в общее хранилище
            # с доступом по имени объекта
            self._visual_objects[name] = new_obj
        # Устанавливаем позиции для оставшихся объектов
        self.set_average_pos(without_pos)

    def set_average_pos(self, without_pos):
        """
        Метод установки позиции объекта
        координаты которого заранее неизвестны
        """
        # Устанавливаем число попыток вычисления
        # приближенного вычисления позиции
        approx_num = 5
        # Устанавливаем значение по умолчанию
        # в верхнем правом углу
        faulty_pos_x = 1000
        faulty_pos_y = self._coordinates["sceneHeight"] - 250
        # Создаём пустой список куда будем
        # сохранять объекты связанные с другими
        obj_with_legs = []
        # Разделяем объекты на связанные
        # друг с другом и остальные
        for name in without_pos:
            log_obj = self._logical_objects[name]
            if log_obj["legs"]:
                obj_with_legs.append(name)
            else:
                # Если объект не связан с остальными
                # устанавливаем его позиции правее
                # от текущей
                v_obj = self._visual_objects[name]
                v_obj.move(faulty_pos_x, faulty_pos_y)
                faulty_pos_x += 100
        # Выставляем приближенную позицию для объекта
        # Установка значений несколько раз обусловлена
        # возможностью наличия более одного объекта
        # в цепочке без координаты
        for _ in range(approx_num):
            self.set_pos_from_obj_with_legs(obj_with_legs)

    def set_pos_from_obj_with_legs(self, objs_with_legs):
        """
        Метод установки приближенной позиции
        объекта по координатам соседей
        """
        for name in objs_with_legs:
            log_obj = self._logical_objects[name]
            v_obj = self._visual_objects[name]
            x_n_poses = []
            y_n_poses = []
            # Для каждого вывода объекта
            for leg in log_obj["legs"]:
                neighbour = log_obj["legs"][leg]["neighbour"]
                # Получаем соседний объект
                n_obj = self._visual_objects[neighbour]
                neigh_pos = n_obj.pos()
                new_x = abs(neigh_pos.x())
                new_y = abs(neigh_pos.y())
                # Если координаты соседнего объекта
                # установлены корректно, добавляем
                # их в список
                if new_x > 10:
                    x_n_poses.append(new_x)
                if new_y > 10:
                    y_n_poses.append(new_y)
            # По координатам соседних объектов
            # вычисляем среднее координаты текущего
            x_avg = mean(x_n_poses) if x_n_poses else 0
            y_avg = mean(y_n_poses) if y_n_poses else 0
            # Перемещаем объект по полученным координатам
            v_obj.move(x_avg, y_avg)

    def build_project_tree(self):
        """
        Метод построения дерева проекта
        """
        # Очищаем дерево проекта и строим
        # с загруженными данными
        self.project_explorer.objects_tree.clear_tree()
        self.project_explorer.build_project_tree(self._components,
                                                 self._logical_objects,
                                                 self._ipu_objects)

    @staticmethod
    def get_leg_pos(scene_object):
        """
        Метод получения модуля позиции объекта
        """
        pos = scene_object.sceneBoundingRect()
        return abs(pos.x()), abs(pos.y())

    def get_flips(self, neighbour_leg, current_leg, legs):
        """
        Метод получения информации о необходимости
        отразить объекта по осям
        """
        # Устанавливаем начальные значения
        # о необходимости отражения
        flip_y, flip_x = False, False
        # Получаем информацию о положении вывода
        # соседнего объекта и текущего вывода
        neighbour_x, neighbour_y = self.get_leg_pos(neighbour_leg)
        current_x, current_y = self.get_leg_pos(current_leg)
        # Вычисляем информацию о расстоянии по осям
        current_distance_x = abs(neighbour_x - current_x)
        current_distance_y = abs(neighbour_y - current_y)
        # Для всех выводов текущего объекта
        # вычисляем расстояние до соседнего вывода
        for leg in legs:
            leg_x, leg_y = self.get_leg_pos(leg)
            leg_distance_x = abs(neighbour_x - leg_x)
            leg_distance_y = abs(neighbour_y - leg_y)
            # Если расстояние меньше чем от текущего,
            # то значит объект необходимо отразить
            # по соответствующей оси
            if leg_distance_y < current_distance_y:
                flip_x = True
            if leg_distance_x < current_distance_x:
                flip_y = True
        return flip_x, flip_y

    def flip_objects(self):
        """
        Метод исправления пространственного
        отображения объекта
        """
        for name in self._visual_objects:
            legs = self._visual_objects[name].objects_legs
            flip_x = False
            flip_y = False
            # Для каждого вывода объекта получаем
            # информацию о соседнем выводе и проверяем
            # необходимость отражения по осям
            for current_leg in legs:
                neighbour_leg = self.get_neighbour_leg(name, current_leg.name)
                need_flip_x, need_flip_y = self.get_flips(neighbour_leg,
                                                          current_leg, legs)
                if need_flip_x:
                    flip_x = True
                if need_flip_y:
                    flip_y = True
            # Применяем отражение если необходимо
            if flip_x:
                self._visual_objects[name].flip_x()
            if flip_y:
                self._visual_objects[name].flip_y()

    def connect_all_objects(self):
        """
        Метод создания соединительных линий
        между выводами объектов
        """
        for name in self._visual_objects:
            legs = self._visual_objects[name].objects_legs
            # Для всех выводов объекта
            # проверяем наличие соединительной линии
            for current_leg in legs:

                if not current_leg.get_connector():
                    # Если линия отсутствует, получаем данные
                    # о соседнем выводе
                    neighbour_leg = self.get_neighbour_leg(name,
                                                           current_leg.name)
                    # Создаём объект соединения
                    new_connector = LogicalConnector(current_leg,
                                                     neighbour_leg)
                    # Добавляем информацию об объекте в выводы
                    current_leg.set_connector(new_connector)
                    neighbour_leg.set_connector(new_connector)
                    # Добавляем объект соединения на сцену
                    self.view.scene.addItem(new_connector)

    def get_neighbour_leg(self, log_name, from_leg):
        """
        Метод получения визуального отображения
        вывода соседнего объекта
        """
        # Получаем имя соседнего объекта
        # с заданного вывода и информацию
        # о номере вывода
        legs = self._logical_objects[log_name]["legs"][from_leg]
        n_name = legs["neighbour"]
        n_leg = int(legs["neighbour_leg"])
        # Получаем объект отображения вывода
        leg = self._visual_objects[n_name].get_leg(n_leg)
        return leg

    def open_site_data(self, config_path):
        """
        Метод получения информации о проекте
        по указанному пути до конфигурационного
        файла
        """
        # Если путь не корректный возвращаемся
        if not os.path.exists(config_path):
            return
        # Пытаемся импортировать данные проекта
        imported = self.import_site_data(config_path)
        # Если импорт прошёл успешно
        if imported:
            # Сбрасываем информацию о предыдущем
            # открытом проекте и удаляем объекты со сцены
            self._selected_obj = None
            for obj in list(self._visual_objects):
                self._visual_objects[obj].deleteLater()

            self.view.scene.clear()
            self._visual_objects.clear()
            # Очищаем дерево проекта и вкладку свойств
            self.project_explorer.clear()
            self.property_explorer.clear_properties()
            # Выстраиваем дерево проекта по новым данным
            self.build_project_tree()
            # Добавляем отображение объектов
            self.create_objects_views()
            # Корректируем ориентацию отображения объектов
            # это необходимо из за некорректных выгрузках
            # из VISIO
            self.flip_objects()
            # Соединяем выводы объектов
            self.connect_all_objects()

    def select_tree_item(self, tree_item):
        """
        Метод обрабатывающий выделение объекта
        в дереве проекта
        """
        if not tree_item:
            return
        # Получаем имя выделенного объекта
        obj_name = tree_item.text(0)
        # Если объект имеет визуальное отображение
        # и уже не выделен
        if obj_name == self._selected_obj:
            return
        if obj_name in self._visual_objects:
            # Устанавливаем переменную ответственную
            # за обработку изменений данных
            # Это необходимо для корректного получения
            # и передачи информации от имитатора
            self._changing_object = True
            # Если какой-то объект был выделен ранее
            # получаем этот объект и снимаем с него выделение
            if self._selected_obj:
                selected = self._visual_objects[self._selected_obj]
                selected.deselect()
            # Выделяем выбранный объект
            selecting = self._visual_objects[obj_name]
            selecting.select()
            self._selected_obj = obj_name
            # Во вкладке свойств устанавливаем
            # все данные по для выделенного объекта
            self.config_settings(obj_name)
            self.config_components(obj_name)
            # Снимаем флаг изменения выделенного объекта
            self._changing_object = False
            # Устанавливаем имя и тип выделанного объекта
            # в окне свойств
            self.property_explorer.obj_name.setText(obj_name)
            self.property_explorer.obj_type.setText(selecting.log_type)
            # Перемещаем камеру отображения так что бы
            # выделенный объект был виден
            self.view.ensureVisible(selecting, 10, 10)

    def config_obj_ibit(self, obj_name):
        """
        Метод конфигурации вкладки индивидуализаций
        в окне свойств объекта
        """
        out_table = self.property_explorer.i_table
        # Получаем информацию об индивидуализациях объекта
        i_bits = self._logical_objects[obj_name]["individualizations"]
        max_row_num = -1
        for row_num, column_data in enumerate(i_bits.items()):
            # Поочередно перебираем все индивидуализации
            # и в зависимости от столбца и содержимого
            # ячейки выставляем название и значение
            for col_num, col_value in enumerate(column_data):
                cell_widget = out_table.cellWidget(row_num, col_num)
                if cell_widget:
                    cell_widget.setValue(int(col_value))
                    cell_widget.name = column_data[0]
                else:
                    out_table.item(row_num, col_num).setText(col_value)
            # Отображаем сформированную строку
            out_table.showRow(row_num)
            # Запоминаем её номер
            max_row_num = row_num
        # Скрываем все строки ниже
        # последней использованной
        out_table.hide_not_used_rows(max_row_num)

    def config_obj_settings_other(self, obj_name, settings_name, out_table):
        """
        Метод конфигурации вкладки свойства объекта
        """
        if settings_name not in self._logical_objects[obj_name]:
            return
        # Получаем информацию о запрошенных
        # настроек объекта и сортируем его
        settings_data = self._logical_objects[obj_name][settings_name]
        sorted_keys = sorted(settings_data)

        max_row_num = -1
        for row_num, name in enumerate(sorted_keys):
            column_data = settings_data[name]
            out_table.item(row_num, 0).setText(name)

            if settings_name in ("status", "orders", "indication", "ofw"):
                # Если это индикационная переменная
                # имя переменной хранится с ключом "cos"
                if settings_name == "indication":
                    ipu = column_data["cos"]
                else:
                    ipu = column_data["ipu"]
                # Получаем значение переменной
                value = column_data["value"]
                # Получаем виджет для значения
                value_widget = out_table.cellWidget(row_num, 2)
                # Переменная может быть списком
                # из за возможности привязок приказов
                # в несколько объектов
                if isinstance(ipu, list):
                    # Собираем информацию в одну строку
                    ipu = [x + "." + y for x in ipu[::2] for y in ipu[1::2]]
                    ipu = ",".join(ipu)
                out_table.item(row_num, 1).setText(ipu)
                if settings_name == "status":
                    value_widget.setValue(int(value))
                    # Если это входящая информация для объекта,
                    # то дополнительно устанавливаем аттрибут
                    value_widget.name = name
                else:
                    out_table.item(row_num, 2).setText(value)
            else:
                # Обработка некорректных данных
                # if "value" not in column_data:
                #     continue
                value = column_data["value"]
                out_table.item(row_num, 1).setText(value)
            max_row_num = row_num
            # Устанавливаем видимость для строки
            out_table.showRow(row_num)
        # Скрываем неиспользуемые
        out_table.hide_not_used_rows(max_row_num)

    def config_obj_channels(self, obj_name):
        """
        Метод конфигурации вкладки каналов
        передачи данных между объектами
        """

        max_row_num = -1
        out_table = self.property_explorer.channels
        channels = self._logical_objects[obj_name].get("channels")
        if channels:
            for row_num, column_data in enumerate(channels.items()):
                for col_num, col_value in enumerate(column_data):
                    # Данные могут быть в виде
                    # строки с названием канала
                    # и в виде словаря со значениями
                    if isinstance(col_value, dict):
                        # Если это словарь со значениями,
                        # записываем каждое значение
                        # в свою ячейку
                        if "IN" in col_value:
                            in_value = col_value["IN"]
                            out_table.item(row_num, 1).setText(in_value)
                        if "OUT" in col_value:
                            out_value = col_value["OUT"]
                            out_table.item(row_num, 2).setText(out_value)
                    else:
                        out_table.item(row_num, 0).setText(col_value)
                out_table.showRow(row_num)
                max_row_num = row_num
        out_table.hide_not_used_rows(max_row_num)

    def config_components(self, obj_name):
        """
        Метод конфигурации вкладки
        с командами от выбранного объекта
        """
        out_table = self.property_explorer.command_table
        current_row = 0
        for comp_type in self._components:
            # Проходим по всем типам команд,
            # если для данного объекта нет
            # такого типа команд,
            # переходим к следующему
            if obj_name not in self._components[comp_type]:
                continue
            for component in self._components[comp_type].get(obj_name):
                # Для каждой команды этого типа
                # записываем в ячейку тип
                out_table.item(current_row, 0).setText(comp_type)
                # В соседнюю записываем параметры в виде строки
                parameters = " ".join(component["Parameters"])
                # В таком виде параметры удобно копировать
                # для составления кейсов в ручную
                out_table.item(current_row, 1).setText(parameters)
                out_table.showRow(current_row)
                current_row += 1
        out_table.hide_not_used_rows(current_row)

    def config_settings(self, obj_name):
        """
        Метод конфигурации свойств объекта
        """

        self.config_obj_ibit(obj_name)
        self.config_obj_settings_other(obj_name, "orders",
                                       self.property_explorer.orders)
        self.config_obj_settings_other(obj_name, "status",
                                       self.property_explorer.statuses)
        self.config_obj_settings_other(obj_name, "ofw",
                                       self.property_explorer.free_wired)
        self.config_obj_settings_other(obj_name, "indication",
                                       self.property_explorer.indications)
        self.config_obj_settings_other(obj_name, "variables",
                                       self.property_explorer.variables)
        self.config_obj_channels(obj_name)

    def show_color_settings(self):
        """
        Метод отображения окна
        настройки цветовой палитры
        """
        self._color_window.show()


class ToolWindow(SimWindow, SiteWindow):
    """
    Класс главного окна программы,
    включающий возможности отображения
    объектов и взаимодействия с имитатором
    """

    def __init__(self):
        super().__init__()
        # В окно свойств проекта добавляем
        # вкладку с подключением к имитатору
        self.property_explorer.tool_box.addItem(self.simulation, "Simulation")

        # Добавляем обработку событий
        # для отправки данных в имитатор
        statuses = self.property_explorer.statuses
        statuses.connect_value_change(2, self.send_status)

        self.command_table = self.property_explorer.command_table
        self.command_table.cellDoubleClicked.connect(self.send_component)

        individualization = self.property_explorer.i_table
        individualization.connect_value_change(1, self.send_bit)

        # Устанавливаем объекту соединения
        # функцию обработчик входящей информации
        self._socket.set_out_function(self.get_data_from_sim)

    def select_tree_item(self, tree_item):
        """
        Расширенный метод обработки выделения
        объекта в дереве проекта
        """

        # Если программа подключена к имитатору,
        # при выделении объекта отправляем запрос
        # на обновление информации о состоянии
        # всех его переменных
        if self._socket.isOpen():
            obj_name = tree_item.text(0)
            out_str = '{}/variables {}\n'.format(self._site_id, obj_name)

            self._socket.send(out_str)

        super().select_tree_item(tree_item)

    def send_status(self):
        """
        Метод отправки информации об изменении
        статуса объекта
        """

        # Если нет соединения с имитатором
        # или происходит выбор нового объекта
        # возвращаемся
        # При сменен объекта у виджетов обновляются
        # значения, что приводит к лишнему вызову функции
        # и ложной отправке сообщений в имитатор.
        # Для исключения этого проверяется флаг
        # смены объекта
        if self._changing_object or not self._socket.isOpen():
            return

        obj_name = self._selected_obj
        # Получаем информацию о значении
        # и имени изменившегося статуса
        value = self.sender().value()
        status_name = self.sender().name

        obj_data = self._logical_objects[obj_name]
        status_obj = obj_data['status'][status_name]['ipu']

        if status_obj and '.' not in status_obj:
            # Если к статусу привязана информация
            # от напольного объекта, то меняем
            # состояние самого объекта
            out_str = '{0}/yard {1} try_set {2}\n'.format(self._site_id,
                                                          status_obj, value)
        else:
            # Если к статусу ничего не привязано
            # или привязан информация
            out_str = '{0}/check {1}.{2}={3}\n'.format(self._site_id, obj_name,
                                                       status_name, value)
        self._socket.send(out_str)

    def send_component(self, line, column):
        """
        Метод отправки команды
        в имитатор
        """
        if self._socket.isOpen():
            # Собираем данные о типе и параметра
            # команды в одну строку
            comm_type = self.command_table.item(line, 0).text()
            comm_param = self.command_table.item(line, 1).text()
            out_str = "{0}/cmd {1} {2}\n".format(self._site_id, comm_type,
                                                 comm_param)

            self._socket.send(out_str)

    def send_bit(self):
        """
        Метод отправки информации
        об изменении индивидуализации
        """
        if self._changing_object or not self._socket.isOpen():
            return

        obj_name = self._selected_obj
        out_str = '{0}/individ {1}.{2}={3}\n'.format(self._site_id, obj_name,
                                                     self.sender().name,
                                                     self.sender().value())
        self._socket.send(out_str)

    def set_channel_value_to_neighbour(self, obj_name, channel, value):
        """
        Метод установки входящего значения
        канала связи соседнему объекту
        """
        log_obj = self._logical_objects.get(obj_name)
        # Из записи вида ИМЯ_КАНАЛА(ВЫВОД)
        # получаем отдельно имя и номер вывода
        channel_name, temp_leg = channel.split('(')
        leg = temp_leg[:-1]
        # С полученного вывода получаем
        # соседний объект и его вывод
        neighbour = log_obj["legs"][leg]["neighbour"]
        neighbour_leg = log_obj["legs"][leg]["neighbour_leg"]
        # Формируем запись вида
        # ИМЯ_КАНАЛА(ВЫВОД_СОСЕДНЕГО_ОБЪЕКТА)
        channel_name = f'{channel_name}({neighbour_leg})'
        # Присваиваем соседнему объекту
        # полученное входящее значение
        self._logical_objects[neighbour]["channels"][channel_name][
            'IN'] = value

    def update_object(self, obj_name, obj_data):
        """
        Метод обновления переменных
        логического объекта
        """

        log_obj = self._logical_objects.get(obj_name)
        if log_obj:
            # Формируем кортеж данных которые
            # необходимо обновить из логов
            chapters = (
                'individualizations', 'orders', 'status', 'indication', 'ofw',
                'variables', 'channels')

            for chapter in chapters:
                for var_name in log_obj[chapter]:
                    if var_name in obj_data[obj_name]:
                        # Для каждой переменной объекта
                        # из выбранного раздела,
                        # если информация по переменной изменилась
                        # получаем новое значение
                        new_value = obj_data[obj_name][var_name]
                        # Разделы с индивидуализациями и каналами
                        # обрабатываем отдельно
                        if chapter == 'individualizations':
                            self._logical_objects[obj_name][chapter][
                                var_name] = new_value['value']
                        elif chapter == 'channels':
                            # Значение каналов будет всегда
                            # исходящим для текущего объекта
                            obj_data = self._logical_objects[obj_name]
                            value = new_value['value_out']
                            obj_data["channels"][var_name]['OUT'] = value
                            # Добавляем исходящее значение
                            # входящим соседнему объекту
                            self.set_channel_value_to_neighbour(obj_name,
                                                                var_name,
                                                                value
                                                                )
                        else:
                            self._logical_objects[obj_name][chapter][
                                var_name].update(new_value)

    def get_data_from_sim(self, sim_data):
        """
        Метод обработки данных полученных
        из имитатора или лог файла
        """

        # Устанавливаем флаг изменения
        # объекта
        self._changing_object = True

        if '!' in sim_data:
            # Если информация была получена
            # в виде потока данных от всех объектов
            # или из лог файла
            new_data = log_data_parser(sim_data.split('\n'))
            # Выбираем данные относящиеся только
            # к текущему проекту
            proj_data = new_data.get(self._product_name, {})
            if proj_data:
                # Обновляем изменившиеся объекты
                for obj_name in proj_data:
                    self.update_object(obj_name, proj_data)

        else:
            # Если данные были получены только
            # для одного объекта
            proj_data = object_variable_parser(sim_data.split('\n'),
                                               self._selected_obj)
            if proj_data:
                # Обновляем изменившийся
                self.update_object(self._selected_obj, proj_data)
                self.config_settings(self._selected_obj)
        # Если данные были получены и
        # выделен какой-то объект, обновляем
        # вкладку параметров
        if self._selected_obj and proj_data:
            # Так как выделенный объект мог измениться
            # во время получения данных от имитатора
            # обновлять данные вкладки раньше обработки
            # полученной информации не имеет смысла
            self.config_settings(self._selected_obj)
        self._changing_object = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Устанавливаем заставку на время
    # загрузки программы
    splash = QSplashScreen()
    splash.setPixmap(QPixmap(START_PICTURE))
    splash.show()

    main_form = ToolWindow()
    main_form.show()

    splash.finish(main_form)

    app.exec_()
