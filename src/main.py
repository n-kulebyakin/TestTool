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


class SiteWindow(ImportSiteDataMixin, MainWindow):
    _css_file = "static/style.css"

    def __init__(self):
        super().__init__()
        self.objects_colors = OBJECT_COLORS
        self._visual_objects = {}
        self._selected_obj = None
        self._changing_object = False
        pt = self.project_explorer.project_tree
        pt.itemClicked.connect(self.select_tree_item)
        pt.currentItemChanged.connect(self.select_tree_item)
        self.set_custom_styles(self._css_file)
        self._color_window = ObjectColorWindow(self.objects_colors,
                                               self._visual_objects)

    def set_custom_styles(self, css_file):
        if os.path.exists(css_file):
            with open(css_file) as css_data:
                self.setStyleSheet(css_data.read())

    def create_objects_views(self):
        without_pos = []
        self.view.scene.setSceneRect(0,
                                     -self._coordinates["sceneHeight"],
                                     self._coordinates["sceneWidth"] + 1000,
                                     self._coordinates["sceneHeight"])
        for deep, name in enumerate(self._logical_objects):
            log_data = self._logical_objects[name]

            new_obj = LogicalObject(name, log_data, deep, self.view.scene,
                                    self.objects_colors,
                                    self.project_explorer.project_tree)

            if name in self._coordinates:
                obj_coordinate = self._coordinates[name]
                matrix = QTransform(obj_coordinate["m11"],
                                    -obj_coordinate["m12"],
                                    obj_coordinate["m21"],
                                    -obj_coordinate["m22"],
                                    new_obj.size().width() / 2,
                                    new_obj.size().height() / 2)

                new_obj.apply_matrix(matrix)
                new_obj.move(obj_coordinate["x"],
                             obj_coordinate["y"])
            else:
                without_pos.append(name)

            self._visual_objects[name] = new_obj

        self.set_average_pos(without_pos)

    def set_average_pos(self, without_pos):
        faulty_pos_x = 1000
        faulty_pos_y = self._coordinates["sceneHeight"] - 250
        obj_with_legs = []
        for name in without_pos:
            log_obj = self._logical_objects[name]
            if log_obj["legs"]:
                obj_with_legs.append(name)
            else:
                v_obj = self._visual_objects[name]
                v_obj.move(faulty_pos_x,
                           faulty_pos_y)
                faulty_pos_x += 100
        for _ in range(5):
            self.set_pos_from_obj_with_legs(obj_with_legs)

    def set_pos_from_obj_with_legs(self, objs_with_legs):
        for name in objs_with_legs:
            log_obj = self._logical_objects[name]
            v_obj = self._visual_objects[name]
            x_n_poses = []
            y_n_poses = []
            for leg in log_obj["legs"]:
                neighbour = log_obj["legs"][leg]["neighbour"]
                n_obj = self._visual_objects[neighbour]
                neigh_pos = n_obj.pos()
                new_x = abs(neigh_pos.x())
                new_y = abs(neigh_pos.y())
                if new_x > 10:
                    x_n_poses.append(new_x)
                if new_y > 10:
                    y_n_poses.append(new_y)
            x_avg = mean(x_n_poses) if x_n_poses else 0
            y_avg = mean(y_n_poses) if y_n_poses else 0
            v_obj.move(x_avg, y_avg)

    def build_project_tree(self):
        self.project_explorer.objects_tree.clear_tree()
        self.project_explorer.build_project_tree(self._components,
                                                 self._logical_objects,
                                                 self._ipu_objects)

    def connect_all_objects(self):
        for name in self._visual_objects:
            legs = self._visual_objects[name].objects_legs

            for current_leg in legs:

                if not current_leg.get_connector():
                    neighbour_leg = self.get_neighbour_leg(name,
                                                           current_leg.name)
                    new_connector = LogicalConnector(current_leg,
                                                     neighbour_leg)

                    current_leg.set_connector(new_connector)
                    neighbour_leg.set_connector(new_connector)
                    self.view.scene.addItem(new_connector)

    def get_neighbour_leg(self, log_name, from_leg):
        legs = self._logical_objects[log_name]["legs"][from_leg]
        n_name = legs["neighbour"]
        n_leg = int(legs["neighbour_leg"])
        leg = self._visual_objects[n_name].get_leg(n_leg)
        return leg

    def open_site_data(self, config_path):

        if not os.path.exists(config_path):
            return
        imported = self.import_site_data(config_path)
        if imported:
            self._selected_obj = None
            for obj in list(self._visual_objects):
                self._visual_objects[obj].deleteLater()

            self.view.scene.clear()
            self._visual_objects.clear()
            self.project_explorer.clear()
            self.property_explorer.clear_properties()
            self.build_project_tree()
            self.create_objects_views()
            self.connect_all_objects()

    def select_tree_item(self, tree_item):
        if not tree_item:
            return

        obj_name = tree_item.text(0)
        if (obj_name in self._visual_objects
                and obj_name != self._selected_obj):
            self._changing_object = True
            if self._selected_obj:
                selected = self._visual_objects[self._selected_obj]
                selected.deselect()
            selecting = self._visual_objects[obj_name]
            selecting.select()
            self._selected_obj = obj_name
            self.config_settings(obj_name)
            self.config_components(obj_name)
            self._changing_object = False
            self.property_explorer.obj_name.setText(obj_name)
            self.property_explorer.obj_type.setText(selecting.log_type)
            self.view.ensureVisible(selecting, 10, 10)

    def config_obj_ibit(self, obj_name):
        out_table = self.property_explorer.i_table
        i_bits = self._logical_objects[obj_name]["individualizations"]
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
        out_table.hide_not_used_rows(max_row_num)

    def config_obj_settings_other(self, obj_name, settings_name, out_table):
        if settings_name not in self._logical_objects[obj_name]:
            return
        settings_data = self._logical_objects[obj_name][settings_name]

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
        out_table.hide_not_used_rows(max_row_num)

    def config_obj_channels(self, obj_name):
        max_row_num = -1
        out_table = self.property_explorer.channels

        channels = self._logical_objects[obj_name].get("channels")
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
        out_table.hide_not_used_rows(max_row_num)

    def config_components(self, obj_name):
        out_table = self.property_explorer.command_table
        current_row = 0
        for comp_type in self._components:
            if obj_name not in self._components[comp_type]:
                continue
            for component in self._components[comp_type].get(obj_name):
                out_table.item(current_row, 0).setText(comp_type)
                parameters = " ".join(component["Parameters"])
                out_table.item(current_row, 1).setText(parameters)
                out_table.showRow(current_row)
                current_row += 1
        out_table.hide_not_used_rows(current_row)

    def config_settings(self, obj_name):
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
        self._color_window.show()


