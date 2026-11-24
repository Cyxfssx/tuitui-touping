import os, re, logging
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QListWidget,QStackedWidget,QLineEdit,QTextEdit,QFileDialog,QMessageBox,QComboBox,QSpinBox,QCheckBox,QFormLayout,QSplitter,QInputDialog,QProgressBar)
from . import adb, apps, clipboard
from .config import Config, DATA
from .mirror import MirrorManager
from .transfer import Transfers
from .window import window_geometry
from .text_bridge import TextBridge, APK
from .image_bridge import ImageJob, IME
from .hotkeys import ImagePasteHook
from .config import ROOT

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.cfg=Config(); self.mirror=MirrorManager(); self.transfer=Transfers(); self.bridge=TextBridge(); self.bridge.completed.connect(self.text_result); self.image_job=None; self.queue=[]; self.last_remote=''; self.serial=''; self.rows=[]
        self.setWindowTitle('推推投屏 Qt · 测试版'); self.resize(1300,800); self.setAcceptDrops(True)
        self.mirror.changed.connect(self.notice); self.paste_hook=ImagePasteHook(self.mirror.processes,self); self.paste_hook.paste_requested.connect(self.window_paste_image); self.paste_hook.start(); self.transfer.status.connect(self.notice); self.transfer.finished.connect(self.transfer_done)
        root=QWidget(); self.setCentralWidget(root); outer=QVBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        bar=QLabel('  ◈  推推投屏 Qt     /     安卓设备工作台'); bar.setObjectName('header'); outer.addWidget(bar)
        body=QHBoxLayout(); body.setContentsMargins(16,16,16,12); body.setSpacing(14); outer.addLayout(body,1)
        nav=QWidget(); nav.setFixedWidth(165); nv=QVBoxLayout(nav); nv.setContentsMargins(0,0,0,0); nv.addWidget(QLabel('工作空间'))
        self.nav=QListWidget(); self.nav.addItems(['设备管理','聊天应用','文字输入','图片传输','文件管理','投屏设置','软件设置']); nv.addWidget(self.nav); body.addWidget(nav)
        center=QWidget(); cv=QVBoxLayout(center); cv.setContentsMargins(0,0,0,0); title=QLabel('设备'); title.setObjectName('title'); cv.addWidget(title)
        self.device_list=QListWidget(); self.device_list.setMinimumWidth(230); self.device_list.currentRowChanged.connect(self.select_device); cv.addWidget(self.device_list,1)
        self.device_info=QLabel('正在检测 USB 设备…'); self.device_info.setWordWrap(True); cv.addWidget(self.device_info)
        row=QHBoxLayout(); row.addWidget(self.btn('刷新',self.refresh)); row.addWidget(self.btn('修改备注',self.rename)); cv.addLayout(row); body.addWidget(center,2)
        right=QWidget(); right.setObjectName('panel'); rv=QVBoxLayout(right); rv.setContentsMargins(22,20,22,20)
        self.pages=QStackedWidget(); rv.addWidget(self.pages); body.addWidget(right,4)
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.build_device(); self.build_apps(); self.build_text(); self.build_image(); self.build_files(); self.build_settings(); self.build_software(); self.nav.setCurrentRow(0)
        self.status=QLabel('就绪'); self.status.setObjectName('status'); outer.addWidget(self.status)
        self.shortcut=QShortcut(QKeySequence('Ctrl+Shift+V'), self); self.shortcut.activated.connect(self.commit_clipboard_image)
        self.timer=QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(5000)
        self.apply_theme(); self.refresh()
    def page(self,title,desc):
        w=QWidget(); v=QVBoxLayout(w); v.setContentsMargins(0,0,0,0); t=QLabel(title); t.setObjectName('title'); v.addWidget(t); d=QLabel(desc); d.setWordWrap(True); d.setObjectName('muted'); v.addWidget(d); v.addSpacing(12); self.pages.addWidget(w); return v
    def btn(self,text,action):
        b=QPushButton(text); b.clicked.connect(action); return b
    def build_device(self):
        v=self.page('设备管理','通过 USB 连接并在手机上允许 USB 调试。每台设备使用独立投屏窗口。')
        v.addWidget(self.btn('启动当前设备投屏',self.start_mirror)); v.addWidget(self.btn('关闭当前设备投屏',self.stop_mirror)); v.addWidget(self.btn('启动全部已连接设备',self.start_all)); v.addWidget(self.btn('关闭全部投屏',self.stop_all)); v.addWidget(self.btn('打开手机物理键盘设置',self.keyboard_settings)); v.addStretch()
    def build_apps(self):
        v=self.page('聊天应用','输入已安装应用的 Android 包名，通过系统启动入口打开。')
        self.package=QLineEdit(); self.package.setPlaceholderText('例如 com.tencent.mm'); self.package.setText(self.cfg.get('package','com.tencent.mm')); v.addWidget(self.package); v.addWidget(self.btn('启动应用',self.launch_app)); v.addStretch()
    def build_text(self):
        v=self.page('文字输入','在手机选择推推2输入法并点击聊天输入框。在投屏窗口使用 Windows 输入法，选词上屏后由投屏引擎通过手机剪贴板写入。使用 SDK 键盘模式。')
        row=QHBoxLayout(); row.addWidget(self.btn('安装推推2输入法',self.install_ime)); row.addWidget(self.btn('打开手机输入法设置',self.ime_settings)); v.addLayout(row)
        self.text=QTextEdit(); self.text.setPlaceholderText('在此使用电脑输入法输入文字…'); v.addWidget(self.text,1)
        v.addWidget(self.btn('复制文字到电脑剪贴板',lambda: (clipboard.copy_text(self.text.toPlainText()),self.notice('文字已复制；请切回投屏窗口粘贴'))))
        lab=QLabel('Windows 输入法直接上屏需要 SDK 键盘模式。输入时手机剪贴板会被更新；目标应用或手机限制可能影响粘贴。'); lab.setWordWrap(True); lab.setObjectName('muted'); v.addWidget(lab)
    def install_ime(self):
        if not self.require(): return
        apk=ROOT/'assets'/'tuitui2.apk'
        if not apk.exists(): QMessageBox.warning(self,'安装失败','找不到推推2安装包。'); return
        try: self.result(adb.run('-s',self.serial,'install','-r',str(apk),timeout=120))
        except Exception as e: QMessageBox.warning(self,'安装失败',str(e))
    def ime_settings(self):
        if self.require(): self.result(adb.shell(self.serial,'am','start','-a','android.settings.INPUT_METHOD_SETTINGS'))
    def text_result(self,ok,message):
        self.notice(message)
        if not ok: QMessageBox.warning(self,'文字提交失败',message)
    def build_image(self):
        v=self.page('图片传输','先在手机选择推推2输入法并点击聊天输入框。桥接会尝试把图片交给聊天应用，不会自动发送。')
        v.addWidget(self.btn('将剪贴板图片交给当前聊天',self.commit_clipboard_image))
        v.addWidget(self.btn('选择图片交给当前聊天',self.commit_image_file))
        v.addWidget(self.btn('上传图片到手机文件夹',self.choose_images))
        note=QLabel('在本程序启动的投屏窗口按 Ctrl+V 可以提交剪贴板图片；文字 Ctrl+V 保持正常操作。聊天应用需要支持图片输入。');note.setWordWrap(True);note.setObjectName('muted');v.addWidget(note);v.addStretch()
    def window_paste_image(self,serial):
        try: self.start_image_job(clipboard.clipboard_image(),serial)
        except Exception as e: QMessageBox.warning(self,'图片不可用',str(e))
    def commit_clipboard_image(self):
        if not self.require(): return
        try: self.start_image_job(clipboard.clipboard_image())
        except Exception as e: QMessageBox.warning(self,'图片不可用',str(e))
    def commit_image_file(self):
        if not self.require(): return
        filename,_=QFileDialog.getOpenFileName(self,'选择图片',filter='图片 (*.png *.jpg *.jpeg *.webp *.bmp *.gif)')
        if filename: self.start_image_job(filename)
    def start_image_job(self,path,serial=None):
        if self.image_job and self.image_job.isRunning(): QMessageBox.information(self,'请稍候','图片正在处理。');return
        self.image_job=ImageJob(serial or self.serial,path,self)
        self.image_job.result.connect(self.image_result); self.image_job.start();self.notice('正在提交图片…')
    def image_result(self,ok,message):
        self.notice(message)
        if ok: QMessageBox.information(self,'图片已提交',message)
        else: QMessageBox.warning(self,'图片提交失败',message)
    def build_files(self):
        v=self.page('文件管理','拖拽本地文件到窗口，或选择多个文件。手机路径为允许 ADB 访问的共享存储路径。')
        self.remote=QLineEdit(self.cfg.get('remote','/sdcard/Download/ChatMirror')); v.addWidget(QLabel('手机目标目录')); v.addWidget(self.remote)
        v.addWidget(self.btn('选择文件并上传',self.choose_files)); self.remote_list=QListWidget(); v.addWidget(QLabel('浏览手机目录')); v.addWidget(self.remote_list,1)
        row=QHBoxLayout(); row.addWidget(self.btn('浏览当前目录',self.browse)); row.addWidget(self.btn('进入所选目录',self.enter_dir)); row.addWidget(self.btn('上一级',self.up_dir)); v.addLayout(row)
        row=QHBoxLayout(); row.addWidget(self.btn('下载所选文件',self.download)); row.addWidget(self.btn('取消传输',self.transfer.cancel)); row.addWidget(self.btn('打开电脑保存目录',self.open_downloads)); v.addLayout(row)
    def build_settings(self):
        v=self.page('投屏设置','更改在下次启动投屏时生效。默认参数兼顾清晰度、流畅度与延迟。'); form=QFormLayout(); v.addLayout(form); self.fields={}
        for key,label,default,lo,hi in [('size','最大分辨率',1280,320,8192),('bitrate','视频码率（Mbps）',8,1,100),('fps','最大帧率',30,1,120),('width','窗口宽度',420,100,4000),('height','窗口高度',800,100,4000)]:
            x=QSpinBox(); x.setRange(lo,hi); x.setValue(self.cfg.get('settings',{}).get(key,default)); x.valueChanged.connect(self.save_settings); form.addRow(label,x); self.fields[key]=x
        for key,label,values in [('codec','视频编码',['h264','h265']),('keyboard','键盘输入模式',['sdk','uhid'])]:
            x=QComboBox(); x.addItems(values); x.setCurrentText(self.cfg.get('settings',{}).get(key,values[0])); x.currentTextChanged.connect(self.save_settings); form.addRow(label,x); self.fields[key]=x
        for key,label,default in [('audio','传输音频',True),('clipboard','同步文字剪贴板',True),('screenoff','关闭手机屏幕',False),('awake','保持手机唤醒',False),('top','窗口置顶',False)]:
            x=QCheckBox(label); x.setChecked(self.cfg.get('settings',{}).get(key,default)); x.toggled.connect(self.save_settings); form.addRow(x); self.fields[key]=x
        v.addStretch()
    def build_software(self):
        v=self.page('软件设置','设置保存在当前 Windows 用户配置目录。')
        self.theme=QComboBox(); self.theme.addItems(['深色','浅色']); self.theme.setCurrentText(self.cfg.get('theme','深色')); self.theme.currentTextChanged.connect(self.change_theme); v.addWidget(QLabel('外观')); v.addWidget(self.theme); v.addWidget(self.btn('打开配置和日志目录',lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(DATA))))); v.addStretch()
    def settings(self):
        s=self.cfg.get('settings',{}).copy()
        for k,x in self.fields.items(): s[k]=x.value() if isinstance(x,QSpinBox) else x.currentText() if isinstance(x,QComboBox) else x.isChecked()
        return s
    def save_settings(self,*_): self.cfg.set('settings',self.settings())
    def change_theme(self,t): self.cfg.set('theme',t); self.apply_theme()
    def apply_theme(self):
        dark=self.cfg.get('theme','深色')=='深色'; bg='#171a20' if dark else '#f1f3f7'; panel='#222731' if dark else '#ffffff'; fg='#e8edf5' if dark else '#202936'; muted='#a0adbd' if dark else '#64748b'; field='#2c3340' if dark else '#e8edf4'; border='#3c4655' if dark else '#d2dbe6'
        self.setStyleSheet(f'''QWidget{{background:{bg};color:{fg};font-family:"Microsoft YaHei UI";font-size:13px}} #header{{background:{panel};padding:18px;font-size:16px;font-weight:600}} #panel{{background:{panel};border:1px solid {border};border-radius:14px}} #panel QWidget{{background:transparent}} #title{{font-size:23px;font-weight:700}} #muted{{color:{muted};line-height:1.4}} #status{{background:{panel};padding:10px;color:{muted}}} QPushButton{{background:{field};border:1px solid {border};border-radius:8px;padding:10px;text-align:left}} QPushButton:hover{{background:#386bd2;color:white}} QListWidget,QLineEdit,QTextEdit,QSpinBox,QComboBox{{background:{field};border:1px solid {border};border-radius:8px;padding:8px;selection-background-color:#386bd2}} QListWidget::item{{padding:10px;border-radius:6px}} QListWidget::item:selected{{background:#386bd2;color:white}} QCheckBox{{padding:5px}}''')
    def notice(self,msg): self.status.setText(str(msg).replace('\n',' ')[:350]); logging.info('%s',msg)
    def require(self):
        if not self.serial or not any(s==self.serial and state=='device' for s,state,_ in self.rows): QMessageBox.warning(self,'设备不可用','请选择已授权的 USB 设备。'); return False
        return True
    def refresh(self):
        try: rows=adb.devices()
        except Exception as e: self.notice('ADB 检测失败：'+str(e)); return
        if rows==self.rows: return
        self.rows=rows; current=self.serial; self.device_list.blockSignals(True); self.device_list.clear(); notes=self.cfg.get('notes',{})
        for s,state,model in rows: self.device_list.addItem(f'{notes.get(s,model)}\n{model} · {s}\n'+('已连接' if state=='device' else '未授权 / '+state))
        idx=next((i for i,r in enumerate(rows) if r[0]==current),0 if rows else -1); self.device_list.setCurrentRow(idx); self.device_list.blockSignals(False); self.select_device(idx)
        if not rows: self.device_info.setText('未检测到 USB 设备。请连接手机并开启 USB 调试。')
    def select_device(self,i):
        self.serial=self.rows[i][0] if 0<=i<len(self.rows) else ''; self.device_info.setText(('当前设备：'+self.serial) if self.serial else '未选择设备')
    def rename(self):
        if not self.serial: return
        val,ok=QInputDialog.getText(self,'设备备注','请输入备注名称：',text=self.cfg.get('notes',{}).get(self.serial,''))
        if ok: notes=self.cfg.get('notes',{}); notes[self.serial]=val.strip(); self.cfg.set('notes',notes); self.rows=[]; self.refresh()
    def start_mirror(self):
        if self.require(): self.mirror.start(self.serial,self.settings()); self.notice('正在启动投屏：'+self.serial)
    def start_all(self):
        for serial,state,_ in self.rows:
            if state=='device': self.mirror.start(serial,self.settings())
        self.notice('正在启动已连接设备的投屏')
    def stop_all(self):
        for serial in list(self.mirror.processes): self.remember(serial); self.mirror.stop(serial)
        self.notice('已关闭本程序启动的投屏')
    def remember(self,serial):
        g=window_geometry(serial)
        if g:
            s=self.settings(); geo=s.get('geometry',{}); geo[serial]=g; s['geometry']=geo; self.cfg.set('settings',s)
    def stop_mirror(self):
        if self.serial: self.remember(self.serial); self.mirror.stop(self.serial)
    def keyboard_settings(self):
        if self.require(): self.result(adb.shell(self.serial,'am','start','-a','android.settings.HARD_KEYBOARD_SETTINGS'))
    def result(self,r):
        msg=(r.stdout+' '+r.stderr).strip(); self.notice(msg or ('操作完成' if r.returncode==0 else '操作失败'))
        if r.returncode or 'Error:' in msg or 'Exception' in msg: QMessageBox.warning(self,'操作失败',msg or '未知错误')
    def launch_app(self):
        if self.require():
            p=self.package.text().strip()
            if not re.fullmatch(r'[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)+',p): QMessageBox.warning(self,'包名无效','请输入有效的 Android 包名。'); return
            self.cfg.set('package',p); self.result(apps.open_app(self.serial,p))
    def choose_files(self):
        files,_=QFileDialog.getOpenFileNames(self,'选择文件'); self.enqueue(files)
    def choose_images(self):
        files,_=QFileDialog.getOpenFileNames(self,'选择图片',filter='图片 (*.png *.jpg *.jpeg *.webp *.bmp)'); self.enqueue(files,True)
    def paste_image(self):
        try: self.enqueue([clipboard.clipboard_image()],True)
        except Exception as e: QMessageBox.warning(self,'图片不可用',str(e))
    def enqueue(self,files,image=False):
        if not files or not self.require(): return
        dest=self.remote.text().strip().rstrip('/')
        if not dest.startswith('/sdcard/'): QMessageBox.warning(self,'路径无效','请输入 /sdcard/ 下的共享存储目录。'); return
        r=adb.shell(self.serial,'mkdir -p '+apps.quote(dest))
        if r.returncode: self.result(r); return
        self.cfg.set('remote',dest); self.queue.extend([(self.serial,'push',str(f),dest+'/'+Path(f).name,image) for f in files]); self.next_transfer()
    def next_transfer(self):
        if self.transfer.p and self.transfer.p.state()!=self.transfer.p.ProcessState.NotRunning: return
        if self.queue:
            self.current=self.queue.pop(0); self.transfer.start(*self.current[:4])
    def transfer_done(self,ok,output):
        serial,direction,source,dest,image=self.current
        if ok:
            self.notice('传输成功：'+dest)
            if direction=='push':
                apps.media_scan(serial,dest)
                if image: self.last_remote=dest
        else:
            self.queue.clear(); self.notice('传输失败或已取消：'+output); QMessageBox.warning(self,'传输未完成',output or '传输被取消或 ADB 返回错误。')
        QTimer.singleShot(0,self.next_transfer)
    def image_action(self,share):
        if self.require() and self.last_remote:
            r=apps.share_image(self.serial,self.last_remote) if share else apps.open_image(self.serial,self.last_remote); self.result(r)
        elif not self.last_remote: QMessageBox.information(self,'尚无图片','请先成功传输图片。')
    def browse(self):
        if not self.require(): return
        path=self.remote.text().strip().rstrip('/')
        if path!='/sdcard' and not path.startswith('/sdcard/'): QMessageBox.warning(self,'路径无效','仅浏览 /sdcard 共享存储。'); return
        r=adb.shell(self.serial,'ls -1Ap '+apps.quote(path)); self.remote_list.clear()
        if r.returncode: self.result(r); return
        self.remote_list.addItems(r.stdout.splitlines())
    def enter_dir(self):
        item=self.remote_list.currentItem()
        if item and item.text().endswith('/'):
            self.remote.setText(self.remote.text().rstrip('/')+'/'+item.text().rstrip('/')); self.browse()
    def up_dir(self):
        p=self.remote.text().rstrip('/'); self.remote.setText(p.rsplit('/',1)[0] if p!='/sdcard' and p.startswith('/sdcard/') else '/sdcard'); self.browse()
    def download(self):
        item=self.remote_list.currentItem()
        if not item or not self.require(): return
        if item.text().endswith('/'): QMessageBox.information(self,'选择文件','请选择文件。'); return
        folder=QFileDialog.getExistingDirectory(self,'选择电脑保存目录',self.cfg.get('downloads',str(Path.home()/'Downloads')))
        if folder:
            self.cfg.set('downloads',folder); self.queue.append((self.serial,'pull',self.remote.text().rstrip('/')+'/'+item.text(),str(Path(folder)/item.text()),False)); self.next_transfer()
    def open_downloads(self): QDesktopServices.openUrl(QUrl.fromLocalFile(self.cfg.get('downloads',str(Path.home()/'Downloads'))))
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self,e): self.enqueue([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile() and Path(u.toLocalFile()).is_file()])
    def closeEvent(self,e):
        if self.image_job and self.image_job.isRunning():
            QMessageBox.information(self,'请稍候','图片传输完成后再关闭程序。'); e.ignore(); return
        self.paste_hook.stop(); self.queue.clear(); self.transfer.cancel()
        for serial in list(self.mirror.processes): self.remember(serial); self.mirror.stop(serial)
        e.accept()


