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
    """
    Класс настройки цветов логических объектов
    отображаемых на сцене.
    На выход принимает словарь цветов объектов по умолчанию
    и список логических объектов отображаемых на сцене.
    """

    def __init__(self, colors, visual_objects):
        super().__init__()
        self._changed_item = []
        self._accept = QPushButton("Accept")
        self._cancel = QPushButton("Cancel")
        self._layout = QVBoxLayout()
        self._color_table = QTableWidget()

        self.setGeometry(400, 400, 250, 300)
        self.setLayout(self._layout)

        # Запрещаем изменение значений данных в таблице
        self._color_table.setEditTriggers(self._color_table.NoEditTriggers)
        self._color_table.setColumnCount(2)
        self._color_table.setHorizontalHeaderLabels(["Type", "Value"])
        self._objects_colors = colors
        self._objects = visual_objects

        self._layout.addWidget(self._color_table)
        self._layout.addWidget(self._accept)
        self._layout.addWidget(self._cancel)

        # Добавляем обработку нажатий на ячейки и кнопки
        self._color_table.cellClicked.connect(self.show_color_dialog)
        self._cancel.clicked.connect(self.hide)
        self._accept.clicked.connect(self.accept_changes)

    def show_color_dialog(self, row, column):
        """
        Функция отображения окна с палитрой цветов
        """
        # Если была нажата не первая колонка таблицы, то возвращаемся
        if column != 1:
            return
        color_item = self._color_table.item(row, column)
        color = QColorDialog.getColor()
        color_name = color.name()

        # Проверяем отличается ли выбранный цвет от текущего
        if color_name != color_item.text():
            color_item.setText(color)
            log_type = self._color_table.item(row, 0).text()
            # Сохраняем выбранный цвет для типа объекта
            self._objects_colors[log_type] = color_name
            # Заливаем задний фон выбранным цветом
            color_item.setBackground(color)
            # Запоминаем тип для которого изменился тип
            self._changed_item.append(log_type)

    def accept_changes(self):
        """
        Функция применения изменённых цветов к объектам
        """
        for obj in self._objects:
            obj_type = self._objects[obj].log_type
            # Проверяем изменился ли цвет для данного типа
            if obj_type == self._changed_item:
                color = self._objects_colors[obj_type]
                # Применяем новый цвет к объекту
                self._objects[obj].accept_new_colors(color)
        self._changed_item.clear()
        super().hide()

    def show(self) -> None:
        # Добавляем цвет по умолчанию для всех новых типов
        # не включенных в изначальные данных
        all_types = [self._objects[x].log_type for x in self._objects]
        for obj_type in all_types:
            if obj_type not in self._objects_colors:
                self._objects_colors[obj_type] = "#c6cdda"

        # Выставляем количество строк равным количеству цветов
        self._color_table.setRowCount(len(self._objects_colors))
        # Выставляем значения в таблице цветов
        for row, obj_type in enumerate(self._objects_colors):
            object_type = QTableWidgetItem(obj_type)
            # Устанавливаем название типа в ячейку 0
            self._color_table.setItem(row, 0, object_type)
            color_name = QTableWidgetItem(self._objects_colors[obj_type])
            # Заливаем задний фон цветом
            color_name.setBackground(QColor(self._objects_colors[obj_type]))
            # Устанавливаем название цвета в ячейку 1
            self._color_table.setItem(row, 1, color_name)
        self._color_table.resizeRowsToContents()
        self._color_table.resizeColumnToContents(1)
        super().show()
