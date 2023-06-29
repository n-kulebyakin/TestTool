# -*- coding: utf-8 -*-
from math import hypot
from math import degrees
from math import atan
from math import atan2

from PyQt5.QtWidgets import QGraphicsWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QSpinBox

from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPen
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QTransform
from PyQt5.QtGui import QFont

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPointF

from PyQt5.Qt import QBrush

from PyQt5.Qt import QMouseEvent
from PyQt5.Qt import QEvent
from PyQt5.Qt import QGraphicsTextItem
from PyQt5.Qt import QGraphicsView


from .designation import paint_graphic

PASSIVE_COLOR = QColor(155, 155, 155)
ACTIVE_COLOR = QColor(255, 0, 184)
EMERGENCY_COLOR = QColor(255, 0, 0)


class MiniRect(QGraphicsWidget):
    '''
    color = passive_color = PASSIVE_COLOR
    active_color = ACTIVE_COLOR
    emergency_color = EMERGENCY_COLOR
    emergency = False
    selected = False
    border = 0
    '''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = self.passive_color = PASSIVE_COLOR
        self.active_color = ACTIVE_COLOR
        self.emergency_color = EMERGENCY_COLOR
        self.emergency = False
        self.selected = False
        self.border = 0

    def paint(self, painter, options, widget):
        painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
        painter.setBrush(self.color)
        painter.drawRect(self.border,
                         self.border,
                         self.size().width() - self.border * 2,
                         self.size().height() - self.border * 2)
        self.drawForm(painter)

    def drawForm(self, painter):
        pass

    def setSelected(self, selected):
        if selected:
            self.color = self.active_color
        else:
            if self.emergency:
                self.color = self.emergency_color
            else:
                self.color = self.passive_color
        self.update()


class LogicalConnector(QGraphicsWidget):
    """    color = QColor(175, 0, 255)
    pen = QPen(QColor("black"))
    pen.setWidth(1)
    length = 0
    selected = False
    rect_pen = QPen(QBrush(), 1, Qt.DashLine)"""

    def __init__(self, leg_1, leg_2):
        super().__init__()
        self.color = QColor(175, 0, 255)
        self.pen = QPen(QColor("black"))
        self.pen.setWidth(1)
        self.length = 0
        self.selected = False
        self.rect_pen = QPen(QBrush(), 1, Qt.DashLine)
        self.setFlag(self.ItemIsFocusable)
        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(0, 5)
        self.setFocusPolicy(Qt.StrongFocus)
        self.leg_1 = leg_1
        self.leg_2 = leg_2
        self.leg_1.connector = self
        self.leg_2.connector = self
        self.specialTransform()

    def paint(self, painter, options, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.pen)
        painter.drawLine(0, 5, self.length, 5)
        if self.selected:
            painter.setPen(self.rect_pen)
            painter.drawRect(0, 0, self.length, 10)

    def specialTransform(self):
        pos_1 = self.leg_1.sceneBoundingRect()
        pos_2 = self.leg_2.sceneBoundingRect()

        self.pos_1 = QPointF(pos_1.x(), pos_1.y())
        self.pos_2 = QPointF(pos_2.x(), pos_2.y())

        self.setPos(self.pos_1.x() + 5, self.pos_1.y() - 1)

        delta_pos = self.pos_1 - self.pos_2

        self.length = hypot(delta_pos.x(), delta_pos.y())
        self.resize(self.length + 5, 10)
        if delta_pos.x() != 0:
            if self.pos_1.x() < self.pos_2.x():
                new_angle = degrees(atan(delta_pos.y() / delta_pos.x()))
            elif self.pos_1.x() > self.pos_2.x():
                new_angle = degrees(atan2(delta_pos.y(), delta_pos.x())) + 180
            else:
                new_angle = 0
        elif self.pos_1.y() < self.pos_2.y():
            new_angle = 90
        else:
            new_angle = -90
        self.setRotation(new_angle)
        self.update()


