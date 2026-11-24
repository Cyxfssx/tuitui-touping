import unittest
from unittest.mock import Mock,patch
from tuitui_web.controller import Controller
class ConfigStub:
 def __init__(self):self.value={'text':True,'directory':'/sdcard/Download','auto_reconnect':True}
 def save(self):pass
class ControllerTests(unittest.TestCase):
 def setUp(self):self.c=Controller();self.c._config=ConfigStub()
 def tearDown(self):self.c._close()
 def test_invalid_setting_is_atomic(self):
  with self.assertRaises(ValueError):self.c.settings({'text':False,'fps':999})
  self.assertTrue(self.c._config.value['text'])
 def test_parent_directory_rejected(self):
  with self.assertRaises(ValueError):self.c.settings({'directory':'/sdcard/../data'})
  with self.assertRaises(ValueError):self.c._backend.transfers.add('device',[],'/sdcard/../data')
 def test_settings_can_be_updated(self):
  self.c.settings({'text':False,'size':1920,'fps':30});self.assertFalse(self.c._config.value['text']);self.assertEqual(self.c._config.value['size'],1920)
class MultiDeviceTests(unittest.TestCase):
 def setUp(self):
  self.c=Controller();self.c._config=ConfigStub();self.c._devices=[('serial-one','device','型号 A'),('serial-two','device','型号 B')];self.c._backend.start=Mock()
 def tearDown(self):self.c._close()
 def test_each_device_start_is_targeted_and_uses_display_name(self):
  self.c.toggle_device('serial-two');self.assertEqual(self.c._selected,'serial-two');args=self.c._backend.start.call_args.args;self.assertEqual(args[0],'serial-two');self.assertEqual(args[1]['notes']['serial-two'],'手机 02 · 型号 B')
 def test_renaming_running_window_uses_only_the_nickname(self):
  self.c._selected='serial-one';process=Mock();process.pid=12345;process.poll.return_value=None;self.c._backend.processes['serial-one']=process
  with patch('tuitui_web.controller.set_title',return_value=True) as title:
   self.c.rename('我的手机');title.assert_called_once_with(12345,'我的手机')
  self.c._backend.processes.clear()
if __name__=='__main__':unittest.main()
