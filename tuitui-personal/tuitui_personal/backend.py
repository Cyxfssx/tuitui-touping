"""Small USB-only backend for the personal desktop interface."""
import json, os, queue, re, secrets, subprocess, sys, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

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
    defaults={'size':1920,'fps':30,'bitrate':4,'audio':False,'top':False,'text':True,'clipboard':True,'images':True,'directory':'/sdcard/Download/推推投屏','notes':{}}
    def __init__(self):
        self.path=DATA/'settings.json';self.value=self.defaults.copy();self.value['notes']={}
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'));self.value.update(data)
        except (OSError,ValueError,TypeError):pass
    def save(self):
        temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(self.value,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(self.path)

class Backend:
    def __init__(self):
        self.events=queue.Queue(); self.executor=ThreadPoolExecutor(max_workers=3,thread_name_prefix='tuitui');self.processes={};self.lock=threading.Lock();self.file_process=None;self.cancelled=False;self.image_busy=False
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
        args=[str(SCRCPY),'-s',serial,'--window-title=推推投屏 · '+serial,'--max-size='+str(settings['size']),'--max-fps='+str(settings['fps']),'--video-bit-rate='+str(settings['bitrate'])+'M','--keyboard=sdk','--no-clipboard-images']
        if settings.get('text'):args.append('--text-via-clipboard')
        if not settings.get('clipboard'):args.append('--no-clipboard-autosync')
        if not settings.get('audio'):args.append('--no-audio')
        if settings.get('top'):args.append('--always-on-top')
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
        if self.file_process is not None:self.emit('error','已有传输任务正在进行。');return
        self.file_process='queued';self.cancelled=False;self.executor.submit(self._file_batch,serial,paths,directory)
    def _file_batch(self,serial,paths,directory):
        try:
            if directory!='/sdcard' and not directory.startswith('/sdcard/'):raise ValueError('保存路径必须位于 /sdcard 下。')
            run('-s',serial,'shell','mkdir -p '+quote(directory))
            for filename in paths:
                if self.cancelled:break
                pth=Path(filename)
                if not pth.is_file():self.emit('file',filename,'失败：不是文件');continue
                self.emit('file',filename,'正在传输')
                p=subprocess.Popen([str(ADB),'-s',serial,'push','-p',str(pth),directory.rstrip('/')+'/'+pth.name],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace',creationflags=CREATE_NO_WINDOW)
                self.file_process=p; output=[]
                for line in p.stdout:
                    output.append(line.strip());match=re.search(r'(\d{1,3})%',line)
                    if match:self.emit('file',filename,'传输中 '+match.group(1)+'%')
                code=p.wait();self.emit('file',filename,'已取消' if self.cancelled else '已完成' if code==0 else '失败：'+(' '.join(output)[-160:] or f'ADB 错误 {code}'))
        except Exception as e:self.emit('error','文件传输失败：'+str(e))
        finally:self.file_process=None;self.emit('file_done')
    def cancel(self):
        self.cancelled=True;p=self.file_process
        if p and p!='queued' and p.poll() is None:p.terminate()
    def submit_image(self,serial,path,temporary=False):
        with self.lock:
            if self.image_busy:self.emit('image',False,'图片正在传输，请稍候。');return
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
        self.cancel()
        for serial in list(self.processes):self.stop(serial)
        self.executor.shutdown(wait=False,cancel_futures=True)
