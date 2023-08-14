# -*- coding: utf-8 -*-
from math import atan2, degrees, pi
from math import hypot

from PyQt5.Qt import QBrush
from PyQt5.Qt import QEvent
from PyQt5.Qt import QGraphicsScene
from PyQt5.Qt import QGraphicsTextItem
from PyQt5.Qt import QGraphicsView
from PyQt5.Qt import QMouseEvent
from PyQt5.QtCore import QPointF
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QTransform
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QGraphicsWidget
from PyQt5.QtWidgets import QMenu

from .signs import paint_graphic

PASSIVE_COLOR = "#D3D3D3"
ACTIVE_COLOR = "#8A2BE2"
EMERGENCY_COLOR = QColor(255, 0, 0)


class Rectangle(QGraphicsWidget):
    """
    Базовый класс для отображения объектов на сцене
    """
    _passive_color = PASSIVE_COLOR
    _active_color = ACTIVE_COLOR
    _border = 0
    _deep = 0
    _max_deep = 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = self._passive_color
        self._selected = False

    def select(self):
        """
        Метод устанавливающий выделение объекта.
        Изменяет цвет объекта и поднимает
        его выше других.
        """
        if not self._selected:
            self._selected = True
            self._color = self._active_color
            self.update()
            self.set_deep(self._max_deep)

    def deselect(self):
        """
        Метод снимающий выделение объекта.
        Возвращает объекту неактивный цвет
        и начальную позицию оси z.
        """
        if self._selected:
            self._selected = False
            self._color = self._passive_color
            self.update()
            self.set_deep(self._deep)

    def set_deep(self, deep):
        """
        Метод устанавливающий глубину объекта.
        """
        self.setZValue(deep)

    def paint(self, painter, options, widget):
        """
        Метод отрисовки объекта на сцене.
        Вызывается автоматически при отображении.
        Отрисовывает прямоугольник по текущим размерам,
        за вычетом границ.
        """
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        # Цвет задаётся на основании текущего
        painter.setBrush(QColor(self._color))
        # Вычисление длинны и высоты с учётом рамки
        paint_width = int(self.size().width() - self._border * 2)
        paint_height = int(self.size().height() - self._border * 2)

        painter.drawRect(
            self._border, self._border, paint_width, paint_height
        )
        self.update()


class LogicalConnector(QGraphicsWidget):
    """
    Класс отображения линии соединения объектов на сцене.
    Соединяет "ноги" двух объектов, которые получает на вход.
    """
    _color = QColor("black")
    _rect_pen = QPen(QBrush(), 1, Qt.DashLine)

    def __init__(self, leg_1, leg_2):
        super().__init__()
        # Задаём цвет и толщину кисти
        self._pen = QPen(self._color)
        self._pen.setWidth(1)

        # Задаём цвет и толщину кисти
        self._length = 0

        # TODO: Добавить возможность выделения
        self._selected = False

        # Сохраняем начальную и конченую ноги
        self._start_leg = leg_1
        self._end_leg = leg_2
        # Задаём координаты начала и конца по умолчанию
        self._start_point = QPointF(0, 0)
        self._end_point = QPointF(0, 0)

        self.setFlag(QGraphicsWidget.ItemIsFocusable)
        self.setAcceptHoverEvents(True)

        # Изменяем точку вращения для удобства расчётов
        # учитывая границы отображаемых объектов

        # TODO: Изменить значения 5,
        #  на получение рамки объектов
        self.setTransformOriginPoint(0, 5)
        self.setFocusPolicy(Qt.StrongFocus)

        self.special_transform()

    def paint(self, painter, options, widget):
        """
        Переопределяем стандартный метод отрисовки
        для отображения сплошной линии нужной длинны
        """
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self._pen)

        # Рисуем линию с учётом границ
        painter.drawLine(0, 5, self._length, 5)

        # TODO: Добавить возможность выделения
        if self._selected:
            painter.setPen(self._rect_pen)
            # Отрисовка прямоугольника вокруг линии
            painter.drawRect(0, 0, self._length, 10)

    def size_change(self, start, end):
        """
        Метод обработки изменения размеров и положения
        линии по заданным начальной и конечной точкам
        """
        # Устанавливаем начало линии
        self.setPos(start.x() + 5, start.y() - 1)
        delta_pos = start - end
        # Вычисляем длину линии
        self._length = int(hypot(delta_pos.x(), delta_pos.y()))
        # Устанавливаем размеры новой длинны
        self.resize(self._length + 5, 10)
        # Вычисляем новый угол наклона
        # по заданным координатам и поворачиваем
        new_angle = self.calculate_angle(start, end)
        self.setRotation(new_angle)

    def special_transform(self):
        """
        Метод изменения отображаемой линии,
        вызываемый при изменении координат
        объекта начала или конца
        """
        pos_1 = self._start_leg.sceneBoundingRect()
        pos_2 = self._end_leg.sceneBoundingRect()
        new_start_point = QPointF(pos_1.x(), pos_1.y())
        new_end_point = QPointF(pos_2.x(), pos_2.y())
        # Проверяем изменилось ли положение
        # начальной или конечной точки
        if (
                new_start_point != self._start_point
                or new_end_point != self._end_point
        ):
            self._start_point = new_start_point
            self._end_point = new_end_point
            self.size_change(self._start_point, self._end_point)

    @staticmethod
    def calculate_angle(start, end):
        """
        Метод вычисления угла наклона
        линии проходящей через две точки
        """
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        rads = atan2(-dy, dx)
        rads %= 2 * pi
        return -degrees(rads)


