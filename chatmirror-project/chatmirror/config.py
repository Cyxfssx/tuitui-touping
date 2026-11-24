import json, os, sys
from pathlib import Path
ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
ENGINE = ROOT / 'tuitui-engine'
ADB = str(ENGINE / 'adb.exe')
SCRCPY = str(ENGINE / 'scrcpy.exe')
DATA = Path(os.getenv('APPDATA', str(ROOT))) / 'ChatMirror'
DATA.mkdir(parents=True, exist_ok=True)
class Config:
    def __init__(self):
        self.path = DATA / 'config.json'
        try: self.data = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError): self.data = {}
    def save(self): self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding='utf-8')
    def get(self, key, default=None): return self.data.get(key, default)
    def set(self, key, value): self.data[key] = value; self.save()

