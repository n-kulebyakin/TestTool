# -*- coding: utf-8 -*-
import sys
import os
import datetime
import logging

from pathlib import Path
from statistics import mean

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import qApp
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QLabel

from PyQt5.QtWidgets import QToolBox
from PyQt5.QtWidgets import QTabWidget

from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem

from PyQt5.QtWidgets import QSpacerItem
from PyQt5.QtWidgets import QSizePolicy

from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QPlainTextEdit

from PyQt5.QtWidgets import QSplashScreen

from PyQt5.QtGui import QFont
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QTransform
from PyQt5.QtGui import QPixmap

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer

from PyQt5.QtNetwork import QNetworkProxy

from PyQt5.Qt import QGraphicsScene
from PyQt5.Qt import QBrush

from test_tool.visual_objects import CustomSpinBox
from test_tool.visual_objects import CustomGraphicsView
from test_tool.visual_objects import LogicalObject
from test_tool.visual_objects import LogicalConnector

# from site_readers.configuration import config_reader
from site_readers.configuration_reader import config_reader
# from site_readers.configuration import get_file_with_key
from site_readers.configuration_reader import get_path_to_key

from site_readers.scene import read_scene_data

from site_readers.data_reader import interlocking_data_parser
from site_readers.command_reader import command_data_parser

from sim_api.sim_data_parser import log_file_parser
from sim_api.sim_data_parser import object_variable_parser

from site_tests.read_test_case import read_test_file

from test_tool.color_dialog import ObjectColorWindow, OBJECT_COLORS

from site_tests import test_writer as tw
from site_readers import logic_reader

from sim_api.connection import SimSocket, send_to_sim
from sim_api.actions import SIM_ACTIONS

CSS_FILE = "static/style.css"

ADAPT_PATH = os.environ.get("CBX_PATH", "X:/eqv/adapt/")


