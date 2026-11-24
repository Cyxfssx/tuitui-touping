import sys, logging
from PySide6.QtWidgets import QApplication, QMessageBox
from chatmirror.logging_setup import setup
from chatmirror.ui import MainWindow

def main():
    setup(); app=QApplication(sys.argv); app.setApplicationName('ChatMirror')
    def exception_hook(t,v,tb):
        logging.exception('未处理异常',exc_info=(t,v,tb)); QMessageBox.critical(None,'发生错误',str(v))
    sys.excepthook=exception_hook
    window=MainWindow(); window.show(); return app.exec()
if __name__=='__main__': sys.exit(main())
