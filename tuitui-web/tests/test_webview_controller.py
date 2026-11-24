import unittest
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
if __name__=='__main__':unittest.main()
