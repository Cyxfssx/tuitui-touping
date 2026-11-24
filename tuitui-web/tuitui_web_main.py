import ctypes
import webview
from pathlib import Path
from tuitui_web.controller import Controller

def main():
    controller=Controller();simple=controller._config.value.get('simple_mode',True)
    path=Path(__file__).resolve().parent/'tuitui_web'/'assets'/'index.html'
    window=webview.create_window('推推投屏 · 现代版',str(path),js_api=controller,width=620 if simple else 1180,height=720 if simple else 850,min_size=(520,500),background_color='#0B1220',resizable=True)
    def dark_titlebar():
        user=ctypes.windll.user32;user.FindWindowW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p];user.FindWindowW.restype=ctypes.c_void_p
        hwnd=user.FindWindowW(None,'推推投屏 · 现代版')
        if hwnd:
            value=ctypes.c_int(1);ctypes.windll.dwmapi.DwmSetWindowAttribute(ctypes.c_void_p(hwnd),20,ctypes.byref(value),ctypes.sizeof(value))
    window.events.shown += dark_titlebar
    controller._start(window)
    window.events.loaded += controller._attach_drop
    window.events.closing += controller._close
    webview.start(gui='edgechromium')
if __name__=='__main__':main()
