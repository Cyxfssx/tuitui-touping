import tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl
from .config import DATA
IMAGE_EXTS={'.png','.jpg','.jpeg','.webp','.bmp'}
def clipboard_image():
    mime=QApplication.clipboard().mimeData()
    if mime.hasUrls():
        for url in mime.urls():
            p=Path(url.toLocalFile())
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS: return str(p)
    image=QApplication.clipboard().image()
    if image.isNull(): raise ValueError('剪贴板中没有可用图片')
    folder=DATA/'temp'; folder.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='clipboard_',suffix='.png',dir=folder,delete=False) as f: path=f.name
    if not image.save(path,'PNG'): raise ValueError('无法保存剪贴板图片')
    return path
def copy_text(text): QApplication.clipboard().setText(text)
