"""Small USB-only backend for the personal desktop interface."""
import json, os, queue, re, secrets, subprocess, sys, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from .transfers import TransferQueue

ROOT=Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent
ENGINE=ROOT/'tuitui-engine'
ADB=ENGINE/'adb.exe'
SCRCPY=ENGINE/'scrcpy.exe'
SCANNER=ROOT/'assets'/'tuitui2-scanner.jar'
DATA=Path(os.getenv('APPDATA',str(ROOT)))/'TuiTuiPersonal'
DATA.mkdir(parents=True,exist_ok=True)
CREATE_NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)
IME='com.chatmirror.warmclone2/com.cyxfssx.warmime.WarmInputMethodService'

def run(*args,timeout=15):
    r=subprocess.run([str(ADB),*map(str,args)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout,creationflags=CREATE_NO_WINDOW)
    if r.returncode: raise RuntimeError((r.stderr+' '+r.stdout).strip() or f'ADB 失败 ({r.returncode})')
    return r.stdout.strip()
def quote(value): return "'"+value.replace("'", "'\\''")+"'"

class Config:
    defaults={'size':1920,'fps':30,'bitrate':4,'audio':False,'top':False,'text':True,'clipboard':True,'images':True,'directory':'/sdcard/Download/推推投屏','notes':{},'stay_awake':False,'screen_off':False,'remember_window':True,'auto_reconnect':True,'simple_mode':True,'geometry':{}}
    def __init__(self):
        self.path=DATA/'settings.json';self.value=self.defaults.copy();self.value['notes']={}
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'));self.value.update(data)
        except (OSError,ValueError,TypeError):pass
    def save(self):
        temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.value,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(self.path)

class Backend:
    def __init__(self):
        self.events=queue.Queue(); self.executor=ThreadPoolExecutor(max_workers=3,thread_name_prefix='tuitui');self.processes={};self.lock=threading.Lock();self.image_busy=False;self.transfers=TransferQueue(run,quote,self.emit)
    def emit(self,name,*args):self.events.put((name,args))
    def devices(self):
        try:
            output=run('devices','-l'); rows=[]
            for line in output.splitlines()[1:]:
                p=line.split()
                if len(p)<2 or ':' in p[0] or p[0].startswith('emulator-'):continue
                model=next((v[6:].replace('_',' ') for v in p[2:] if v.startswith('model:')),'安卓设备')
                rows.append((p[0],p[1],model))
            self.emit('devices',rows)
        except Exception as e:self.emit('device_error',str(e))
    def refresh(self):self.executor.submit(self.devices)
    def start(self,serial,settings):
        if serial in self.processes and self.processes[serial].poll() is None:return
        name=settings.get('notes',{}).get(serial,'').strip() or '手机'
        args=[str(SCRCPY),'-s',serial,'--window-title=推推投屏 · '+name,'--max-size='+str(settings['size']),'--max-fps='+str(settings['fps']),'--video-bit-rate='+str(settings['bitrate'])+'M','--keyboard=sdk','--no-clipboard-images']
        if settings.get('text'):args.append('--text-via-clipboard')
        if not settings.get('clipboard'):args.append('--no-clipboard-autosync')
        if not settings.get('audio'):args.append('--no-audio')
        if settings.get('top'):args.append('--always-on-top')
        if settings.get('stay_awake'):args.append('--stay-awake')
        if settings.get('screen_off'):args.append('--turn-screen-off')
        geo=settings.get('geometry',{}).get(serial) if settings.get('remember_window') else None
        if geo and len(geo)==4:args.extend(['--window-x='+str(geo[0]),'--window-y='+str(geo[1]),'--window-width='+str(geo[2]),'--window-height='+str(geo[3])])
        try:
            p=subprocess.Popen(args,cwd=str(ENGINE),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=CREATE_NO_WINDOW);self.processes[serial]=p
            self.emit('mirror_started',serial,p.pid); self.executor.submit(self._monitor,serial,p)
        except Exception as e:self.emit('error','投屏启动失败：'+str(e))
    def _monitor(self,serial,p):
        for line in p.stdout:
            line=line.strip()
            if line:self.emit('mirror_log',serial,line)
        code=p.wait()
        if self.processes.get(serial) is p:self.processes.pop(serial,None)
        self.emit('mirror_stopped',serial,code)
    def stop(self,serial):
        p=self.processes.get(serial)
        if p and p.poll() is None:p.terminate()
    def file_batch(self,serial,paths,directory):
        return self.transfers.add(serial,paths,directory)
    def submit_image(self,serial,path,temporary=False):
        with self.lock:
            if self.image_busy:
                if temporary:
                    try:Path(path).unlink(missing_ok=True)
                    except OSError:pass
                self.emit('image',False,'图片正在传输，请稍候。');return
            self.image_busy=True
        self.executor.submit(self._image,serial,Path(path),temporary)
    def _image(self,serial,path,temporary):
        token=secrets.token_hex(16); scanner='/data/local/tmp/tuitui2-personal-bridge.jar'; remote='/data/local/tmp/warm-image-'+token+'.tmp'
        try:
            if not SCANNER.is_file():raise ValueError('找不到推推2图片桥接器。')
            if not path.is_file() or not 0<path.stat().st_size<=32*1024*1024:raise ValueError('图片为空或超过 32 MB。')
            if run('-s',serial,'shell','settings','get','secure','default_input_method')!=IME:raise ValueError('请在手机上选择推推2输入法。')
            run('-s',serial,'push',SCANNER,scanner,timeout=30)
            cmd='CLASSPATH='+scanner+' app_process / com.genymobile.scrcpy.WarmImeBridge '
            try:run('-s',serial,'shell',cmd+'arm '+token)
            except RuntimeError as e:raise ValueError('请先点击目标聊天输入框。') from e
            run('-s',serial,'push',path,remote,timeout=120)
            out=run('-s',serial,'shell',cmd+'deliver '+token+' '+remote,timeout=30)
            if 'Warm IME: accepted' not in out:raise ValueError('聊天应用未确认接收图片：'+out)
            self.emit('image',True,'图片已交给聊天应用，请检查预览。')
        except Exception as e:self.emit('image',False,str(e))
        finally:
            try:run('-s',serial,'shell','rm','-f',remote,timeout=5)
            except Exception:pass
            if temporary:
                try:path.unlink(missing_ok=True)
                except OSError:pass
            with self.lock:self.image_busy=False
    def close(self):
        self.transfers.close()
        for serial in list(self.processes):self.stop(serial)
        self.executor.shutdown(wait=False,cancel_futures=True)
