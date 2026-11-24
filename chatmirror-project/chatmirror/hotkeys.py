"""Intercept image Ctrl+V only while a managed scrcpy window is foreground."""
import ctypes
from ctypes import wintypes
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

user32=ctypes.WinDLL('user32',use_last_error=True)
kernel32=ctypes.WinDLL('kernel32',use_last_error=True)
LRESULT=ctypes.c_ssize_t
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_=[('vkCode',wintypes.DWORD),('scanCode',wintypes.DWORD),('flags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ctypes.c_size_t)]
HOOKPROC=ctypes.WINFUNCTYPE(LRESULT,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
user32.SetWindowsHookExW.argtypes=[ctypes.c_int,HOOKPROC,wintypes.HINSTANCE,wintypes.DWORD]; user32.SetWindowsHookExW.restype=wintypes.HHOOK
user32.CallNextHookEx.argtypes=[wintypes.HHOOK,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM];user32.CallNextHookEx.restype=LRESULT
user32.UnhookWindowsHookEx.argtypes=[wintypes.HHOOK];user32.UnhookWindowsHookEx.restype=wintypes.BOOL
user32.GetForegroundWindow.restype=wintypes.HWND
user32.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
user32.GetAsyncKeyState.argtypes=[ctypes.c_int];user32.GetAsyncKeyState.restype=ctypes.c_short
kernel32.GetModuleHandleW.argtypes=[wintypes.LPCWSTR];kernel32.GetModuleHandleW.restype=wintypes.HMODULE

class ImagePasteHook(QObject):
    paste_requested=Signal(str)
    def __init__(self,processes,parent=None):
        super().__init__(parent);self.processes=processes;self.hook=None;self.suppress_v=False;self.callback=HOOKPROC(self.on_key)
    def start(self):
        if self.hook:return
        self.hook=user32.SetWindowsHookExW(13,self.callback,kernel32.GetModuleHandleW(None),0)
        if not self.hook: raise OSError(ctypes.get_last_error(),'无法启用投屏窗口图片快捷键')
    def stop(self):
        if self.hook:user32.UnhookWindowsHookEx(self.hook);self.hook=None
    def target(self):
        hwnd=user32.GetForegroundWindow(); pid=wintypes.DWORD();user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        return next((serial for serial,p in self.processes.items() if p.processId() and p.processId()==pid.value),None)
    def image_available(self):
        mime=QApplication.clipboard().mimeData()
        if mime is None:return False
        if mime.hasImage():return True
        return any(u.isLocalFile() and Path(u.toLocalFile()).is_file() and Path(u.toLocalFile()).suffix.lower() in ('.png','.jpg','.jpeg','.webp','.bmp','.gif') for u in mime.urls()) if mime.hasUrls() else False
    def on_key(self,code,wparam,lparam):
        if code>=0:
            event=ctypes.cast(lparam,ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            if event.vkCode==0x56:
                if wparam in (0x101,0x105) and self.suppress_v:
                    self.suppress_v=False;return 1
                if wparam in (0x100,0x104):
                    if self.suppress_v:return 1
                    serial=self.target()
                    if serial and (user32.GetAsyncKeyState(0x11)&0x8000) and not (user32.GetAsyncKeyState(0x12)&0x8000) and self.image_available():
                        self.suppress_v=True;self.paste_requested.emit(serial);return 1
        return user32.CallNextHookEx(self.hook,code,wparam,lparam)
