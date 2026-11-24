"""Locate scrcpy windows by process ID and record their on-screen bounds."""
import ctypes
from ctypes import wintypes
u=ctypes.WinDLL('user32',use_last_error=True)
ENUMPROC=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
u.EnumWindows.argtypes=[ENUMPROC,wintypes.LPARAM];u.EnumWindows.restype=wintypes.BOOL
u.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
u.IsWindowVisible.argtypes=[wintypes.HWND];u.IsWindowVisible.restype=wintypes.BOOL
u.IsIconic.argtypes=[wintypes.HWND];u.IsIconic.restype=wintypes.BOOL
u.GetWindowRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)];u.GetWindowRect.restype=wintypes.BOOL
u.GetWindowTextLengthW.argtypes=[wintypes.HWND];u.GetWindowTextLengthW.restype=ctypes.c_int
u.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
u.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int];u.SetForegroundWindow.argtypes=[wintypes.HWND]
u.SetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPCWSTR];u.SetWindowTextW.restype=wintypes.BOOL

def window_for_pid(pid):
    found=[]
    @ENUMPROC
    def visit(hwnd,_):
        actual=wintypes.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(actual))
        if actual.value==pid and u.IsWindowVisible(hwnd) and u.GetWindowTextLengthW(hwnd)>0:found.append(hwnd);return False
        return True
    u.EnumWindows(visit,0);return found[0] if found else None

def bounds(pid):
    hwnd=window_for_pid(pid)
    if not hwnd or u.IsIconic(hwnd):return None
    r=wintypes.RECT()
    if not u.GetWindowRect(hwnd,ctypes.byref(r)):return None
    width,height=r.right-r.left,r.bottom-r.top
    return [r.left,r.top,width,height] if width>=100 and height>=100 else None

def show(pid):
    hwnd=window_for_pid(pid)
    if not hwnd:return False
    u.ShowWindow(hwnd,9);return bool(u.SetForegroundWindow(hwnd))


def set_title(pid,title):
    hwnd=window_for_pid(pid)
    return bool(hwnd and u.SetWindowTextW(hwnd,title))