class LogicalLeg(Rectangle):
    """
    Класс отображения "ног" логических объектов.
    Принимает на вход:
    Имя ноги, общее количество ног у объекта,
    высоту логического объекта, логический объект.
    """

    _width = 8
    _height = 8
    _border = 0
    _offset = 4
    def __init__(self, name, legs_num, parent_height, parent):
        super().__init__(parent)
        # Устанавливаем размеры по умолчанию
        self.resize(self._width, self._height)

        # Сохраняем полученную информацию
        self._parent_name = parent.name
        self._name = name
        self._connector = None

        # Вычисляем координаты расположения
        x, y = self.get_pos(
            int(name),
            legs_num,
            parent_height,
            parent_height,
            self._width,
            self._height,
            self._offset,
        )

        self.setPos(x, y)
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)

    @property
    def name(self):
        return self._name

    def get_connector(self):
        return self._connector

    def set_connector(self, connector):
        self._connector = connector

    def deleteLater(self) -> None:
        if self._connector:
            self._connector.deleteLater()
        super().deleteLater()

    def hoverLeaveEvent(self, event):
        self.deselect()

    def hoverEnterEvent(self, event):
        self.select()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()



    @staticmethod
    def get_pos(leg, legs, parent_w, parent_h, height, width, border):
        """
        Метод поиска положения
        на родительском объекте
        """

        # TODO: Пересмотреть алгоритм поиска

        if legs > 4:
            if (
                    leg <= 3
                    and legs % 4 < (leg + 1)
                    or leg > 3
                    and legs % 4 < (leg + 1) % 4
            ):
                delta_pos_1 = (parent_h / (legs // 4)) / 2
            else:
                delta_pos_1 = (parent_w / (legs // 4 + 1)) / 2
                if leg > 3:
                    delta_pos_1 += delta_pos_1 * (legs // (leg + 1)) * 2
        else:
            delta_pos_1 = parent_h / 2
        if (leg + 1) % 4 == 0:
            x, y = delta_pos_1, height
        elif (leg + 1) % 3 == 0:
            x = delta_pos_1 - width / 2
            y = 0 + border - height / 2
        elif (leg + 1) % 2 == 0:
            x = parent_h - border - width / 2
            y = delta_pos_1 - height / 2
        else:
            x = border - width / 2
            y = delta_pos_1 - height / 2
        return x, y


class MoveMixin:
    """
    Класс добавляющий функционал перемещения
    объектов по сцене.
    Стандартное поведение перемещения
    позволяло вытащить объект за пределы
    сцены.
    """
    def __init__(self):
        self._old_pos = None

    @staticmethod
    def get_new_pos(new_pos, max_x, max_y):
        """
        Метод проверки и корректировки
        координат для исключения выхода
        за пределы сцены.
        """
        x, y = new_pos.x(), new_pos.y()
        if x > max_x:
            new_pos = QPointF(max_x - 100, y)
        elif x < 0:
            new_pos = QPointF(10, y)
        if y > 0:
            new_pos = QPointF(x, -5)
        elif y < -max_y:
            new_pos = QPointF(x, -max_y + 5)
        return new_pos

    def mousePressEvent(self, event):
        """
        Стандартное событие PyQT,
        если была нажата левая кнопка
        мыши, запоминаем координаты нажатия
        """
        if event.button() == Qt.LeftButton:
            self._old_pos = event.pos()
        self.custom_mouse_press(event)

    def mouseReleaseEvent(self, event):
        """
        Стандартное событие PyQT
        отпускание ранее нажатой
        клавиши мыши.
        """
        self.custom_mouse_release(event)
        # Если сохранено какое-то значение
        # позиции, то сбрасываем его
        if self._old_pos is not None:
            self._old_pos = None

    def mouseMoveEvent(self, event):
        """
        Стандартное событие PyQT
        перемещения мыши.
        """

        # Считываем текущую позицию
        new_pos = current_pos = self.pos()

        # Если была сохранена предыдущая позиция
        # высчитываем координату смещения с учётом
        # размера сцены и устанавливаем её объекту
        if self._old_pos is not None:
            scene_event_pos = self.mapFromScene(event.pos())
            scene_old_pos = self.mapFromScene(self._old_pos)
            delta = scene_event_pos - scene_old_pos
            new_pos = current_pos + delta
            new_pos = self.get_new_pos(new_pos, self._max_x_pos,
                                       self._max_y_pos)
            self.setPos(new_pos)
        # Передаём данные для возможности
        # дальнейшей обработки
        self.custom_mouse_move(event, current_pos, new_pos)

    def custom_mouse_press(self, event):
        """
        Пользовательский метод обработки
        нажатия кнопок мыши.
        """
        pass

    def custom_mouse_move(self, event, current_pos, new_pos):
        """
        Пользовательский метод обработки
        перемещения мыши.
        """
        pass

    def custom_mouse_release(self, event):
        """
        Пользовательский метод обработки
        отпускания кнопок мыши.
        """
        pass


class ObjectLabel(MoveMixin, QGraphicsTextItem):
    """
    Класс отображения названия объекта
    на сцене.
    Может перемещаться по сцене отдельно
    от основного объекта.
    """

    # Устанавливаем шрифт по умолчанию
    _font = QFont("Times new roman", 10, QFont.Bold)

    def __init__(self, text, x=0.0, y=0.0, max_x_pos=0, max_y_pos=0):
        super().__init__()
        self._old_pos = None
        # Сохраняем информацию об ограничении
        # перемещения по сцене
        self._max_x_pos = max_x_pos
        self._max_y_pos = max_y_pos
        self.setPos(x, y)
        self.setPlainText(text)
        self.setFont(self._font)


class LogicalObject(MoveMixin, Rectangle):
    """
    Класс отображения логического объекта.
    Представляет собой сам объект, его ноги,
    их названия и надпись содержащую название
    объекта.
    Принимает на вход название объекта, данные
    о нём, координату оси Z, сцену отображения,
    словарь с цветами объектов и дерево проекта.
    """

    _pen = QPen(Qt.black, 2, Qt.SolidLine)
    _leg_font = QFont("Times New Roman", 8, QFont.Bold)
    _height = 80
    _weight = 80
    _border = 5

    def __init__(self, name, object_data, deep, scene, colors, project_tree):
        super().__init__()

        self.resize(self._weight, self._height)

        self._current_angle = 0
        self._name = name
        self._scene = scene
        # self._old_pos = None
        self._legs_data = object_data["legs"]
        self._log_type = object_data["Type"]
        self._deep = deep

        # Данные об объектах ног и
        # их обозначениях будут храниться
        # в списках
        self._object_legs = []
        self._legs_text = []

        self._max_x_pos = scene.width() - 10
        self._max_y_pos = scene.height() - 10

        self.setFocusPolicy(Qt.StrongFocus)
        self._project_tree = project_tree

        # Получаем объект представления
        # в дереве проекта
        self._tree_item = project_tree.findItems(name, Qt.MatchRecursive, 0)[0]

        # Изменяем точку относительно которой
        # будут происходить поворот и
        # зеркальное отображение
        self.setTransformOriginPoint(self._weight / 2, self._height / 2)

        self.setAcceptHoverEvents(True)
        self.colors = colors

        if self._log_type in colors:
            self._passive_color = QColor(colors.get(self._log_type))
            self._color = self._passive_color

        # Добавляем отображение названия
        self.obj_label = ObjectLabel(
            name,
            self.x(),
            self.y(),
            self._max_x_pos,
            self._max_y_pos,
        )

        # Добавляем отображение ног объекта
        # и подписей к ним
        legs_num = len(self._legs_data)
        for leg_num, leg_name in enumerate(self._legs_data):
            # Создаём новый объект ноги
            new_leg = LogicalLeg(
                leg_name, legs_num, self._height, self
            )
            # Создаём подпись к ноге
            new_text = self._scene.addSimpleText(leg_name)
            new_text.setFont(self._leg_font)

            # Сохраняем ссылки на объекты
            # в списки
            self._object_legs.append(new_leg)
            self._legs_text.append(new_text)
        # Устанавливаем координату по оси z
        self.set_deep(self._deep)

        # Добавляем контекстное меню
        # с возможностью отразить объект
        self.menu = QMenu(self._scene.views()[0])
        # TODO: Добавить функционал вращения
        actions = (
            ('Flip X', self.flip_x),
            ('Flip Y', self.flip_y),
        )
        for action_name, func in actions:
            new_action = QAction(action_name, self)
            new_action.triggered.connect(func)
            self.menu.addAction(new_action)

        scene.addItem(self)
        scene.addItem(self.obj_label)

    def deleteLater(self) -> None:
        """
        Переопределяем стандартный
        метод PyQT для удаления объекта.
        """

        # Удаляем объекты ног
        for leg in self._object_legs:
            leg.deleteLater()
        self._object_legs.clear()

        # Удаляем подписи к ногам
        for leg_text in self._legs_text:
            self._scene.removeItem(leg_text)
        self._legs_text.clear()

        # Удаляем название объекта
        self.obj_label.deleteLater()

        # Удаляем объект из дерева проекта
        del self._tree_item

        super().deleteLater()


    @property
    def name(self):
        return self._name

    @property
    def color(self):
        return self.colors.get(self._log_type)

    @property
    def log_type(self):
        return self._log_type

    @property
    def objects_legs(self):
        return self._object_legs

    def accept_new_colors(self, color):
        """
        Метод применения нового цвета
        """
        # Изменяем цвет по умолчанию
        self._passive_color = QColor(color)
        if not self._selected:
            # Если объект не выделен,
            # обновляем текущий цвет
            self._color = self._passive_color

    def set_deep(self, deep):
        """
        Метод установки координаты по
        оси Z
        """
        # Устанавливаем значение для
        # подписей к ногам чуть выше
        # основного объекта
        for leg_text in self._legs_text:
            leg_text.setZValue(deep + 0.2)

        # Устанавливаем значения для надписи
        # и самого объекта так, что бы надпись
        # была выше
        self.obj_label.setZValue(deep)
        self.setZValue(deep + 0.1)

    def rotate_left(self):
        """
        Метод поворота в лево
        на 45 градусов
        """
        if self._current_angle != 315:
            self._current_angle = self._current_angle + 45
        else:
            self._current_angle = 0
        self.rotate()

    def rotate_right(self):
        """
        Метод поворота в право
        на 45 градусов
        """
        if self._current_angle != -315:
            self._current_angle = self._current_angle - 45
        else:
            self._current_angle = 0
        self.rotate()

    def rotate(self):
        """
        Метод вращения объекта,
        на заранее выставленный угол
        """
        self.setRotation(self._current_angle)

        # При вращении обновляются положения
        # подписей к ногам и
        # соединительные линии
        self.update_leg_text_pos()
        self.leg_connector_update()

    def flip_x(self):
        """
        Метод отражения по оси X
        """
        matrix = QTransform(1.0, 0.0, 0.0, -1.0, 0, self._height)
        self.apply_matrix(matrix)

    def flip_y(self):
        """
        Метод отражения по оси Y
        """
        matrix = QTransform(-1.0, 0.0, 0.0, 1.0, self._weight, 0)
        self.apply_matrix(matrix)

    def apply_matrix(self, matrix):
        """
        Метод применения трансформации
        объекта
        """
        self.setTransform(matrix, Qt.SmoothTransformation)
        # При трансформации обновляются положения
        # подписей к ногам и
        # соединительные линии
        self.leg_connector_update()
        self.update_leg_text_pos()

    def contextMenuEvent(self, event):
        """
        Метод вызова контекстного меню
        """
        self.menu.exec_(event.screenPos())

    def set_passive_color(self, color):
        """
        Метод установки цвета в неактивный
        """
        self._color = QColor(color)

    def custom_mouse_press(self, event):
        """
        Пользовательский метод обработки
        нажатия кнопок мыши
        """
        if event.button() == Qt.LeftButton:
            # Если была нажата левая кнопка,
            # то выделяем объект
            self.select()

            # Если текущий объект в дереве проекта
            # не равен данному, то меняем выделение
            if self._project_tree.currentItem() != self._tree_item:
                self._project_tree.setCurrentItem(self._tree_item)

    def custom_mouse_move(self, event, current_pos, new_pos):
        """
        Пользовательский метод обработки
        перемещения курсора мыши
        """

        # Если ранее была сохранена
        # предыдущая позиция курсора
        # обновляем координаты ног,
        # подписей к ним и имени объекта
        if self._old_pos is not None:
            self.leg_connector_update()
            self.update_leg_text_pos()
            self.obj_label.setPos(self.obj_label.pos() + new_pos - current_pos)

    def update_leg_text_pos(self):
        """
        Метод обновления позиции
        подписей к ногам объекта.
        """
        for leg_num, leg_text in enumerate(self._legs_text):
            # Получаем объект соответствующей ноги
            leg_obj = self._object_legs[leg_num]
            # Получаем координаты объекта ноги
            leg_pos = leg_obj.sceneBoundingRect()
            # Устанавливаем координаты
            # текста с небольшим смещение
            leg_text.setPos(leg_pos.x() + 2, leg_pos.y() + 6)


    def move(self, x, y):
        """
        Метод перемещения объекта
        вместе с именем и подписями
        к ногам
        """
        self.setPos(x, -y)
        pos = self.sceneBoundingRect()
        self.obj_label.setPos(pos.x(), pos.y() - 20)
        self.update_leg_text_pos()

    def get_leg(self, leg_num):
        """
        Метод получения объекта ноги
        по номеру
        """
        return self._object_legs[leg_num]

    def leg_connector_update(self):
        """
        Метод обновления расположения
        соединительных линий
        """
        for leg in self._object_legs:
            # Для каждой ноги получаем
            # объект соединительной линии
            connector = leg.get_connector()
            if connector:
                # Если линия существует,
                # то обновляем её расположение
                connector.special_transform()
                connector.update()

    def paint(self, painter, options, widget):
        """
        Метод отрисовки изображения
        объекта
        """
        super().paint(painter, options, widget)
        # Добавляем отрисовку значка на объекта
        self.draw_sign(painter)

    def draw_sign(self, painter):
        """
        Метод отрисовки значка объекта
        """
        paint_graphic(
            self._log_type,
            painter,
            self.size().height(),
            self.size().width(),
            self._border,
        )


class CustomGraphicsView(QGraphicsView):
    """
    Класс графического отображения.
    Реализует функцию масштабирования
    и позиционирования
    в привычном виде.
    """
    _current_modifier = None
    # Максимальный зум
    _max_scale = 5
    # Минимальный зум
    _min_scale = 0.2
    _current_scale = 1
    # Шаг масштабирования
    _ratio = 1.2

    def __init__(self):
        super().__init__()
        self.setViewportUpdateMode(self.FullViewportUpdate)
        self.scene = QGraphicsScene(0, 0, 1700, 1700)
        self.setScene(self.scene)

    def wheelEvent(self, event):
        """
        Стандартное событие PyQT
        прокрутки колеса мыши.
        Добавлена функциональность
        масштабирования.
        """
        # Если зажата клавиша Ctrl
        if self._current_modifier == Qt.ControlModifier:
            # Получение изменение координаты колеса
            wheel_move = event.angleDelta().y()
            # В зависимости от направления движения
            # колеса увеличиваем или уменьшаем машстаб
            if wheel_move > 0 and self._max_scale > self._current_scale:
                self._current_scale = self._current_scale * self._ratio
                self.scale(self._ratio, self._ratio)
            elif wheel_move < 0 and self._min_scale < self._current_scale:
                self.scale(1 / self._ratio, 1 / self._ratio)
                self._current_scale = self._current_scale * 1 / self._ratio

    def keyPressEvent(self, event):
        """
        Стандартное событие PyQT
        нажатия клавиши клавиатуры.
        """

        # Если нажата клавиша Ctrl
        # запоминаем это событие
        # и передаём обработку стандартному
        # методу
        if event.modifiers() == Qt.ControlModifier:
            self._current_modifier = Qt.ControlModifier
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """
        Стандартное событие PyQT
        нажатия клавиши мыши.
        """
        # Если была нажата средняя кнопка мыши
        # изменяем событие для реализации
        # позиционирования по сцене

        if event.button() == Qt.MidButton:
            self.setDragMode(self.ScrollHandDrag)
            # Изменяем событие,
            # подменяя нажатие средней кнопки
            # на левую
            handmade_event = QMouseEvent(
                QEvent.MouseButtonPress,
                QPointF(event.pos()),
                Qt.LeftButton,
                event.buttons(),
                Qt.KeyboardModifiers(),
            )
            # Передаём дальше изменённое событие
            self.mousePressEvent(handmade_event)
        # Передаём первоначальное событие
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setDragMode(self.NoDrag)
            handmade_event = QMouseEvent(
                QEvent.MouseButtonRelease,
                QPointF(event.pos()),
                Qt.LeftButton,
                event.buttons(),
                Qt.KeyboardModifiers(),
            )

            self.mouseReleaseEvent(handmade_event)
        super().mouseReleaseEvent(event)

    def keyReleaseEvent(self, event):
        self._current_modifier = None
        event.accept()
