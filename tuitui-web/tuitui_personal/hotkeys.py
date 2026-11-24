"""Windows clipboard and keyboard hook. Text keystrokes always pass through."""
import ctypes, tempfile
from ctypes import wintypes
from pathlib import Path
from PIL import Image, ImageGrab
from .backend import DATA

u=ctypes.WinDLL('user32',use_last_error=True);k=ctypes.WinDLL('kernel32',use_last_error=True)
LRESULT=ctypes.c_ssize_t
class Event(ctypes.Structure):
    _fields_=[('vkCode',wintypes.DWORD),('scanCode',wintypes.DWORD),('flags',wintypes.DWORD),('time',wintypes.DWORD),('extra',ctypes.c_size_t)]
CALLBACK=ctypes.WINFUNCTYPE(LRESULT,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
u.SetWindowsHookExW.argtypes=[ctypes.c_int,CALLBACK,wintypes.HINSTANCE,wintypes.DWORD];u.SetWindowsHookExW.restype=wintypes.HHOOK
u.CallNextHookEx.argtypes=[wintypes.HHOOK,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM];u.CallNextHookEx.restype=LRESULT
u.UnhookWindowsHookEx.argtypes=[wintypes.HHOOK];u.GetForegroundWindow.restype=wintypes.HWND
u.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
u.GetAsyncKeyState.argtypes=[ctypes.c_int];u.GetAsyncKeyState.restype=ctypes.c_short
u.IsClipboardFormatAvailable.argtypes=[wintypes.UINT];u.IsClipboardFormatAvailable.restype=wintypes.BOOL
u.RegisterClipboardFormatW.argtypes=[wintypes.LPCWSTR];u.RegisterClipboardFormatW.restype=wintypes.UINT
PNG_FORMAT=u.RegisterClipboardFormatW('PNG')
k.GetModuleHandleW.argtypes=[wintypes.LPCWSTR];k.GetModuleHandleW.restype=wintypes.HMODULE

def image_available():
    if any(u.IsClipboardFormatAvailable(x) for x in (2,8,17,PNG_FORMAT)):return True
    if u.IsClipboardFormatAvailable(15):
        obj=ImageGrab.grabclipboard()
        return isinstance(obj,list) and any(Path(p).is_file() and Path(p).suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif','.bmp'} for p in obj)
    return False

def capture():
    obj=ImageGrab.grabclipboard()
    if isinstance(obj,list):
        for name in obj:
            p=Path(name)
            if p.is_file() and p.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.gif','.bmp'}:return str(p),False
    if isinstance(obj,Image.Image):
        folder=DATA/'temp';folder.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix='clip-',suffix='.png',dir=folder,delete=False) as f:path=f.name
        try:obj.save(path,'PNG')
        except Exception:Path(path).unlink(missing_ok=True);raise
        return path,True
    return None

class Hook:
    def __init__(self,root,backend,enabled,notify):
        self.root=root;self.backend=backend;self.enabled=enabled;self.notify=notify;self.hook=None;self.blocked=False;self.fn=CALLBACK(self.callback)
    def start(self):
        self.hook=u.SetWindowsHookExW(13,self.fn,k.GetModuleHandleW(None),0)
        if not self.hook:raise OSError(ctypes.get_last_error(),'无法启用图片快捷键')
    def stop(self):
        if self.hook:u.UnhookWindowsHookEx(self.hook);self.hook=None
    def callback(self,code,kind,ptr):
        try:
            if code>=0:
                event=ctypes.cast(ptr,ctypes.POINTER(Event)).contents
                if event.vkCode==0x56:
                    if kind in (0x101,0x105) and self.blocked:self.blocked=False;return 1
                    if kind in (0x100,0x104):
                        if self.blocked:return 1
                        pid=wintypes.DWORD();u.GetWindowThreadProcessId(u.GetForegroundWindow(),ctypes.byref(pid))
                        serial=next((s for s,p in self.backend.processes.items() if p.pid==pid.value and p.poll() is None),None)
                        if serial and self.enabled() and u.GetAsyncKeyState(0x11)&0x8000 and not u.GetAsyncKeyState(0x12)&0x8000:
                            if image_available():
                                self.blocked=True;self.backend.emit('hotkey_image',serial);return 1
        except Exception as exc:self.backend.emit('hotkey_error',str(exc))
        return u.CallNextHookEx(self.hook,code,kind,ptr)
