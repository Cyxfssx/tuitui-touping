from PySide6.QtCore import QObject, QProcess, Signal
from .config import SCRCPY, ENGINE
class MirrorManager(QObject):
    changed = Signal(str)
    def __init__(self): super().__init__(); self.processes = {}
    def start(self, serial, settings):
        if serial in self.processes: return
        args = ['-s',serial, '--window-title=ChatMirror - '+serial, '--max-size='+str(settings.get('size',1280)), '--video-bit-rate='+str(settings.get('bitrate',8))+'M', '--max-fps='+str(settings.get('fps',30)), '--video-codec='+settings.get('codec','h264'), '--keyboard='+settings.get('keyboard','sdk'), '--window-width='+str(settings.get('width',420)), '--window-height='+str(settings.get('height',800))]
        for key,flag in [('audio','--no-audio'),('clipboard','--no-clipboard-autosync')]:
            if not settings.get(key, True): args.append(flag)
        for key,flag in [('screenoff','--turn-screen-off'),('awake','--stay-awake'),('top','--always-on-top')]:
            if settings.get(key,False): args.append(flag)
        geo=settings.get('geometry',{}).get(serial)
        if geo: args += ['--window-x='+str(geo[0]), '--window-y='+str(geo[1]), '--window-width='+str(geo[2]), '--window-height='+str(geo[3])]
        p=QProcess(self); p.setWorkingDirectory(str(ENGINE)); p.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        p.readyReadStandardOutput.connect(lambda: self.changed.emit(bytes(p.readAllStandardOutput()).decode('utf-8','replace')))
        p.errorOccurred.connect(lambda e: self.changed.emit('投屏进程错误：'+p.errorString()))
        p.finished.connect(lambda *_: (self.processes.pop(serial,None), self.changed.emit(serial+' 投屏已结束')))
        self.processes[serial]=p; p.start(SCRCPY,args)
    def stop(self,serial):
        p=self.processes.get(serial)
        if p: p.terminate(); p.waitForFinished(1500); p.kill() if p.state()!=QProcess.ProcessState.NotRunning else None