class ToolWindow(SimWindow, SiteWindow):
    def __init__(self):
        super().__init__()

        self.property_explorer.tool_box.addItem(self.simulation, "Simulation")
        statuses = self.property_explorer.statuses
        statuses.connect_value_change(2, self.send_status)
        self.command_table = self.property_explorer.command_table
        self.command_table.cellDoubleClicked.connect(self.send_component)

        individualization = self.property_explorer.i_table
        individualization.connect_value_change(1, self.send_ibit)

    def send_status(self):
        if self._changing_object or not self._socket.isOpen():
            return

        obj_name = self._selected_obj

        value = self.sender().value()
        status_name = self.sender().name

        obj_data = self._logical_objects[obj_name]
        status_obj = obj_data['status'][status_name]['ipu']

        if status_obj and '.' not in status_obj:
            send_str = '{0}/yard {1} try_set {2}\n'.format(self._site_id,
                                                           status_obj,
                                                           value)
        else:
            send_str = '{0}/check {1}.{2}={3}\n'.format(self._site_id,
                                                        obj_name,
                                                        status_name,
                                                        value)
        self._socket.send(send_str)

    def send_component(self, line, column):
        if self._socket.isOpen():
            comm_type = self.command_table.item(line, 0).text()
            comm_param = self.command_table.item(line, 1).text()
            out_str = "{0}/cmd {1} {2}\n".format(self._site_id,
                                                 comm_type,
                                                 comm_param)

            self._socket.send(out_str)

    def send_ibit(self):
        if self._changing_object or not self._socket.isOpen():
            return

        obj_name = self._selected_obj
        out_str = '{0}/individ {1}.{2}={3}\n'.format(self._site_id,
                                                     obj_name,
                                                     self.sender().name,
                                                     self.sender().value())
        self._socket.send(out_str)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = QSplashScreen()
    splash.setPixmap(QPixmap("static/start_screen.gif"))
    splash.show()

    main_form = ToolWindow()
    main_form.show()

    splash.finish(main_form)

    app.exec_()
