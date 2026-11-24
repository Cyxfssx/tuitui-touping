# 推推投屏 · 个人版（Windows 测试版）

这是在原桌面源码丢失后重新实现的单设备控制面板，使用 Python、Tk 和 tkinterdnd2，不依赖 Qt。它与原推推投屏分别运行，不修改原 EXE 和配置；两版不要同时使用图片快捷键。

## 启动

在 Windows 安装 Python 3.12，项目根目录执行：

```bat
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-native.txt
```

项目根目录需要 `tuitui-engine` 与 `assets/tuitui2-scanner.jar`。`tuitui-engine` 为原推推投屏安装包里的 `engine` 文件夹，不能用官方原版 scrcpy 替代：原版定制引擎提供 `--text-via-clipboard` 和 `--no-clipboard-images`。当前引擎及原 Windows 图片桥接器的完整源码尚未恢复。本机已配置好引擎与依赖，双击 `启动推推个人版.bat`。

## 操作

1. USB 连接手机并授权调试，在设备下拉框选择设备，点击“启动投屏”。
2. 使用推推2输入法（包名 `com.chatmirror.warmclone2`）。SDK 键盘模式的 Windows 输入法上屏会通过手机文字剪贴板完成；手机剪贴板会被更新。电脑复制图片后在个人版启动的投屏窗口按 Ctrl+V，目标应用若支持图片输入，则进入其预览；不自动发送。
3. 将文件拖到虚线区域或点击选择文件，立即上传到当前设备路径。ADB 可能覆盖目标目录中的同名文件。可取消当前及剩余队列。百分比只显示 ADB 实际输出。
4. 画面设置默认折叠。参数修改在下次启动投屏时生效；配置写入 `%APPDATA%\TuiTuiPersonal`，与原版隔离。

## 已验证和限制

- Windows 界面启动、设置展开与折叠通过检查；USB 真机投屏启动通过；测试文件上传到手机并比较内容通过。
- 在 SM-A376B、推推2及用户授权的测试聊天中，投屏窗口 Ctrl+V 测试图片已由聊天应用接受；不会自动发送消息。此结果不保证所有聊天应用支持图片输入。
- 当前设备卡显示的是配置目标帧率和码率，不是实时测量。视频解码状态尚未接入。
- 原桌面源码缺失，个人版是新实现，不能声称保留所有旧函数或回调；尚未实现原版的逐项暂停/继续、传输下载、自动重连、窗口位置记忆、录屏控制、设备重命名和多设备群控。卡片使用 Tk 的细边框，未实现精确 8px 圆角和真实磨砂。
- 推推2图片桥接器沿用已验证的适配二进制；当前仓库保留重建脚本但没有完整原生桌面源码。

## 代码

` tuitui_personal_main.py` 为入口；`tuitui_personal/ui.py` 负责界面，`backend.py` 负责 ADB、投屏和文件，`hotkeys.py` 负责投屏窗口图片快捷键，`requirements-native.txt` 列出依赖。请不要在日志里记录聊天内容。
