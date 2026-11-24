import base64
import re
from PySide6.QtCore import QObject, QProcess, Signal
from .config import ADB, ROOT
IME = 'com.chatmirror.ime/.BridgeIme'
APK = ROOT / 'android-ime' / 'app' / 'build' / 'outputs' / 'apk' / 'debug' / 'app-debug.apk'
class TextBridge(QObject):
    completed = Signal(bool, str)
    def __init__(self): super().__init__(); self.process=None; self.output=''
    def send(self, serial, text):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.completed.emit(False, '上一条文字仍在提交，请稍候。'); return
        data=text.encode('utf-8')
        if not data: self.completed.emit(False, '请输入文字。'); return
        if len(data)>6000: self.completed.emit(False, '文字过长，请分段发送（每次最多 6000 UTF-8 字节）。'); return
        payload=base64.b64encode(data).decode('ascii'); self.output=''; p=QProcess(self); self.process=p
        p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        p.readyReadStandardOutput.connect(lambda: self.read(p))
        p.errorOccurred.connect(lambda _: self.completed.emit(False, '无法启动 ADB：'+p.errorString()))
        def done(code, status):
            self.read(p)
            if code==0 and re.search(r'Broadcast completed: result=1(?:,|\s|$)', self.output): self.completed.emit(True,'文字已由手机输入法提交；请检查目标输入框。')
            elif 'result=3' in self.output: self.completed.emit(False,'手机上没有活动的输入框，请先点击目标聊天输入框。')
            else: self.completed.emit(False,'提交失败：请确认已安装并启用 ChatMirror 输入法。'+self.output.strip()[:350])
        p.finished.connect(done)
        p.start(ADB,['-s',serial,'shell','am','broadcast','--receiver-foreground','-a','com.chatmirror.ime.COMMIT_TEXT','-p','com.chatmirror.ime','--es','text64',payload])
    def read(self,p): self.output+=bytes(p.readAllStandardOutput()).decode('utf-8','replace')
