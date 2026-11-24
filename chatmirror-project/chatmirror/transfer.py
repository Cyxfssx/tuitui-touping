from PySide6.QtCore import QObject, QProcess, Signal
from .config import ADB
class Transfers(QObject):
    status=Signal(str)
    finished=Signal(bool,str)
    def __init__(self): super().__init__(); self.p=None; self.buffer=''
    def start(self, serial, direction, source, destination):
        if self.p and self.p.state()!=QProcess.ProcessState.NotRunning: self.status.emit('已有传输正在进行'); return False
        self.buffer=''; self.p=QProcess(self); self.p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.p.readyReadStandardOutput.connect(self.read)
        self.p.errorOccurred.connect(lambda _: self.status.emit('传输错误：'+self.p.errorString()))
        self.p.finished.connect(lambda code, status: self.finished.emit(code==0 and status==QProcess.ExitStatus.NormalExit, self.buffer[-2000:]))
        self.p.start(ADB,['-s',serial,direction,source,destination]); self.status.emit('传输中：'+source); return True
    def read(self):
        s=bytes(self.p.readAllStandardOutput()).decode('utf-8','replace'); self.buffer+=s; self.status.emit(s.strip()[-250:] or '传输中')
    def cancel(self):
        if self.p and self.p.state()!=QProcess.ProcessState.NotRunning: self.p.kill(); self.status.emit('传输已取消')
