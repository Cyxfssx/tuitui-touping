from . import adb
# Android shell commands are passed as one quoted command because adb shell joins arguments.
def quote(s): return "'"+s.replace("'", "'\\''")+"'"
def open_app(serial, package): return adb.shell(serial, 'monkey', '-p', package, '-c', 'android.intent.category.LAUNCHER', '1')
def media_scan(serial,path): return adb.shell(serial, 'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d '+quote('file://'+path))
def open_image(serial,path):
    # file:// URIs may be rejected on newer Android versions; surface the error to the user.
    return adb.shell(serial, 'am start -a android.intent.action.VIEW -d '+quote('file://'+path)+' -t image/*')
def share_image(serial,path):
    return adb.shell(serial, 'am start -a android.intent.action.SEND -t image/* --eu android.intent.extra.STREAM '+quote('file://'+path)+' --grant-read-uri-permission')
