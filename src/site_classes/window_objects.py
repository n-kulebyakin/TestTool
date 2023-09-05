# -*- coding: utf-8 -*-
import copy
import logging
import os
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QToolBox
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import qApp
from site_classes.scene_objects import CustomGraphicsView
from site_readers import logic_reader
from site_readers.command_reader import command_data_parser
from site_readers.configuration_reader import config_reader
from site_readers.configuration_reader import get_path_to_key
from site_readers.data_reader import interlocking_data_parser
from site_readers.scene_reader import read_scene_data


class CustomDockWidget(QDockWidget):
    """
    Класс шаблон для виджита с пристыковкой
    с заранее установленными размерами и
    сеткой-слоем
    """

    def __init__(self, title):
        super().__init__(title)
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        self.main_widget.setMinimumSize(400, 300)
        self.grid = QGridLayout()
        self.main_widget.setLayout(self.grid)


class CustomSpinBox(QSpinBox):
    """
    Класс поля с дополнительным аттрибутом
    в виде имени и отключенной прокруткой
    значений колёсиком мыши
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # добавляем атрибут имени
        self.name = None

    def wheelEvent(self, event):
        """
        Функция обработчик вращения колёсика мыши.
        Переопределяется для исключения изменения
        значения прокруткой.
        """
        event.ignore()


class CustomTreeItem(QTreeWidgetItem):
    """
    Класс объекта дерева с дополнительным
    методом очистки дерева.
    """

    def clear_tree(self):
        for index in range(self.childCount()):
            child = self.child(0)
            self.removeChild(child)


class ProjectExplorer(CustomDockWidget):
    """
    Класс инспектора структуры проекта.
    Позволяет построить и просмотреть дерево
    проекта. Найти объект в дереве.
    """

    def __init__(self, title):

        super().__init__(title)
        # Создаём объект дерева и устанавливаем заголовок
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderLabel("Project model")
        # Добавляем поле и кнопку для поиска объектов
        self.search_field = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.find_object)

        self.grid.addWidget(self.search_field, 0, 0)
        self.grid.addWidget(self.search_button, 0, 1)
        self.grid.addWidget(self.project_tree, 1, 0, 2, 2)

        # К корневому дереву добавляем подкаталоги
        # для трех типов объектов
        self.objects_tree = CustomTreeItem()
        self.objects_tree.setText(0, "Logical objects")

        self.ipu_tree = CustomTreeItem()
        self.ipu_tree.setText(0, "IPU objects")

        self.components_tree = CustomTreeItem()
        self.components_tree.setText(0, "Components")

        self.project_tree.addTopLevelItem(self.objects_tree)
        self.project_tree.addTopLevelItem(self.ipu_tree)
        self.project_tree.addTopLevelItem(self.components_tree)

    def find_object(self):
        """
        Метод поиска объекта
        из поля в дереве проекта
        """
        obj_name = self.search_field.text()
        if not obj_name:
            return
        matches = self.project_tree.findItems(obj_name, Qt.MatchRecursive, 0)
        if matches:
            self.project_tree.setCurrentItem(matches[0])

    def clear(self):
        """
        Метод очистки дерева
        """
        self.objects_tree.clear_tree()
        self.ipu_tree.clear_tree()
        self.components_tree.clear_tree()

    @staticmethod
    def build_tree(obj_data, parent_item):
        """
        Метод построения дерева по заданным
        в словаре данным
        """
        for key, values in obj_data.items():
            # Обходим словарь по парам ключ-значение
            # Для каждого ключа создаём поддерево
            type_tree = QTreeWidgetItem(parent_item)
            type_tree.setText(0, key)
            # Значения сортируем, создаём для каждого
            # объект в дереве ключа
            for value in sorted(values):
                value_item = QTreeWidgetItem(type_tree)
                value_item.setText(0, value)

    @staticmethod
    def collect_objects_data(obj_data):
        """
        Метод сбора объектов в словарь по типам
        """
        out_data = {}
        # Сначала собираем все типы объектов в кортеж
        all_types = (obj_data[x].get("Type", None) for x in obj_data)
        for obj_type in all_types:
            # Для каждого типа получаем соответствующие объекты
            target_objs = [x for x in obj_data
                           if obj_data[x].get("Type", None) == obj_type]
            out_data[obj_type] = target_objs
        return out_data

    @staticmethod
    def collect_components_data(components_data):
        """
        Метод сбора компонентов в словарь по типам
        """
        out_data = {}
        for component_type in components_data:
            target_objs = components_data[component_type]
            for obj in target_objs:
                # Для каждого типа компонента и начального
                # объекта выбираем все компоненты
                for component in target_objs[obj]:
                    # Преобразуем компоненты в одну неразрывную
                    # строку из типа и параметров
                    header = (component_type + "-" +
                              "-".join(component["Parameters"]))
                    # Если тип компонента уже есть в словаре, то
                    # добавляем получившийся заголовок к списку,
                    # если его нет, то добавляем тип в виде ключа
                    # со значением пустого списка и к пустому списку
                    # добавляем заголовок
                    out_data.setdefault(component_type, []).append(header)

        return out_data

    def build_project_tree(self, components, site_objects, site_ipu):
        """
        Метод построения и заполнения дерева проекта
        """
        components_data = self.collect_components_data(components)
        self.build_tree(components_data, self.components_tree)
        objects_data = self.collect_objects_data(site_objects)
        self.build_tree(objects_data, self.objects_tree)
        ipu_data = self.collect_objects_data(site_ipu)
        self.build_tree(ipu_data, self.ipu_tree)


class PropertyTable(QTableWidget):
    """
    Класс таблицы свойств объектов
    """

    def __init__(self, tab_data):
        super().__init__()

        # В зависимости от переданной информации
        # устанавливаем заголовок таблицы
        columns = len(tab_data)
        header = (x[0] for x in tab_data)
        self.setColumnCount(columns)
        self.setHorizontalHeaderLabels(header)
        # Устанавливаем начальное максимальное
        # количество строк таблицы
        self._max_rows = 200
        self.setRowCount(self._max_rows)

        # Заранее создаём строки в таблице,
        # для того что бы в последующем не тратить
        # время на их создание/удаление при выборе
        # объекта
        for row in range(self._max_rows):
            # Скрываем строку, что бы не показывать пустую
            self.hideRow(row)
            # По информации из входных данных строим строку таблице
            for column_num, (col_name, widget, func) in enumerate(tab_data):
                # В зависимости от объекта в ячейки заполняем её
                if widget == "label":
                    # Если объект должен быть подписью, то создаём её
                    new_item = QTableWidgetItem()
                    # Исключаем возможность изменения текста в ячейке
                    new_item.setFlags(new_item.flags()
                                      & ~Qt.ItemIsEditable)
                    self.setItem(row, column_num, new_item)
                else:
                    new_item = CustomSpinBox()
                    self.setCellWidget(row, column_num, new_item)
                # if func:
                #     new_item.valueChanged.connect(func)

    def hide_not_used_rows(self, start_row):
        """
        Метод сокрытия неиспользуемых строк
        """
        if start_row > 0:
            start_row += 1
        for row_num in range(start_row, self._max_rows):
            self.hideRow(row_num)

    def connect_value_change(self, column, func):
        """
        Метод подключения функции при изменении
        значения виджета ячейки.
        Выставляется сразу для всего столбца
        """

        for row in range(self._max_rows):
            cell_item = self.cellWidget(row, column)
            cell_item.valueChanged.connect(func)


class PropertyExplorer(CustomDockWidget):
    """
    Класс окна просмотра свойств объекта
    """

    def __init__(self, title):
        super().__init__(title)

        # Создаём объект отвечающий
        # за хранение вкладок с параметрами
        self.property_tab = QTabWidget()

        # Создаём объект обработки
        # всех вкладок
        self.tool_box = QToolBox()

        # Добавляем две надписи, которе
        # буду содержать имя и тип выбранного
        # объекта
        self.obj_name = QLabel("")
        self.obj_type = QLabel("")

        # Добавляем подписи к имени и типу
        # и размещаем всё на сетке
        self.grid.addWidget(QLabel("Name:"), 0, 0)
        self.grid.addWidget(self.obj_name, 0, 1, 1, 2)
        self.grid.addWidget(QLabel("Type:"), 0, 3)
        self.grid.addWidget(self.obj_type, 0, 4)
        self.grid.addWidget(self.tool_box, 1, 0, 1, 5)

        # Заполняем шаблон заголовка и виджетов
        # для индивидуализаций
        tab_data = (("Name", "label", None),
                    ("Value", "spin", None),
                    ("Description", "label", None),
                    )

        # Создаём вкладку индивидуализаций
        self.i_table = PropertyTable(tab_data)
        self.i_table.setColumnWidth(1, 80)
        self.i_table.setColumnWidth(2, 100)

        # Аналогично индивидуализациям заполняем
        # остальные вкладки
        tab_data = (("Order", "label", None),
                    ("Object/Check", "label", None),
                    ("Value", "label", None),
                    )

        self.free_wired = PropertyTable(tab_data)

        tab_data = (("Status", "label", None),
                    ("IPU object", "label", None),
                    ("Value", "spin", None),
                    )

        self.statuses = PropertyTable(tab_data)

        tab_data = (("Order", "label", None),
                    ("IPU object", "label", None),
                    ("Value", "label", None),
                    )

        self.orders = PropertyTable(tab_data)

        tab_data = (("Name", "label", None),
                    ("COS object", "label", None),
                    ("Value", "label", None),
                    )

        self.indications = PropertyTable(tab_data)

        tab_data = (("Name", "label", None),
                    ("Value", "label", None),
                    )

        self.variables = PropertyTable(tab_data)

        tab_data = (("Name", "label", None),
                    ("IN", "label", None),
                    ("OUT", "label", None),
                    )

        self.channels = PropertyTable(tab_data)

        tab_data = (("Command", "label", None),
                    ("Parameters", "label", None),
                    )

        self.command_table = PropertyTable(tab_data)

        # Все вкладки собираем в один объект
        self.property_tab.addTab(self.i_table, "BIT")
        self.property_tab.addTab(self.free_wired, "Free wired")
        self.property_tab.addTab(self.statuses, "Status")
        self.property_tab.addTab(self.orders, "Orders")
        self.property_tab.addTab(self.indications, "Indications")
        self.property_tab.addTab(self.variables, "Variables")
        self.property_tab.addTab(self.channels, "Channels")
        # Добавляем объекты со свойствами и компонентами
        # на панель инструментов
        self.tool_box.addItem(self.property_tab, "Property")
        self.tool_box.addItem(self.command_table, "Components")

    def clear_properties(self):
        """
        Метод сокрытия всех свойств и компонентов
        """
        for table in (self.i_table,
                      self.free_wired,
                      self.statuses,
                      self.orders,
                      self.indications,
                      self.variables,
                      self.channels,
                      self.command_table):
            table.hide_not_used_rows(0)


class MainWindow(QMainWindow):
    """
    Класс отображение главного окна.
    Содержит в себе инспектор проекта,
    свойств объекта, сцену объектов.
    """

    def __init__(self):
        super().__init__()
        # Устанавливаем путь до папки с проектами
        self._proj_path = "E:/"
        # Выставляем минимальные размеры окна
        self.setMinimumSize(1000, 600)
        # -------------------------------------------------------------
        # Добавляем стандартный набор действий
        # - открыть/закрыть/свойства проекта
        self.open_action = QAction("&Open", self)
        self.open_action.triggered.connect(self.show_open_dialog)

        self.exit_action = QAction("&Exit", self)
        self.exit_action.triggered.connect(qApp.quit)

        self.proj_settings_action = QMenu("&Project settings", self)
        # В меню настроек проекта добавляем
        # опцию изменения цветовой схемы объектов
        self.color_settings = QAction("Yard colors", self)
        self.color_settings.triggered.connect(self.show_color_settings)
        self.proj_settings_action.addAction(self.color_settings)

        self.program_settings_action = QAction("&Program settings", self)
        # -------------------------------------------------------------
        # Добавляем действия в раздел меню программы
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("&File")
        settings_menu.addAction(self.open_action)
        settings_menu.addAction(self.exit_action)
        settings_menu = menubar.addMenu("&Settings")
        settings_menu.addAction(self.color_settings)

        # ------------------------------------------------------------
        # Часть действий добавляем в панель быстрого доступа
        self.main_toolbar = self.addToolBar("Main Tool Bar")
        self.main_toolbar.addAction(self.open_action)
        # ------------------------------------------------------------
        # Создаём окна инспектора проекта и свойств объекта
        self.project_explorer = ProjectExplorer("Project explorer")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_explorer)

        self.property_explorer = PropertyExplorer("Object properties")
        self.addDockWidget(Qt.RightDockWidgetArea, self.property_explorer)
        # ---------------------------------------------------------
        # Создаём поле для графического отображение
        # объектов проекта и их соединений
        self.view = CustomGraphicsView()
        self.setCentralWidget(self.view)

    def show_open_dialog(self):
        """
        Метод вызова окна выбора конфигурационного
        файла проекта который необходимо открыть
        """
        # Отображаем окно выбора файла и сохраняем
        # путь до выбранного файла
        path_to_ci = QFileDialog.getOpenFileName(self,
                                                 "Open file",
                                                 self._proj_path,
                                                 "ConfigInfo (*.CI)")
        # Передаём путь в функцию обработки
        # выбранного проекта
        self.open_site_data(path_to_ci[0])

    def open_site_data(self, config_path):
        """
        Метод обработки данных выбранного проекта
        """
        pass

    def show_color_settings(self):
        """
        Метод отображения настроек цветовой
        палитры проекта
        """
        pass


class ImportSiteDataMixin:
    """
    Класс примесь, реализующий
    функционал загрузки данных проекта
    """

    def __init__(self):
        super().__init__()
        self._config_data = {}
        self._site_keys = {}
        self._components = {}
        self._logical_objects = {}
        self._ipu_objects = {}
        self._product_name = {}
        self._logic_data = {}
        self._coordinates = {}

    def load_coordinates(self, path):
        """
        Метод загрузки координат
        расположения объектов
        """
        cad_path = os.path.join(path, "LogicScene.xml")
        yard_path = os.path.join(path, "yard.xml")
        # Файлы с координатами могут быть либо выгружены
        # напрямую с Visio с помощью VBA, либо сохранены
        # ранее с какими то изменениями
        if os.path.exists(cad_path):
            # Если есть ранее сохраненные данных,
            # то получаем информацию из них
            self._coordinates = read_scene_data(cad_path)
        elif os.path.exists(yard_path):
            self._coordinates = read_scene_data(yard_path)
        else:
            # Если файлы отсутствуют то выдаём предупреждение
            # TODO: Добавить окно предупреждений
            #  об ошибках загрузки
            pass

    def load_components(self, com_data_file):
        """
        Метод загрузки команд проекта
        """
        com_data = command_data_parser(com_data_file)
        self._components = com_data["Components"]

    def load_data(self, int_data_file):
        """
        Метод загрузки данных об объектах
        """
        int_data = interlocking_data_parser(int_data_file)
        # Сохраняем отдельно данные о логических объектах
        # и объектах увязки с напольными устройствами
        self._logical_objects = int_data["Logical_objects"]
        self._ipu_objects = int_data["IPU_objects"]
        # Сохраняем имя загруженного проекта без кавычек
        # (кавычки могут быть только двойные)
        self._product_name = int_data["Site_product_name"].replace('"', '')

    def add_variable_from_logic(self, obj, obj_type):
        """
        Метод добавления к объектам информации о
        внутренних переменных
        """

        for key in self._logic_data[obj_type]["#OWN"]:
            # Для каждой внутренней переменной для данного
            # типа объекта, получаем начальное значение
            # из файла описания логики и добавляем его к
            # объекту
            init = self._logic_data[obj_type]["#OWN"][key]["init"]
            if "variables" not in self._logical_objects[obj]:
                self._logical_objects[obj]["variables"] = {
                    key: {"value": init}}
            else:
                self._logical_objects[obj]["variables"][key] = {"value": init}

    def load_logic(self, ste_path):
        """
        Метод загрузки информации о логике проекта
        """
        # Для загружаем логику по заданному пути
        self._logic_data = logic_reader.logic_analyse(ste_path)

        for obj in self._logical_objects:
            # Проходим по каждому объекту и получаем его тип
            obj_type = self._logical_objects[obj]["Type"]
            if not self._logic_data.get(obj_type):
                continue
            if "#OWN" in self._logic_data.get(obj_type):
                # Если у данного типа есть внутренние переменные
                # добавляем информацию о них
                self.add_variable_from_logic(obj, obj_type)
            else:
                # Если внутренних переменных нет, добавляем
                # пустое значение
                self._logical_objects[obj]["variables"] = {"value": ""}

            # Добавляем остальную информацию о
            # значения по умолчанию и наличию
            # свойств объекта
            self.add_channel(obj, obj_type)
            self.add_ind(obj, obj_type)
            self.add_orders(obj, obj_type)
            self.add_indication(obj, obj_type)
            self.add_status(obj, obj_type)
        return True

    def add_channel(self, obj, obj_type):
        """
        Метод добавления к объектам информации о
        канал связи с другими объектами
        """
        # Если объект не связан каналами с другими
        # то возвращаемся
        if "#INOUT" not in self._logic_data[obj_type]:
            return
        # Для каждого канала для данного типа объекта
        for key in self._logic_data[obj_type]["#INOUT"]:
            channels = self._logic_data[obj_type]["#INOUT"][key]
            # для каждого соединительного вывода
            for leg in channels:
                # Формируем информацию о начальных значениях
                # входящей и исходящей информации по каналу
                channel = channels[leg]["init"]
                value = {"IN": channel, "OUT": channel}
                # Формируем имя канала по образцу
                # ИМЯ(СОЕДИНИТЕЛЬНЫЙ_ВЫВОД)
                # и добавляем информацию к объекту
                name = f'{key}({leg})'
                if "channels" not in self._logical_objects[obj]:
                    self._logical_objects[obj]["channels"] = {name: value}
                else:
                    self._logical_objects[obj]["channels"][name] = value

    def add_ind(self, obj, obj_type):
        """
        Метод добавления к объектам информации об
        индивидуализации
        """
        # Cобираем все данные об индивидуализации из логики
        all_ind = logic_reader.get_ibits_list(obj_type, self._logic_data)
        # Cобираем все данные об индивидуализации из проекта
        obj_ind = self._logical_objects[obj]["individualizations"]
        # Формируем список неучтённых в проекте индивидуализаций
        new_i_bit = [x for x in all_ind if x not in obj_ind]
        # Добавляем их к объекту со значением по умолчанию
        for i_bit in new_i_bit:
            default_val = logic_reader.get_default_value(i_bit,
                                                         obj_type,
                                                         self._logic_data)

            obj_ind[i_bit] = default_val

    def add_orders(self, obj, obj_type):
        """
        Метод добавления к объектам информации о
        приказах передаваемых в напольные объекты
        и в другие логические объекты
        """

        if "#OUT" not in self._logic_data[obj_type]:
            return
        # Получаем все приказы объекта
        ste_orders = logic_reader.get_orders(obj_type, self._logic_data)

        if not ste_orders:
            return

        # Если хотя бы какие-то приказы объекта задействованы в проекте
        if "orders" in self._logical_objects[obj]:
            # Формируем список из неиспользованных
            obj_orders = self._logical_objects[obj]["orders"]
            new_orders = [x for x in ste_orders if x not in obj_orders]
            # Добавляем их к информации об объекте
            for order in new_orders:
                obj_orders[order] = {"ipu": "", "value": ""}
        else:
            # Если в объекте не было задействовано ни одного приказа
            # добавляем все как новые
            obj_orders = {}
            for order in ste_orders:
                obj_orders[order] = {"ipu": "", "value": ""}
            self._logical_objects[obj]["orders"] = obj_orders
        # Аналогично приказам в напольные объекты
        # добавляем информацию о приказах в другие
        # логические объекты
        logic_ofw = logic_reader.get_ofw(obj_type, self._logic_data)
        obj_ofw = self._logical_objects[obj]["ofw"]
        if logic_ofw:
            new_ofw = [x for x in logic_ofw if x not in obj_ofw]
            for order in new_ofw:
                self._logical_objects[obj]["ofw"][order] = {"ipu": "",
                                                            "value": ""}

    def add_indication(self, obj, obj_type):
        """
        Метод добавления к объектам информации о
        индикационных переменных
        """
        # Добавляем значение индикационной переменной
        # в ключ cos и поле value.
        obj_indication = self._logical_objects[obj]["indication"]
        for indication in self._logical_objects[obj]["indication"]:
            cos = self._logical_objects[obj]["indication"][indication]
            # Значение по умолчанию у данного типа переменных нет
            obj_indication[indication] = {"cos": cos, "value": ""}

        logic_ind = logic_reader.get_status(obj_type, self._logic_data)
        for indication in logic_ind:
            if indication not in obj_indication:
                obj_indication[indication] = {"cos": "", "value": ""}

    def add_status(self, obj, obj_type):
        """
        Метод добавления к объектам информации о
        статусах
        """
        logic_status = logic_reader.get_checks(obj_type, self._logic_data)
        obj_status = self._logical_objects[obj]["status"]
        new_status = [x for x in logic_status if x not in obj_status]
        # Добавляем незадействованные статусы
        for status in new_status:
            obj_status[status] = {"ipu": "", "value": ""}
        for status in obj_status:
            # Если в статус приходит информация от
            # другого логического объекта, не добавляем значения
            if status.count("."):
                continue
            # Получаем начальное значение из файлов логики
            init = self._logic_data[obj_type]["#IN"][status]["init"]
            # Если статус из проекта есть в логике,
            # устанавливаем ему значение
            if status in self._logic_data[obj_type]["#IN"]:
                obj_status[status]["value"] = init
            else:
                # Если статус отсутствует в логике, значит данные
                # проекта не корректны
                # TODO: Добавить логирование
                logging.error("not compatible with site data")
                return

    def import_site_data(self, config_path):
        """
        Метод загрузки данных проекта из конфигурационного
        файла
        """

        # Сохраняем путь к корневой директории проекта
        ils_path = str(Path(config_path).parent.absolute())

        # Проверяем наличие конфигурационного файла
        if not os.path.exists(config_path):
            # TODO: Добавить логирование
            return

        # Получаем данные конфигурации проекта
        config = config_reader(config_path)

        # Формируем кортеж из критически важных
        # ключей проекта
        # и функций обработчиков данных
        parsers = (
            ("CommandTable", self.load_components),
            ("IntData", self.load_data),
            ("ILL_STERNOL_FILE", self.load_logic),
        )

        for key, parser in parsers:
            # Получаем путь к файлу по ключу из конфигурации
            path_to_key = get_path_to_key(config, key)
            if not path_to_key:
                # Если ключа нет в конфигурации,
                # то прекращаем загрузку
                # TODO: Добавить логирование
                return

            if not os.path.exists(path_to_key):
                # Если файла не существует,
                # то прекращаем загрузку
                # TODO: Добавить логирование
                return
        # Очищаем данные от предыдущих загрузок проектов
        self.clear_site()

        data_keys = {}
        # Для каждого критически важного ключа
        # получаем его путь и производим анализ
        for key, parser in parsers:
            path_to_key = get_path_to_key(config, key)
            data_keys[key] = path_to_key
            with open(path_to_key) as file_data:
                parser(file_data)

        # Сохраняем данные, делая глубокую копию полученной
        # информации, т.к. она содержит вложенные изменяемые
        # объекты
        self._site_keys.update(copy.deepcopy(data_keys))
        self._config_data = copy.deepcopy(config)
        self.load_coordinates(ils_path)

        # Возвращаем информацию об удачной загрузке проекта
        return True

    def clear_site(self):
        """
        Метод очистки данных проекта
        """
        self._config_data.clear()
        self._site_keys.clear()
        self._components.clear()
        self._logical_objects.clear()
        self._ipu_objects.clear()
        self._product_name = ""
        self._logic_data.clear()
        self._coordinates.clear()
