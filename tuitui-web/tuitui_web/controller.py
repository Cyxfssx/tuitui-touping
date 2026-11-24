"""Controller exposed to the local WebView interface."""
import ctypes, logging, os, threading, time
from ctypes import wintypes
from pathlib import Path
import webview
from webview.dom import DOMEventHandler
from tuitui_personal.backend import Backend,Config,DATA,ROOT,run
from tuitui_personal.hotkeys import Hook,capture
from tuitui_personal.windows import bounds,show,set_title

user32=ctypes.WinDLL('user32',use_last_error=True);kernel32=ctypes.WinDLL('kernel32',use_last_error=True)
kernel32.GetCurrentThreadId.restype=wintypes.DWORD
user32.GetMessageW.argtypes=[ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT];user32.GetMessageW.restype=ctypes.c_int
user32.PostThreadMessageW.argtypes=[wintypes.DWORD,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM];user32.PostThreadMessageW.restype=wintypes.BOOL
user32.TranslateMessage.argtypes=[ctypes.POINTER(wintypes.MSG)];user32.DispatchMessageW.argtypes=[ctypes.POINTER(wintypes.MSG)]

class Controller:
    def __init__(self):
        self._backend=Backend();self._config=Config();self._lock=threading.RLock();self._window=None;self._devices=[];self._selected='';self._status='正在检测 USB 设备…';self._want={};self._manual=set();self._stop_requested=set();self._retry={};self._count={};self._closing=False;self._hook_thread_id=0
        self._last_poll=0;self._polling=False;self._last_window_save=0
        logdir=DATA/'logs';logdir.mkdir(exist_ok=True);self._logger=logging.getLogger('tuitui.web');self._logger.setLevel(logging.INFO)
        if not self._logger.handlers:
            handler=logging.FileHandler(logdir/'webview.log',encoding='utf-8');handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'));self._logger.addHandler(handler)
    def _start(self,window):
        self._window=window
        threading.Thread(target=self._hook_loop,name='image-keyboard-hook',daemon=True).start()
        threading.Thread(target=self._event_loop,name='desktop-controller',daemon=True).start()
    def _hook_loop(self):
        hook=Hook(None,self._backend,lambda:bool(self._config.value.get('images',True)),lambda _:None)
        try:
            hook.start();self._hook_thread_id=kernel32.GetCurrentThreadId();msg=wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg),None,0,0)>0:
                user32.TranslateMessage(ctypes.byref(msg));user32.DispatchMessageW(ctypes.byref(msg))
        except Exception as e:self._status='图片快捷键不可用：'+str(e)
        finally:hook.stop()
    def _attach_drop(self):
        try:
            drop=self._window.dom.get_element('#dropzone')
            drop.events.dragover += DOMEventHandler(lambda e:None,prevent_default=True)
            drop.events.drop += DOMEventHandler(self._dropped,prevent_default=True)
        except Exception as e:self._status='拖放初始化失败：'+str(e)
    def _dropped(self,event):
        paths=[f.get('pywebviewFullPath') for f in event.get('dataTransfer',{}).get('files',[]) if f.get('pywebviewFullPath')]
        if not paths:self._status='无法读取拖放文件，请使用选择文件。';return
        self._add_files(paths)
    def _event_loop(self):
        while not self._closing:
            now=time.monotonic()
            if now-self._last_poll>=4 and not self._polling:self._polling=True;self._last_poll=now;self._backend.refresh()
            if now-self._last_window_save>=1.5:self._last_window_save=now;self._save_positions()
            try:name,args=self._backend.events.get(timeout=.2);self._event(name,args)
            except __import__('queue').Empty:pass
            except Exception as e:self._status='后台状态更新失败：'+str(e)
            self._retry_due()
    def _event(self,name,args):
        if name in ('error','device_error','hotkey_error','image'):
            self._logger.info('%s: %s',name,args[-1] if args else '')
        elif name=='mirror_log' and ('ERROR' in args[1] or 'WARN' in args[1]):self._logger.warning('%s',args[1])
        with self._lock:
            if name=='devices':
                self._polling=False;self._devices=args[0]
                if self._devices and (self._status.startswith('正在检测') or self._status.startswith('未检测到')):self._status='USB 设备已连接。'
                if not any(row[0]==self._selected for row in self._devices):self._selected=self._devices[0][0] if self._devices else ''
                if not self._devices:self._status='未检测到 USB 设备，请连接并授权调试。'
            elif name=='device_error':self._polling=False;self._status='ADB 检测失败：'+args[0]
            elif name=='mirror_started':self._status='投屏正在启动…'
            elif name=='mirror_log':
                if 'Texture' in args[1]:self._count[args[0]]=0;self._status='投屏已连接。'
                if 'ERROR' in args[1] or 'WARN' in args[1]:self._status=args[1][:250]
            elif name=='mirror_stopped':
                serial,code=args
                if serial in self._stop_requested:self._stop_requested.discard(serial);self._status='投屏已停止。'
                elif serial in self._manual:self._manual.discard(serial);self._schedule(serial,0,True)
                elif self._want.get(serial):
                    if code==0:
                        if not self._polling:self._polling=True;self._backend.refresh()
                        self._retry[serial]=(time.monotonic()+2,'check')
                    else:self._schedule(serial,None,False)
                else:self._status='投屏已结束。'
            elif name=='task_state':self._status=args[1]
            elif name=='hotkey_image':
                try:
                    image=capture()
                    if image:self._backend.submit_image(args[0],*image);self._status='正在提交剪贴板图片…'
                    else:self._status='剪贴板图片已变化，请重试。'
                except Exception as e:self._status='读取剪贴板失败：'+str(e)
            elif name=='hotkey_error':self._status='图片快捷键错误：'+args[0]
            elif name=='image':self._status=args[1]
            elif name=='error':self._status=args[0]
    def _save_positions(self):
        with self._lock:
            if not self._config.value.get('remember_window',True):return
            changed=False
            for serial,p in list(self._backend.processes.items()):
                if p.poll() is not None:continue
                geo=bounds(p.pid)
                if geo and self._config.value.setdefault('geometry',{}).get(serial)!=geo:self._config.value['geometry'][serial]=geo;changed=True
            if changed:
                try:self._config.save()
                except OSError as e:self._status='窗口位置保存失败：'+str(e)
    def _schedule(self,serial,delay=None,manual=False):
        if not self._want.get(serial):return
        if not manual and not self._config.value.get('auto_reconnect',True):return
        count=self._count.get(serial,0);self._retry[serial]=(time.monotonic()+(delay if delay is not None else min(30,2*(2**min(count,4)))), 'manual' if manual else 'auto');self._status='等待 USB 设备重新连接…'
    def _retry_due(self):
        with self._lock:
            now=time.monotonic()
            for serial,(deadline,mode) in list(self._retry.items()):
                if now<deadline:continue
                self._retry.pop(serial,None)
                if not self._want.get(serial):continue
                p=self._backend.processes.get(serial)
                if p and p.poll() is None:continue
                connected=any(row[0]==serial and row[1]=='device' for row in self._devices)
                if mode=='check':
                    if connected:self._want.pop(serial,None);self._status='投屏已结束。'
                    else:self._schedule(serial,0,False)
                elif not connected:self._schedule(serial,4,mode=='manual')
                elif mode=='manual' or self._config.value.get('auto_reconnect',True):
                    self._count[serial]=self._count.get(serial,0)+1;self._status='正在重新连接…';self._backend.start(serial,self._mirror_settings(serial))
    def _mirror_settings(self,serial):
        settings=self._config.value.copy();notes=dict(settings.get('notes',{}))
        if not notes.get(serial):
            row=next(((i,r) for i,r in enumerate(self._devices) if r[0]==serial),None)
            notes[serial]=(f'手机 {row[0]+1:02d} · {row[1][2]}' if row else '手机')
        settings['notes']=notes
        return settings
    def _require(self):
        if not any(row[0]==self._selected and row[1]=='device' for row in self._devices):raise ValueError('请先选择已授权的 USB 设备。')
        return self._selected
    def state(self):
        with self._lock:
            notes=self._config.value.get('notes',{});devices=[]
            for i,(serial,state,model) in enumerate(self._devices):
                p=self._backend.processes.get(serial);devices.append({'id':serial,'name':notes.get(serial) or f'手机 {i+1:02d} · {model}','model':model,'state':state,'running':bool(p and p.poll() is None)})
            tasks=[]
            for t in list(self._backend.transfers.tasks.values()):tasks.append({'id':t.id,'name':t.source.name,'state':t.state,'done':t.committed,'total':t.total})
            return {'devices':devices,'selected':self._selected,'settings':{k:v for k,v in self._config.value.items() if k not in ('notes','geometry')},'tasks':tasks,'status':self._status}
    def refresh(self):
        if not self._polling:self._polling=True;self._backend.refresh()
        return True
    def select_device(self,serial):
        with self._lock:
            if not any(row[0]==serial for row in self._devices):raise ValueError('设备已断开。')
            self._selected=serial
        return True
    def rename(self,name):
        name=str(name).strip()
        if not name or len(name)>64 or any(ord(c)<32 for c in name):raise ValueError('请输入 1 至 64 个字符的设备名称。')
        with self._lock:
            serial=self._require();self._config.value.setdefault('notes',{})[serial]=name;self._config.save();p=self._backend.processes.get(serial)
            if p and p.poll() is None and not set_title(p.pid,name):self._status='名称已保存，投屏窗口下次启动时生效。'
            else:self._status='设备名称已更新。'
        return True
    def toggle_mirror(self):
        with self._lock:
            serial=self._selected
            if not serial:raise ValueError('请先选择设备。')
            p=self._backend.processes.get(serial)
            if p and p.poll() is None:
                self._want.pop(serial,None);self._retry.pop(serial,None);self._stop_requested.add(serial);self._save_positions();self._backend.stop(serial)
            else:
                self._require();self._want[serial]=True;self._count[serial]=0;self._stop_requested.discard(serial);self._backend.start(serial,self._mirror_settings(serial))
        return True
    def toggle_device(self,serial):
        with self._lock:
            p=self._backend.processes.get(serial);running=bool(p and p.poll() is None)
            if not any(row[0]==serial and row[1]=='device' for row in self._devices) and not running:raise ValueError('设备已断开或未授权。')
            self._selected=serial
            return self.toggle_mirror()
    def reconnect(self):
        with self._lock:
            serial=self._require();self._want[serial]=True;self._count[serial]=0;p=self._backend.processes.get(serial)
            if p and p.poll() is None:self._manual.add(serial);self._save_positions();self._backend.stop(serial)
            else:self._schedule(serial,0,True)
        return True
    def show_mirror(self):
        with self._lock:
            serial=self._require();p=self._backend.processes.get(serial)
            if not p or p.poll() is not None or not show(p.pid):raise ValueError('当前设备尚未启动投屏，或窗口无法置前。')
        return True
    def settings(self,values):
        allowed={'size','fps','bitrate','audio','top','text','clipboard','images','directory','stay_awake','screen_off','remember_window','auto_reconnect','simple_mode'}
        if not isinstance(values,dict) or any(k not in allowed for k in values):raise ValueError('设置不合法。')
        validated={}
        for k,v in values.items():
            if k in ('size','fps','bitrate'):
                if isinstance(v,bool):raise ValueError('数值不合法。')
                v=int(v);limits={'size':(320,8192),'fps':(1,120),'bitrate':(1,100)};lo,hi=limits[k]
                if not lo<=v<=hi:raise ValueError('数值超出范围。')
            elif k=='directory':
                v=str(v).strip()
                if (v!='/sdcard' and not v.startswith('/sdcard/')) or any(part in ('.','..') for part in v.split('/')) or '\x00' in v:raise ValueError('手机保存目录必须位于 /sdcard 下。')
            elif not isinstance(v,bool):raise ValueError('开关值不合法。')
            validated[k]=v
        with self._lock:
            self._config.value.update(validated);self._config.save()
            if validated.get('auto_reconnect') is False:self._retry={}
            self._status='设置已保存；画面设置将在下次启动投屏时生效。'
        return True
    def set_mode(self,simple):
        if not isinstance(simple,bool):raise ValueError('模式不合法。')
        self.settings({'simple_mode':simple})
        if self._window:self._window.resize(620 if simple else 1180,720 if simple else 850)
        return True
    def choose_files(self):
        paths=self._window.create_file_dialog(webview.FileDialog.OPEN,allow_multiple=True)
        if paths:self._add_files(paths)
        return True
    def _add_files(self,paths):
        try:
            with self._lock:
                serial=self._require();files=[str(Path(p)) for p in paths if p and Path(p).is_file()]
                if not files:raise ValueError('请选择普通文件，不支持文件夹。')
                tasks=self._backend.file_batch(serial,files,self._config.value.get('directory','/sdcard/Download/推推投屏'))
                self._status=f'已添加 {len(tasks)} 个文件。' if len(tasks)==len(files) else f'队列已满，仅添加 {len(tasks)} 个文件。'
        except Exception as e:self._status='添加文件失败：'+str(e)
    def task_action(self,action,task_id):
        if action not in ('pause','resume','cancel'):raise ValueError('无效操作。')
        with self._lock:getattr(self._backend.transfers,action)(str(task_id))
        return True
    def clear_tasks(self):
        with self._lock:self._backend.transfers.clear_finished()
        return True
    def install_ime(self):
        with self._lock:serial=self._require()
        apk=ROOT/'assets'/'tuitui2.apk'
        if not apk.is_file():raise ValueError('找不到推推2输入法安装包。')
        self._status='正在安装推推2输入法…'
        run('-s',serial,'install','-r',str(apk),timeout=120)
        self._status='推推2已安装，请在手机输入法设置中启用并选择。'
        return True
    def ime_settings(self):
        with self._lock:serial=self._require()
        run('-s',serial,'shell','am','start','-a','android.settings.INPUT_METHOD_SETTINGS')
        self._status='已打开手机输入法设置。'
        return True
    def open_logs(self):
        path=DATA/'logs';path.mkdir(exist_ok=True);os.startfile(str(path));return True
    def _close(self):
        if self._closing:return
        self._closing=True;self._save_positions();self._backend.close()
        if self._hook_thread_id:user32.PostThreadMessageW(self._hook_thread_id,0x0012,0,0)

