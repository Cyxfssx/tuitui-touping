# 从安装包恢复的参考代码

此目录是从用户提供的已编译安装包中用 JADX 1.5.7 反编译得到的参考材料，不是原始项目源码，也不是可直接构建的完整工程。反编译可能丢失变量名、注释、构建配置和逻辑，并可能生成不能编译的 Java；尚未编译或在设备上验证。

- `android-ime/`：从 `tuitui-ime-0.1.5-preview.apk` 恢复的输入法 Java、AndroidManifest 和资源，涉及文字输入、图片导入和分享。
- `android-bridge/`：从 Windows 安装包的 `engine/warm-transfer-scanner` 恢复的 `WarmImeBridge` 和对应编译器合成类。它依赖 scrcpy 的 Android 运行环境，单独不能编译。`warm-clipboard-scanner` 与它的 SHA-256 相同。
- Windows 控制窗口和 ClipboardBridge 是编译后的原生程序，不能从安装包直接恢复原有 C 源文件；此目录不含其实现。

若要获得完整、可维护的源码和可重现构建，请提供原先 Codex 使用的 Windows 项目目录（尤其是 `.c`、`.h`、构建脚本及 Android 项目文件）。此目录不包含 scrcpy 核心源码。
