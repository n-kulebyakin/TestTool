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

    def __init__(self, title):
        super().__init__(title)
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        self.main_widget.setMinimumSize(400, 300)
        self.grid = QGridLayout()
        self.main_widget.setLayout(self.grid)


class CustomSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = None

    def wheelEvent(self, event):
        event.ignore()


class CustomTreeItem(QTreeWidgetItem):
    def clear_tree(self):
        for index in range(self.childCount()):
            child = self.child(0)
            self.removeChild(child)


class ProjectExplorer(CustomDockWidget):

    def __init__(self, title):

        super().__init__(title)
        self.project_tree = QTreeWidget()

        self.project_tree.setHeaderLabel("Project model")
        self.search_field = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.find_object)

        self.grid.addWidget(self.search_field, 0, 0)
        self.grid.addWidget(self.search_button, 0, 1)
        self.grid.addWidget(self.project_tree, 1, 0, 2, 2)

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
        obj_name = self.search_field.text()
        if not obj_name:
            return
        matches = self.project_tree.findItems(obj_name, Qt.MatchRecursive, 0)
        if matches:
            self.project_tree.setCurrentItem(matches[0])

    def clear(self):
        self.objects_tree.clear_tree()
        self.ipu_tree.clear_tree()
        self.components_tree.clear_tree()

    @staticmethod
    def build_tree(obj_data, parent_item):
        for key, values in obj_data.items():
            type_tree = QTreeWidgetItem(parent_item)
            type_tree.setText(0, key)
            for value in sorted(values):
                value_item = QTreeWidgetItem(type_tree)
                value_item.setText(0, value)

    @staticmethod
    def collect_objects_data(obj_data):
        out_data = {}
        all_types = (obj_data[x].get("Type", None) for x in obj_data)
        for obj_type in all_types:
            target_objs = [x for x in obj_data
                           if obj_data[x].get("Type", None) == obj_type]
            out_data[obj_type] = target_objs
        return out_data

    @staticmethod
    def collect_components_data(components_data):
        out_data = {}
        for component_type in components_data:
            target_objs = components_data[component_type]
            for obj in target_objs:
                for component in target_objs[obj]:
                    header = (component_type + "-" +
                              "-".join(component["Parameters"]))
                    out_data.setdefault(component_type, []).append(header)

        return out_data

    def build_project_tree(self, components, site_objects, site_ipu):
        components_data = self.collect_components_data(components)
        self.build_tree(components_data, self.components_tree)
        objects_data = self.collect_objects_data(site_objects)
        self.build_tree(objects_data, self.objects_tree)
        ipu_data = self.collect_objects_data(site_ipu)
        self.build_tree(ipu_data, self.ipu_tree)


class PropertyTable(QTableWidget):
    _max_rows = 200

    def __init__(self, tab_data):
        super().__init__()
        columns = len(tab_data)
        header = (x[0] for x in tab_data)
        self.setColumnCount(columns)
        self.setHorizontalHeaderLabels(header)
        self.setRowCount(self._max_rows)

        for row in range(self._max_rows):
            self.hideRow(row)
            for column_num, (col_name, widget, func) in enumerate(tab_data):
                if widget == "label":
                    new_item = QTableWidgetItem()
                    new_item.setFlags(new_item.flags()
                                      & ~Qt.ItemIsEditable)
                    self.setItem(row, column_num, new_item)
                else:
                    new_item = CustomSpinBox()
                    self.setCellWidget(row, column_num, new_item)
                if func:
                    new_item.valueChanged.connect(func)

    def hide_not_used_rows(self, start_row):
        if start_row > 0:
            start_row += 1

        for row_num in range(start_row, self._max_rows):
            self.hideRow(row_num)


