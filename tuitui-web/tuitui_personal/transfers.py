"""Sequential, per-item pausable transfers. Pause applies at chunk boundaries."""
import os, queue, secrets, tempfile, threading
from dataclasses import dataclass, field
from pathlib import Path

CHUNK=2*1024*1024
@dataclass
class Task:
    id: str
    serial: str
    source: Path
    directory: str
    state: str='等待中'
    paused: bool=False
    cancelled: bool=False
    committed: int=0
    total: int=0
    condition: threading.Condition=field(default_factory=threading.Condition)

class TransferQueue:
    def __init__(self,run,quote,emit):
        self.run=run;self.quote=quote;self.emit=emit;self.tasks={};self.pending=queue.Queue();self.closed=False
        self.worker=threading.Thread(target=self._loop,name='transfer-queue',daemon=True);self.worker.start()
    def add(self,serial,paths,directory):
        if (directory!='/sdcard' and not directory.startswith('/sdcard/')) or any(p in ('.','..') for p in directory.split('/')) or '\x00' in directory:raise ValueError('保存路径必须位于 /sdcard 下。')
        result=[]
        for path in paths:
            if len(self.tasks)>=128:break
            task=Task(secrets.token_hex(12),serial,Path(path),directory.rstrip('/'));self.tasks[task.id]=task;result.append(task)
            self.emit('task_added',task.id,str(task.source));self.pending.put(task)
        return result
    def _state(self,task,state):
        task.state=state;self.emit('task_state',task.id,state,task.committed,task.total)
    def pause(self,task_id):
        task=self.tasks.get(task_id)
        if task and task.state not in ('已完成','已取消') and not task.state.startswith('失败'):
            with task.condition:task.paused=True
            self._state(task,'暂停中（等待当前分块）' if task.state=='传输中' else '已暂停')
    def resume(self,task_id):
        task=self.tasks.get(task_id)
        if task:
            with task.condition:task.paused=False;task.condition.notify_all()
            if task.state in ('已暂停','暂停中（等待当前分块）'):self._state(task,'等待中')
    def cancel(self,task_id):
        task=self.tasks.get(task_id)
        if task and task.state not in ('已完成','已取消') and not task.state.startswith('失败'):
            with task.condition:task.cancelled=True;task.paused=False;task.condition.notify_all()
            self._state(task,'正在取消')
    def clear_finished(self):
        for key,task in list(self.tasks.items()):
            if task.state in ('已完成','已取消') or task.state.startswith('失败'):
                self.tasks.pop(key,None);self.emit('task_remove',key)
    def _wait(self,task):
        with task.condition:
            while task.paused and not task.cancelled and not self.closed:
                if task.state!='已暂停':self._state(task,'已暂停')
                task.condition.wait(timeout=1)
            if self.closed or task.cancelled:raise InterruptedError('已取消')
    def _loop(self):
        while True:
            task=self.pending.get()
            if task is None:return
            self._transfer(task)
    def _adb(self,task,*args,timeout=120):return self.run('-s',task.serial,*args,timeout=timeout)
    def _transfer(self,task):
        marker=task.id;part=task.directory+'/.tuitui-'+marker+'.part';chunk='/data/local/tmp/tuitui-'+marker+'.chunk'; final=task.directory+'/'+task.source.name;remote_started=False
        try:
            self._wait(task)
            if not task.source.is_file():raise ValueError('文件不存在或不是普通文件')
            initial=task.source.stat();task.total=initial.st_size
            self._adb(task,'shell','mkdir -p '+self.quote(task.directory))
            remote_started=True;self._adb(task,'shell',': > '+self.quote(part))
            with task.source.open('rb') as source, tempfile.TemporaryDirectory(prefix='tuitui-transfer-') as tmp:
                chunk_file=Path(tmp)/'chunk'
                while True:
                    self._wait(task)
                    if task.source.stat().st_size!=initial.st_size or task.source.stat().st_mtime_ns!=initial.st_mtime_ns:raise ValueError('本地文件在传输期间被修改')
                    data=source.read(CHUNK)
                    if not data:break
                    self._state(task,'传输中');chunk_file.write_bytes(data)
                    self._adb(task,'push',str(chunk_file),chunk)
                    self._wait(task)
                    self._adb(task,'shell','cat '+self.quote(chunk)+' >> '+self.quote(part))
                    task.committed+=len(data);self._state(task,'传输中')
                self._wait(task)
                if task.committed!=task.total:raise ValueError('文件大小不一致')
                self._adb(task,'shell','mv -f '+self.quote(part)+' '+self.quote(final))
            self._state(task,'已完成')
        except InterruptedError:self._state(task,'已取消')
        except Exception as e:self._state(task,'失败：'+str(e)[:150])
        finally:
            if remote_started:
                try:self._adb(task,'shell','rm -f '+self.quote(chunk)+' '+self.quote(part),timeout=8)
                except Exception:pass
            self.emit('task_done',task.id)
    def close(self):
        self.closed=True
        for task in list(self.tasks.values()):
            with task.condition:task.cancelled=True;task.paused=False;task.condition.notify_all()
        self.pending.put(None)
