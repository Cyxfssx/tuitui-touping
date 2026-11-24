"""TuiTui Screen: a single-device Windows desktop front end, without Qt."""
import ctypes, logging, os, queue, subprocess, threading, tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from .backend import Backend, Config, DATA, ENGINE, run, IME
from .hotkeys import Hook, capture

BG='#0F172A'; CARD='#1E293B'; BORDER='#334155'; TEXT='#E2E8F0'; MUTED='#94A3B8'; BLUE='#2563EB'; AMBER='#D6B87B'; BTN='#334155'; RED='#B43C46'
FONT=('Microsoft YaHei UI',10); SMALL=('Microsoft YaHei UI',9); TITLE=('Microsoft YaHei UI',15,'bold')
class App:
    def __init__(self):
        try:ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:pass
        self.root=TkinterDnD.Tk();self.root.title('推推投屏 · 个人版');self.root.geometry('1030x760');self.root.minsize(820,600);self.root.configure(bg=BG)
        (DATA/'logs').mkdir(exist_ok=True);logging.basicConfig(filename=DATA/'logs'/'app.log',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',encoding='utf-8')
        self.backend=Backend();self.cfg=Config();self.devices=[];self.serial='';self.polling=False;self.files={};self.closing=False;self.settings_open=False;self.settings_animation=None
        self.size=tk.StringVar(value=str(self.cfg.value['size']));self.fps=tk.StringVar(value=str(self.cfg.value['fps']));self.bitrate=tk.StringVar(value=str(self.cfg.value['bitrate']));self.directory=tk.StringVar(value=self.cfg.value['directory'])
        self.flags={k:tk.BooleanVar(value=bool(self.cfg.value[k])) for k in ('text','clipboard','images','audio','top')}
        self.device_var=tk.StringVar();self.status=tk.StringVar(value='正在检测 USB 设备…');self.summary=tk.StringVar();self.card_title=tk.StringVar(value='未连接设备');self.card_detail=tk.StringVar(value='请使用 USB 连接手机并允许 USB 调试');self.mirror_label=tk.StringVar(value='▶  启动投屏')
        self.init_styles();self.build();self.update_summary()
        self.hook=Hook(self.root,self.backend,lambda:self.cfg.value.get('images',True),self.set_status)
        try:self.hook.start()
        except Exception as e:self.set_status('图片快捷键不可用：'+str(e))
        self.root.protocol('WM_DELETE_WINDOW',self.close);self.root.after(100,self.pump);self.refresh()
    def init_styles(self):
        style=ttk.Style(self.root);style.theme_use('clam');style.configure('Dark.TCombobox',fieldbackground=BTN,background=BTN,foreground=TEXT,arrowcolor=TEXT,bordercolor=BORDER,lightcolor=BTN,darkcolor=BTN,padding=6)
        style.map('Dark.TCombobox',fieldbackground=[('readonly',BTN)],foreground=[('readonly',TEXT)])
        style.configure('Treeview',background=CARD,fieldbackground=CARD,foreground=TEXT,rowheight=29,borderwidth=0,font=SMALL);style.map('Treeview',background=[('selected','#34527A')]);style.configure('Treeview.Heading',background=BTN,foreground=TEXT,relief='flat',font=SMALL)
    def label(self,parent,text='',**kw):return tk.Label(parent,text=text,bg=kw.pop('bg',CARD),fg=kw.pop('fg',TEXT),font=kw.pop('font',FONT),anchor='w',**kw)
    def button(self,parent,text,command,primary=False,**kw):
        b=tk.Button(parent,text=text,command=command,bd=0,highlightthickness=0,relief='flat',bg=kw.pop('bg',BLUE if primary else BTN),fg='white' if primary else TEXT,activebackground=kw.pop('activebackground','#3B82F6' if primary else '#475569'),activeforeground='white',font=FONT,cursor='hand2',padx=kw.pop('padx',14),pady=kw.pop('pady',7),**kw);return b
    def card(self,parent):return tk.Frame(parent,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
    def build(self):
        head=tk.Frame(self.root,bg=BG);head.pack(fill='x',padx=18,pady=(14,8));self.label(head,'●',bg=BG,fg='#60A5FA',font=('Segoe UI',13,'bold')).pack(side='left');self.label(head,'推推投屏',bg=BG,font=('Microsoft YaHei UI',17,'bold')).pack(side='left',padx=(8,5));self.label(head,'TuiTui Screen  /  个人版',bg=BG,fg=MUTED,font=SMALL).pack(side='left')
        self.button(head,'设置',self.toggle_settings).pack(side='right',padx=(6,0));self.button(head,'日志文件夹',lambda:self.open_folder(DATA/'logs')).pack(side='right',padx=(6,0));self.button(head,'录屏文件夹',self.open_recordings).pack(side='right')
        self.banner=tk.Frame(self.root,bg='#3A3429',highlightbackground='#66563A',highlightthickness=1);self.banner.pack(fill='x',padx=18,pady=(0,12));self.label(self.banner,'✦   祝兄弟们在公司行大运、爆大单、日进斗金，日子顺风顺水顺财神、有钱有势有前程。',bg='#3A3429',fg=AMBER,font=SMALL).pack(side='left',padx=14,pady=8);self.button(self.banner,'×',lambda:self.banner.pack_forget(),bg='#3A3429',activebackground='#514430',padx=9,pady=3).pack(side='right',padx=6)
        body=tk.Frame(self.root,bg=BG);body.pack(fill='both',expand=True,padx=18)
        dev=self.card(body);dev.pack(fill='x',pady=(0,12));inner=tk.Frame(dev,bg=CARD);inner.pack(fill='x',padx=16,pady=14)
        left=tk.Frame(inner,bg=CARD);left.pack(side='left',fill='x',expand=True);self.label(left,textvariable=self.card_title,font=TITLE).pack(fill='x');self.label(left,textvariable=self.card_detail,fg=MUTED,font=SMALL).pack(fill='x',pady=(5,7))
        self.devices_combo=ttk.Combobox(left,textvariable=self.device_var,style='Dark.TCombobox',state='readonly',width=28);self.devices_combo.pack(anchor='w');self.devices_combo.bind('<<ComboboxSelected>>',self.select_device)
        actions=tk.Frame(inner,bg=CARD);actions.pack(side='right',padx=(10,0));self.primary=self.button(actions,'',self.toggle_mirror,primary=True);self.primary.configure(textvariable=self.mirror_label,width=13);self.primary.pack(side='top',fill='x');row=tk.Frame(actions,bg=CARD);row.pack(fill='x',pady=(6,0));self.button(row,'查看投屏',self.show_mirror,padx=8).pack(side='left');self.button(row,'重连',self.reconnect,padx=8).pack(side='left',padx=(6,0))
        settings=self.card(body);settings.pack(fill='x',pady=(0,12));bar=tk.Frame(settings,bg=CARD);bar.pack(fill='x',padx=16,pady=10);self.label(bar,textvariable=self.summary,fg=TEXT,font=SMALL).pack(side='left',fill='x',expand=True);self.expand=self.button(bar,'展开设置  ∨',self.toggle_settings,padx=9,pady=4);self.expand.pack(side='right')
        self.settings_frame=tk.Frame(settings,bg=CARD);self.build_settings()
        transfer=self.card(body);transfer.pack(fill='both',expand=True,pady=(0,12));inside=tk.Frame(transfer,bg=CARD);inside.pack(fill='both',expand=True,padx=16,pady=14)
        hdr=tk.Frame(inside,bg=CARD);hdr.pack(fill='x');self.label(hdr,'文件快传',font=('Microsoft YaHei UI',13,'bold')).pack(side='left');self.label(hdr,'仅传输到当前设备',fg=MUTED,font=SMALL).pack(side='left',padx=12);self.button(hdr,'取消传输',self.backend.cancel,padx=9,pady=4).pack(side='right')
        self.drop=tk.Canvas(inside,height=108,bg='#162235',highlightthickness=0,cursor='hand2');self.drop.pack(fill='x',pady=(10,10));self.drop.bind('<Configure>',self.draw_drop);self.drop.bind('<Button-1>',lambda e:self.choose_files());self.drop.drop_target_register(DND_FILES);self.drop.dnd_bind('<<Drop>>',self.on_drop)
        pathrow=tk.Frame(inside,bg=CARD);pathrow.pack(fill='x',pady=(0,8));self.label(pathrow,'保存路径',fg=MUTED,font=SMALL).pack(side='left');entry=tk.Entry(pathrow,textvariable=self.directory,bg=BG,fg=TEXT,insertbackground=TEXT,relief='flat',font=SMALL);entry.pack(side='left',fill='x',expand=True,padx=(8,6),ipady=5);entry.bind('<FocusOut>',lambda e:self.save_settings());self.button(pathrow,'选择文件',self.choose_files,padx=9,pady=3).pack(side='left')
        self.label(inside,'传输列表',fg=MUTED,font=SMALL).pack(anchor='w',pady=(2,5));self.tree=ttk.Treeview(inside,columns=('name','state'),show='headings',height=4);self.tree.heading('name',text='文件');self.tree.heading('state',text='状态');self.tree.column('name',width=450);self.tree.column('state',width=180);self.tree.pack(fill='both',expand=True)
        status=tk.Frame(self.root,bg=BG);status.pack(fill='x',padx=18,pady=(0,12));self.label(status,'●',bg=BG,fg='#10B981',font=SMALL).pack(side='left');self.label(status,textvariable=self.status,bg=BG,fg=MUTED,font=SMALL).pack(side='left',padx=6,fill='x',expand=True)
    def draw_drop(self,event):
        self.drop.delete('all');w=event.width;h=event.height;self.drop.create_rectangle(2,2,w-3,h-3,outline='#64748B',dash=(5,4),width=1);self.drop.create_text(w/2,h/2-10,text='⇧   拖拽文件或图片到这里',fill=TEXT,font=('Microsoft YaHei UI',11,'bold'));self.drop.create_text(w/2,h/2+20,text='或点击选择文件，发送至当前手机',fill=MUTED,font=SMALL)
    def build_settings(self):
        f=self.settings_frame
        presets=tk.Frame(f,bg=CARD);presets.pack(fill='x',pady=(0,8));self.label(presets,'画质预设',fg=MUTED,font=SMALL).pack(side='left',padx=(0,12))
        for name,values in [('流畅',(1280,30,3)),('均衡',(1920,30,4)),('清晰聊天',(1920,30,8))]:self.button(presets,name,lambda v=values:self.preset(v),padx=9,pady=3).pack(side='left',padx=(0,6))
        row=tk.Frame(f,bg=CARD);row.pack(fill='x',pady=(0,8))
        for label,var,values in [('分辨率',self.size,['720','1280','1920','2560']),('帧率',self.fps,['15','24','30','60']),('码率 Mbps',self.bitrate,['2','3','4','6','8','12','16'])]:
            self.label(row,label,fg=MUTED,font=SMALL).pack(side='left',padx=(0,6));c=ttk.Combobox(row,textvariable=var,values=values,state='readonly',width=6,style='Dark.TCombobox');c.pack(side='left',padx=(0,16));c.bind('<<ComboboxSelected>>',lambda e:self.save_settings())
        switches=tk.Frame(f,bg=CARD);switches.pack(fill='x')
        for key,label in [('text','中文输入'),('clipboard','文字剪贴板'),('images','图片 Ctrl+V'),('audio','音频'),('top','窗口置顶')]:
            tk.Checkbutton(switches,text=label,variable=self.flags[key],command=self.save_settings,bg=CARD,fg=TEXT,selectcolor=BG,activebackground=CARD,activeforeground=TEXT,font=SMALL,highlightthickness=0).pack(side='left',padx=(0,12))
        self.label(f,'更改画面和功能设置后，重新启动投屏生效。',fg=MUTED,font=SMALL).pack(anchor='w',pady=(8,0))
    def toggle_settings(self):
        self.settings_open=not self.settings_open
        if self.settings_animation:
            self.root.after_cancel(self.settings_animation);self.settings_animation=None
        if self.settings_open:
            self.settings_frame.pack(fill='x',padx=16,pady=(0,14));self.settings_frame.pack_propagate(True);self.root.update_idletasks();target=self.settings_frame.winfo_reqheight();self.settings_frame.pack_propagate(False);self.settings_frame.configure(height=1);self.expand.configure(text='收起设置  ∧');self.animate_settings(1,target)
        else:
            height=self.settings_frame.winfo_height();self.settings_frame.pack_propagate(False);self.expand.configure(text='展开设置  ∨');self.animate_settings(height,0)
    def animate_settings(self,current,target):
        step=max(8,abs(target-current)//3);next_height=min(target,current+step) if target>current else max(target,current-step)
        if next_height<=0:
            self.settings_frame.pack_forget();self.settings_frame.pack_propagate(True);self.settings_animation=None;return
        self.settings_frame.configure(height=next_height)
        if next_height!=target:self.settings_animation=self.root.after(16,lambda:self.animate_settings(next_height,target))
        else:self.settings_animation=None
    def preset(self,v):self.size.set(str(v[0]));self.fps.set(str(v[1]));self.bitrate.set(str(v[2]));self.save_settings()
    def save_settings(self):
        try:
            self.cfg.value.update(size=int(self.size.get()),fps=int(self.fps.get()),bitrate=int(self.bitrate.get()),directory=self.directory.get().strip(),**{k:v.get() for k,v in self.flags.items()});self.cfg.save();self.update_summary();self.update_device()
        except (ValueError,OSError) as e:self.set_status('设置保存失败：'+str(e))
    def update_summary(self):
        n=sum(v.get() for v in self.flags.values());self.summary.set(f'⚙  画面与功能配置：{self.size.get()}P · {self.fps.get()} FPS · {self.bitrate.get()} Mbps   |   已开启 {n} 项功能')
    def set_status(self,text):self.status.set(text[:200]);logging.info('%s',text[:500])
    def refresh(self):
        if self.closing:return
        if not self.polling:self.polling=True;self.backend.refresh()
        self.root.after(5000,self.refresh)
    def select_device(self,event=None):
        i=self.devices_combo.current();self.serial=self.devices[i][0] if 0<=i<len(self.devices) else '';self.update_device()
    def update_device(self):
        d=next((r for r in self.devices if r[0]==self.serial),None)
        if not d:self.card_title.set('未连接设备');self.card_detail.set('请使用 USB 连接手机并允许 USB 调试');self.primary.configure(state='disabled');self.mirror_label.set('▶  启动投屏');return
        serial,state,model=d;name=self.cfg.value.get('notes',{}).get(serial,'手机 01');self.card_title.set(name+'  ·  '+model);self.card_detail.set(('USB · 已连接' if state=='device' else 'USB · '+state)+f'   |   目标 {self.fps.get()} FPS · {self.bitrate.get()} Mbps')
        p=self.backend.processes.get(serial);running=p is not None and p.poll() is None;self.primary.configure(state='normal' if state=='device' or running else 'disabled',bg=RED if running else BLUE);self.mirror_label.set('■  停止投屏' if running else '▶  启动投屏')
    def require(self):
        if not any(s==self.serial and state=='device' for s,state,_ in self.devices):messagebox.showwarning('设备不可用','请选择已授权的 USB 设备。',parent=self.root);return False
        return True
    def toggle_mirror(self):
        p=self.backend.processes.get(self.serial)
        if p and p.poll() is None:self.backend.stop(self.serial);return
        if not self.require():return
        self.save_settings();self.backend.start(self.serial,self.cfg.value.copy());self.update_device()
    def show_mirror(self):
        if not self.serial:return
        u=ctypes.windll.user32;u.FindWindowW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p];u.FindWindowW.restype=ctypes.c_void_p;u.SetForegroundWindow.argtypes=[ctypes.c_void_p];h=u.FindWindowW(None,'推推投屏 · '+self.serial)
        if h:u.ShowWindow(ctypes.c_void_p(h),9);u.SetForegroundWindow(h)
        else:self.set_status('当前设备尚未启动投屏。')
    def reconnect(self):
        if not self.require():return
        serial=self.serial;p=self.backend.processes.get(serial)
        if p and p.poll() is None:
            self.backend.stop(serial);self.set_status('正在重连投屏…');self.root.after(150,lambda:self._restart_when_stopped(serial,0));return
        self.backend.start(serial,self.cfg.value.copy());self.update_device()
    def _restart_when_stopped(self,serial,attempt):
        p=self.backend.processes.get(serial)
        if p and p.poll() is None:
            if attempt<40:self.root.after(150,lambda:self._restart_when_stopped(serial,attempt+1))
            else:self.set_status('投屏进程未退出，无法重连。')
            return
        if any(s==serial and state=='device' for s,state,_ in self.devices):self.backend.start(serial,self.cfg.value.copy());self.update_device()
        else:self.set_status('设备已断开，无法重连。')
    def choose_files(self):
        paths=filedialog.askopenfilenames(parent=self.root,title='选择要发送到手机的文件')
        if paths:self.send_files(list(paths))
    def on_drop(self,event):
        try:paths=list(self.root.tk.splitlist(event.data))
        except tk.TclError:messagebox.showerror('拖放失败','无法读取拖放文件路径。',parent=self.root);return
        self.send_files(paths)
    def send_files(self,paths):
        if not self.require():return
        files=[str(Path(p)) for p in paths if Path(p).is_file()]
        if not files:messagebox.showwarning('没有文件','请选择普通文件，暂不支持文件夹。',parent=self.root);return
        if self.backend.file_process is not None:messagebox.showinfo('请稍候','已有文件传输正在进行。',parent=self.root);return
        self.save_settings()
        for file in files:self.files[file]=self.tree.insert('', 'end',values=(Path(file).name,'等待中'))
        self.backend.file_batch(self.serial,files,self.directory.get().strip())
    def open_folder(self,path):
        Path(path).mkdir(parents=True,exist_ok=True);os.startfile(str(path))
    def open_recordings(self):self.open_folder(Path(__file__).resolve().parent.parent/'推推投屏-推推2测试版'/'recordings')
    def pump(self):
        try:
            while True:
                name,args=self.backend.events.get_nowait();self.event(name,*args)
        except queue.Empty:pass
        if not self.closing:self.root.after(100,self.pump)
    def event(self,name,*args):
        if name=='devices':
            self.polling=False;rows=args[0]
            if rows!=self.devices:
                self.devices=rows;self.devices_combo['values']=[self.cfg.value.get('notes',{}).get(s,'手机 01')+' · '+m+' ('+s+')' for s,_,m in rows]
                index=next((i for i,r in enumerate(rows) if r[0]==self.serial),0 if rows else -1);self.devices_combo.current(index) if index>=0 else self.device_var.set('');self.select_device()
            if not rows:self.set_status('未检测到 USB 设备。')
        elif name=='device_error':self.polling=False;self.set_status('ADB 检测失败：'+args[0])
        elif name=='mirror_started':self.update_device();self.set_status('正在启动投屏：'+args[0])
        elif name=='mirror_stopped':self.update_device();self.set_status('投屏已结束：'+args[0])
        elif name=='mirror_log':
            if 'ERROR' in args[1] or 'WARN' in args[1]:self.set_status(args[1])
        elif name=='file':
            item=self.files.get(args[0]);
            if item:self.tree.item(item,values=(Path(args[0]).name,args[1]));self.set_status(Path(args[0]).name+' · '+args[1])
        elif name=='file_done':self.set_status('文件传输队列已结束。')
        elif name=='hotkey_image':
            try:
                image=capture()
                if image:self.backend.submit_image(args[0],*image)
                else:self.set_status('剪贴板图片已变化，请重试。')
            except Exception as e:self.set_status('读取剪贴板失败：'+str(e))
        elif name=='hotkey_error':self.set_status('图片快捷键错误：'+args[0])
        elif name=='image':self.set_status(args[1]);messagebox.showwarning('图片未提交',args[1],parent=self.root) if not args[0] else None
        elif name=='error':self.set_status(args[0]);messagebox.showwarning('操作失败',args[0],parent=self.root)
    def close(self):
        if self.backend.image_busy:messagebox.showinfo('请稍候','图片传输完成后再退出。',parent=self.root);return
        self.closing=True;self.hook.stop();self.backend.close();self.root.destroy()
    def run(self):self.root.mainloop()
