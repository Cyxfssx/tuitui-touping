"""Send one image to the active editor of the Tuitui 2 IME through ADB."""
from pathlib import Path
import secrets
from PySide6.QtCore import QThread, Signal
from . import adb
from .config import ROOT

SCANNER = ROOT / 'assets' / 'tuitui2-scanner.jar'
IME = 'com.chatmirror.warmclone2/com.cyxfssx.warmime.WarmInputMethodService'

class ImageJob(QThread):
    result = Signal(bool, str)
    def __init__(self, serial, image_path, parent=None):
        super().__init__(parent); self.serial=serial; self.image_path=Path(image_path)
    def run(self):
        token=secrets.token_hex(16)
        scanner='/data/local/tmp/tuitui2-qt-bridge.jar'
        remote='/data/local/tmp/warm-image-'+token+'.tmp'
        def execute(*args,timeout=20):
            r=adb.run('-s',self.serial,*args,timeout=timeout)
            if r.returncode: raise RuntimeError((r.stderr+' '+r.stdout).strip() or 'ADB 操作失败')
            return r.stdout.strip()
        try:
            if not SCANNER.is_file(): raise RuntimeError('找不到推推2图片桥接器')
            if not self.image_path.is_file() or not (0 < self.image_path.stat().st_size <= 32*1024*1024): raise RuntimeError('图片不存在、为空或超过 32 MB')
            selected=execute('shell','settings','get','secure','default_input_method')
            if selected != IME: raise RuntimeError('请在手机上切换到推推2输入法')
            execute('push',str(SCANNER),scanner,timeout=30)
            command='CLASSPATH='+scanner+' app_process / com.genymobile.scrcpy.WarmImeBridge '
            try: execute('shell',command+'arm '+token)
            except RuntimeError as e: raise RuntimeError('请先点击支持图片输入的手机聊天输入框，再试一次。'+str(e)) from e
            execute('push',str(self.image_path),remote,timeout=120)
            out=execute('shell',command+'deliver '+token+' '+remote,timeout=30)
            if 'Warm IME: accepted' not in out: raise RuntimeError('聊天应用未确认接收图片：'+out)
            self.result.emit(True,'聊天应用已接受图片，请检查预览；不会自动发送消息。')
        except Exception as e: self.result.emit(False,str(e))
        finally:
            try: adb.run('-s',self.serial,'shell','rm','-f',remote,timeout=5)
            except Exception: pass
