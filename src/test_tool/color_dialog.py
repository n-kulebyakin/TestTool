from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtGui import QColor

OBJECT_COLORS = {"SHSIGNAL": "#aa8c77",
                 "SECTION": "#d3c9c2",
                 "POINT": "#b0a6ab",
                 "ABTCE": "#d3c9c2",
                 "LINEBLOCK": "#524636",
                 "INTERFACE": "#c6cdda"}


class ObjectColorWindow(QDialog):
    objects_colors = None
    objects = None

    def __init__(self, colors, visual_objects):
        super().__init__()
        self.accept_button = QPushButton("Accept")
        self.cancel_button = QPushButton("Cancel")
        self.v_layout = QVBoxLayout()
        self.color_table = QTableWidget()

        self.setGeometry(400, 400, 250, 300)
        self.setLayout(self.v_layout)

        self.color_table.setEditTriggers(self.color_table.NoEditTriggers)
        self.color_table.setColumnCount(2)
        self.color_table.setHorizontalHeaderLabels(["Type", "Value"])
        self.objects_colors = colors
        self.objects = visual_objects
        self.color_table.setRowCount(len(colors))
        self.v_layout.addWidget(self.color_table)

        self.v_layout.addWidget(self.accept_button)
        self.v_layout.addWidget(self.cancel_button)
        self.color_table.cellClicked.connect(self.show_color_dialog)
        self.cancel_button.clicked.connect(self.close)
        self.changed_item = []
        self.accept_button.clicked.connect(self.accept_changes)

        all_types = [self.objects[x].object_data["Type"] for x in self.objects]

        for key in all_types:
            if key not in self.objects_colors:
                self.objects_colors[key] = "#c6cdda"
        for n, key in enumerate(self.objects_colors):
            object_type = QTableWidgetItem(key)
            self.color_table.setItem(n, 0, object_type)
            color_name = QTableWidgetItem(self.objects_colors[key])
            color_name.setBackground(QColor(self.objects_colors[key]))
            self.color_table.setItem(n, 1, color_name)
        self.color_table.resizeRowsToContents()
        self.color_table.resizeColumnToContents(1)

    def show_color_dialog(self, row, column):
        if column != 1:
            return None
        color = QColorDialog.getColor()
        if color.name() != self.color_table.item(row, column).text():
            self.color_table.item(row, column).setText(color.name())
            log_type = self.color_table.item(row, 0).text()
            self.objects_colors[log_type] = color.name()
            self.color_table.item(row, column).setBackground(color)
            self.changed_item.append(row)

    def accept_changes(self):
        for row in self.changed_item:
            logical_type = self.color_table.item(row, 0).text()
            for obj in self.objects:
                obj_type = self.objects[obj].object_data["Type"]
                if obj_type == logical_type:
                    self.objects[obj].accept_new_colors(self.objects_colors)
        self.close()
