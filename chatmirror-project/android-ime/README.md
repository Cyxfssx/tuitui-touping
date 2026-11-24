# ChatMirror Android 输入法（开发中）

此目录包含 Android 输入法源码，尚未构建或完成真机验证。它使用 Android InputConnection 提交 Windows 辅助输入框中确认后的文字，不会发送聊天消息；图片仍使用桌面端独立上传功能。

## 构建

需要 JDK 17、Gradle 8.7、Android SDK Platform 35 和 Build Tools（由 Android Gradle Plugin 安装），并设置 `ANDROID_HOME`。在本目录运行：

```powershell
gradle assembleDebug
```

生成 `app/build/outputs/apk/debug/app-debug.apk`。在桌面应用中选择设备，点击“安装手机输入法”和“打开手机输入法设置”，在手机上启用并选择 ChatMirror 输入法。点击目标聊天输入框，回到桌面输入框输入文字并点击提交。测试完可在手机设置中恢复原来的输入法。

## 安全及限制

Android 输入法服务运行时注册动态广播接收器，要求发送方具有 `android.permission.DUMP`；已连接设备的 shell 持有此权限。它不监听网络、不保存文字，非已授权 ADB 不应具备发送该广播的权限。ADB 命令行参数包含 Base64 编码的文字，并非加密，同一电脑上有权限检查进程命令行的程序可能读取；请勿输入密码或敏感信息。成功结果仅代表编辑器接受了提交，不代表用户已发送消息。每次不超过 6000 UTF-8 字节。输入法、广播限制及富内容兼容性需在真实设备上验证。
