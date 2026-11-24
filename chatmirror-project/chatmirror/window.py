import ctypes
from ctypes import wintypes
from .config import SCRCPY
# Capture the independent scrcpy window rectangle before closing or exiting.
def window_geometry(serial):
    user=ctypes.windll.user32; hwnd=user.FindWindowW(None,'ChatMirror - '+serial)
    if not hwnd: return None
    rect=wintypes.RECT()
    if not user.GetWindowRect(hwnd,ctypes.byref(rect)): return None
    return [rect.left,rect.top,rect.right-rect.left,rect.bottom-rect.top]
