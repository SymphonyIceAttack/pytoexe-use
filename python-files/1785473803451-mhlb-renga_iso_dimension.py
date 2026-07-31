# -*- coding: utf-8 -*-
"""
RENGA — изометрический размер трассы (черновая версия, шаг 1)
================================================================

Что делает:
  1) Подключается к уже ЗАПУЩЕННОЙ Renga с открытым проектом
  2) Спрашивает координаты двух точек трассы (X, Y, Z в мм — как в Ренге)
  3) Считает реальную 3D-длину между точками
  4) Пересчитывает точки в изометрическую проекцию (30°)
  5) Ставит на активном чертеже подпись длины (DrawingText),
     развёрнутую под правильным изометрическим углом
  6) Печатает список свойств пустого DrawingLine — это нужно нам,
     чтобы на шаге 2 дорисовать сами линии размера (выноски + стрелки)

Что нужно перед запуском:
  1) pip install pywin32
  2) Renga должна быть ОТКРЫТА, проект открыт, активен ЛИСТ ЧЕРТЕЖА
     (не 3D-вид! DrawingText/DrawingLine создаются только на чертеже)
  3) Запускать скрипт: python renga_iso_dimension.py
"""

import math
import win32com.client


def connect_to_renga():
    """Подключение к уже запущенному экземпляру Renga через COM (ROT)."""
    try:
        app = win32com.client.GetActiveObject("Renga.Application.1")
    except Exception as e:
        raise RuntimeError(
            "Не удалось подключиться к Renga. Проверьте, что Renga запущена "
            "и открыт проект.\nТекст ошибки: %s" % e
        )
    if app.Project is None:
        raise RuntimeError("В Renga нет открытого проекта.")
    return app


def get_active_drawing_model(app):
    """
    Возвращает IModel активного чертежа.
    ВАЖНО: этот кусок — то самое место, которое может потребовать правки,
    если в вашей версии API активный чертёж достаётся иначе.
    Если тут будет ошибка — просто скажите мне текст ошибки, поправим.
    """
    project = app.Project
    drawings = project.Drawings2
    if drawings.Count == 0:
        raise RuntimeError("В проекте нет ни одного чертежа. Создайте лист чертежа.")
    # берём первый чертёж по умолчанию — потом заменим на "активный"
    drawing = drawings.GetByIndex(0)
    drawing_model = drawing.QueryInterface_IModel() if hasattr(drawing, "QueryInterface_IModel") else drawing
    # pywin32 обычно сам даёт нужный интерфейс, если он у объекта есть:
    return drawing


def to_point3d(x, y, z):
    return (float(x), float(y), float(z))


def real_length(p1, p2):
    return math.sqrt(
        (p2[0] - p1[0]) ** 2 +
        (p2[1] - p1[1]) ** 2 +
        (p2[2] - p1[2]) ** 2
    )


def project_isometric(p):
    """
    Стандартная изометрическая проекция 30 градусов.
    Вход: 3D точка (x, y, z) в мм
    Выход: 2D точка (X_iso, Y_iso) для размещения на листе чертежа
    """
    x, y, z = p
    cos30 = math.cos(math.radians(30))
    sin30 = math.sin(math.radians(30))
    x_iso = (x - y) * cos30
    y_iso = z + (x + y) * sin30
    return (x_iso, y_iso)


def iso_angle_degrees(p1_iso, p2_iso):
    """Угол направления отрезка в изометрической проекции (для поворота текста/линий)."""
    dx = p2_iso[0] - p1_iso[0]
    dy = p2_iso[1] - p1_iso[1]
    return math.degrees(math.atan2(dy, dx))


def create_length_text(drawing_model, mid_point_iso, angle_deg, length_value_mm):
    """
    Создаёт подпись длины (DrawingText) в середине отрезка,
    развёрнутую вдоль направления трубы в изометрии.
    """
    args = drawing_model.CreateNewEntityArgs()
    args.TypeId = win32com.client.constants.DrawingText  # если constants не подтянулись — заменим на GUID вручную

    angle_rad = math.radians(angle_deg)
    placement = win32com.client.Dispatch("Renga.Placement2D")
    # ниже — Origin и xAxis, как описано в документации CreateNewEntityArgs
    placement.Origin = (mid_point_iso[0], mid_point_iso[1])
    placement.xAxis = (math.cos(angle_rad), math.sin(angle_rad))
    args.Placement2D = placement

    text_object = drawing_model.CreateObject(args)

    # Текст значения — имя свойства может отличаться (Text / Value / Content).
    # Пробуем самый вероятный вариант:
    text_str = "%.0f" % round(length_value_mm)
    try:
        text_object.Text = text_str
    except Exception:
        print("!! Не удалось сразу задать текст через .Text — "
              "нужно уточнить правильное имя свойства (см. диагностику ниже).")

    return text_object


def inspect_drawingline_properties(drawing_model):
    """
    Диагностика: создаём временный DrawingLine и печатаем всё, что у него есть,
    чтобы найти точное имя свойства для координат начала/конца.
    """
    print("\n--- Диагностика объекта DrawingLine ---")
    args = drawing_model.CreateNewEntityArgs()
    args.TypeId = win32com.client.constants.DrawingLine
    try:
        line_obj = drawing_model.CreateObject(args)
    except Exception as e:
        print("Не удалось создать тестовую DrawingLine:", e)
        return

    print("Тип объекта Python:", type(line_obj))
    print("Доступные атрибуты/методы:")
    for name in dir(line_obj):
        if not name.startswith("_"):
            print("   ", name)
    print("--- конец диагностики ---\n")
    print("Скопируйте этот список и пришлите мне — я допишу построение")
    print("выносных линий, размерной линии и стрелок под изометрию.")


def main():
    print("=== Renga: изометрический размер трассы ===\n")

    app = connect_to_renga()
    drawing_model = get_active_drawing_model(app)

    print("Введите координаты ТОЧКИ 1 (в мм, как в Ренге):")
    x1 = input("  X1 = ")
    y1 = input("  Y1 = ")
    z1 = input("  Z1 = ")

    print("Введите координаты ТОЧКИ 2 (в мм, как в Ренге):")
    x2 = input("  X2 = ")
    y2 = input("  Y2 = ")
    z2 = input("  Z2 = ")

    p1 = to_point3d(x1, y1, z1)
    p2 = to_point3d(x2, y2, z2)

    length_mm = real_length(p1, p2)
    print("\nРеальная длина участка: %.1f мм" % length_mm)

    p1_iso = project_isometric(p1)
    p2_iso = project_isometric(p2)
    mid_iso = ((p1_iso[0] + p2_iso[0]) / 2, (p1_iso[1] + p2_iso[1]) / 2)
    angle = iso_angle_degrees(p1_iso, p2_iso)

    print("Изометрическая точка 1: %s" % (p1_iso,))
    print("Изометрическая точка 2: %s" % (p2_iso,))
    print("Угол линии в изометрии: %.1f°" % angle)

    operation = app.Project.CreateOperation()
    operation.Start()
    try:
        create_length_text(drawing_model, mid_iso, angle, length_mm)
        operation.Apply()
        print("\nГотово: подпись длины создана на чертеже.")
    except Exception as e:
        operation.Cancel() if hasattr(operation, "Cancel") else None
        print("Ошибка при создании объекта:", e)
        return

    # Диагностика для следующего шага (линии/стрелки)
    operation2 = app.Project.CreateOperation()
    operation2.Start()
    inspect_drawingline_properties(drawing_model)
    operation2.Cancel() if hasattr(operation2, "Cancel") else operation2.Apply()


if __name__ == "__main__":
    main()