class PropertyExplorer(CustomDockWidget):

    def __init__(self, title):
        super().__init__(title)

        self._max_settings_rows = 200
        self.property_tab = QTabWidget()

        self.tool_box = QToolBox()

        self.obj_name = QLabel("")
        self.obj_type = QLabel("")

        self.grid.addWidget(QLabel("Name:"), 0, 0)
        self.grid.addWidget(self.obj_name, 0, 1, 1, 2)
        self.grid.addWidget(QLabel("Type:"), 0, 3)
        self.grid.addWidget(self.obj_type, 0, 4)
        self.grid.addWidget(self.tool_box, 1, 0, 1, 5)

        tab_data = (("Name", "label", None),
                    ("Value", "spin", self.send_change_ibit),
                    ("Description", "label", None),
                    )

        self.i_table = PropertyTable(tab_data)
        self.i_table.setColumnWidth(1, 80)
        self.i_table.setColumnWidth(2, 100)

        tab_data = (("Order", "label", None),
                    ("Object/Check", "label", None),
                    ("Value", "label", None),
                    )

        self.free_wiredes = PropertyTable(tab_data)

        tab_data = (("Status", "label", None),
                    ("IPU object", "label", None),
                    ("Value", "spin", self.set_status),
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

        self.command_table.cellDoubleClicked.connect(self.send_component)

        self.property_tab.addTab(self.i_table, "I_BIT")
        self.property_tab.addTab(self.free_wiredes, "Free wired")
        self.property_tab.addTab(self.statuses, "Status")
        self.property_tab.addTab(self.orders, "Orders")
        self.property_tab.addTab(self.indications, "Indications")
        self.property_tab.addTab(self.variables, "Variables")
        self.property_tab.addTab(self.channels, "Channels")

        self.tool_box.addItem(self.property_tab, "Property")
        self.tool_box.addItem(self.command_table, "Components")

    def clear_properties(self):
        for table in (self.i_table,
                      self.free_wiredes,
                      self.statuses,
                      self.orders,
                      self.indications,
                      self.variables,
                      self.channels,
                      self.command_table):
            table.hide_not_used_rows(0)


    def send_component(self, line, colum):
        pass

    def set_status(self):
        pass

    def send_change_ibit(self):
        pass


class PropertyExplorerWithSim(PropertyExplorer):

    def __init__(self, title):
        super().__init__(title)
        self._socket = None
        self._site_id = None

    def set_socket(self, sim_socket):
        self._socket = sim_socket

    def set_site_id(self, site_id):
        self._site_id = site_id

    def send_component(self, line, colum):

        if self._socket is not None:
            comm_type = self.command_table.item(line, 0).text()
            comm_param = self.command_table.item(line, 1).text()
            out_str = "{0}/cmd {1} {2}\n".format(self._site_id,
                                                 comm_type,
                                                 comm_param)

    def set_status(self):
        pass

    def send_change_ibit(self):
        pass



class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self._proj_path = "E:/"
        self.setMinimumSize(1000, 600)
        # -------------------------------------------------------------
        self.open_action = QAction("&Open", self)
        self.open_action.triggered.connect(self.show_open_dialog)

        self.exit_action = QAction("&Exit", self)
        self.exit_action.triggered.connect(qApp.quit)

        self.proj_settings_action = QMenu("&Project settings", self)
        self.color_settings = QAction("Yard colors", self)
        self.color_settings.triggered.connect(self.show_color_settings)
        self.proj_settings_action.addAction(self.color_settings)

        self.program_settings_action = QAction("&Program settings", self)
        # -------------------------------------------------------------
        # init_menu

        menubar = self.menuBar()

        settings_menu = menubar.addMenu("&File")
        settings_menu.addAction(self.open_action)
        settings_menu.addAction(self.exit_action)
        settings_menu = menubar.addMenu("&Settings")
        settings_menu.addAction(self.color_settings)

        # ------------------------------------------------------------
        # init_main_toolbar
        self.main_toolbar = self.addToolBar("Main Tool Bar")
        self.main_toolbar.addAction(self.open_action)
        # ------------------------------------------------------------
        # init_dock_project_tree
        self.project_explorer = ProjectExplorer("Project explorer")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_explorer)
        # ---------------------------------------------------------
        # init_dock_object_settings
        self.property_explorer = PropertyExplorer("Object properties")
        self.addDockWidget(Qt.RightDockWidgetArea, self.property_explorer)
        # ---------------------------------------------------------
        # init_center
        self.view = CustomGraphicsView()

        self.setCentralWidget(self.view)

    def show_open_dialog(self):
        path_to_ci = QFileDialog.getOpenFileName(self,
                                                 "Open file",
                                                 self._proj_path,
                                                 "ConfigInfo (*.CI)")

        self.open_site_data(path_to_ci[0])

    def open_site_data(self, config_path):
        pass

    def show_color_settings(self):
        pass


