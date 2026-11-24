import pathlib, re
root = pathlib.Path('decoded')
manifest = root / 'AndroidManifest.xml'
s = manifest.read_text(encoding='utf-8')
s = s.replace('package="com.cyxfssx.warmime"', 'package="com.chatmirror.warmclone"')
s = s.replace('com.cyxfssx.warmime.images', 'com.chatmirror.warmclone.images')
s = s.replace('com.cyxfssx.warmime.picker', 'com.chatmirror.warmclone.picker')
manifest.write_text(s, encoding='utf-8')
strings = root / 'res/values/strings.xml'
s = strings.read_text(encoding='utf-8')
s, count = re.subn(r'(<string name="app_name">).*?(</string>)', r'\1ChatMirror 输入法\2', s)
if count != 1: raise RuntimeError('Could not identify app label')
strings.write_text(s, encoding='utf-8')
count = 0
for path in root.glob('smali*/**/*.smali'):
    text = path.read_text(encoding='utf-8')
    if 'com.cyxfssx.warmime.images' in text:
        text = text.replace('com.cyxfssx.warmime.images', 'com.chatmirror.warmclone.images')
        path.write_text(text, encoding='utf-8')
        count += 1
if not count: raise RuntimeError('Image provider authority not found in code')
print('Updated image authority in', count, 'files')
