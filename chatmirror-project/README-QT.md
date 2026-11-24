# 推推投屏 Qt 测试版

本项目是 PySide6 重建的桌面程序，不替换原推推投屏。Android 投屏使用 `tuitui-engine`，图片发送到推推2使用 `assets/tuitui2-scanner.jar`。手机端推推2 APK 是重新打包的测试版，并非可维护的完整手机端源码；相关重新构建过程在仓库 `warmime-rebuild`。图片桥接器的原始完整源码尚未恢复，对应修改脚本在仓库 `.github/workflows/tuitui2-bridge.yml`。

## 启动

Windows + Python 3.12：`python -m venv .venv`，`.venv\Scripts\python -m pip install -r requirements.txt`。保留原 `tuitui-engine` 目录和 `assets` 文件夹，双击 `启动推推投屏Qt.bat`。运行前先退出旧的推推投屏和它启动的桥接进程，避免快捷键或设备操作冲突。数据配置保存在 `%APPDATA%\ChatMirror`。

## 当前功能

- 自动读取 USB 设备、设备备注、单台和全部设备独立投屏、手动关闭时保存窗口位置、视频/音频参数、设备置顶设置。
- SDK 键盘模式使用原推推投屏定制的 `--text-via-clipboard`：Windows 输入法在投屏窗口上屏后，通过手机文字剪贴板写入输入框。输入时会更新手机剪贴板；目标应用和手机系统可能影响结果。
- 在图片页提交剪贴板图片或文件：推推2的 InputConnection 把图片交给目标聊天应用，不自动发送；目标应用须支持图片输入。仅表示应用接受请求，不能保证实际显示。Qt 版监听本程序启动的投屏窗口中的 Ctrl+V；剪贴板有图片时提交给该窗口对应的手机。只有文字时继续交给 scrcpy。Ctrl+Shift+V 只在 Qt 主窗口获得焦点时可用。
- 文件多选上传、拖拽上传、共享存储浏览、下载单个文件、取消当前传输。进度仅显示 ADB 实际输出。重名文件可能被覆盖。
- 已有原版测试副本及其正在运行的投屏不会被新 Qt 程序管理或覆盖。

## 尚未完成

投屏窗口图片快捷键和 Windows 输入法尚待真机完整验证；逐任务暂停/继续和队列状态、按设备分别设置目录与参数、批量文件分发、自动重连和窗口排列，以及打包后的真实手机多设备测试。请不要把此测试版当作原版完整替代品。

## EXE 打包

在 Windows 上安装 `pyinstaller`，执行 `.venv\Scripts\python -m PyInstaller --noconfirm --windowed --name TuituiQt main.py`。将 `tuitui-engine` 和 `assets` 目录复制到 `dist\TuituiQt` 下，与 EXE 一起分发。打包过程与产物尚未验证。

## 定制投屏引擎

桌面端使用随原推推投屏分发的定制 scrcpy，引擎位于原安装包的 `engine` 文件夹。将该文件夹完整复制到本项目并改名为 `tuitui-engine`。这套引擎提供 `--text-via-clipboard` 和 `--no-clipboard-images`；仓库未恢复其对应的 C/SDL 源码，因此不能将它描述为已完整重建的开源部分。Qt 自己的图片快捷键源码在 `chatmirror/hotkeys.py`，图片通道在 `chatmirror/image_bridge.py`。