class ImportSiteDataMixin:
    _config_data = {}
    _site_keys = {}
    _components = {}
    _logical_objects = {}
    _ipu_objects = {}
    _product_name = {}
    _logic_data = {}
    _coordinates = {}

    def load_coordinates(self, path):
        cad_path = os.path.join(path, "LogicScene.xml")
        yard_path = os.path.join(path, "yard.xml")
        if os.path.exists(cad_path):
            self._coordinates = read_scene_data(cad_path)
        elif os.path.exists(yard_path):
            self._coordinates = read_scene_data(yard_path)
        else:
            # TODO: Добавить логирование
            return

    def load_components(self, com_data_file):
        com_data = command_data_parser(com_data_file)
        self._components = com_data["Components"]

    def load_data(self, int_data_file):
        int_data = interlocking_data_parser(int_data_file)
        self._logical_objects = int_data["Logical_objects"]
        self._ipu_objects = int_data["IPU_objects"]
        self._product_name = int_data["Site_product_name"]

    def add_variable_from_logic(self, obj, obj_type):
        for key in self._logic_data[obj_type]["#OWN"]:
            init = self._logic_data[obj_type]["#OWN"][key]["init"]
            if "variables" not in self._logical_objects[obj]:
                self._logical_objects[obj]["variables"] = {
                    key: {"value": init}}
            else:
                self._logical_objects[obj]["variables"][key] = {"value": init}

    def load_logic(self, ste_path):
        self._logic_data = logic_reader.logic_analyse(ste_path)

        for obj in self._logical_objects:
            obj_type = self._logical_objects[obj]["Type"]
            if not self._logic_data.get(obj_type):
                continue
            if "#OWN" in self._logic_data.get(obj_type):
                self.add_variable_from_logic(obj, obj_type)
            else:
                self._logical_objects[obj]["variables"] = {"value": ""}
            self.add_channel(obj, obj_type)
            self.add_ind(obj, obj_type)
            self.add_orders(obj, obj_type)
            self.add_indication(obj, obj_type)
            self.add_status(obj, obj_type)
        return True

    def add_channel(self, obj, obj_type):
        if "#INOUT" not in self._logic_data[obj_type]:
            return
        for key in self._logic_data[obj_type]["#INOUT"]:
            channels = self._logic_data[obj_type]["#INOUT"][key]['0']["init"]
            in_out_data = {"IN": channels, "OUT": channels}
            if "channels" not in self._logical_objects[obj]:
                self._logical_objects[obj]["channels"] = {key: in_out_data}
            else:
                self._logical_objects[obj]["channels"][key] = in_out_data

    def add_ind(self, obj, obj_type):
        all_ind = logic_reader.get_ibits_list(obj_type, self._logic_data)
        obj_ind = self._logical_objects[obj]["individualizations"]
        new_i_bit = [x for x in all_ind if x not in obj_ind]
        for i_bit in new_i_bit:
            default_val = logic_reader.get_default_value(i_bit,
                                                         obj_type,
                                                         self._logic_data)

            obj_ind[i_bit] = default_val

    def add_orders(self, obj, obj_type):

        if "#OUT" not in self._logic_data[obj_type]:
            return
        ste_orders = logic_reader.get_orders(obj_type, self._logic_data)

        if not ste_orders:
            return

        if "orders" in self._logical_objects[obj]:
            obj_orders = self._logical_objects[obj]["orders"]
            new_orders = [x for x in ste_orders if x not in obj_orders]
            for order in new_orders:
                obj_orders[order] = {"ipu": "", "value": ""}
        else:
            obj_orders = {}
            for order in ste_orders:
                obj_orders[order] = {"ipu": "", "value": ""}
            self._logical_objects[obj]["orders"] = obj_orders
        logic_ofw = logic_reader.get_ofw(obj_type, self._logic_data)
        obj_ofw = self._logical_objects[obj]["ofw"]
        if logic_ofw:
            new_ofw = [x for x in logic_ofw if x not in obj_ofw]
            for order in new_ofw:
                self._logical_objects[obj]["ofw"][order] = {"ipu": "",
                                                            "value": ""}

    def add_indication(self, obj, obj_type):
        obj_indication = self._logical_objects[obj]["indication"]
        for indication in self._logical_objects[obj]["indication"]:
            cos = self._logical_objects[obj]["indication"][indication]
            obj_indication[indication] = {"cos": cos, "value": ""}

        logic_ind = logic_reader.get_status(obj_type, self._logic_data)
        for indication in logic_ind:
            if indication not in obj_indication:
                obj_indication[indication] = {"cos": "", "value": ""}

    def add_status(self, obj, obj_type):
        logic_status = logic_reader.get_checks(obj_type, self._logic_data)
        obj_status = self._logical_objects[obj]["status"]
        new_status = [x for x in logic_status if x not in obj_status]
        for status in new_status:
            obj_status[status] = {"ipu": "", "value": ""}
        for status in obj_status:
            if status.count("."):
                continue
            init = self._logic_data[obj_type]["#IN"][status]["init"]
            if status in self._logic_data[obj_type]["#IN"]:
                obj_status[status]["value"] = init
            else:
                # TODO: Обновить логирование
                logging.error("not compatible with site data")
                return

    def import_site_data(self, config_path):
        ils_path = str(Path(config_path).parent.absolute())

        if not os.path.exists(config_path):
            # TODO: Добавить логирование
            return

        config = config_reader(config_path)
        parsers = (
            ("CommandTable", self.load_components),
            ("IntData", self.load_data),
            ("ILL_STERNOL_FILE", self.load_logic),
        )

        for key, parser in parsers:
            path_to_key = get_path_to_key(config, key)
            if not path_to_key:
                # TODO: Добавить логирование
                return

            if not os.path.exists(path_to_key):
                # TODO: Добавить логирование
                return

        self.clear_site()

        data_keys = {}
        for key, parser in parsers:
            path_to_key = get_path_to_key(config, key)
            data_keys[key] = path_to_key
            with open(path_to_key) as file_data:
                parser(file_data)

        self._site_keys.update(copy.deepcopy(data_keys))
        self._config_data = copy.deepcopy(config)
        self.load_coordinates(ils_path)

        return True

    def clear_site(self):
        self._config_data.clear()
        self._site_keys.clear()
        self._components.clear()
        self._logical_objects.clear()
        self._ipu_objects.clear()
        self._product_name = ""
        self._logic_data.clear()
        self._coordinates.clear()
