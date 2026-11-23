# coding: utf-8
"""Windows WeChat mini-program screenshot helper.

Returns a BGR image at the legacy detector's expected resolution (1040x629).
Pillow captures the visible desktop; the game must not be covered by other windows.
"""
import ctypes

import cv2
import numpy as np
import win32gui
from PIL import ImageGrab


def enable_dpi_awareness():
    try:
        # Per-monitor awareness, required to keep Win32 coordinates and pixels aligned.
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


enable_dpi_awareness()


def find_game_window():
    for title in ("腾讯欢乐斗地主", "欢乐斗地主"):
        hwnd = win32gui.FindWindow(None, title)
        if hwnd and win32gui.IsWindow(hwnd):
            return hwnd
    return 0


def screen(hwnd=None):
    hwnd = hwnd if hwnd and win32gui.IsWindow(hwnd) else find_game_window()
    if not hwnd or win32gui.IsIconic(hwnd):
        return None

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    if right <= left or bottom <= top:
        return None

    try:
        pil_image = ImageGrab.grab(
            bbox=(left, top, right, bottom),
            all_screens=True,
        )
        image = cv2.cvtColor(np.asarray(pil_image), cv2.COLOR_RGB2BGR)
        return cv2.resize(image, (1040, 629), interpolation=cv2.INTER_CUBIC)
    except (OSError, ValueError, cv2.error) as exc:
        print("游戏截图失败:", exc)
        return None