class MainWindow(QMainWindow):
    st_id = 1
    obj_properties_font = QFont("Times", 8)
    ils_path = ("D:/depot/projects")
    site_keys = {}
    visual_objects = {}
    logical_objects_site = {}
    max_settings_rows = 200
    objects_colors = OBJECT_COLORS
    sim_actions = SIM_ACTIONS
    temp_log = ""
    change_object = False
    test_case = {}
    stream_array = []
    tcp_no = 98
    ts_no = 1
    tc_no = 1
    t_no = 1
    selected_obj = None
    full_message = True

    def __init__(self):
        super().__init__()
        proxy = QNetworkProxy()
        proxy.setType(QNetworkProxy.NoProxy)
        QNetworkProxy.setApplicationProxy(proxy)

        self.sock = SimSocket(self.get_from_sim)
        self.init_action()
        self.init_menu()
        self.init_main_toolbar()
        self.init_action_toolbar()
        self.init_sim_toolbar()
        self.init_dock_project_tree()
        self.init_dock_object_settings()
        self.init_dock_logging()
        self.init_center()
        self.setGeometry(100, 100, 1000, 700)
        self.setWindowTitle("TestTool")
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.send_sim)
        self.show()
        self.set_custom_styles(CSS_FILE)

    def set_custom_styles(self, css_file):
        if os.path.exists(css_file):
            with open(css_file) as css_data:
                self.setStyleSheet(css_data.read())

    def init_action(self):
        self.open_action = QAction("&Open", self)
        self.open_action.triggered.connect(self.show_open_dialog)

        self.exit_action = QAction("&Exit", self)
        self.exit_action.triggered.connect(qApp.quit)

        self.rotate_right_action = QAction("&Rotate right", self)
        self.rotate_left_action = QAction("&Rotate left", self)

        self.proj_settings_action = QMenu("&Project settings", self)
        self.color_settings = QAction("Yard colors", self)
        self.color_settings.triggered.connect(self.show_color_settings)
        self.proj_settings_action.addAction(self.color_settings)

        self.program_settings_action = QAction("&Program settings", self)
        self.logic_view_action = QAction("&Logic plane", self)

    def show_color_settings(self):
        color_window = ObjectColorWindow(self.objects_colors, self.visual_objects)
        color_window.exec_()

    def init_menu(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("&File")
        settings_menu.addAction(self.open_action)
        settings_menu.addAction(self.exit_action)
        settings_menu = menubar.addMenu("&Settings")
        settings_menu.addAction(self.color_settings)

    def init_main_toolbar(self):
        self.main_toolbar = self.addToolBar("Main Tool Bar")
        self.main_toolbar.addAction(self.open_action)

    def init_action_toolbar(self):
        self.action_toolbar = self.addToolBar("Action Tool Bar")
        self.action_toolbar.addAction(self.rotate_right_action)
        self.action_toolbar.insertSeparator(self.rotate_right_action)
        self.action_toolbar.addAction(self.rotate_left_action)

    def init_dock_project_tree(self):
        self.docked_left = QDockWidget("Project explorer", self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.docked_left)
        docked_left_widget = QWidget(self)
        self.docked_left.setWidget(docked_left_widget)
        grid_dock_left = QGridLayout()
        docked_left_widget.setLayout(grid_dock_left)
        self.project_tree = QTreeWidget()

        self.project_tree.itemClicked.connect(self.select_tree_item)
        self.project_tree.currentItemChanged.connect(self.select_tree_item)
        self.project_tree.setHeaderLabel("Project model")
        self.object_search_edit = QLineEdit()
        self.object_search_button = QPushButton("Search")
        self.object_search_button.clicked.connect(self.find_object)

        grid_dock_left.addWidget(self.object_search_edit, 0, 0)
        grid_dock_left.addWidget(self.object_search_button, 0, 1)
        grid_dock_left.addWidget(self.project_tree, 1, 0, 2, 2)

    def init_sim_toolbar(self):
        self.simulation_toolbar = self.addToolBar("Simulation tool bar")

        def create_e_action(name):
            action = QAction(name, self)
            action.triggered.connect(self.do_sim_action)
            self.simulation_toolbar.addAction(action)

        for action in self.sim_actions:
            create_e_action(action)

    def create_new_property_tab(self, tab_data, rows=max_settings_rows):
        header_len = len(tab_data)
        new_tab = QTableWidget()
        new_tab.setColumnCount(header_len)
        tab_header = [x[0] for x in tab_data]
        new_tab.setHorizontalHeaderLabels(tab_header)
        new_tab.setRowCount(rows)

        for row_num in range(0, rows):
            new_tab.hideRow(row_num)
            for column_num, (col_name, widget, func) in enumerate(tab_data):
                if widget == "label":
                    new_item = QTableWidgetItem()
                    new_item.setFlags(new_item.flags()
                                      & ~Qt.ItemIsEditable)
                    new_tab.setItem(row_num, column_num, new_item)
                else:
                    new_item = CustomSpinBox()
                    new_tab.setCellWidget(row_num, column_num, new_item)
                if func:
                    new_item.valueChanged.connect(func)
        new_tab.setFont(self.obj_properties_font)
        return new_tab

    def init_dock_object_settings(self):
        self.docked_right = QDockWidget("Object properties", self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.docked_right)
        self.right_dock_widget = QWidget(self)
        self.right_dock_widget.setMinimumSize(400, 300)
        self.docked_right.setWidget(self.right_dock_widget)
        self.right_dock_grid = QGridLayout()
        self.right_dock_widget.setLayout(self.right_dock_grid)

        self.logic_property_widget = QTabWidget()

        self.rigth_dock_tab = QToolBox()
        # Properties tab
        tab_data = [("Name", "label", None),
                    ("Value", "spin", self.send_change_ibit),
                    ("Description", "label", None),
                    ]

        self.ibit_table = self.create_new_property_tab(tab_data)
        self.ibit_table.setColumnWidth(1, 80)
        self.ibit_table.setColumnWidth(2, 100)

        tab_data = [("Order", "label", None),
                    ("Object/Check", "label", None),
                    ("Value", "label", None),
                    ]
        self.free_wired_table = self.create_new_property_tab(tab_data)

        tab_data = [("Status", "label", None),
                    ("IPU object", "label", None),
                    ("Value", "spin", self.set_status),
                    ]
        self.status_table = self.create_new_property_tab(tab_data)

        tab_data = [("Order", "label", None),
                    ("IPU object", "label", None),
                    ("Value", "label", None),
                    ]
        self.order_table = self.create_new_property_tab(tab_data)

        tab_data = [("Name", "label", None),
                    ("COS object", "label", None),
                    ("Value", "label", None),
                    ]
        self.indication_table = self.create_new_property_tab(tab_data)

        tab_data = [("Name", "label", None),
                    ("Value", "label", None),
                    ]
        self.variable_table = self.create_new_property_tab(tab_data)

        tab_data = [("Name", "label", None),
                    ("IN", "label", None),
                    ("OUT", "label", None),
                    ]

        self.channel_table = self.create_new_property_tab(tab_data)

        self.logic_property_widget.addTab(self.ibit_table, "I_BIT")
        self.logic_property_widget.addTab(self.free_wired_table, "Free wired")
        self.logic_property_widget.addTab(self.status_table, "Status")
        self.logic_property_widget.addTab(self.order_table, "Orders")
        self.logic_property_widget.addTab(self.indication_table, "Indications")
        self.logic_property_widget.addTab(self.variable_table, "Variables")
        self.logic_property_widget.addTab(self.channel_table, "Channels")

        self.rigth_dock_tab.addItem(self.logic_property_widget, "Property")

        name_label = QLabel("Name:")
        name_label.setFixedWidth(35)
        type_label = QLabel("Type:")
        type_label.setFixedWidth(25)

        self.object_name_edit = QLabel("")
        self.obj_type_lable = QLabel("test")
        self.obj_type_lable.setFixedWidth(80)

        self.right_dock_grid.addWidget(name_label, 0, 0)
        self.right_dock_grid.addWidget(self.object_name_edit, 0, 1, 1, 2)
        self.right_dock_grid.addWidget(type_label, 0, 3)
        self.right_dock_grid.addWidget(self.obj_type_lable, 0, 4)
        self.right_dock_grid.addWidget(self.rigth_dock_tab, 1, 0, 1, 5)
        # Component tab
        tab_data = [("Command", "label", None),
                    ("Parameters", "label", None),
                    ]

        self.command_table = self.create_new_property_tab(tab_data, 300)
        self.command_table.cellDoubleClicked.connect(self.send_component)

        self.rigth_dock_tab.addItem(self.command_table, "Components")
        # sim connect tab
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_eqsim)
        self.sock.state_button = self.connect_button
        self.connect_button.setMinimumSize(40, 60)
        self.eqsim_addr = QLineEdit("192.168.0.6")
        self.eqsim_port = QLineEdit("9090")
        self.st_id_spin = CustomSpinBox()
        self.st_id_spin.setMinimum(1)
        self.st_id_spin.valueChanged.connect(self.set_stantion_id)
        self.sim_ratio_aspect = CustomSpinBox()
        self.sim_ratio_aspect.setMinimum(1)
        self.start_sim_button = QPushButton("Start simulation")
        self.start_sim_button.clicked.connect(self.start_sim_timer)
        self.tc_start_button = QPushButton("Start test recording")
        self.tc_start_button.clicked.connect(self.start_test_recording)
        self.save_tc_button = QPushButton("Save test case")
        self.save_tc_button.clicked.connect(self.save_test_case)
        self.add_read_cp_button = QPushButton("Add StartCP")
        self.add_read_cp_button.clicked.connect(self.add_read_cp_to_tc)

        self.sim_layout = QGridLayout()
        self.sim_layout.addWidget(QLabel("ADDRESS:"), 0, 0, 1, 1)
        self.sim_layout.addWidget(QLabel("PORT:"), 1, 0, 1, 1)
        self.sim_layout.addWidget(QLabel("ILS ID:"), 2, 0, 1, 1)
        self.sim_layout.addWidget(QLabel("RATIO:"), 3, 0, 1, 1)

        self.sim_layout.addWidget(self.eqsim_addr, 0, 1, 1, 1)
        self.sim_layout.addWidget(self.eqsim_port, 1, 1, 1, 1)
        self.sim_layout.addWidget(self.st_id_spin, 2, 1, 1, 1)
        self.sim_layout.addWidget(self.sim_ratio_aspect, 3, 1, 1, 1)
        self.sim_layout.addWidget(self.connect_button, 4, 0, 1, 2)
        self.sim_layout.addWidget(self.start_sim_button, 5, 0, 1, 2)

        sim_spacer = QSpacerItem(20, 40,
                                 QSizePolicy.Minimum,
                                 QSizePolicy.Expanding)
        self.sim_layout.addItem(sim_spacer)
        simulation_widget = QWidget()
        simulation_widget.setLayout(self.sim_layout)
        self.rigth_dock_tab.addItem(simulation_widget, "Simulation")

        self.test_layout = QGridLayout()
        self.tcp_spin = CustomSpinBox()
        self.tcp_spin.setValue(98)
        self.ts_spin = CustomSpinBox()
        self.ts_spin.setValue(1)
        self.tc_spin = CustomSpinBox()
        self.tc_spin.setValue(1)
        self.t_spin = CustomSpinBox()
        self.t_spin.setValue(1)

        self.test_layout.addWidget(QLabel("TCP_NO"), 0, 0, 1, 1)
        self.test_layout.addWidget(self.tcp_spin, 0, 1, 1, 1)
        self.test_layout.addWidget(QLabel("TS_NO"), 0, 2, 1, 1)
        self.test_layout.addWidget(self.ts_spin, 0, 3, 1, 1)
        self.test_layout.addWidget(QLabel("TC_NO"), 0, 4, 1, 1)
        self.test_layout.addWidget(self.tc_spin, 0, 5, 1, 1)
        self.test_layout.addWidget(QLabel("T_NO"), 0, 6, 1, 1)
        self.test_layout.addWidget(self.t_spin, 0, 7, 1, 1)

        self.test_layout.addWidget(self.tc_start_button, 1, 0, 1, 8)
        self.test_layout.addWidget(self.add_read_cp_button, 2, 0, 1, 8)
        self.test_layout.addWidget(self.save_tc_button, 3, 0, 1, 8)

        test_spacer = QSpacerItem(20, 40,
                                  QSizePolicy.Minimum,
                                  QSizePolicy.Expanding)

        test_widget = QWidget()
        self.test_layout.addItem(test_spacer)
        test_widget.setLayout(self.test_layout)

        self.open_case_button = QPushButton("Open test case")
        self.open_case_button.clicked.connect(self.show_open_test)
        self.test_layout.addWidget(self.open_case_button, 8, 0, 1, 8)
        self.play_case_button = QPushButton("Send test case")
        self.play_case_button.clicked.connect(self.run_test_cases)
        self.test_layout.addWidget(self.play_case_button, 9, 0, 1, 8)
        self.rigth_dock_tab.addItem(test_widget, "Test case")

    def set_stantion_id(self):
        self.st_id = self.st_id_spin.value()

    def init_dock_logging(self):
        self.docked_logging = QDockWidget("Logging", self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.docked_logging)
        self.eqsim_log = QPlainTextEdit("")
        self.eqsim_log.setReadOnly(True)
        self.docked_logging.setWidget(self.eqsim_log)

    def init_center(self):
        self.scen = QGraphicsScene(0, 0, 1700, 1700)
        self.scen.setBackgroundBrush(QBrush(QColor("white"), Qt.SolidPattern))
        self.view = CustomGraphicsView()
        self.view.setScene(self.scen)
        self.setCentralWidget(self.view)

    def open_site_data(self, config_path=ils_path):
        ils_path = str(Path(config_path).parent.absolute())
        # ils_path = config_path[0:config_path.rfind("/") + 1]
        if not os.path.exists(config_path):
            return
        self.clear_logical_site()
        self.config_info = config_reader(config_path)

        rcad_scene = os.path.join(ils_path, "LogicScene.xml")
        yard_scene = os.path.join(ils_path, "yard.xml")

        for key in ("CommandTable", "IntData", "ILL_STERNOL_FILE"):
            self.site_keys[key] = get_path_to_key(self.config_info, key)

        if os.path.exists(rcad_scene):
            self.rcad_data = read_scene_data(rcad_scene)
        elif os.path.exists(yard_scene):
            self.rcad_data = read_scene_data(yard_scene)
        else:
            return
        self.scen.setSceneRect(0,
                               -self.rcad_data["sceneHeight"],
                               self.rcad_data["sceneWidth"] + 1000,
                               self.rcad_data["sceneHeight"])

        comm_table_path = self.site_keys["CommandTable"]
        int_data_path = self.site_keys["IntData"]
        ste_path = self.site_keys["ILL_STERNOL_FILE"]

        if os.path.exists(comm_table_path):
            command_table_file = open(comm_table_path)
            self.site_command_table = command_data_parser(command_table_file)
            self.site_components = self.site_command_table["Components"]
            command_table_file.close()
        else:
            return

        import_funcs = [(self.import_com_data, comm_table_path),
                        (self.import_int_data, int_data_path),
                        (self.import_logic_data, ste_path)]

        for func, attr in import_funcs:
            results = func(attr)
            if not results:
                logging.error("Error import")
                return

        self.build_project_tree()
        self.create_logical_objects_views()
        self.connect_all_objects()

    def set_pos_from_obj_with_legs(self, objs_with_legs):
        for name in objs_with_legs:
            log_obj = self.logical_objects_site[name]
            v_obj = self.visual_objects[name]
            x_n_poses = []
            y_n_poses = []
            for leg in log_obj["legs"]:
                neighbour = log_obj["legs"][leg]["neighbour"]
                n_obj = self.visual_objects[neighbour]
                neigh_pos = n_obj.object_view.pos()
                new_x = abs(neigh_pos.x())
                new_y = abs(neigh_pos.y())
                if new_x > 10:
                    x_n_poses.append(new_x)
                if new_y > 10:
                    y_n_poses.append(new_y)
            x_avg = mean(x_n_poses) if x_n_poses else 0
            y_avg = mean(y_n_poses) if y_n_poses else 0

            v_obj.move(x_avg, y_avg)

    def set_average_pos(self, without_pos):
        faulty_pos_x = 1000
        faulty_pos_y = self.rcad_data["sceneHeight"] - 250
        obj_with_legs = []
        for name in without_pos:
            log_obj = self.logical_objects_site[name]
            if log_obj["legs"]:
                obj_with_legs.append(name)
            else:
                v_obj = self.visual_objects[name]
                v_obj.move(faulty_pos_x,
                           faulty_pos_y)
                faulty_pos_x += 100
        for x in range(5):
            self.set_pos_from_obj_with_legs(obj_with_legs)

    def create_logical_objects_views(self):
        without_pos = []
        for z_level, name in enumerate(self.logical_objects_site):
            log_data = self.logical_objects_site[name]

            new_obj = LogicalObject(name, log_data, z_level, self.scen,
                                    self.objects_colors, self.project_tree)

            if name in self.rcad_data:
                matrix = QTransform(self.rcad_data[name]["m11"],
                                    -self.rcad_data[name]["m12"],
                                    self.rcad_data[name]["m21"],
                                    -self.rcad_data[name]["m22"],
                                    new_obj.object_view.size().width() / 2,
                                    new_obj.object_view.size().height() / 2)

                new_obj.object_view.apply_matrix(matrix)
                new_obj.move(self.rcad_data[name]["x"],
                             self.rcad_data[name]["y"])

            else:
                without_pos.append(name)

            self.visual_objects[name] = new_obj

        logging.error(without_pos)
        self.set_average_pos(without_pos)

    def connect_all_objects(self):

        for name in self.visual_objects:
            legs = self.visual_objects[name].object_view.object_legs

            for current_leg in legs:
                if not current_leg.connector:
                    neighbour_leg = self.get_neighbour_leg(name,
                                                           current_leg.leg)
                    new_connector = LogicalConnector(current_leg, neighbour_leg)
                    self.scen.addItem(new_connector)

    def get_neighbour_leg(self, log_name, from_leg):
        legs = self.logical_objects_site[log_name]["legs"][from_leg]
        n_name = legs["neighbour"]
        n_leg = int(legs["neighbour_leg"])
        leg = self.visual_objects[n_name].object_view.object_legs[n_leg]
        return leg

    def import_com_data(self, comm_table_path):
        if os.path.exists(comm_table_path):
            com_data_file = open(comm_table_path)
            self.com_data = command_data_parser(com_data_file)
            self.components_site = self.com_data["Components"]
            com_data_file.close()
            return True

    def import_int_data(self, int_data_path):
        if os.path.exists(int_data_path):
            with open(int_data_path) as int_data_file:
                self.int_data = interlocking_data_parser(int_data_file)
                self.logical_objects_site = self.int_data["Logical_objects"]

                self.ipu_objects_site = self.int_data["IPU_objects"]
                self.stantion_name = self.int_data["Site_product_name"]

            return True

    def add_variable_from_logic(self, obj, obj_type):
        for key in self.logic_data[obj_type]["#OWN"]:
            init = self.logic_data[obj_type]["#OWN"][key]["init"]
            if "variables" not in self.logical_objects_site[obj]:
                self.logical_objects_site[obj]["variables"] = {key: {"value": init}}
            else:
                self.logical_objects_site[obj]["variables"][key] = {"value": init}

    def add_chennel_from_logic(self, obj, obj_type):
        if "#INOUT" not in self.logic_data[obj_type]:
            return
        for key in self.logic_data[obj_type]["#INOUT"]:
            t = self.logic_data[obj_type]["#INOUT"][key]
            print(self.logic_data[obj_type]["#INOUT"][key])
            in_channel = self.logic_data[obj_type]["#INOUT"][key]['0']["init"]
            out_channel = self.logic_data[obj_type]["#INOUT"][key]['0']["init"]
            in_out_data = {"IN": in_channel, "OUT": out_channel}
            if "channels" not in self.logical_objects_site[obj]:
                self.logical_objects_site[obj]["channels"] = {key: in_out_data}
            else:
                self.logical_objects_site[obj]["channels"][key] = in_out_data

    def add_ibit_from_logic(self, obj, obj_type):
        all_i_bit = logic_reader.get_ibits_list(obj_type, self.logic_data)
        obj_i_bit = self.logical_objects_site[obj]["individualizations"]
        new_i_bit = [x for x in all_i_bit if x not in obj_i_bit]

        for i_bit in new_i_bit:
            default_val = logic_reader.get_default_value(i_bit,
                                                         obj_type,
                                                         self.logic_data)

            obj_i_bit[i_bit] = default_val

    def add_orders_from_logic(self, obj, obj_type):
        if "#OUT" not in self.logic_data[obj_type]:
            return

        ste_orders = logic_reader.get_orders(obj_type, self.logic_data)

        if not ste_orders:
            return

        if "orders" in self.logical_objects_site[obj]:
            obj_orders = self.logical_objects_site[obj]["orders"]
            new_orders = [x for x in ste_orders if x not in obj_orders]
            for order in new_orders:
                obj_orders[order] = {"ipu": "", "value": ""}
        else:
            obj_orders = {}
            for order in ste_orders:
                obj_orders[order] = {"ipu": "", "value": ""}
            self.logical_objects_site[obj]["orders"] = obj_orders
        logic_ofw = logic_reader.get_ofw(obj_type, self.logic_data)
        obj_ofw = self.logical_objects_site[obj]["ofw"]
        if logic_ofw:
            new_ofw = [x for x in logic_ofw if x not in obj_ofw]
            for order in new_ofw:
                self.logical_objects_site[obj]["ofw"][order] = {"ipu": "",
                                                                "value": ""}

    def add_indication_from_logic(self, obj, obj_type):
        obj_indication = self.logical_objects_site[obj]["indication"]
        for indication in self.logical_objects_site[obj]["indication"]:
            cos = self.logical_objects_site[obj]["indication"][indication]
            obj_indication[indication] = {"cos": cos, "value": ""}

        logic_ind = logic_reader.get_status(obj_type, self.logic_data)
        for indication in logic_ind:
            if indication not in obj_indication:
                obj_indication[indication] = {"cos": "", "value": ""}

    def add_status_from_logic(self, obj, obj_type):
        sternol_status = logic_reader.get_checks(obj_type, self.logic_data)
        obj_status = self.logical_objects_site[obj]["status"]
        new_status = [x for x in sternol_status if x not in obj_status]
        for status in new_status:
            obj_status[status] = {"ipu": "", "value": ""}
        for status in obj_status:
            if status.count("."):
                continue

            init = self.logic_data[obj_type]["#IN"][status]["init"]
            if status in self.logic_data[obj_type]["#IN"]:
                obj_status[status]["value"] = init
            else:
                logging.error("not compatible with site data")
                return

    def import_logic_data(self, ste_path):
        if not os.path.exists(ste_path):
            logging.error("NO FOUND ILL FILE")
            return
        self.logic_data = logic_reader.read_logic(ste_path)
        new_object_types = [x for x in self.logic_data
                            if x[0] != "#" and x not in self.objects_colors]
        for object_type in new_object_types:
            self.objects_colors[object_type] = "#c6cdda"

        for obj in self.logical_objects_site:
            obj_type = self.logical_objects_site[obj]["Type"]
            if not self.logic_data.get(obj_type):
                continue
            if "#OWN" in self.logic_data.get(obj_type):
                self.add_variable_from_logic(obj, obj_type)
            else:
                self.logical_objects_site[obj]["variables"] = {"value": ""}

            self.add_chennel_from_logic(obj, obj_type)
            self.add_ibit_from_logic(obj, obj_type)
            self.add_orders_from_logic(obj, obj_type)
            self.add_indication_from_logic(obj, obj_type)
            self.add_status_from_logic(obj, obj_type)
        return True

    def build_project_tree(self):
        self.project_tree.clear()
        self.tree_widget = QTreeWidgetItem()
        self.tree_widget.setText(0, self.stantion_name)
        self.objects_tree = QTreeWidgetItem(self.tree_widget)

        self.objects_tree.setText(0, "Logical objects")

        self.ipu_tree = QTreeWidgetItem(self.tree_widget)
        self.ipu_tree.setText(0, "IPU objects")

        self.components_tree = QTreeWidgetItem(self.tree_widget)
        self.components_tree.setText(0, "Components")

        self.build_tree(self.logical_objects_site, self.objects_tree)
        self.build_tree(self.ipu_objects_site, self.ipu_tree)
        self.build_commands_tree(self.components_site, self.components_tree)
        self.project_tree.addTopLevelItem(self.tree_widget)

    def get_all_types(self, obj_data):
        all_types = [obj_data[x]["Type"] for x in obj_data]
        return set(all_types)

    def get_objects_of_type(self, target_types, obj_data):
        target_objs = [x for x in obj_data
                       if obj_data[x]["Type"] == target_types]
        target_objs.sort()
        return target_objs

    def build_tree(self, obj_data, out_tree):

        for obj_type in self.get_all_types(obj_data):
            obj_tree = QTreeWidgetItem(out_tree)
            obj_tree.setText(0, obj_type)
            target_objs = self.get_objects_of_type(obj_type, obj_data)
            for obj in target_objs:
                obj_item = QTreeWidgetItem(obj_tree)
                obj_item.setText(0, obj)
                if obj in self.logical_objects_site:
                    self.logical_objects_site[obj]["tree_item"] = obj_item

    def build_commands_tree(self, components_data, out_tree):
        for component_type in components_data:
            type_tree = QTreeWidgetItem(out_tree)
            type_tree.setText(0, component_type)
            target_objs = components_data[component_type]
            for obj in target_objs:
                obj_item = QTreeWidgetItem(type_tree)
                obj_item.setText(0, obj)
                for component in components_data[component_type][obj]:
                    component_tree = QTreeWidgetItem(component)
                    component_header = (component_type + "-" +
                                        "-".join(component["Parameters"]))
                    component_tree.setText(0, component_header)

    def clear_logical_site(self):
        self.selected_obj = None
        for obj in self.visual_objects:
            self.visual_objects[obj].deleteLater()
        self.visual_objects.clear()
        self.project_tree.clear()
        self.scen.clear()
        self.obj_properties_clear()

    def show_open_test(self):
        path_to_tc = QFileDialog.getOpenFileName(self,
                                                 "Open test case",
                                                 self.ils_path,
                                                 "TestCase (*.xml)")
        self.test_case = read_test_file(path_to_tc[0])

    def show_open_dialog(self):
        path_to_ci = QFileDialog.getOpenFileName(self,
                                                 "Open file",
                                                 self.ils_path,
                                                 "ConfigInfo (*.CI)")
        self.open_site_data(path_to_ci[0])

    def hide_non_used_rows(self, target_table, start_row):
        for row_num in range(start_row + 1, self.max_settings_rows):
            target_table.hideRow(row_num)

    def config_obj_settings_ibit(self, obj_name):
        out_table = self.ibit_table
        i_bits = self.logical_objects_site[obj_name]["individualizations"]
        max_row_num = -1
        for row_num, column_data in enumerate(i_bits.items()):
            for col_num, col_value in enumerate(column_data):
                cell_widget = out_table.cellWidget(row_num, col_num)
                if cell_widget:
                    cell_widget.setValue(int(col_value))
                    cell_widget.name = column_data[0]
                else:
                    out_table.item(row_num, col_num).setText(col_value)
            out_table.showRow(row_num)
            max_row_num = row_num
        self.hide_non_used_rows(out_table, max_row_num)

    def config_obj_settings_other(self, obj_name, settings_name, out_table):
        settings_data = self.logical_objects_site[obj_name][settings_name]

        sorted_keys = sorted(settings_data)
        max_row_num = -1
        for row_num, name in enumerate(sorted_keys):
            column_data = settings_data[name]

            out_table.item(row_num, 0).setText(name)
            if settings_name in ("status", "orders", "indication", "ofw"):
                if settings_name == "indication":
                    ipu = column_data["cos"]
                else:
                    ipu = column_data["ipu"]
                value = column_data["value"]
                value_widget = out_table.cellWidget(row_num, 2)
                if isinstance(ipu, list):
                    ipu = [x + "." + y for x in ipu[::2] for y in ipu[1::2]]
                    ipu = ",".join(ipu)
                out_table.item(row_num, 1).setText(ipu)
                if settings_name == "status":
                    value_widget.setValue(int(value))
                    value_widget.name = name
                else:
                    out_table.item(row_num, 2).setText(value)
            else:
                if "value" not in column_data:
                    continue
                value = column_data["value"]
                out_table.item(row_num, 1).setText(value)
            max_row_num = row_num
            out_table.showRow(row_num)
        self.hide_non_used_rows(out_table, max_row_num)

    def config_obj_channels(self, obj_name):
        max_row_num = -1
        out_table = self.channel_table
        channels = self.logical_objects_site[obj_name].get("channels")
        if channels:
            for row_num, column_data in enumerate(channels.items()):
                for col_num, col_value in enumerate(column_data):
                    if isinstance(col_value, dict):
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
        self.hide_non_used_rows(out_table, max_row_num)

    def config_components(self, obj_name):
        out_table = self.command_table
        current_row = 0
        for comp_type in self.components_site:
            if obj_name not in self.components_site[comp_type]:
                continue
            for component in self.components_site[comp_type].get(obj_name):
                out_table.item(current_row, 0).setText(comp_type)
                parameters = " ".join(component["Parameters"])
                out_table.item(current_row, 1).setText(parameters)
                out_table.showRow(current_row)
                current_row += 1
        self.hide_non_used_rows(out_table, current_row)

    def config_settings(self, obj_name):
        self.config_obj_settings_ibit(obj_name)
        self.config_obj_settings_other(obj_name, "orders",
                                       self.order_table)
        self.config_obj_settings_other(obj_name, "status",
                                       self.status_table)
        self.config_obj_settings_other(obj_name, "ofw",
                                       self.free_wired_table)
        self.config_obj_settings_other(obj_name, "indication",
                                       self.indication_table)
        self.config_obj_settings_other(obj_name, "indication",
                                       self.indication_table)
        self.config_obj_settings_other(obj_name, "variables",
                                       self.variable_table)
        self.config_obj_channels(obj_name)

    def obj_properties_clear(self):
        for table in (self.order_table,
                      self.status_table,
                      self.free_wired_table,
                      self.indication_table,
                      self.variable_table,
                      self.ibit_table,
                      self.channel_table,
                      self.command_table):
            self.hide_non_used_rows(table, 0)

    def select_tree_item(self, tree_item):
        if not tree_item:
            return
        obj_name = tree_item.text(0)
        if (obj_name in self.logical_objects_site
                and obj_name != self.selected_obj):
            self.change_object = True
            if self.connect_button.text() == "Disconnect":
                send_to_sim(self.sock, "{}/variables {}".format(self.st_id,
                                                                obj_name))
                self.sock.waitForReadyRead()

            if self.selected_obj:
                selected = self.visual_objects[self.selected_obj]
                selected.setSelected()
            selecting = self.visual_objects[obj_name]
            selecting.setSelected(1000)
            self.selected_obj = obj_name
            self.config_settings(obj_name)
            self.config_components(obj_name)
            self.change_object = False
            self.view.ensureVisible(selecting.object_view, 10, 10)

    def find_object(self):
        obj_name = self.object_search_edit.text()
        matches = self.project_tree.findItems(obj_name, Qt.MatchRecursive, 0)
        if matches:
            self.project_tree.setCurrentItem(matches[0])

    # -------------- EQSIM E ------------------------
    def normalise_objects(self):
        if self.connect_button.text() != "Disconnect":
            return
        objects = self.logical_objects_site
        for obj in self.logical_objects_site:
            if objects[obj]["Type"] == "FEED":
                if "C_AVP" in objects[obj]["status"]:
                    c_avp = objects[obj]["status"]["C_AVP"]["ipu"]
                    out_str = "{0}/yard {1} try_set 1".format(self.st_id, c_avp)
                    self.stream_array.append(out_str)
                    self.stream_array.append("{}/go\n".format(self.st_id))
            elif objects[obj]["Type"] == "SECTION":
                if objects[obj]["individualizations"]["I_Z"] == "0":
                    out_str = "{0}/cmd {1} {2}\n".format(self.st_id, "SEIR", obj)
                    self.stream_array.append(out_str)
                    self.stream_array.append("{}/go\n".format(self.st_id))
                    out_str = "{0}/cmd {1} {2}\n".format(self.st_id, "POK", obj)
                    self.stream_array.append(out_str)
                    self.stream_array.append("{}/break steady\n".format(self.st_id))
                    self.stream_array.append("{}/go\n".format(self.st_id))
                out_str = "{0}/cmd {1} {2}\n".format(self.st_id, "VKP", obj)
                self.stream_array.append(out_str)
                self.stream_array.append("{}/go\n".format(self.st_id))
                out_str = "{0}/cmd {1} {2}\n".format(self.st_id, "POK", obj)
                self.stream_array.append(out_str)
                self.stream_array.append("{}/break steady\n".format(self.st_id))
                self.stream_array.append("{}/go\n".format(self.st_id))
            elif objects[obj]["Type"] == "BUFFER":
                if "C_UP" in objects[obj]["status"]:
                    c_up = objects[obj]["status"]["C_UP"]["ipu"]
                    out_str = "{0}/yard {1} try_set 1".format(self.st_id, c_up)
                elif "C_POS" in objects[obj]["status"]:
                    c_pos = objects[obj]["status"]["C_POS"]["ipu"]
                    out_str = ("{0}/yard {1} try_set is_left" +
                               "_central_working".format(self.st_id, c_pos))
                self.stream_array.append(out_str)
            elif objects[obj]["Type"] == "INTERFACE":
                if objects[obj]["individualizations"]["I_KG"] != "0":
                    if "VKS" in self.components_site:
                        out_str = "{0}/cmd {1} {2}\n".format(self.st_id,
                                                             "VKS", obj)
                        self.stream_array.append(out_str)
                    elif ("COM1" in self.components_site
                          and obj in self.components_site["COM1"]):

                        out_str = "{0}/cmd {1} {2}\n".format(self.st_id,
                                                             "COM1",
                                                             obj)
                        self.stream_array.append(out_str)
                    elif "C_KD" in objects[obj]["status"]:
                        c_kd = objects[obj]["status"]["C_KD"]["ipu"]
                        out_str = "{0}/yard {1} try_set 1".format(self.st_id,
                                                                  c_kd)
                        self.stream_array.append(out_str)
                        self.stream_array.append("{}/go\n".format(self.st_id))
                        out_str = "{0}/yard {1} try_set 2".format(self.st_id,
                                                                  c_kd)
                        self.stream_array.append(out_str)
                        self.stream_array.append("{}/go\n".format(self.st_id))
                    message = "{}/break steady\n".format(self.st_id)
                    self.stream_array.append(message)
                    self.stream_array.append("{}/go\n".format(self.st_id))
            elif objects[obj]["Type"] == "POINT":
                if objects[obj]["individualizations"].get("I_REL") == "1":
                    c_mk = objects[obj]["status"]["C_MK"]["ipu"]
                    c_pk = objects[obj]["status"]["C_PK"]["ipu"]
                    out_str = "{0}/yard {1} try_set 2".format(self.st_id, c_mk)
                    self.stream_array.append(out_str)
                    out_str = "{0}/yard {1} try_set 1".format(self.st_id, c_pk)
                    self.stream_array.append(out_str)
                    message = "{}/break steady\n".format(self.st_id)
                    self.stream_array.append(message)
                    self.stream_array.append("{}/go\n".format(self.st_id))
        if self.full_message:
            send_to_sim(self.sock, "{}/go\n".format(self.st_id))

    def send_change_ibit(self):
        current_obj = self.project_tree.currentItem()

        if not self.change_object and self.sock and current_obj:
            obj_name = current_obj.text(0)
            if self.tc_start_button.text() == "Stop recording tests":
                tc_str = "illSetIbit {} {} {} {}".format(self.st_id,
                                                         obj_name,
                                                         self.sender().name,
                                                         self.sender().value()
                                                         )
                tw.add_event(tc_str)

            if self.connect_button.text() != "Disconnect":
                return
            send_str = "{0}/individ {1}.{2}={3}".format(self.st_id,
                                                        obj_name,
                                                        self.sender().name,
                                                        self.sender().value())
            send_to_sim(self.sock, send_str)

    def set_status(self):
        current_obj = self.project_tree.currentItem()
        if not current_obj or self.change_object:
            return
        current_obj = self.project_tree.currentItem()
        obj_name = current_obj.text(0)
        log_obj = self.logical_objects_site[obj_name]
        value = self.sender().value()
        status = log_obj["status"][self.sender().name]

        if status["ipu"] and not status["ipu"].count("."):
            send_str = "{0}/yard {1} try_set {2}".format(self.st_id,
                                                         status["ipu"],
                                                         value)
            if self.tc_start_button.text() == "Stop recording tests":
                value = "Free" if self.sender().value() == 2 else "Occ"
                test_str = "yardSetStatusTryCycles {} 0 {} {}"
                tw.add_event(test_str.format(self.st_id,
                                             status["ipu"],
                                             value))

        else:
            send_str = "{0}/check {1}.{2}={3}".format(self.st_id,
                                                      obj_name,
                                                      self.sender().name,
                                                      value)
            test_str = "illSetChcSeconds {} 1 {} {} {}"
            tw.add_event(test_str.format(self.st_id,
                                         obj_name,
                                         self.sender().name,
                                         value))

        if self.connect_button.text() == "Disconnect":
            send_to_sim(self.sock, send_str)

    def send_component(self, line, column):
        comm_type = self.command_table.item(line, 0).text()
        comm_param = self.command_table.item(line, 1).text()
        out_str = "{0}/cmd {1} {2}\n".format(self.st_id,
                                             comm_type,
                                             comm_param)
        if self.connect_button.text() == "Disconnect":
            send_to_sim(self.sock, out_str)
            self.sock.waitForReadyRead()
            send_to_sim(self.sock, "{}/go".format(self.st_id))
        if self.tc_start_button.text() == "Stop recording tests":
            tw.add_event("cosCmdSeconds {} 1 {} {}".format(self.st_id,
                                                           comm_type,
                                                           comm_param))

    def connect_to_eqsim(self):
        if self.connect_button.text() == "Connect":
            port = self.eqsim_port.text()
            addr = self.eqsim_addr.text()
            if port.isdigit() and not addr.isalpha():
                logging.info("connect:", addr, port)
                self.sock.connectToHost(addr, port)
                self.sock.send("{}/display +".format(self.st_id))
        else:
            self.sock.disconnectFromHost()
            logging.info("disconnected")

    def get_from_sim(self, log):
        if log.count("* > ") and log[-4:] == "* > ":
            self.temp_log += log
            self.eqsim_log.appendPlainText(log.replace("\\n", "\n"))
            self.full_message = True
            for data in self.temp_log.split("* > "):
                self.analyse_sim_data(data)
            self.temp_log = ""
            if self.stream_array:
                send_to_sim(self.sock, self.stream_array.pop(0))
        else:
            self.temp_log += log
            self.eqsim_log.appendPlainText(log.replace("\\n", "\n"))
            self.full_message = False

    def do_sim_action(self, *args, log=""):
        e_action = self.sender().text()
        is_data_to_sim = self.connect_button.text() == "Disconnect" and e_action != "FF"
        is_data_to_record = self.tc_start_button.text() == "Stop recording tests"
        if not is_data_to_sim:
            logging.info("NO CONNECTING")
            if not is_data_to_record:
                return
        if e_action == "GO":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/go\n".format(self.st_id))
            if is_data_to_record:
                tw.add_event("execGoCycles {} 1".format(self.st_id))
        elif e_action == "BS":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/break steady\n".format(self.st_id))
            if is_data_to_record:
                tw.add_event("execGoALL")
        elif e_action == "GOS":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/break seconds 1\n".format(self.st_id))
            if is_data_to_record:
                tw.add_event("execGoSeconds {} 1".format(self.st_id))
        elif e_action == "GOS5":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/break seconds 5\n".format(self.st_id))
            if is_data_to_record:
                tw.add_event("execGoSeconds {} 5".format(self.st_id))
        elif e_action == "GOS10":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/break seconds 10\n".format(self.st_id))
            if is_data_to_record:
                tw.add_event("execGoSeconds {} 10".format(self.st_id))
        elif e_action == "GOC":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/break after 1\n".format(self.st_id))
            if is_data_to_record:
                tw.add_event("execGoCycles {} 1".format(self.st_id))
        elif e_action == "GOC5":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/break after 5\n".format(self.st_id))
            if is_data_to_record:
                tw.add_event("execGoCycles {} 5".format(self.st_id))
        elif e_action == "GOC10":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/break after 10\n".format(self.st_id))
            if is_data_to_record:
                tw.add_event("execGoCycles {} 10".format(self.st_id))
        elif e_action == "GOALL":
            if is_data_to_sim:
                send_to_sim(self.sock, "go\n")
            if is_data_to_record:
                tw.add_event("execGoALL")
        elif e_action == "RF":
            if is_data_to_sim:
                send_to_sim(self.sock, "{}/variables *\n".format(self.st_id))
        elif e_action == "NR":
            if is_data_to_sim:
                self.normalise_objects()
        elif e_action == "FF":
            if os.path.exists(os.getcwd() + "/complete.log"):
                with open("complete.log") as log_file:
                    variablesValue = log_file_parser(log_file.readlines())
                    self.fill_sim_data(variablesValue)

    def fill_sim_data(self, data):
        obj_name = ""
        current_obj = self.project_tree.currentItem()
        if current_obj:
            obj_name = current_obj.text(0)
        for log_obj in data:
            if log_obj not in self.logical_objects_site:
                continue
            obj_data = self.logical_objects_site[log_obj]
            for variable in data[log_obj]:
                value = data[log_obj][variable].get("value")
                if variable in obj_data.get("status"):
                    obj_data["status"][variable]["value"] = value
                elif variable in obj_data.get("indication"):
                    obj_data["indication"][variable]["value"] = value
                elif variable in obj_data["orders"]:
                    obj_data["orders"][variable]["value"] = value
                elif variable in obj_data["variables"]:
                    obj_data["variables"][variable]["value"] = value
                elif ("channels" in obj_data
                      and variable in obj_data.get("channels")):
                    if "value" in data[log_obj][variable]:
                        obj_data["channels"][variable]["IN"] = value
                    if "valueOUT" in data[log_obj][variable]:
                        value = data[log_obj][variable].get("valueOUT")
                        obj_data["channels"][variable]["OUT"] = value
                elif variable in obj_data["ofw"]:
                    obj_data["ofw"][variable]["value"] = value
            if log_obj not in self.visual_objects:
                continue
            if log_obj == obj_name:
                self.change_object = True
                self.config_settings(log_obj)
                self.change_object = False
            self.visual_objects[log_obj].updateColor()

    def send_sim(self):
        if self.connect_button.text() == "Disconnect" and not self.temp_log:
            cycles = str(self.sim_ratio_aspect.value())
            message = "{}/break after {}\n".format(self.st_id, cycles)
            send_to_sim(self.sock, message)
            self.sock.waitForReadyRead()
            send_to_sim(self.sock, "{}/go".format(self.st_id))

    def start_sim_timer(self):
        if self.connect_button.text() == "Disconnect":
            if self.sim_timer.isActive():
                self.start_sim_button.setText("Start simulation")
                self.sim_timer.stop()
            else:
                self.start_sim_button.setText("Stop simulation")
                self.sim_timer.start(1000)

    def analyse_sim_data(self, log):
        current_obj = self.project_tree.currentItem()
        if current_obj:
            obj_name = current_obj.text(0)
        else:
            obj_name = ""
        if log.count("!") or log.count(" [ "):
            variables_values = log_file_parser(log.split("\\n"))
            self.fill_sim_data(variables_values)
        elif log.count(" = ") and log[0] not in ("!", "*", " "):
            obj = "" if log.count(".") else obj_name
            variables_values = object_variable_parser(log.split("\\n"), obj)
            self.fill_sim_data(variables_values)
        else:
            logging.info("another data")

    def start_test_recording(self):
        if self.tc_start_button.text() == "Start test recording":
            date = datetime.datetime.now().strftime("%d-%m-%Y-%H-%M")
            tw.create_xml_file("{}_{}.xml".format(self.tcp_spin.value(), date))
            tw.write_file_header()
            tw.write_function_header("TestCAD script")
            tw.write_testsuite_header("TestCAD script")
            tcId = "%d.%d.%d.%d" % (self.tcp_spin.value(),
                                    self.ts_spin.value(),
                                    self.tc_spin.value(),
                                    self.t_spin.value())
            tId = "%s" % (tcId)
            tw.write_testcase_header(tcId, "")
            tw.set_id(tId)
            tw.set_comment("TestCAD test case")
            tw.add_init("ilsInitCurrent {}".format(self.st_id))
            tw.add_init("ilsLoadCurrent {}".format(self.st_id))
            tw.add_init("execGoCycles {} 45".format(self.st_id))
            tw.add_init("ilsCheckpointRead {} StartCP".format(self.st_id))
            tw.add_init("execGoCycles {} 45".format(self.st_id))
            self.tc_start_button.setText("Stop recording tests")
        else:
            self.tc_start_button.setText("Start test recording")
            if len(tw.out_array) < 15:
                tw.out_array.clear()
            else:
                tw.write_subtest_obj()
                tw.write_testcase_footer()
                tw.write_testsuite_footer()
                tw.write_function_footer()
                tw.write_file_footer()
                tw.close_xml_file()
                current_ts_no = self.ts_spin.value() + 1
                self.ts_spin.setValue(current_ts_no)

    def save_test_case(self):
        if (self.tc_start_button.text() != "Start test recording"
                and tw.test_event_array):
            tw.write_subtest_obj()
            tw.write_testcase_footer()
            current_t_no = self.t_spin.value() + 1
            self.t_spin.setValue(current_t_no)

            tcId = "%d.%d.%d.%d" % (self.tcp_spin.value(),
                                    self.ts_spin.value(),
                                    self.tc_spin.value(),
                                    self.t_spin.value())
            tId = "%s" % (tcId)
            tw.write_testcase_header(tcId, "")
            tw.set_id(tId)
            tw.set_comment("FailCAD test case")

    def add_read_cp_to_tc(self):
        if self.tc_start_button.text() != "Start test recording":
            tw.add_init("ilsCheckpointRead {} StartCP".format(self.st_id))
            tw.add_init("execGoCycles {} 45".format(self.st_id))

    def run_test_cases(self):
        if self.connect_button.text() == "Disconnect":
            for case in self.test_case:
                for event in self.test_case[case]:
                    self.stream_array.append(event)
            self.test_case.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = QSplashScreen()
    splash.setPixmap(QPixmap("static/start_screen.gif"))
    splash.show()

    main_form = MainWindow()
    main_form.show()

    splash.finish(main_form)

    app.exec_()
