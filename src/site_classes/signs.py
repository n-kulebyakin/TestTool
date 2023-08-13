from PyQt5.QtGui import QColor
from PyQt5.QtGui import QPen


def paint_shsignal(painter, half_height, border):
    painter.drawLine(20 + border, half_height - 8, 20 + border,
                     half_height + 8)
    painter.drawEllipse(20 + border, half_height - 8, 16, 16)


def paint_signal(painter, half_height, border):
    painter.drawLine(11 + border, half_height - 8, 11 + border,
                     half_height + 8)
    painter.drawEllipse(12 + border, half_height - 8, 16, 16)
    painter.drawEllipse(28 + border, half_height - 8, 16, 16)


def paint_point(painter, half_height, half_width, width, border):
    painter.drawLine(10 + border, half_height, width - 10 - border,
                     half_height)
    painter.drawLine(half_width - 1, half_height, width - 10 - border,
                     half_height - 15)


def paint_section(painter, half_height, half_width, height, width, border):
    painter.drawLine(10 + border, half_height, width - 10 - border,
                     half_height)
    painter.drawLine(border + 10, half_height - 8, border + 10,
                     half_height + 8)
    painter.drawLine(height - 10 - border, half_height - 8,
                     height - 10 - border, half_width + 8)


def paint_station_border(painter, half_height, width, border):
    painter.drawRect(15 + border, half_height - 10, 30, 20)
    painter.drawLine(15 + border, half_height, width - 15, half_height)


def print_endblock(painter, half_height, width, border):
    painter.drawRect(15 + border, half_height - 10, 30, 20)
    painter.drawLine(15 + border, half_height, width - 15, half_height)


def paint_graphic(obj_type, painter, height, width, border):
    height = int(height)
    width = int(width)
    half_height = height // 2
    half_width = width // 2
    pen = QPen(QColor("black"))
    pen.setWidth(2)
    painter.setPen(pen)

    if obj_type == "SHSIGNAL":
        paint_shsignal(painter, half_height, border)
    elif obj_type == "SIGNAL":

        paint_signal(painter, half_height, border)
    elif obj_type == "POINT":
        paint_point(painter, half_height, half_width, width, border)
    elif obj_type == "SECTION":
        paint_section(painter, half_height, half_width, height, width, border)
    elif obj_type in ("LINEBLOCK", "ABTC"):
        paint_station_border(painter, half_height, width, border)
    elif obj_type == "ENDBLOCK":
        print_endblock(painter, half_height, width, border)
