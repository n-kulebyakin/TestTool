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
from PyQt5.QtWidgets import QGraphicsWidget
from PyQt5.QtWidgets import QSpinBox

from .signs import paint_graphic

PASSIVE_COLOR = "#D3D3D3"
ACTIVE_COLOR = "#8A2BE2"
EMERGENCY_COLOR = QColor(255, 0, 0)


class Rectangle(QGraphicsWidget):
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
        if not self._selected:
            self._selected = True
            self._color = self._active_color
            self.update()
            self.set_deep(self._max_deep)

    def deselect(self):
        if self._selected:
            self._selected = False
            self._color = self._passive_color
            self.update()
            self.set_deep(self._deep)

    def set_deep(self, deep):
        self.setZValue(deep)

    def paint(self, painter, options, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(QColor(self._color))
        paint_weight = int(self.size().width() - self._border * 2)
        paint_height = int(self.size().height() - self._border * 2)
        painter.drawRect(
            self._border, self._border, paint_weight, paint_height
        )
        self.update()


class LogicalConnector(QGraphicsWidget):
    _color = QColor("black")
    _rect_pen = QPen(QBrush(), 1, Qt.DashLine)

    def __init__(self, leg_1, leg_2):
        super().__init__()

        self._pen = QPen(self._color)
        self._pen.setWidth(1)
        self._length = 0
        self._selected = False

        self._start_leg = leg_1
        self._end_leg = leg_2

        self._start_point = QPointF(0, 0)
        self._end_point = QPointF(0, 0)

        self.setFlag(QGraphicsWidget.ItemIsFocusable)
        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(0, 5)
        self.setFocusPolicy(Qt.StrongFocus)

        self.special_transform()

    def paint(self, painter, options, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self._pen)
        painter.drawLine(0, 5, self._length, 5)

        if self._selected:
            painter.setPen(self._rect_pen)
            painter.drawRect(0, 0, self._length, 10)

    def size_change(self, start, end):
        self.setPos(start.x() + 5, start.y() - 1)
        delta_pos = start - end
        self._length = int(hypot(delta_pos.x(), delta_pos.y()))

        self.resize(self._length + 5, 10)
        new_angle = self.calculate_angle(start, end)
        self.setRotation(new_angle)

    def special_transform(self):
        pos_1 = self._start_leg.sceneBoundingRect()
        pos_2 = self._end_leg.sceneBoundingRect()
        new_start_point = QPointF(pos_1.x(), pos_1.y())
        new_end_point = QPointF(pos_2.x(), pos_2.y())
        if (
            new_start_point != self._start_point
            or new_end_point != self._end_point
        ):
            self._start_point = new_start_point
            self._end_point = new_end_point
            self.size_change(self._start_point, self._end_point)

    @staticmethod
    def calculate_angle(start, end):
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        rads = atan2(-dy, dx)
        rads %= 2 * pi
        return -degrees(rads)


class LogicalLeg(Rectangle):
    _width = 8
    _height = 8

    def __init__(self, name, legs_num, parent_name, parent_height, parent):
        super().__init__(parent)
        self.resize(self._width, self._height)
        self._border = 0
        self._parent_name = parent_name
        self._connector = None

        self._offset = 4
        self._name = name
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
    @staticmethod
    def get_new_pos(new_pos, max_x, max_y):
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
        if event.button() == Qt.LeftButton:
            self._old_pos = event.pos()
        self.custom_mouse_press(event)

    def mouseReleaseEvent(self, event):
        self.custom_mouse_release(event)
        if event.button() == Qt.LeftButton:
            self._old_pos = None

    def mouseMoveEvent(self, event):
        current_pos = self.pos()
        scene_event_pos = self.mapFromScene(event.pos())
        scene_old_pos = self.mapFromScene(self._old_pos)
        delta = scene_event_pos - scene_old_pos
        new_pos = current_pos + delta
        new_pos = self.get_new_pos(new_pos, self._max_x_pos, self._max_y_pos)
        if self._old_pos:
            self.setPos(new_pos)
        self.custom_mouse_move(event, current_pos, new_pos)

    def custom_mouse_press(self, event):
        pass

    def custom_mouse_move(self, event, current_pos, new_pos):
        pass

    def custom_mouse_release(self, event):
        pass


class ObjectLabel(MoveMixin, QGraphicsTextItem):
    _font = QFont("Times new roman", 10, QFont.Bold)

    def __init__(self, text, x=0.0, y=0.0, max_x_pos=0, max_y_pos=0):
        super().__init__()
        self._old_pos = None
        self._max_x_pos = max_x_pos
        self._max_y_pos = max_y_pos
        self.setPos(x, y)
        self.setPlainText(text)
        self.setFont(self._font)


class LogicalObject(MoveMixin, Rectangle):
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
        self._old_pos = None
        self._legs_data = object_data["legs"]
        self._log_type = object_data["Type"]

        self._deep = deep
        self._object_legs = []
        self._legs_text = []
        self._max_x_pos = scene.width() - 10
        self._max_y_pos = scene.height() - 10

        self.setFocusPolicy(Qt.StrongFocus)
        self._project_tree = project_tree
        self._tree_item = project_tree.findItems(name, Qt.MatchRecursive, 0)[0]
        self.setTransformOriginPoint(self._weight / 2, self._height / 2)
        self.setAcceptHoverEvents(True)
        self.colors = colors

        if self._log_type in colors:
            self._passive_color = QColor(colors.get(self._log_type))
            self._color = self._passive_color
        self.obj_label = ObjectLabel(
            name,
            self.x(),
            self.y(),
            self._max_x_pos,
            self._max_y_pos,
        )

        legs_num = len(self._legs_data)
        for leg_num, leg_name in enumerate(self._legs_data):
            new_leg = LogicalLeg(
                leg_name, legs_num, self._name, self._height, self
            )
            new_text = self._scene.addSimpleText(leg_name)
            new_text.setFont(self._leg_font)
            self._object_legs.append(new_leg)
            self._legs_text.append(new_text)
        self.set_deep(self._deep)
        scene.addItem(self)
        scene.addItem(self.obj_label)

    def deleteLater(self) -> None:
        for leg in self._object_legs:
            leg.deleteLater()
        self._object_legs.clear()
        for leg_text in self._legs_text:
            self._scene.removeItem(leg_text)
        self._legs_text.clear()
        self.obj_label.deleteLater()
        del self._tree_item
        super().deleteLater()

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
        self._passive_color = QColor(color)
        if not self._selected:
            self._color = self._passive_color

    def set_deep(self, deep):
        for leg_text in self._legs_text:
            leg_text.setZValue(deep + 0.2)
        self.obj_label.setZValue(deep)
        self.setZValue(deep + 0.1)

    def rotate_left(self):
        if self._current_angle != 315:
            self._current_angle = self._current_angle + 45
        else:
            self._current_angle = 0
        self.rotate()

    def rotate_right(self):
        if self._current_angle != -315:
            self._current_angle = self._current_angle - 45
        else:
            self._current_angle = 0
        self.rotate()

    def rotate(self):
        self.setRotation(self._current_angle)
        self.update_leg_text_pos()
        self.leg_connector_update()

    def flip_x(self):
        matrix = QTransform(1.0, 0.0, 0.0, -1.0, 0, self._height)
        self.apply_matrix(matrix)

    def flip_y(self):
        matrix = QTransform(-1.0, 0.0, 0.0, 1.0, self._weight, 0)
        self.apply_matrix(matrix)

    def apply_matrix(self, matrix):
        self.setTransform(matrix, Qt.SmoothTransformation)
        self.leg_connector_update()
        self.update_leg_text_pos()

    def set_passive_color(self, color):
        self._color = QColor(color)

    def custom_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.select()
            if self._project_tree.currentItem() != self._tree_item:
                self._project_tree.setCurrentItem(self._tree_item)

    def custom_mouse_move(self, event, current_pos, new_pos):
        if self._old_pos:
            self.leg_connector_update()
            self.update_leg_text_pos()
            self.obj_label.setPos(self.obj_label.pos() + new_pos - current_pos)

    def update_leg_text_pos(self):
        for leg_num, leg_text in enumerate(self._legs_text):
            leg_obj = self._object_legs[leg_num]
            leg_pos = leg_obj.sceneBoundingRect()
            leg_text.setPos(leg_pos.x() + 2, leg_pos.y() + 6)

    def move(self, x, y):
        self.setPos(x, -y)
        pos = self.sceneBoundingRect()
        self.obj_label.setPos(pos.x(), pos.y() - 20)
        self.update_leg_text_pos()

    def get_leg(self, leg_num):
        return self._object_legs[leg_num]

    def leg_connector_update(self):
        for leg in self._object_legs:
            connector = leg.get_connector()
            if connector:
                connector.special_transform()
                connector.update()

    def paint(self, painter, options, widget):
        super().paint(painter, options, widget)
        self.draw_sign(painter)

    def draw_sign(self, painter):
        paint_graphic(
            self._log_type,
            painter,
            self.size().height(),
            self.size().width(),
            self._border,
        )


class CustomGraphicsView(QGraphicsView):
    _current_modifier = None
    _max_scale = 5
    _min_scale = 0.2
    _current_scale = 1
    _ratio = 1.2

    def __init__(self):
        super().__init__()
        self.setViewportUpdateMode(self.FullViewportUpdate)
        self.scene = QGraphicsScene(0, 0, 1700, 1700)
        self.setScene(self.scene)

    def wheelEvent(self, event):
        if self._current_modifier == Qt.ControlModifier:
            wheel_move = event.angleDelta().y()
            if wheel_move > 0 and self._max_scale > self._current_scale:
                self._current_scale = self._current_scale * self._ratio
                self.scale(self._ratio, self._ratio)
            elif wheel_move < 0 and self._min_scale < self._current_scale:
                self.scale(1 / self._ratio, 1 / self._ratio)
                self._current_scale = self._current_scale * 1 / self._ratio

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self._current_modifier = Qt.ControlModifier
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setDragMode(self.ScrollHandDrag)
            handmade_event = QMouseEvent(
                QEvent.MouseButtonPress,
                QPointF(event.pos()),
                Qt.LeftButton,
                event.buttons(),
                Qt.KeyboardModifiers(),
            )
            self.mousePressEvent(handmade_event)
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

    def keyReleaseEvent(self, event):
        self._current_modifier = None
        event.accept()


class CustomSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = None

    def wheelEvent(self, event):
        event.ignore()
