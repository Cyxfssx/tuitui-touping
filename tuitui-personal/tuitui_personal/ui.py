"""USB personal-mode frontend for TuiTui Screen, without Qt."""
import ctypes, logging, os, queue, tkinter as tk
from pathlib import Path
from tkinter import ttk,filedialog,messagebox,simpledialog
from tkinterdnd2 import DND_FILES,TkinterDnD
from .backend import Backend,Config,DATA,ROOT
from .hotkeys import Hook,capture
from .windows import bounds,show

BG='#0F172A';CARD='#1E293B';BORDER='#334155';TEXT='#E2E8F0';MUTED='#94A3B8';BLUE='#2563EB';BTN='#334155';RED='#B43C46'
FONT=('Microsoft YaHei UI',10);SMALL=('Microsoft YaHei UI',9);TITLE=('Microsoft YaHei UI',15,'bold')
class App:
    def __init__(self):
        try:ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:pass
        self.root=TkinterDnD.Tk();self.root.title('推推投屏 · 个人版');self.root.configure(bg=BG);self.root.minsize(500,380)
        (DATA/'logs').mkdir(exist_ok=True);logging.basicConfig(filename=DATA/'logs'/'app.log',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',encoding='utf-8')
        self.backend=Backend();self.cfg=Config()
        if self.cfg.value.get('layout_version',0)<2:
            self.cfg.value['simple_mode']=True;self.cfg.value['layout_version']=2;self.cfg.save()
        self.devices=[];self.serial='';self.polling=False;self.closing=False;self.want={};self.retry_id={};self.retry_count={};self.stopped_by_user=set();self.manual_reconnect=set();self.geometry_cache={}
        self.simple=tk.BooleanVar(value=self.cfg.value.get('simple_mode',True));self.status=tk.StringVar(value='正在检测 USB 设备…');self.name_var=tk.StringVar();self.device_detail=tk.StringVar(value='请使用 USB 连接手机并允许 USB 调试');self.mirror_label=tk.StringVar(value='一键 USB 连接')
        self.size=tk.StringVar(value=str(self.cfg.value['size']));self.fps=tk.StringVar(value=str(self.cfg.value['fps']));self.bitrate=tk.StringVar(value=str(self.cfg.value['bitrate']));self.directory=tk.StringVar(value=self.cfg.value['directory'])
        self.flags={k:tk.BooleanVar(value=bool(self.cfg.value[k])) for k in ('text','clipboard','images','audio','top','stay_awake','screen_off','remember_window','auto_reconnect')}
        self.init_styles();self.build();self.set_mode(initial=True)
        self.hook=Hook(self.root,self.backend,lambda:self.cfg.value.get('images',True),self.set_status)
        try:self.hook.start()
        except Exception as e:self.set_status('图片快捷键不可用：'+str(e))
        self.root.protocol('WM_DELETE_WINDOW',self.close);self.root.after(100,self.pump);self.root.after(1000,self.snapshot);self.refresh()
    def init_styles(self):
        style=ttk.Style(self.root);style.theme_use('clam');style.configure('Treeview',background=CARD,fieldbackground=CARD,foreground=TEXT,rowheight=30,borderwidth=0,font=SMALL);style.map('Treeview',background=[('selected','#34527A')]);style.configure('Treeview.Heading',background=BTN,foreground=TEXT,relief='flat',font=SMALL)
        style.configure('Dark.TCombobox',fieldbackground=BTN,background=BTN,foreground=TEXT,arrowcolor=TEXT,bordercolor=BORDER,padding=6);style.map('Dark.TCombobox',fieldbackground=[('readonly',BTN)],foreground=[('readonly',TEXT)])
    def label(self,parent,text='',**kw):return tk.Label(parent,text=text,bg=kw.pop('bg',CARD),fg=kw.pop('fg',TEXT),font=kw.pop('font',FONT),anchor='w',**kw)
    def button(self,parent,text,command,primary=False,**kw):return tk.Button(parent,text=text,command=command,bd=0,highlightthickness=0,relief='flat',bg=kw.pop('bg',BLUE if primary else BTN),fg='white' if primary else TEXT,activebackground=kw.pop('activebackground','#3B82F6' if primary else '#475569'),activeforeground='white',font=FONT,cursor='hand2',padx=kw.pop('padx',12),pady=kw.pop('pady',6),**kw)
    def card(self,parent):return tk.Frame(parent,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
    def build(self):
        head=tk.Frame(self.root,bg=BG);head.pack(fill='x',padx=16,pady=(14,8));self.label(head,'推推投屏',bg=BG,font=('Microsoft YaHei UI',16,'bold')).pack(side='left');self.label(head,'  个人版',bg=BG,fg=MUTED,font=SMALL).pack(side='left')
        tk.Checkbutton(head,text='启用精简模式',variable=self.simple,command=self.set_mode,bg=BG,fg=TEXT,selectcolor=CARD,activebackground=BG,activeforeground=TEXT,font=SMALL,highlightthickness=0).pack(side='right');self.button(head,'高级设置',self.open_advanced,padx=8,pady=3).pack(side='right',padx=8)
        body=tk.Frame(self.root,bg=BG);body.pack(fill='both',expand=True,padx=16,pady=(0,8));self.body=body
        self.left=self.card(body);self.left.pack(side='left',fill='both',expand=True);lf=tk.Frame(self.left,bg=CARD);lf.pack(fill='both',expand=True,padx=16,pady=14)
        self.label(lf,'USB 设备',font=TITLE).pack(anchor='w');self.label(lf,textvariable=self.device_detail,fg=MUTED,font=SMALL,wraplength=360).pack(fill='x',pady=(4,12))
        row=tk.Frame(lf,bg=CARD);row.pack(fill='x');self.primary=self.button(row,'',self.toggle_mirror,primary=True);self.primary.configure(textvariable=self.mirror_label);self.primary.pack(side='left',fill='x',expand=True);self.button(row,'刷新设备',self.refresh_once).pack(side='left',padx=(8,0))
        self.label(lf,'双击设备可启动或查看投屏',fg=MUTED,font=SMALL).pack(anchor='w',pady=(12,5));self.list=tk.Listbox(lf,bg='#182332',fg=TEXT,selectbackground='#3159A8',selectforeground='white',font=FONT,bd=0,highlightthickness=1,highlightbackground=BORDER,activestyle='none',exportselection=False,height=7);self.list.pack(fill='both',expand=True);self.list.bind('<<ListboxSelect>>',self.select_device);self.list.bind('<Double-Button-1>',self.double_click)
        rename=tk.Frame(lf,bg=CARD);rename.pack(fill='x',pady=(12,0));self.label(rename,'设备名称',fg=MUTED,font=SMALL).pack(side='left');entry=tk.Entry(rename,textvariable=self.name_var,bg=BG,fg=TEXT,insertbackground=TEXT,relief='flat',font=FONT);entry.pack(side='left',fill='x',expand=True,padx=8,ipady=6);self.button(rename,'更新名称',self.rename,padx=10,pady=4).pack(side='right')
        self.advanced=self.card(body);right=tk.Frame(self.advanced,bg=CARD);right.pack(fill='both',expand=True,padx=16,pady=14)
        self.label(right,'画面设置',font=('Microsoft YaHei UI',13,'bold')).pack(anchor='w');presets=tk.Frame(right,bg=CARD);presets.pack(fill='x',pady=(8,7));self.label(presets,'画质预设',fg=MUTED,font=SMALL).pack(side='left',padx=(0,8))
        for name,values in [('流畅',(1280,30,3)),('均衡',(1920,30,4)),('清晰聊天',(1920,30,8))]:self.button(presets,name,lambda v=values:self.preset(v),padx=8,pady=3).pack(side='left',padx=(0,5))
        selectors=tk.Frame(right,bg=CARD);selectors.pack(fill='x',pady=(0,7))
        for label,var,values in [('分辨率',self.size,['720','1280','1920','2560']),('帧率',self.fps,['15','24','30','60']),('码率 Mbps',self.bitrate,['2','3','4','6','8','12','16'])]:
            self.label(selectors,label,fg=MUTED,font=SMALL).pack(side='left',padx=(0,4));combo=ttk.Combobox(selectors,textvariable=var,values=values,state='readonly',width=5,style='Dark.TCombobox');combo.pack(side='left',padx=(0,10));combo.bind('<<ComboboxSelected>>',lambda e:self.save_settings())
        switches=tk.Frame(right,bg=CARD);switches.pack(fill='x')
        items=[('stay_awake','保持唤醒'),('screen_off','自动息屏'),('remember_window','记住窗口位置'),('auto_reconnect','自动重连'),('text','中文输入'),('clipboard','文字剪贴板'),('images','图片 Ctrl+V'),('audio','音频'),('top','窗口置顶')]
        for i,(key,label) in enumerate(items):tk.Checkbutton(switches,text=label,variable=self.flags[key],command=self.save_settings,bg=CARD,fg=TEXT,selectcolor=BG,activebackground=CARD,activeforeground=TEXT,font=SMALL,highlightthickness=0).grid(row=i//3,column=i%3,sticky='w',padx=(0,12),pady=2)
        self.label(right,'自动息屏会在启动投屏后关闭手机屏幕；修改画面参数后需重启投屏。',fg=MUTED,font=SMALL,wraplength=590).pack(anchor='w',pady=(6,8))
        bar=tk.Frame(right,bg=CARD);bar.pack(fill='x');self.label(bar,'文件传输',font=('Microsoft YaHei UI',13,'bold')).pack(side='left');self.button(bar,'查看投屏',self.show_mirror,padx=8,pady=3).pack(side='right');self.button(bar,'重新连接',self.reconnect,padx=8,pady=3).pack(side='right',padx=6)
        self.drop=tk.Canvas(right,height=88,bg='#162235',highlightthickness=0,cursor='hand2');self.drop.pack(fill='x',pady=(8,8));self.drop.bind('<Configure>',self.draw_drop);self.drop.bind('<Button-1>',lambda e:self.choose_files());self.drop.drop_target_register(DND_FILES);self.drop.dnd_bind('<<Drop>>',self.on_drop)
        pathrow=tk.Frame(right,bg=CARD);pathrow.pack(fill='x',pady=(0,8));self.label(pathrow,'保存路径',fg=MUTED,font=SMALL).pack(side='left');entry=tk.Entry(pathrow,textvariable=self.directory,bg=BG,fg=TEXT,insertbackground=TEXT,relief='flat',font=SMALL);entry.pack(side='left',fill='x',expand=True,padx=8,ipady=5);entry.bind('<FocusOut>',lambda e:self.save_settings());self.button(pathrow,'选择文件',self.choose_files,padx=8,pady=3).pack(side='left')
        controls=tk.Frame(right,bg=CARD);controls.pack(fill='x',pady=(0,4));self.label(controls,'传输列表',fg=MUTED,font=SMALL).pack(side='left');self.button(controls,'暂停',lambda:self.task_action('pause'),padx=8,pady=3).pack(side='left',padx=(10,4));self.button(controls,'继续',lambda:self.task_action('resume'),padx=8,pady=3).pack(side='left',padx=4);self.button(controls,'取消',lambda:self.task_action('cancel'),padx=8,pady=3).pack(side='left',padx=4);self.button(controls,'清理已结束',self.backend.transfers.clear_finished,padx=8,pady=3).pack(side='right')
        self.tree=ttk.Treeview(right,columns=('name','state','progress'),show='headings',height=5);self.tree.heading('name',text='文件');self.tree.heading('state',text='状态');self.tree.heading('progress',text='进度');self.tree.column('name',width=230);self.tree.column('state',width=180);self.tree.column('progress',width=70,anchor='center');self.tree.pack(fill='both',expand=True)
        footer=tk.Frame(self.root,bg=BG);footer.pack(fill='x',padx=16,pady=(0,10));self.label(footer,textvariable=self.status,bg=BG,fg=MUTED,font=SMALL).pack(side='left',fill='x',expand=True)
    def set_mode(self,initial=False):
        simple=self.simple.get();self.cfg.value['simple_mode']=simple
        if not initial:self.cfg.save()
        if simple:
            self.advanced.pack_forget();self.left.configure(width=0);self.left.pack_configure(expand=True,fill='both');self.root.minsize(500,380);self.root.geometry('540x500')
        else:
            self.left.configure(width=365);self.left.pack_configure(expand=False,fill='both');self.left.pack_propagate(False);self.advanced.pack(side='left',fill='both',expand=True,padx=(12,0));self.root.minsize(850,580);self.root.geometry('1120x760')
        if simple:self.left.pack_propagate(True)
    def open_advanced(self):
        if self.simple.get():self.simple.set(False);self.set_mode()
    def draw_drop(self,event):
        self.drop.delete('all');w=event.width;h=event.height;self.drop.create_rectangle(2,2,w-3,h-3,outline='#64748B',dash=(5,4));self.drop.create_text(w/2,h/2-9,text='⇧   拖拽文件到这里，或点击选择文件',fill=TEXT,font=('Microsoft YaHei UI',10,'bold'));self.drop.create_text(w/2,h/2+18,text='仅发送至当前 USB 设备',fill=MUTED,font=SMALL)
    def set_status(self,text):self.status.set(str(text)[:200]);logging.info('%s',str(text)[:500])
    def preset(self,v):self.size.set(str(v[0]));self.fps.set(str(v[1]));self.bitrate.set(str(v[2]));self.save_settings()
    def save_settings(self):
        try:
            self.cfg.value.update(size=int(self.size.get()),fps=int(self.fps.get()),bitrate=int(self.bitrate.get()),directory=self.directory.get().strip(),**{k:v.get() for k,v in self.flags.items()});self.cfg.save();self.update_device()
            if not self.flags['auto_reconnect'].get():self.cancel_retries()
        except (ValueError,OSError) as e:self.set_status('设置保存失败：'+str(e))
    def refresh(self):
        if self.closing:return
        self.refresh_once();self.root.after(4000,self.refresh)
    def refresh_once(self):
        if not self.polling:self.polling=True;self.backend.refresh()
    def select_device(self,event=None):
        selected=self.list.curselection()
        if not selected:return
        self.serial=self.devices[selected[0]][0];self.update_device()
    def rename(self):
        if not self.serial:messagebox.showwarning('未选择设备','请先选择设备。',parent=self.root);return
        name=self.name_var.get().strip()
        if not name:messagebox.showwarning('名称为空','请输入设备名称。',parent=self.root);return
        self.cfg.value.setdefault('notes',{})[self.serial]=name;self.cfg.save();self.populate_devices();self.set_status('设备名称已更新。')
    def populate_devices(self):
        self.list.delete(0,'end');notes=self.cfg.value.get('notes',{})
        for i,(serial,state,model) in enumerate(self.devices):self.list.insert('end',notes.get(serial) or f'手机 {i+1:02d} · {model}')
        index=next((i for i,r in enumerate(self.devices) if r[0]==self.serial),-1)
        if index<0 and self.devices:index=0;self.serial=self.devices[0][0]
        if index>=0:self.list.selection_set(index);self.list.activate(index)
        self.update_device()
    def update_device(self):
        item=next((r for r in self.devices if r[0]==self.serial),None)
        if not item:
            waiting=bool(self.serial and self.want.get(self.serial));self.name_var.set(self.cfg.value.get('notes',{}).get(self.serial,''));self.device_detail.set('等待 USB 设备重新连接…' if waiting else '请使用 USB 连接手机并允许 USB 调试');self.primary.config(state='normal' if waiting else 'disabled',bg=BTN if waiting else BLUE);self.mirror_label.set('取消自动重连' if waiting else '一键 USB 连接');return
        serial,state,model=item;index=next(i for i,r in enumerate(self.devices) if r[0]==serial);name=self.cfg.value.get('notes',{}).get(serial,'')
        self.name_var.set(name or f'手机 {index+1:02d}');self.device_detail.set(model+'  ·  '+('USB 已连接' if state=='device' else '未授权 / '+state))
        p=self.backend.processes.get(serial);running=p is not None and p.poll() is None;self.primary.config(state='normal' if state=='device' or running else 'disabled',bg=RED if running else BLUE);self.mirror_label.set('■ 停止投屏' if running else '一键 USB 连接')
    def require(self):
        if not any(s==self.serial and state=='device' for s,state,_ in self.devices):messagebox.showwarning('设备不可用','请选择已授权的 USB 设备。',parent=self.root);return False
        return True
    def toggle_mirror(self):
        connected=any(s==self.serial and state=='device' for s,state,_ in self.devices)
        if not connected and self.want.get(self.serial):
            self.want.pop(self.serial,None);timer=self.retry_id.pop(self.serial,None)
            if timer:self.root.after_cancel(timer)
            self.update_device();self.set_status('自动重连已取消。');return
        p=self.backend.processes.get(self.serial)
        if p and p.poll() is None:
            self.want.pop(self.serial,None);self.stopped_by_user.add(self.serial);self.remember(self.serial);self.backend.stop(self.serial);return
        if not self.require():return
        self.save_settings();self.want[self.serial]=True;self.stopped_by_user.discard(self.serial);self.retry_count[self.serial]=0;self.backend.start(self.serial,self.cfg.value.copy());self.update_device()
    def double_click(self,event):
        p=self.backend.processes.get(self.serial)
        if p and p.poll() is None:self.show_mirror()
        else:self.toggle_mirror()
    def remember(self,serial):
        if not self.cfg.value.get('remember_window',True):return
        p=self.backend.processes.get(serial)
        if p and p.poll() is None:
            geo=bounds(p.pid)
            if geo and self.cfg.value.setdefault('geometry',{}).get(serial)!=geo:self.cfg.value['geometry'][serial]=geo;self.cfg.save()
    def snapshot(self):
        if self.closing:return
        for serial in list(self.backend.processes):self.remember(serial)
        self.root.after(1500,self.snapshot)
    def show_mirror(self):
        p=self.backend.processes.get(self.serial)
        if not p or p.poll() is not None or not show(p.pid):self.set_status('当前设备尚未启动投屏或窗口无法置前。')
    def reconnect(self):
        if not self.require():return
        serial=self.serial;self.want[serial]=True;self.retry_count[serial]=0;self.remember(serial);p=self.backend.processes.get(serial)
        if p and p.poll() is None:self.manual_reconnect.add(serial);self.backend.stop(serial);self.set_status('正在重新连接…')
        else:self.schedule_retry(serial,0,manual=True)
    def cancel_retries(self):
        for ident in list(self.retry_id.values()):self.root.after_cancel(ident)
        self.retry_id.clear()
    def schedule_retry(self,serial,delay=None,manual=False):
        if self.closing or serial in self.retry_id or not self.want.get(serial):return
        if not manual and not self.cfg.value.get('auto_reconnect',True):return
        count=self.retry_count.get(serial,0);wait=delay if delay is not None else min(30000,2000*(2**min(count,4)));self.retry_id[serial]=self.root.after(wait,lambda:self.retry(serial,manual))
    def retry(self,serial,manual=False):
        self.retry_id.pop(serial,None)
        if self.closing or not self.want.get(serial):return
        if not manual and not self.cfg.value.get('auto_reconnect',True):return
        if not any(s==serial and state=='device' for s,state,_ in self.devices):self.set_status('等待 USB 设备重新连接…');self.refresh_once();self.schedule_retry(serial,4000,manual);return
        p=self.backend.processes.get(serial)
        if p and p.poll() is None:return
        self.retry_count[serial]=self.retry_count.get(serial,0)+1;self.set_status('正在重新连接…');self.backend.start(serial,self.cfg.value.copy())
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
        self.save_settings()
        try:
            tasks=self.backend.file_batch(self.serial,files,self.directory.get().strip())
            if len(tasks)<len(files):messagebox.showwarning('队列已满',f'只添加了 {len(tasks)} 个文件；队列最多 128 项。',parent=self.root)
        except ValueError as e:messagebox.showwarning('路径无效',str(e),parent=self.root)
    def task_action(self,action):
        selected=self.tree.selection()
        if not selected:self.set_status('请先选择一个传输任务。');return
        getattr(self.backend.transfers,action)(selected[0])
    def pump(self):
        try:
            while True:name,args=self.backend.events.get_nowait();self.event(name,*args)
        except queue.Empty:pass
        if not self.closing:self.root.after(100,self.pump)
    def event(self,name,*args):
        if name=='devices':
            self.polling=False;rows=args[0]
            if rows!=self.devices:
                self.devices=rows;self.populate_devices()
            if not rows:self.set_status('未检测到 USB 设备。')
            for serial in list(self.want):
                p=self.backend.processes.get(serial)
                if (not p or p.poll() is not None) and any(s==serial and state=='device' for s,state,_ in rows):self.schedule_retry(serial,1000)
        elif name=='device_error':self.polling=False;self.set_status('ADB 检测失败：'+args[0])
        elif name=='mirror_started':self.update_device();self.set_status('正在启动投屏…')
        elif name=='mirror_stopped':
            serial,code=args;self.update_device()
            if serial in self.manual_reconnect:self.manual_reconnect.discard(serial);self.set_status('正在重新连接…');self.schedule_retry(serial,500,manual=True)
            elif serial in self.stopped_by_user:self.stopped_by_user.discard(serial);self.set_status('投屏已停止。')
            elif self.want.get(serial) and (code!=0 or not any(s==serial and state=='device' for s,state,_ in self.devices)):
                self.set_status('投屏中断，等待自动重连。');self.schedule_retry(serial)
            elif self.want.get(serial) and code==0:
                self.refresh_once();self.root.after(2000,lambda:self.confirm_normal_exit(serial))
            else:self.want.pop(serial,None);self.set_status('投屏已结束。')
        elif name=='mirror_log':
            if 'Texture' in args[1]:self.retry_count[args[0]]=0
            if 'ERROR' in args[1] or 'WARN' in args[1]:self.set_status(args[1])
        elif name=='task_added':
            task_id,path=args;self.tree.insert('', 'end',iid=task_id,values=(Path(path).name,'等待中','0%'))
        elif name=='task_state':
            task_id,state,done,total=args
            if self.tree.exists(task_id):self.tree.set(task_id,'state',state);self.tree.set(task_id,'progress',str(min(100,int(done*100/total)))+'%' if total else ('100%' if state=='已完成' else '0%'))
            self.set_status(state)
        elif name=='task_remove':
            if self.tree.exists(args[0]):self.tree.delete(args[0])
        elif name=='hotkey_image':
            try:
                image=capture()
                if image:self.backend.submit_image(args[0],*image)
                else:self.set_status('剪贴板图片已变化，请重试。')
            except Exception as e:self.set_status('读取剪贴板失败：'+str(e))
        elif name=='hotkey_error':self.set_status('图片快捷键错误：'+args[0])
        elif name=='image':self.set_status(args[1]);messagebox.showwarning('图片未提交',args[1],parent=self.root) if not args[0] else None
        elif name=='error':self.set_status(args[0]);messagebox.showwarning('操作失败',args[0],parent=self.root)
    def confirm_normal_exit(self,serial):
        if self.closing or not self.want.get(serial):return
        p=self.backend.processes.get(serial)
        if p and p.poll() is None:return
        if not any(s==serial and state=='device' for s,state,_ in self.devices) and self.cfg.value.get('auto_reconnect',True):
            self.set_status('USB 连接中断，等待设备重新连接。');self.schedule_retry(serial)
        else:self.want.pop(serial,None);self.set_status('投屏已结束。')
    def close(self):
        if self.backend.image_busy:messagebox.showinfo('请稍候','图片传输完成后再退出。',parent=self.root);return
        self.closing=True;self.cancel_retries()
        for serial in list(self.backend.processes):self.remember(serial)
        self.hook.stop();self.backend.close();self.set_status('正在结束传输并清理临时文件…');self.finish_close()
    def finish_close(self):
        if self.backend.transfers.worker.is_alive():self.root.after(100,self.finish_close)
        else:self.root.destroy()
    def run(self):self.root.mainloop()
