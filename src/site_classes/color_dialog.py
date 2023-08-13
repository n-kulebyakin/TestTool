from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QVBoxLayout

# @formatter:off
OBJECT_COLORS = {
    "SHSIGNAL": "#aa8c77",
    "SECTION": "#d3c9c2",
    "POINT": "#b0a6ab",
    "ABTCE": "#d3c9c2",
    "LINEBLOCK": "#524636",
    "INTERFACE": "#c6cdda",
}
# @formatter:on


class ObjectColorWindow(QDialog):
    _objects_colors = None
    _objects = None

    def __init__(self, colors, visual_objects):
        super().__init__()
        self._accept = QPushButton("Accept")
        self._cancel = QPushButton("Cancel")
        self._layout = QVBoxLayout()
        self._color_table = QTableWidget()

        self.setGeometry(400, 400, 250, 300)
        self.setLayout(self._layout)

        self._color_table.setEditTriggers(self._color_table.NoEditTriggers)
        self._color_table.setColumnCount(2)
        self._color_table.setHorizontalHeaderLabels(["Type", "Value"])
        self._objects_colors = colors
        self._objects = visual_objects

        all_types = [self._objects[x].log_type for x in self._objects]
        for key in all_types:
            if key not in self._objects_colors:
                self._objects_colors[key] = "#c6cdda"

        self._color_table.setRowCount(len(colors))
        self._layout.addWidget(self._color_table)

        self._layout.addWidget(self._accept)
        self._layout.addWidget(self._cancel)
        self._color_table.cellClicked.connect(self.show_color_dialog)
        self._cancel.clicked.connect(self.close)
        self._changed_item = []
        self._accept.clicked.connect(self.accept_changes)

    def show_color_dialog(self, row, column):
        if column != 1:
            return None

        color = QColorDialog.getColor()
        if color.name() != self._color_table.item(row, column).text():
            self._color_table.item(row, column).setText(color.name())
            log_type = self._color_table.item(row, 0).text()
            self._objects_colors[log_type] = color.name()
            self._color_table.item(row, column).setBackground(color)
            self._changed_item.append(row)

    def accept_changes(self):
        for row in self._changed_item:
            logical_type = self._color_table.item(row, 0).text()
            for obj in self._objects:
                obj_type = self._objects[obj].log_type
                if obj_type == logical_type:
                    color = self._objects_colors[obj_type]
                    self._objects[obj].accept_new_colors(color)
                    self._objects_colors[obj_type] = color
        super().hide()

    def show(self) -> None:
        all_types = [self._objects[x].log_type for x in self._objects]
        for key in all_types:
            if key not in self._objects_colors:
                self._objects_colors[key] = "#c6cdda"

        self._color_table.setRowCount(len(self._objects_colors))

        for n, key in enumerate(self._objects_colors):
            object_type = QTableWidgetItem(key)
            self._color_table.setItem(n, 0, object_type)
            color_name = QTableWidgetItem(self._objects_colors[key])
            color_name.setBackground(QColor(self._objects_colors[key]))
            self._color_table.setItem(n, 1, color_name)
        self._color_table.resizeRowsToContents()
        self._color_table.resizeColumnToContents(1)
        super().show()
