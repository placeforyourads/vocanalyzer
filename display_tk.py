"""from displayer import load_diagram
def draw_bar_on_canvas(canvas, diagram, x, y, width, height):
    """"""
    Рисует шкалу вокала на общем Canvas в области (x, y, width, height).

    Параметры:
        canvas   — tk.Canvas, на котором рисуем
        diagram  — список [start_sec, end_sec, vocal] или None
        x, y     — координаты левого верхнего угла шкалы на Canvas
        width    — ширина шкалы в пикселях (например, 640)
        height   — высота шкалы в пикселях (например, 50)
    """"""
    # Уникальный тег, чтобы можно было удалить/перерисовать только эту шкалу,
    # не трогая другие элементы на общем Canvas.
    tag = f"bar_{x}_{y}"
    COLOR_BG = 'black'
    COLOR_BORDER = 'grey'
    COLOR_VOCAL = 'green'
    COLOR_NO_VOCAL = 'black'


    # Стираем предыдущую отрисовку этой шкалы (если была)
    canvas.delete(tag)

    if not diagram:
        # Нет данных — пустая шкала с тонкой рамкой
        canvas.create_rectangle(
            x, y, x + width, y + height,
            fill=COLOR_BG,
            outline=COLOR_BORDER,
            width=1,
            tags=tag
        )
        return

    # Находим максимальное время, чтобы масштабировать шкалу по ширине.
    # Если все сегменты нулевые — защита от деления на ноль.
    max_time = max((seg[1] for seg in diagram if seg[1] > 0), default=0)
    if max_time <= 0:
        max_time = 1.0

    # Рисуем каждый сегмент
    for seg in diagram:
        start, end, vocal = seg

        # Переводим секунды в пиксели относительно области шкалы
        x1 = x + (start / max_time) * width
        x2 = x + (end / max_time) * width

        # Защита от нулевой ширины (совпадающие start и end)
        if x2 - x1 < 1:
            x2 = x1 + 1

        color = COLOR_VOCAL if vocal == 1 else COLOR_NO_VOCAL

        canvas.create_rectangle(
            x1, y, x2, y + height,
            fill=color,
            outline="",
            tags=tag
        )

import tkinter as tk
import win32gui, win32con, win32api

def make_clickthrough(root):
    root.update_idletasks()
    hwnd = root.winfo_id()
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
    colorkey = win32api.RGB(1, 2, 3)
    win32gui.SetLayeredWindowAttributes(hwnd, colorkey, 0, win32con.LWA_COLORKEY)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,0,0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

"""