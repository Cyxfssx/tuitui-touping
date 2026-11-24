package com.cyxfssx.warmime;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.CompoundButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

/* JADX INFO: loaded from: classes.dex */
public final class MainActivity extends Activity {
    private TextView status;

    private int dp(int i) {
        return Math.round(i * getResources().getDisplayMetrics().density);
    }

    private TextView text(LinearLayout linearLayout, String str, int i) {
        TextView textView = new TextView(this);
        textView.setText(str);
        textView.setTextSize(i);
        textView.setTextColor(-14077635);
        textView.setPadding(0, dp(10), 0, dp(10));
        linearLayout.addView(textView);
        return textView;
    }

    private void button(LinearLayout linearLayout, String str, View.OnClickListener onClickListener) {
        Button button = new Button(this);
        button.setText(str);
        button.setAllCaps(false);
        button.setOnClickListener(onClickListener);
        LinearLayout.LayoutParams layoutParams = new LinearLayout.LayoutParams(-1, dp(56));
        layoutParams.topMargin = dp(8);
        linearLayout.addView(button, layoutParams);
    }

    @Override // android.app.Activity
    public void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        ScrollView scrollView = new ScrollView(this);
        LinearLayout linearLayout = new LinearLayout(this);
        linearLayout.setOrientation(1);
        linearLayout.setPadding(dp(24), dp(20), dp(24), dp(28));
        scrollView.setBackgroundColor(-1808);
        scrollView.addView(linearLayout);
        setContentView(scrollView);
        scrollView.setOnApplyWindowInsetsListener(new View.OnApplyWindowInsetsListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda2
            @Override // android.view.View.OnApplyWindowInsetsListener
            public final WindowInsets onApplyWindowInsets(View view, WindowInsets windowInsets) {
                return MainActivity.lambda$onCreate$0(view, windowInsets);
            }
        });
        scrollView.requestApplyInsets();
        text(linearLayout, "推推输入法", 28);
        text(linearLayout, "无键盘面板 · 自动识别兼容版 0.1.5", 17);
        text(linearLayout, "电脑搜狗继续负责选词。本输入法不显示字母键盘。KakaoTalk 中粘贴文字后按 Enter 请求发送，Shift+Enter 换行；粘贴本身不发送。图片仍通过原通道进入预览。", 16);
        button(linearLayout, "1．打开系统设置，启用推推输入法", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda6
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m1lambda$onCreate$1$comcyxfssxwarmimeMainActivity(view);
            }
        });
        button(linearLayout, "2．切换到推推输入法", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda7
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m6lambda$onCreate$2$comcyxfssxwarmimeMainActivity(view);
            }
        });
        button(linearLayout, "3．选择一张图片做本机测试", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda8
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m7lambda$onCreate$3$comcyxfssxwarmimeMainActivity(view);
            }
        });
        text(linearLayout, "本机测试：选图后，在 60 秒内返回 KakaoTalk，点当前聊天输入框。只尝试插入一次。请先用测试图片观察应用是否出现预览。\n\n电脑 Ctrl+V：需要配套的独立图片桥接更新；仅安装 APK 不会自动接收到旧模块的图片。", 15);
        Switch r9 = new Switch(this);
        r9.setText("KakaoTalk：回车发送文字");
        r9.setTextSize(16.0f);
        r9.setPadding(0, dp(12), 0, dp(12));
        r9.setChecked(ImageStore.prefs(this).getBoolean("enter_send", true));
        r9.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda9
            @Override // android.widget.CompoundButton.OnCheckedChangeListener
            public final void onCheckedChanged(CompoundButton compoundButton, boolean z) {
                this.f$0.m8lambda$onCreate$4$comcyxfssxwarmimeMainActivity(compoundButton, z);
            }
        });
        linearLayout.addView(r9);
        text(linearLayout, "测试：回聊天点文字输入框，Ctrl+V 粘贴一句文字，再按 Enter。仅主动按回车才请求发送。声明为搜索、密码的输入框及其他应用保留原操作。请先在测试聊天验证；你已实测手动模式可发送；新增自动识别请先在一台手机上验证。", 15);
        Switch r10 = new Switch(this);
        r10.setText("自动识别已验证的 KakaoTalk 聊天框");
        r10.setTextSize(16.0f);
        r10.setPadding(0, dp(12), 0, dp(12));
        r10.setChecked(ImageStore.prefs(this).getBoolean("auto_chat", true));
        r10.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda10
            @Override // android.widget.CompoundButton.OnCheckedChangeListener
            public final void onCheckedChanged(CompoundButton compoundButton, boolean z) {
                this.f$0.m9lambda$onCreate$5$comcyxfssxwarmimeMainActivity(compoundButton, z);
            }
        });
        linearLayout.addView(r10);
        text(linearLayout, "匹配已验证版本时，进入聊天点输入框即可自动识别，无需每台手机手动校准。粘贴后主动按 Enter 才请求发送，Shift+Enter 换行。其他版本未匹配时，可用下方手动识别。", 15);
        button(linearLayout, "手动识别（自动未匹配时使用）", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda11
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m10lambda$onCreate$6$comcyxfssxwarmimeMainActivity(view);
            }
        });
        button(linearLayout, "清除手动识别记录", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda12
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m11lambda$onCreate$7$comcyxfssxwarmimeMainActivity(view);
            }
        });
        this.status = text(linearLayout, "", 15);
        button(linearLayout, "刷新测试结果", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda13
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m12lambda$onCreate$8$comcyxfssxwarmimeMainActivity(view);
            }
        });
        button(linearLayout, "复制测试信息", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda14
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m13lambda$onCreate$9$comcyxfssxwarmimeMainActivity(view);
            }
        });
        button(linearLayout, "切回三星／其他输入法", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda3
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m2lambda$onCreate$10$comcyxfssxwarmimeMainActivity(view);
            }
        });
        button(linearLayout, "清理本机图片缓存", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda4
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m4lambda$onCreate$12$comcyxfssxwarmimeMainActivity(view);
            }
        });
        button(linearLayout, "赞助联系 @lailai995", new View.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda5
            @Override // android.view.View.OnClickListener
            public final void onClick(View view) {
                this.f$0.m5lambda$onCreate$13$comcyxfssxwarmimeMainActivity(view);
            }
        });
        text(linearLayout, "本应用没有联网权限。不记录聊天文字。图片只缓存在本机，按你的操作提供给当前应用。\n若应用不接受标准图片接口，需要根据测试结果继续适配，当前不保证出现预览。", 14);
    }

    static /* synthetic */ WindowInsets lambda$onCreate$0(View view, WindowInsets windowInsets) {
        view.setPadding(0, windowInsets.getSystemWindowInsetTop(), 0, windowInsets.getSystemWindowInsetBottom());
        return windowInsets;
    }

    /* JADX INFO: renamed from: lambda$onCreate$1$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m1lambda$onCreate$1$comcyxfssxwarmimeMainActivity(View view) {
        startActivity(new Intent("android.settings.INPUT_METHOD_SETTINGS"));
    }

    /* JADX INFO: renamed from: lambda$onCreate$2$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m6lambda$onCreate$2$comcyxfssxwarmimeMainActivity(View view) {
        ((InputMethodManager) getSystemService("input_method")).showInputMethodPicker();
    }

    /* JADX INFO: renamed from: lambda$onCreate$3$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m7lambda$onCreate$3$comcyxfssxwarmimeMainActivity(View view) {
        Intent intent = new Intent(this, (Class<?>) PickImageActivity.class);
        intent.addFlags(268435456);
        startActivity(intent);
    }

    /* JADX INFO: renamed from: lambda$onCreate$4$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m8lambda$onCreate$4$comcyxfssxwarmimeMainActivity(CompoundButton compoundButton, boolean z) {
        ImageStore.prefs(this).edit().putBoolean("enter_send", z).apply();
    }

    /* JADX INFO: renamed from: lambda$onCreate$5$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m9lambda$onCreate$5$comcyxfssxwarmimeMainActivity(CompoundButton compoundButton, boolean z) {
        ImageStore.prefs(this).edit().putBoolean("auto_chat", z).apply();
    }

    /* JADX INFO: renamed from: lambda$onCreate$6$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m10lambda$onCreate$6$comcyxfssxwarmimeMainActivity(View view) {
        confirmChat();
    }

    /* JADX INFO: renamed from: lambda$onCreate$7$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m11lambda$onCreate$7$comcyxfssxwarmimeMainActivity(View view) {
        ImageStore.prefs(this).edit().remove("chat_confirmed").remove("chat_pending_until").apply();
        Toast.makeText(this, "已清除手动记录，自动识别开关不受影响", 0).show();
        refresh();
    }

    /* JADX INFO: renamed from: lambda$onCreate$8$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m12lambda$onCreate$8$comcyxfssxwarmimeMainActivity(View view) {
        refresh();
    }

    /* JADX INFO: renamed from: lambda$onCreate$9$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m13lambda$onCreate$9$comcyxfssxwarmimeMainActivity(View view) {
        ((ClipboardManager) getSystemService("clipboard")).setPrimaryClip(ClipData.newPlainText("推推输入法测试", report()));
        Toast.makeText(this, "已复制测试信息，不包含聊天文字或图片", 0).show();
    }

    /* JADX INFO: renamed from: lambda$onCreate$10$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m2lambda$onCreate$10$comcyxfssxwarmimeMainActivity(View view) {
        ((InputMethodManager) getSystemService("input_method")).showInputMethodPicker();
    }

    /* JADX INFO: renamed from: lambda$onCreate$11$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m3lambda$onCreate$11$comcyxfssxwarmimeMainActivity(DialogInterface dialogInterface, int i) {
        try {
            ImageStore.clear(this);
            refresh();
        } catch (Exception e) {
            this.status.setText(e.getMessage());
        }
    }

    /* JADX INFO: renamed from: lambda$onCreate$12$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m4lambda$onCreate$12$comcyxfssxwarmimeMainActivity(View view) {
        new AlertDialog.Builder(this).setMessage("请先完成当前待发送图片。清理后，尚未读取图片的预览可能失效。是否清理？").setPositiveButton("清理", new DialogInterface.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda1
            @Override // android.content.DialogInterface.OnClickListener
            public final void onClick(DialogInterface dialogInterface, int i) {
                this.f$0.m3lambda$onCreate$11$comcyxfssxwarmimeMainActivity(dialogInterface, i);
            }
        }).setNegativeButton("取消", (DialogInterface.OnClickListener) null).show();
    }

    /* JADX INFO: renamed from: lambda$onCreate$13$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m5lambda$onCreate$13$comcyxfssxwarmimeMainActivity(View view) {
        openSponsor();
    }

    private void openSponsor() {
        try {
            startActivity(new Intent("android.intent.action.VIEW", Uri.parse("tg://resolve?domain=lailai995")));
        } catch (ActivityNotFoundException | SecurityException e) {
            try {
                startActivity(new Intent("android.intent.action.VIEW", Uri.parse("https://t.me/lailai995")));
            } catch (ActivityNotFoundException | SecurityException e2) {
                Toast.makeText(this, "无法打开 Telegram，请在 Telegram 搜索 @lailai995", 1).show();
            }
        }
    }

    private void confirmChat() {
        final SharedPreferences sharedPreferencesPrefs = ImageStore.prefs(this);
        if (System.currentTimeMillis() - sharedPreferencesPrefs.getLong("kakao_editor_seen", 0L) > 300000) {
            Toast.makeText(this, "请先回 KakaoTalk 点聊天输入框，再返回识别", 1).show();
            return;
        }
        final int i = sharedPreferencesPrefs.getInt("kakao_type", 0);
        final int i2 = sharedPreferencesPrefs.getInt("kakao_options", 0);
        final int i3 = sharedPreferencesPrefs.getInt("kakao_field", 0);
        if (EnterRouter.mayConfirm(i, i2)) {
            new AlertDialog.Builder(this).setMessage("确认刚才点的是 KakaoTalk 聊天文字输入框？识别后，该字段普通回车将请求发送，Shift+Enter 换行；不会立即发送。").setNegativeButton("取消", (DialogInterface.OnClickListener) null).setPositiveButton("确认聊天框", new DialogInterface.OnClickListener() { // from class: com.cyxfssx.warmime.MainActivity$$ExternalSyntheticLambda0
                @Override // android.content.DialogInterface.OnClickListener
                public final void onClick(DialogInterface dialogInterface, int i4) {
                    this.f$0.m0lambda$confirmChat$14$comcyxfssxwarmimeMainActivity(sharedPreferencesPrefs, i3, i, i2, dialogInterface, i4);
                }
            }).show();
        } else {
            Toast.makeText(this, "该字段不符合文字聊天条件，请复制测试信息反馈", 1).show();
        }
    }

    /* JADX INFO: renamed from: lambda$confirmChat$14$com-cyxfssx-warmime-MainActivity, reason: not valid java name */
    /* synthetic */ void m0lambda$confirmChat$14$comcyxfssxwarmimeMainActivity(SharedPreferences sharedPreferences, int i, int i2, int i3, DialogInterface dialogInterface, int i4) {
        sharedPreferences.edit().putBoolean("chat_confirmed", true).putInt("chat_field", i).putInt("chat_type", i2).putInt("chat_options", i3).putLong("chat_pending_until", System.currentTimeMillis() + 60000).apply();
        Toast.makeText(this, i <= 0 ? "请在60秒内回刚才聊天；本次焦点有效" : "已识别，请返回刚才的聊天测试回车", 1).show();
        refresh();
    }

    private static String hex(int i) {
        return "0x" + Integer.toHexString(i);
    }

    private String report() {
        SharedPreferences sharedPreferencesPrefs = ImageStore.prefs(this);
        return "推推输入法 0.1.5-preview\nAndroid API: " + Build.VERSION.SDK_INT + "\n已选中: " + WarmInputMethodService.selected(this) + "\n当前/最近输入应用（非回车快照）: " + sharedPreferencesPrefs.getString("editor_package", "尚未检测") + "\n回车时应用: " + sharedPreferencesPrefs.getString("enter_package", "尚未捕获") + "\n回车时连接: " + sharedPreferencesPrefs.getBoolean("enter_connection", false) + " / 输入法选中=" + sharedPreferencesPrefs.getBoolean("enter_selected_at_key", false) + " / 开关=" + sharedPreferencesPrefs.getBoolean("enter_switch_at_key", false) + "\n回车时类型: " + hex(sharedPreferencesPrefs.getInt("enter_input_type", 0)) + " / variation=" + hex(sharedPreferencesPrefs.getInt("enter_input_type", 0) & 4080) + "\n回车时imeOptions: " + hex(sharedPreferencesPrefs.getInt("enter_ime_options", 0)) + " / action=" + (sharedPreferencesPrefs.getInt("enter_ime_options", 0) & 255) + "\n回车时fieldId: " + hex(sharedPreferencesPrefs.getInt("enter_field", 0)) + "\n回车修饰键: " + hex(sharedPreferencesPrefs.getInt("enter_meta", 0)) + " / repeat=" + sharedPreferencesPrefs.getInt("enter_repeat", 0) + "\n已检查选词: " + sharedPreferencesPrefs.getBoolean("enter_composition_checked", false) + " / composing=" + sharedPreferencesPrefs.getBoolean("enter_composing", false) + "\n回车时聊天框已识别: " + sharedPreferencesPrefs.getBoolean("enter_confirmed", false) + " / 识别方式=" + sharedPreferencesPrefs.getString("enter_recognition", "尚未测试") + "\n自动识别开关: " + sharedPreferencesPrefs.getBoolean("auto_chat", true) + "\n最近路由: " + sharedPreferencesPrefs.getString("enter_mode", "无") + " / 原因: " + sharedPreferencesPrefs.getString("enter_reason", "未测试") + "\n图片预览保护: " + sharedPreferencesPrefs.getBoolean("enter_image_guard", false) + "\n回车发送开关: " + sharedPreferencesPrefs.getBoolean("enter_send", true) + "\n回车结果: " + sharedPreferencesPrefs.getString("enter_result", "尚未捕获") + "\n回车说明: " + sharedPreferencesPrefs.getString("enter_detail", "请测试") + "\n最近Kakao字段: " + hex(sharedPreferencesPrefs.getInt("kakao_field", 0)) + " / type=" + hex(sharedPreferencesPrefs.getInt("kakao_type", 0)) + " / action=" + (sharedPreferencesPrefs.getInt("kakao_options", 0) & 255) + "\n聊天框校准保存: " + sharedPreferencesPrefs.getBoolean("chat_confirmed", false) + "\n图片结果: " + sharedPreferencesPrefs.getString("last_result", "尚未测试") + "\n图片说明: " + sharedPreferencesPrefs.getString("last_detail", "无");
    }

    private void refresh() {
        this.status.setText(report());
    }

    @Override // android.app.Activity
    protected void onResume() {
        super.onResume();
        if (this.status != null) {
            refresh();
        }
    }
}
