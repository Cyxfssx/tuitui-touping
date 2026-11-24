import subprocess
from .config import ADB
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
def run(*args, timeout=15):
    return subprocess.run([ADB, *map(str,args)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, creationflags=CREATE_NO_WINDOW)
def shell(serial, *args): return run('-s', serial, 'shell', *args)
def devices():
    result = run('devices', '-l')
    if result.returncode: raise RuntimeError(result.stderr or result.stdout)
    found = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2 or ':' in parts[0] or parts[0].startswith('emulator-'): continue
        model = next((x[6:].replace('_',' ') for x in parts[2:] if x.startswith('model:')), '未知型号')
        found.append((parts[0], parts[1], model))
    return found
