# 推推投屏 Qt 测试版

本项目是 PySide6 重建的桌面程序，不替换原推推投屏。Android 投屏使用 `scrcpy-win64-v5.0.1`，图片发送到推推2使用 `assets/tuitui2-scanner.jar`。手机端推推2 APK 是重新打包的测试版，并非可维护的完整手机端源码；相关重新构建过程在仓库 `warmime-rebuild`。图片桥接器的原始完整源码尚未恢复，对应修改脚本在仓库 `.github/workflows/tuitui2-bridge.yml`。

## 启动

Windows + Python 3.12：`python -m venv .venv`，`.venv\Scripts\python -m pip install -r requirements.txt`。保留原 `scrcpy-win64-v5.0.1` 目录和 `assets` 文件夹，双击 `启动推推投屏Qt.bat`。运行前先退出旧的推推投屏和它启动的桥接进程，避免快捷键或设备操作冲突。数据配置保存在 `%APPDATA%\ChatMirror`。

## 当前功能

- 自动读取 USB 设备、设备备注、单台和全部设备独立投屏、手动关闭时保存窗口位置、视频/音频参数、设备置顶设置。
- 普通文字使用 scrcpy 的键盘和文字剪贴板功能。Windows 中文/韩文输入可在文字辅助框选词、复制，再在投屏窗口粘贴；此版本尚未重建原桌面程序在投屏窗口内的输入法捕获。
- 在图片页提交剪贴板图片或文件：推推2的 InputConnection 把图片交给目标聊天应用，不自动发送；目标应用须支持图片输入。仅表示应用接受请求，不能保证实际显示。该操作不等同于投屏窗口 Ctrl+V 自动拦截。Ctrl+Shift+V 只在 Qt 主窗口获得焦点时可用。
- 文件多选上传、拖拽上传、共享存储浏览、下载单个文件、取消当前传输。进度仅显示 ADB 实际输出。重名文件可能被覆盖。
- 已有原版测试副本及其正在运行的投屏不会被新 Qt 程序管理或覆盖。

## 尚未完成

投屏窗口自动拦截 Ctrl+V 图片、原版中文直接输入方式、逐任务暂停/继续和队列状态、按设备分别设置目录与参数、批量文件分发、自动重连和窗口排列，以及打包后的真实手机多设备测试。请不要把此测试版当作原版完整替代品。

## EXE 打包

在 Windows 上安装 `pyinstaller`，执行 `.venv\Scripts\python -m PyInstaller --noconfirm --windowed --name TuituiQt main.py`。将 `scrcpy-win64-v5.0.1` 和 `assets` 目录复制到 `dist\TuituiQt` 下，与 EXE 一起分发。打包过程与产物尚未验证。
