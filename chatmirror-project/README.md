# ChatMirror

基于 scrcpy 5.0.1 的 USB 安卓投屏与文件管理工具。需要 Windows、Python 3.12、USB 调试及手机授权。

## 启动

项目已创建 `.venv`，双击 `start.bat`。重新安装：`py -3.12 -m venv .venv`，然后运行 `.venv\Scripts\python -m pip install -r requirements.txt`，最后运行 `.venv\Scripts\python main.py`。

## 使用说明

- 选择左侧设备，启动独立投屏。设置在下次启动时生效；从本软件关闭投屏或退出时保存窗口位置和大小。
- 文字输入框将完整 Unicode 文本复制到 Windows 剪贴板，在手机输入框按 Ctrl+V；可尝试左 Alt+V（scrcpy 默认 MOD+V）。目标应用和设备限制可能影响粘贴。UHID 需要在安卓系统配置物理键盘布局。不要使用模拟按键逐字输入 Unicode。
- 图片粘贴按钮（主窗口 Ctrl+Shift+V）将剪贴板图片存成 PNG 并上传；剪贴板为本地图片文件时保留原文件。它不是图片剪贴板同步或聊天应用原生粘贴。上传后可在聊天应用的文件/相册选择器选择。系统打开和分享使用 file URI，现代 Android 可能拒绝；请使用手动选择。不同设备的媒体库扫描结果可能不同。
- 文件管理支持多文件上传、取消、浏览 `/sdcard`、下载单个选中文件。ADB 的输出在底部显示；进度取决于 ADB 实际输出。仅处理文件，不递归拖拽目录。目标目录重名文件可能被覆盖。
- 配置与日志位于 `%APPDATA%\ChatMirror`；剪贴板图片临时文件位于其中的 `temp`，可以手动清理。
- 投屏窗口由 scrcpy 独立管理；辅助工具的快捷键只在主窗口有焦点时生效。scrcpy 自身快捷键请参阅 `scrcpy-help.txt`。窗口手动关闭时无法记录最终位置，请使用软件中的关闭按钮。

## 打包 EXE

在 Windows 上执行：

```bat
.venv\Scripts\python -m pip install pyinstaller
.venv\Scripts\python -m PyInstaller --noconfirm --windowed --name ChatMirror --collect-all PySide6 main.py
xcopy /E /I /Y scrcpy-win64-v5.0.1 dist\ChatMirror\scrcpy-win64-v5.0.1
```

把整个 `dist\ChatMirror` 文件夹一起分发，保留 scrcpy 子目录。不要仅复制 exe。引擎及其许可文件来自原目录。配置仍写入用户的 AppData。打包后应在目标 Windows 和真实手机上重新验证。
