"""
Traktor 4 Vocal Diagram Overlay
Отображает статичную шкалу вокала поверх окна Traktor.
Требует: pip install pywin32
"""

import json
import os
import tkinter as tk
import win32gui
import win32con
import win32api


# ============================================================
# НАСТРОЙКИ — меняйте здесь
# ============================================================

# Размер одного оверлея: 640 x 50
OVERLAY_W = 640
OVERLAY_H = 50

# Координаты дек на экране (левый верхний угол каждого оверлея)
# Отрегулируйте под положение дек в вашем Traktor 4.
DECK_RECTS = {
    "A": (100, 600),   # (x, y) для деки A
    "B": (850, 600),   # (x, y) для деки B
}

# Путь к папке с диаграммами (файлы <name>_diagramm.json)
DIAGRAM_DIR = "./diagrams"

# Цвета
COLOR_VOCAL = "#00FF00"      # зелёный — есть вокал
COLOR_NO_VOCAL = "#000000"   # чёрный — нет вокала
COLOR_BG = "#000000"         # фон пустой шкалы (когда нет диаграммы)
COLOR_BORDER = "#333333"     # рамка (опционально)

# Прозрачность фона оверлея (0-255, 0 = полностью прозрачный)
# Сам Canvas рисуется поверх, фон окна должен пропадать.
TRANSPARENT_COLORKEY = "#010203"  # цвет-ключ, который станет прозрачным

# ============================================================
# Логика
# ============================================================

def load_diagram(track_name: str) -> list | None:
    """
    Загружает диаграмму для трека.
    Ищет файл <track_name>_diagramm.json в DIAGRAM_DIR.
    Возвращает список [start, end, vocal] или None, если файла нет.
    """
    # Убираем расширение .mp3, если есть
    base = os.path.splitext(track_name)[0]
    filename = f"{base}_diagramm.json"
    path = os.path.join(DIAGRAM_DIR, filename)

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Валидация: каждый элемент — список из 3 чисел
        if not isinstance(data, list):
            return None
        for item in data:
            if not (isinstance(item, list) and len(item) == 3):
                return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def make_clickthrough(root):
    root.update_idletasks()

    # Ключевой момент: использовать wm_frame(), а не winfo_id()
    hwnd = int(root.wm_frame(), 16)

    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    colorkey = win32api.RGB(1, 2, 3)
    win32gui.SetLayeredWindowAttributes(hwnd, colorkey, 0, win32con.LWA_COLORKEY)

    # Принудительно установить поверх всех окон, без активации и без изменения размера/позиции
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOPMOST,
        0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
    )


def draw_bar(canvas: tk.Canvas, diagram: list | None, width: int, height: int):
    """
    Рисует шкалу на canvas.
    diagram = None → пустая шкала (только фон).
    diagram = список [start, end, vocal] → цветные сегменты.
    """
    canvas.delete("all")

    if not diagram or not diagram:
        # Нет данных — просто пустая шкала с тонкой рамкой
        canvas.create_rectangle(
            0, 0, width, height,
            fill=COLOR_BG, outline=COLOR_BORDER, width=1
        )
        return

    # Находим максимальное время, чтобы масштабировать шкалу
    max_time = max(seg[1] for seg in diagram if seg[1] > 0)
    if max_time <= 0:
        max_time = 1.0

    for seg in diagram:
        start, end, vocal = seg
        # Переводим секунды в пиксели
        x1 = (start / max_time) * width
        x2 = (end / max_time) * width

        color = COLOR_VOCAL if vocal == 1 else COLOR_NO_VOCAL
        canvas.create_rectangle(
            x1, 0, x2, height,
            fill=color, outline=""
        )


def create_deck_overlay(deck_name: str, x: int, y: int, diagram: list | None):
    """
    Создаёт одно окно-оверлей для деки.
    diagram — загруженная диаграмма или None.
    """
    root = tk.Tk()
    root.title(f"Vocal Diagram - Deck {deck_name}")
    root.geometry(f"{OVERLAY_W}x{OVERLAY_H}+{x}+{y}")
    root.configure(bg=TRANSPARENT_COLORKEY)

    # Canvas для рисования шкалы
    canvas = tk.Canvas(
        root, width=OVERLAY_W, height=OVERLAY_H,
        bg=TRANSPARENT_COLORKEY, highlightthickness=0
    )
    canvas.pack(fill="both", expand=True)

    # Делаем окно click-through и topmost
    make_clickthrough(root)

    # Рисуем шкалу
    draw_bar(canvas, diagram, OVERLAY_W, OVERLAY_H)

    return root

def keep_on_top(root, hwnd):
    win32gui.SetWindowPos(
        hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
        win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
    )
    root.after(1000, lambda: keep_on_top(root, hwnd))

def draw_bar_on_canvas(canvas, diagram, x, y, width, height):
    """
    Рисует шкалу вокала на общем Canvas в области (x, y, width, height).

    Параметры:
        canvas   — tk.Canvas, на котором рисуем
        diagram  — список [start_sec, end_sec, vocal] или None
        x, y     — координаты левого верхнего угла шкалы на Canvas
        width    — ширина шкалы в пикселях (например, 640)
        height   — высота шкалы в пикселях (например, 50)
    """
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


def main():
    """
    Точка входа.
    В текущей версии: для каждой деки загружается диаграмма
    и создаётся отдельное окно-оверлей.

    Здесь жёстко заданы имена треков для теста.
    В реальной интеграции эти имена будет передавать Track Listener
    (через traktor_nowplaying или другой механизм).
    """
    # --- ТЕСТОВЫЕ ДАННЫЕ: имена треков для каждой деки ---
    # В реальной системе эти значения приходят от слушателя Traktor.
    track_names = {
        "A": "name.mp3",      # замените на имя трека, играющего в деке A
        "B": "other_track.mp3",
    }

    roots = []

    for deck, (x, y) in DECK_RECTS.items():
        track = track_names.get(deck)
        diagram = load_diagram(track) if track else None

        if diagram is None:
            print(f"[Deck {deck}] Диаграмма для '{track}' не найдена — шкала будет пустой.")
        else:
            print(f"[Deck {deck}] Загружена диаграмма для '{track}': {len(diagram)} сегментов.")



        root = create_deck_overlay(deck, x, y, diagram)
        roots.append(root)

    if not roots:
        print("Нет дек для отображения.")
        return


    # Запускаем главный цикл (все окна живут в одном цикле)
    roots[0].mainloop()




