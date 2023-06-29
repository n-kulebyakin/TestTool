def paint_shsignal(painter, height, border):
    painter.drawLine(20 + border,
                     height / 2 - 8,
                     20 + border,
                     height / 2 + 8)
    painter.drawEllipse(20 + border,
                        height / 2 - 8,
                        16, 16)


def paint_signal(painter, height, border):
    painter.drawLine(11 + border,
                     height / 2 - 8,
                     11 + border,
                     height / 2 + 8)
    painter.drawEllipse(12 + border,
                        height / 2 - 8,
                        16, 16)
    painter.drawEllipse(28 + border,
                        height / 2 - 8,
                        16, 16)


def paint_point(painter, height, width, border):
    painter.drawLine(10 + border,
                     height / 2,
                     width - 10 - border,
                     height / 2)
    painter.drawLine(width / 2 - 1,
                     height / 2,
                     width - 10 - border,
                     height / 2 - 15)


def paint_section(painter, height, width, border):
    painter.drawLine(10 + border,
                     height / 2,
                     width - 10 - border,
                     height / 2)
    painter.drawLine(border + 10,
                     height / 2 - 8,
                     border + 10,
                     height / 2 + 8)
    painter.drawLine(height - 10 - border,
                     height / 2 - 8,
                     height - 10 - border,
                     width / 2 + 8)


def paint_station_border(painter, height, width, border):
    painter.drawRect(15 + border,
                     height / 2 - 10,
                     30, 20)
    painter.drawLine(15 + border,
                     height / 2,
                     width - 15,
                     height / 2)


def print_endblock(painter, height, width, border):
    painter.drawRect(15 + border,
                     height / 2 - 10,
                     30, 20)
    painter.drawLine(15 + border,
                     height / 2,
                     width - 15,
                     height / 2)


def paint_graphic(obj_type, painter, height, width, border):
    if obj_type == "SHSIGNAL":
        paint_shsignal(painter, height, border)
    elif obj_type == "SIGNAL":
        paint_signal(painter, height, border)
    elif obj_type == "POINT":
        paint_point(painter, height, width, border)
    elif obj_type == "SECTION":
        paint_section(painter, height, width, border)
    elif obj_type in ("LINEBLOCK", "ABTC"):
        paint_station_border(painter, height, width, border)
    elif obj_type == "ENDBLOCK":
        print_endblock(painter, height, width, border)