class LogLeg(MiniRect):
    """    width = 8
    height = 8
    border = 0
    connector = None"""

    def __init__(self, leg, n_leg, max_legs, parent, obj_name):
        super().__init__(parent)
        self.width = 8
        self.height = 8
        self.border = 0
        self.connector = None
        self.resize(self.width, self.height)
        self.leg = leg
        self.setAcceptDrops(True)
        self.setAcceptHoverEvents(True)

        x, y = self.get_leg_pos(n_leg, max_legs,
                                parent.size().width(),
                                parent.size().height(),
                                parent.border)
        self.setPos(x, y)

    def get_leg_pos(self, n_leg, max_legs, parent_h, parent_w, parent_n):
        if max_legs > 4:
            if (n_leg <= 3 and max_legs % 4 < (n_leg + 1)
                    or n_leg > 3 and max_legs % 4 < (n_leg + 1) % 4):
                delta_pos_1 = ((parent_h) / (max_legs // 4)) / 2
            else:
                delta_pos_1 = ((parent_h) / (max_legs // 4 + 1)) / 2
                if n_leg > 3:
                    delta_pos_1 += delta_pos_1 * (max_legs // (n_leg + 1)) * 2
        else:
            delta_pos_1 = parent_h / 2
        if (n_leg + 1) % 4 == 0:
            x, y = delta_pos_1, self.height
        elif (n_leg + 1) % 3 == 0:
            x = delta_pos_1 - self.width / 2
            y = 0 + parent_n - self.height / 2
        elif (n_leg + 1) % 2 == 0:
            x = parent_h - parent_n - self.width / 2
            y = delta_pos_1 - self.height / 2
        else:
            x = parent_n - self.width / 2
            y = delta_pos_1 - self.height / 2
        return (x, y)

    def hoverLeaveEvent(self, mouseEvent):
        self.setSelected(False)
        self.update()

    def hoverEnterEvent(self, mouseEvent):
        self.setSelected(True)
        self.update()

    def mousePressEvent(self, mouseEvent):
        if mouseEvent.button() == Qt.LeftButton:
            mouseEvent.accept()

    def delete(self):
        if self.connector:
            self.connector.delete_connection()


class ObjectView(MiniRect):

    def __init__(self, colors, name, log_scen, legs, obj_type, project_tree):
        super().__init__()
        self.custom_angle = 0
        self.object_pen = QPen(Qt.black, 2, Qt.SolidLine)
        self.height = 80
        self.weight = 80
        self.old_pos = None
        self.log_object = None
        self.obj_label = None

        self.passive_color = PASSIVE_COLOR
        self.border = 5
        self.object_legs = []
        self.legs_text = []


        self.active_color = QColor(255, 50, 50)
        self.obj_type = obj_type
        self.setFocusPolicy(Qt.StrongFocus)
        self.resize(self.weight, self.height)
        self.scen = log_scen
        self.colors = colors
        self.menu = QMenu(self.scen.views()[0])
        self.project_tree = project_tree
        self.tree_item = project_tree.findItems(name, Qt.MatchRecursive, 0)[0]
        self.obj_name = name

        max_legs = len(legs)
        for leg_num, leg in enumerate(legs):
            new_leg = LogLeg(leg, leg_num, max_legs, self, self.obj_name)
            new_text = self.scen.addSimpleText(leg)
            new_text.setFont(QFont("Times New Roman", 8))
            self.object_legs.append(new_leg)
            self.legs_text.append(new_text)

        actions = (('Rotate left', self.custom_rotation_left),
                   ('Rotate right', self.custom_rotation_right),
                   ('Flip X', self.flip_x),
                   ('Flip Y', self.flip_y),
                   )

        for action_name, func in actions:
            new_action = QAction(action_name, self)
            new_action.triggered.connect(func)
            self.menu.addAction(new_action)

        if self.obj_type in colors:
            self.color = self.passive_color = QColor(colors[self.obj_type])

        self.setTransformOriginPoint(self.weight / 2,
                                     self.height / 2)
        self.setAcceptHoverEvents(True)

    def flip_x(self):
        matrix = QTransform(1.0, 0.0, 0.0, -1.0, 0, self.height)
        self.apply_matrix(matrix)

    def flip_y(self):
        matrix = QTransform(-1.0, 0.0, 0.0, 1.0, self.weight, 0)
        self.apply_matrix(matrix)

    def apply_matrix(self, transformMatrix):
        self.setTransform(transformMatrix, Qt.SmoothTransformation)
        self.legConnectorUpdate()
        self.updateLegTextPos()

    def custom_rotation_left(self):
        if self.custom_angle != 315:
            self.custom_angle = self.custom_angle + 45
        else:
            self.custom_angle = 0
        self.custom_rotate()

    def custom_rotation_right(self):
        if self.custom_angle != -315:
            self.custom_angle = self.custom_angle - 45
        else:
            self.custom_angle = 0
        self.custom_rotate()

    def custom_rotate(self):
        self.setRotation(self.custom_angle)
        self.legConnectorUpdate()
        self.updateLegTextPos()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.pos()
            self.selected = True
            if self.project_tree.currentItem() != self.tree_item:
                self.project_tree.setCurrentItem(self.tree_item)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None
            self.delta_label = None
            self.legConnectorUpdate()

    def mouseMoveEvent(self, event):
        if not self.old_pos:
            return
        delta = self.mapToScene(event.pos()) - self.mapToScene(self.old_pos)
        old_pos = self.pos()
        new_pos = self.pos() + delta
        if new_pos.x() > self.scen.width():
            new_pos = QPointF(self.scen.width() - 100, new_pos.y())
        elif new_pos.x() < 0:
            new_pos = QPointF(10, new_pos.y())
        if new_pos.y() > 0:
            new_pos = QPointF(new_pos.x(), -5)
        elif new_pos.y() < - self.scen.height():
            new_pos = QPointF(new_pos.x(), - self.scen.height() + 5)
        self.setPos(new_pos)
        if self.obj_label:
            self.obj_label.setPos(self.obj_label.pos() + new_pos - old_pos)
        self.updateLegTextPos()

    def legConnectorUpdate(self):
        for leg in self.object_legs:
            if leg.connector:
                leg.connector.specialTransform()
                leg.connector.update()

    def drawForm(self, painter):
        painter.setPen(self.object_pen)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.selected:
            for leg in self.object_legs:
                if leg.connector:
                    leg.connector.specialTransform()
        '''
        designation.paint_graphic(self.obj_type,
                                  painter,
                                  self.size().height(),
                                  self.size().width(),
                                  self.border)
        '''
        paint_graphic(self.obj_type,
                                  painter,
                                  self.size().height(),
                                  self.size().width(),
                                  self.border)
    def updateLegTextPos(self):
        for text in self.legs_text:
            leg_obj = self.object_legs[self.legs_text.index(text)]
            leg_pos = leg_obj.sceneBoundingRect()
            text.setPos(leg_pos.x() + 4, leg_pos.y() + 10)

    def setDeepValue(self, value):
        self.setZValue(value)
        for text in self.legs_text:
            text.setZValue(value + 0.2)

    def contextMenuEvent(self, event):
        self.menu.exec_(event.screenPos())

    def delete(self):
        for text in self.legs_text:
            self.scen.removeItem(text)


class ObjectLabel(QGraphicsTextItem):
    def __init__(self, text, x=0, y=0):
        super().__init__()
        self.setPos(x, y)
        self.setPlainText(text)
        self.setFont(QFont('Times new roman', 10, QFont.Bold))
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = None

    def mouseMoveEvent(self, event):
        if not self.old_pos:
            return
        delta = event.pos() - self.old_pos
        self.setPos(self.pos() + delta)


class LogicalObject(QGraphicsWidget):

    def __init__(self, name, object_data, z_level, scene, colors, project_tree):
        super().__init__()
        self.selected = False

        # -------------------------------------------------------
        self.name = name
        self.object_data = object_data
        self.colors = colors.get(object_data['Type'])
        # ------------------------------------------------------
        self.scene = scene

        self.object_view = ObjectView(colors, name,
                                      scene, object_data['legs'],
                                      object_data['Type'],
                                      project_tree)
        self.object_view.setObjectName(name)
        self.obj_label = ObjectLabel(name,
                                     self.object_view.x(),
                                     self.object_view.y() - 25
                                     )
        self.object_view.obj_label = self.obj_label
        self.scene.addItem(self.object_view)
        self.scene.addItem(self.obj_label)
        self.setZValue(z_level)
        self.init_z_level = z_level
        self.update()

    def setSelected(self, value=0):
        if not value:
            self.object_view.setSelected(False)
            self.selected = False
            self.setZValue(self.init_z_level)
        else:
            self.object_view.setSelected(True)
            self.setZValue(value)
            self.selected = True

    def setEmergency(self, value=False):
        self.object_view.emergency = value

    def setZValue(self, value):
        self.object_view.setDeepValue(value)
        self.obj_label.setZValue(value + 0.1)

    def move(self, x, y):
        self.object_view.setPos(x, -y)
        pos = self.object_view.sceneBoundingRect()
        self.obj_label.setPos(pos.x(), pos.y() - 20)
        self.object_view.updateLegTextPos()

    def updateColor(self):
        if self.selected:
            return
        indication = self.object_data['indication']
        obj_type = self.object_data['Type']
        if obj_type == 'POINT':
            if 'S_VZ' in indication and indication['S_VZ']['value'] == '0':
                self.object_view.color = QColor(0, 6, 253)
                self.object_view.passive_color = self.object_view.color
            elif 'S_ZVZ' in indication and indication['S_ZVZ']['value'] == '0':
                self.object_view.color = QColor(0, 6, 253)
                self.object_view.passive_color = QColor(0, 6, 253)
            elif 'S_POS' in indication and indication['S_POS']['value'] == '0':
                self.object_view.color = QColor(245, 96, 253)
                self.object_view.passive_color = QColor(245, 96, 253)
            elif 'S_POS' in indication and indication['S_POS']['value'] == '1':
                self.object_view.color = QColor(82, 138, 194)
                self.object_view.passive_color = QColor(82, 138, 194)
            elif 'S_POS' in indication and indication['S_POS']['value'] == '2':
                self.object_view.color = QColor(32, 164, 68)
                self.object_view.passive_color = QColor(32, 164, 68)
            elif 'S_POS' in indication and indication['S_POS']['value'] == '3':
                self.object_view.color = QColor(237, 237, 39)
                self.object_view.passive_color = QColor(237, 237, 39)
            else:
                self.object_view.color = QColor(self.colors)
                self.object_view.passive_color = QColor(self.colors)
        elif obj_type == 'SECTION':
            if 'S_TC' in indication and indication['S_TC']['value'] == '0':
                self.object_view.color = QColor(245, 96, 253)
                self.object_view.passive_color = QColor(245, 96, 253)
            elif 'S_TC' in indication and indication['S_TC']['value'] == '1':
                self.object_view.color = QColor(82, 138, 194)
                self.object_view.passive_color = QColor(82, 138, 194)
            else:
                self.object_view.color = QColor(self.colors)
                self.object_view.passive_color = QColor(self.colors)

        elif obj_type in ('SIGNAL', 'SHSIGNAL'):
            if 'S_SIG' in indication and indication['S_SIG']['value'] == '0':
                self.object_view.color = self.object_view.passive_color = QColor(245, 96, 253)
            elif 'S_SIG' in indication and indication['S_SIG']['value'] not in ('1', ''):
                self.object_view.color = self.object_view.passive_color = QColor(113, 255, 131)
            else:
                self.object_view.color = QColor(self.colors)
                self.object_view.passive_color = QColor(self.colors)
        self.object_view.update()

    def accept_new_colors(self, colors):
        self.colors = colors[self.object_data['Type']]
        self.object_view.color = QColor(self.colors)
        self.object_view.passive_color = QColor(self.colors)
        self.updateColor()

    def delete(self):
        if self.object_view:
            self.object_view.delete()
        self.deleteLater()


class CustomGraphicsView(QGraphicsView):
    current_modifier = None
    max_scale = 5
    min_scale = 0.2
    current_scale = 1
    scale_ratio = 1.2

    def __init__(self):
        super().__init__()
        self.setViewportUpdateMode(self.FullViewportUpdate)

    def wheelEvent(self, event):
        if self.current_modifier == Qt.ControlModifier:
            if (event.angleDelta().y() > 0
                    and self.max_scale > self.current_scale):
                self.current_scale = self.current_scale * self.scale_ratio
                self.scale(self.scale_ratio, self.scale_ratio)
            elif (event.angleDelta().y() < 0
                  and self.min_scale < self.current_scale):

                self.scale(1 / self.scale_ratio, 1 / self.scale_ratio)
                self.current_scale = self.current_scale * 1 / self.scale_ratio

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.current_modifier = Qt.ControlModifier
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setDragMode(self.ScrollHandDrag)
            self.original_event = event
            handmade_event = QMouseEvent(QEvent.MouseButtonPress,
                                         QPointF(event.pos()),
                                         Qt.LeftButton,
                                         event.buttons(),
                                         Qt.KeyboardModifiers())
            self.mousePressEvent(handmade_event)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MidButton:
            self.setDragMode(self.NoDrag)
            handmade_event = QMouseEvent(QEvent.MouseButtonRelease,
                                         QPointF(event.pos()),
                                         Qt.LeftButton,
                                         event.buttons(),
                                         Qt.KeyboardModifiers())
            self.mouseReleaseEvent(handmade_event)

    def keyReleaseEvent(self, event):
        self.current_modifier = None
        event.accept()


class CustomSpinBox(QSpinBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = None

    def wheelEvent(self, event):
        event.ignore()
