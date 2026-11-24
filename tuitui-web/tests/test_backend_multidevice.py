import threading,time,unittest
from unittest.mock import patch
from tuitui_personal.backend import Backend,Config
class Stream:
 def __init__(self,done):self.done=done
 def __iter__(self):return self
 def __next__(self):self.done.wait(5);raise StopIteration
class Mirror:
 counter=0
 def __init__(self,args,**kwargs):
  type(self).counter+=1;self.pid=type(self).counter;self.args=args;self.done=threading.Event();self.stdout=Stream(self.done)
 def poll(self):return 0 if self.done.is_set() else None
 def wait(self):self.done.wait(5);return 0
 def terminate(self):self.done.set()
class MultiDeviceBackendTests(unittest.TestCase):
 def test_window_title_is_nickname_without_product_prefix(self):
  created=[]
  def make(*args,**kwargs):
   p=Mirror(*args,**kwargs);created.append(p);return p
  settings=Config.defaults.copy();settings['notes']={'serial-one':'KK4-手工'}
  with patch('tuitui_personal.backend.subprocess.Popen',side_effect=make):
   b=Backend()
   try:
    b.start('serial-one',settings);self.assertIn('--window-title=KK4-手工',created[0].args)
    self.assertFalse(any(x.startswith('--window-title=推推投屏') for x in created[0].args))
   finally:b.close()
 def test_active_mirror_monitors_do_not_block_device_refresh(self):
  with patch('tuitui_personal.backend.subprocess.Popen',Mirror),patch('tuitui_personal.backend.run',return_value='List of devices attached\nabc device model:Example\n'):
   b=Backend()
   try:
    for i in range(8):b.start('serial'+str(i),Config.defaults.copy())
    b.refresh();end=time.monotonic()+3;found=False
    while time.monotonic()<end:
     name,args=b.events.get(timeout=1)
     if name=='devices':found=True;self.assertEqual(args[0][0][0],'abc');break
    self.assertTrue(found,'device polling was blocked by mirror monitors')
   finally:b.close()
if __name__=='__main__':unittest.main()
