# 推推投屏 · 现代版

USB 安卓投屏桌面软件。每台设备独立启动/关闭投屏，列表和投屏窗口只显示备注名；图片 Ctrl+V 使用推推2输入法桥接。界面为 WebView2，本地渲染，不是网站。

## 使用已打包软件

解压完整 `TuiTuiScreenV2` 文件夹，双击 `TuiTuiScreenV2.exe`，不要只复制 EXE。电脑需要 64 位 Windows、Edge WebView2 Runtime 和手机 USB 驱动。开启手机 USB 调试并确认授权。旧版推推投屏不要同时运行，避免多个程序同时监听快捷键。

高级设置中可为所选手机安装 `assets/tuitui2.apk` 并打开手机输入法设置；必须在手机上启用并选择“推推2”。投屏窗口 Ctrl+V 的图片会交给支持输入法图片接口的聊天应用，是否显示预览取决于应用，程序不会自动发送消息。中文输入通过定制 scrcpy 的手机文字剪贴板上屏，会更新手机剪贴板。

配置和设备备注保存在 `%APPDATA%\TuiTuiPersonal`，软件包不包含个人配置。文件传输完成后会覆盖目标同名文件。逐项暂停/取消在当前 2 MiB 分块后生效，不支持应用重启后的断点续传。

## 源码和重新构建

- `tuitui_web/`、`tuitui_personal/` 是重建的 Windows 前端、设备管理、快捷键及文件传输源码。
- `tuitui-engine/` 是本软件需要的原定制投屏引擎和对应许可证；它是二进制，不是该定制版本的完整源码。原定制 scrcpy 源码及原 Windows 桌面桥接器源码尚未找回，不能仅凭本仓库完整重新编译它们。
- `assets/tuitui2.apk` 是推推2测试安装包，`assets/tuitui2-scanner.jar` 是适配后的图片桥接二进制。仓库另有 `recovered-source/` 中的输入法/桥接反编译参考代码、`warmime-rebuild/` 与 `.github/workflows/` 中的重打包脚本；反编译代码不等于完整原始源码。
- APK 目前使用测试签名。当前 APK 可供分发，但后续重新构建产生不同签名时，不能保证覆盖更新；正式发布前应建立并安全保管稳定的签名密钥，不要提交密钥到仓库。

Windows 安装 Python 3.12 和 Microsoft Edge WebView2 Runtime。执行：

```bat
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-webview.txt
.venv\Scripts\python -m pip install pyinstaller==6.22.3
powershell -NoProfile -ExecutionPolicy Bypass -File build-portable.ps1
```

本版已进行打包启动和基本设备读取检查，多设备监控和按设备操作已通过代码测试；多个真实手机、不同聊天应用及全部传输场景仍需要使用者测试。

