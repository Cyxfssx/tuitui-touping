import shlex, tempfile, threading, time, unittest
from pathlib import Path
from unittest.mock import patch
from tuitui_personal.transfers import TransferQueue

class FakeAdb:
    def __init__(self):self.files={};self.enter=threading.Event();self.release=threading.Event()
    def run(self,*args,timeout=None):
        args=list(args[2:])
        if args[0]=='push':
            data=Path(args[1]).read_bytes();self.files[args[2]]=data;self.enter.set()
            if not self.release.wait(5):raise TimeoutError('test gate timed out')
        elif args[0]=='shell':
            p=shlex.split(args[1])
            if p[0]=='mkdir':pass
            elif p[0]==':':self.files[p[-1]]=b''
            elif p[0]=='cat':self.files[p[-1]]+=self.files[p[1]]
            elif p[0]=='mv':self.files[p[-1]]=self.files.pop(p[-2])
            elif p[0]=='rm':
                for name in p[2:]:self.files.pop(name,None)
        return ''

def wait(predicate):
    until=time.monotonic()+5
    while time.monotonic()<until:
        if predicate():return True
        time.sleep(.01)
    return False

class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.source=Path(self.temp.name)/'my file.bin';self.source.write_bytes(b'abcdefghij');self.adb=FakeAdb();self.events=[];self.queue=TransferQueue(self.adb.run,shlex.quote,lambda *e:self.events.append(e));self.patch=patch('tuitui_personal.transfers.CHUNK',4);self.patch.start()
    def tearDown(self):
        self.adb.release.set();self.queue.close();self.queue.worker.join(5);self.patch.stop();self.temp.cleanup()
    def test_pause_resume_commits_exact_bytes(self):
        task=self.queue.add('device',[self.source],'/sdcard/Download')[0];self.assertTrue(self.adb.enter.wait(5));self.queue.pause(task.id);self.adb.release.set();self.assertTrue(wait(lambda:task.state=='已暂停'));self.assertEqual(task.committed,0)
        self.queue.resume(task.id);self.assertTrue(wait(lambda:task.state=='已完成'));self.assertEqual(self.adb.files['/sdcard/Download/my file.bin'],b'abcdefghij')
    def test_cancel_preserves_existing_destination(self):
        final='/sdcard/Download/my file.bin';self.adb.files[final]=b'existing'
        task=self.queue.add('device',[self.source],'/sdcard/Download')[0];self.assertTrue(self.adb.enter.wait(5));self.queue.pause(task.id);self.adb.release.set();self.assertTrue(wait(lambda:task.state=='已暂停'));self.queue.cancel(task.id)
        self.assertTrue(wait(lambda:task.state=='已取消'));self.assertEqual(self.adb.files[final],b'existing')
if __name__=='__main__':unittest.main()
