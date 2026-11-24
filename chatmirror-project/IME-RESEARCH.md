# Windows 输入法与 Android 输入法接入：技术验证记录

## 已验证环境（2026-11-24）

- scrcpy 5.0.1；USB 设备 SM-A376B，Android API 36。
- 当前设备默认输入法为 `com.cyxfssx.warmime/.WarmInputMethodService`，版本 0.1.5-preview。未改变设备输入法或安装应用。
- 当前 PATH 未发现 Java、javac 或 Gradle，常见 Android SDK 路径未发现 SDK。尚未构建 Android 应用。
- scrcpy 默认文本注入受字符集限制；UHID 是 Android 端物理键盘，不等同 Windows 输入法。

## 拟验证方案

1. Windows 原生输入法捕获层需持有 Windows 文本输入焦点并接收 IME 组合和提交事件；不能假定外部 Qt 进程可以直接拦截属于 scrcpy/SDL 进程的输入法事件。必须先验证不嵌入 scrcpy 时的焦点、候选框定位、鼠标操作和普通快捷键转发。简单地放一个不可见输入框或全局键盘钩子不能保证 TSF/IME、所有按键和应用兼容。
2. 自建 Android InputMethodService 使用当前 InputConnection 的 commitText 提交已确认 Unicode 文本；需要显示用户授权、安装和选择输入法，且不能读取或记录输入文本。多设备分别建立 USB 本地通道，设计随机会话令牌、长度上限、超时、重连与确认，避免开放未经认证的远程输入接口。
3. 图片使用单独数据路径。支持时通过带临时读取授权的 content URI 和 commitContent 交给当前编辑器；编辑器须声明支持的 MIME 类型。拒绝或不支持时上传至共享存储并提示手动选择。返回成功仅表示提交被接受，不能当作消息已发送。
4. 验证矩阵：中文拼音、韩文组合、英文、换行、Emoji、输入法候选取消、Ctrl+C/X/V/A、退格和方向键、多个设备及切换焦点、截图剪贴板、浏览器图片与文件、支持与不支持 rich content 的应用。

本文件为设计和环境记录，不表示功能已实现或已真机通过。

参考：
- https://developer.android.com/reference/android/view/inputmethod/InputConnection#commitContent(android.view.inputmethod.InputContentInfo,%20int,%20android.os.Bundle)
- https://developer.android.com/develop/ui/views/touch-and-input/image-keyboard
- https://github.com/Genymobile/scrcpy/blob/master/FAQ.md
