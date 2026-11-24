package com.cyxfssx.warmime;

import android.content.ClipDescription;
import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.inputmethodservice.InputMethodService;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.provider.Settings;
import android.text.Spanned;
import android.text.TextUtils;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputConnection;
import android.view.inputmethod.InputContentInfo;
import android.widget.Toast;
import java.io.IOException;
import java.util.HashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/* JADX INFO: loaded from: classes.dex */
public final class WarmInputMethodService extends InputMethodService {
    private static volatile WarmInputMethodService instance;
    private boolean confirmedChatSession;
    private EditorInfo editor;
    private boolean imageEditorLeft;
    private int imageField;
    private boolean imageGuard;
    private long session;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final HashMap<String, Arm> arms = new HashMap<>();
    private final EnterRouter enterRouter = new EnterRouter();

    private String chatRecognition() {
        if (this.editor == null || !"com.kakao.talk".equals(this.editor.packageName)) {
            return "none";
        }
        SharedPreferences sharedPreferencesPrefs = ImageStore.prefs(this);
        if (sharedPreferencesPrefs.getBoolean("auto_chat", true) && EnterRouter.knownKakaoChat(this.editor.packageName, this.editor.fieldId, this.editor.inputType, this.editor.imeOptions)) {
            return "auto_verified";
        }
        if (this.confirmedChatSession) {
            return "manual_session";
        }
        return (sharedPreferencesPrefs.getBoolean("chat_confirmed", false) && EnterRouter.sameConfirmedEditor(this.editor.fieldId, this.editor.inputType, this.editor.imeOptions, sharedPreferencesPrefs.getInt("chat_field", 0), sharedPreferencesPrefs.getInt("chat_type", 0), sharedPreferencesPrefs.getInt("chat_options", 0))) ? "manual_saved" : "none";
    }

    private static boolean enterKey(int i) {
        return i == 66 || i == 160;
    }

    /* JADX INFO: Access modifiers changed from: private */
    public void enterResult(String str, String str2) {
        ImageStore.prefs(this).edit().putString("enter_result", str).putString("enter_detail", str2).apply();
    }

    private static boolean composing(CharSequence charSequence) {
        if (!(charSequence instanceof Spanned)) {
            return false;
        }
        Spanned spanned = (Spanned) charSequence;
        for (Object obj : spanned.getSpans(0, spanned.length(), Object.class)) {
            if ((spanned.getSpanFlags(obj) & 256) != 0) {
                return true;
            }
        }
        return false;
    }

    private static boolean hasText(CharSequence charSequence) {
        if (charSequence == null) {
            return false;
        }
        for (int i = 0; i < charSequence.length(); i++) {
            if (!Character.isWhitespace(charSequence.charAt(i)) && charSequence.charAt(i) != 65532) {
                return true;
            }
        }
        return false;
    }

    @Override // android.inputmethodservice.InputMethodService, android.view.KeyEvent.Callback
    public boolean onKeyDown(int i, KeyEvent keyEvent) {
        CharSequence charSequence;
        CharSequence textAfterCursor;
        String str;
        String str2;
        CharSequence textBeforeCursor;
        if (!enterKey(i)) {
            return super.onKeyDown(i, keyEvent);
        }
        final InputConnection currentInputConnection = getCurrentInputConnection();
        boolean zSelected = selected(this);
        boolean z = ImageStore.prefs(this).getBoolean("enter_send", true);
        boolean z2 = currentInputConnection != null && zSelected && z;
        boolean z3 = keyEvent.isCtrlPressed() || keyEvent.isAltPressed() || keyEvent.isMetaPressed() || keyEvent.isSymPressed() || keyEvent.isFunctionPressed();
        CharSequence selectedText = null;
        String str3 = this.editor == null ? null : this.editor.packageName;
        int i2 = this.editor == null ? 0 : this.editor.inputType;
        int i3 = this.editor == null ? 0 : this.editor.imeOptions;
        String strChatRecognition = chatRecognition();
        boolean z4 = !"none".equals(strChatRecognition);
        EnterRouter.Mode mode = EnterRouter.mode(str3, i2, i3, z2, keyEvent.isShiftPressed(), z3, false, this.imageGuard, true, z4);
        if (mode == EnterRouter.Mode.PASS) {
            charSequence = null;
            textAfterCursor = null;
        } else {
            try {
                textBeforeCursor = currentInputConnection.getTextBeforeCursor(4096, 1);
                try {
                    textAfterCursor = currentInputConnection.getTextAfterCursor(4096, 1);
                    try {
                        selectedText = currentInputConnection.getSelectedText(1);
                    } catch (RuntimeException e) {
                    }
                } catch (RuntimeException e2) {
                    textAfterCursor = null;
                }
            } catch (RuntimeException e3) {
                textBeforeCursor = null;
                textAfterCursor = null;
            }
            charSequence = selectedText;
            selectedText = textBeforeCursor;
        }
        boolean z5 = composing(selectedText) || composing(textAfterCursor) || composing(charSequence);
        EnterRouter.Mode mode2 = EnterRouter.mode(str3, i2, i3, z2, keyEvent.isShiftPressed(), z3, z5, this.imageGuard, hasText(selectedText) || hasText(textAfterCursor) || hasText(charSequence), z4);
        boolean z6 = z3;
        boolean z7 = z5;
        String strReason = EnterRouter.reason(str3, i2, i3, z2, z6, z7, this.imageGuard, z4);
        if (!z2) {
            if (currentInputConnection == null) {
                str2 = "no_input_connection";
            } else {
                str2 = !zSelected ? "ime_not_selected" : "switch_disabled";
            }
            strReason = str2;
        }
        if ("com.kakao.talk".equals(str3)) {
            str = strReason;
            ImageStore.prefs(this).edit().putLong("enter_key_seen", System.currentTimeMillis()).putString("enter_package", str3).putInt("enter_input_type", i2).putInt("enter_ime_options", i3).putInt("enter_field", this.editor.fieldId).putBoolean("enter_connection", currentInputConnection != null).putBoolean("enter_selected_at_key", zSelected).putBoolean("enter_switch_at_key", z).putInt("enter_meta", keyEvent.getMetaState()).putInt("enter_repeat", keyEvent.getRepeatCount()).putBoolean("enter_composition_checked", mode != EnterRouter.Mode.PASS).putBoolean("enter_composing", z7).putBoolean("enter_confirmed", z4).putString("enter_recognition", strChatRecognition).putString("enter_reason", str).putString("enter_mode", mode2.toString()).putBoolean("enter_image_guard", this.imageGuard).apply();
        } else {
            str = strReason;
        }
        boolean zDown = this.enterRouter.down(i, keyEvent.getRepeatCount(), mode2, new EnterRouter.Actions() { // from class: com.cyxfssx.warmime.WarmInputMethodService.1
            @Override // com.cyxfssx.warmime.EnterRouter.Actions
            public void send() {
                boolean zPerformEditorAction;
                try {
                    zPerformEditorAction = currentInputConnection.performEditorAction(4);
                } catch (RuntimeException e4) {
                    zPerformEditorAction = false;
                }
                WarmInputMethodService.this.enterResult(zPerformEditorAction ? "send_requested" : "send_rejected", zPerformEditorAction ? "KakaoTalk 返回接受发送动作；请以实际聊天记录为准。" : "应用未接受标准发送动作；没有重试、点击按钮或改为换行。");
                if (!zPerformEditorAction) {
                    Toast.makeText(WarmInputMethodService.this, "未接受回车发送，请点击发送按钮并反馈测试信息", 0).show();
                }
            }

            @Override // com.cyxfssx.warmime.EnterRouter.Actions
            public void newline() {
                boolean zCommitText;
                try {
                    zCommitText = currentInputConnection.commitText("\n", 1);
                } catch (RuntimeException e4) {
                    zCommitText = false;
                }
                WarmInputMethodService.this.enterResult(zCommitText ? "newline_requested" : "newline_rejected", "Shift+Enter：请求插入换行，不请求发送。");
            }

            @Override // com.cyxfssx.warmime.EnterRouter.Actions
            public void empty() {
                WarmInputMethodService.this.enterResult("empty_or_unreadable", "输入框为空或无法读取文字；未发送、未插入换行。");
            }
        });
        if (!zDown && "com.kakao.talk".equals(str3)) {
            enterResult("passed_through", "保持原按键，具体原因：" + str);
        }
        return zDown || super.onKeyDown(i, keyEvent);
    }

    @Override // android.inputmethodservice.InputMethodService, android.view.KeyEvent.Callback
    public boolean onKeyUp(int i, KeyEvent keyEvent) {
        if (enterKey(i) && this.enterRouter.up(i)) {
            return true;
        }
        return super.onKeyUp(i, keyEvent);
    }

    /* JADX INFO: Access modifiers changed from: private */
    static final class Arm {
        long at;
        String pkg;
        String result;
        long session;

        private Arm() {
            this.result = "ready";
        }
    }

    @Override // android.inputmethodservice.InputMethodService, android.app.Service
    public void onCreate() {
        super.onCreate();
        instance = this;
    }

    @Override // android.inputmethodservice.InputMethodService
    public View onCreateInputView() {
        View view = new View(this) { // from class: com.cyxfssx.warmime.WarmInputMethodService.2
            @Override // android.view.View
            protected void onMeasure(int i, int i2) {
                setMeasuredDimension(View.MeasureSpec.getSize(i), View.MeasureSpec.getMode(i2) != 0 ? Math.min(1, View.MeasureSpec.getSize(i2)) : 1);
            }
        };
        view.setMinimumHeight(0);
        view.setPadding(0, 0, 0, 0);
        view.setLayoutParams(new ViewGroup.LayoutParams(-1, 1));
        view.setBackgroundColor(0);
        return view;
    }

    @Override // android.inputmethodservice.InputMethodService
    public boolean onEvaluateFullscreenMode() {
        return false;
    }

    @Override // android.inputmethodservice.InputMethodService
    public boolean onEvaluateInputViewShown() {
        return true;
    }

    @Override // android.inputmethodservice.InputMethodService
    public void onStartInput(EditorInfo editorInfo, boolean z) {
        boolean z2 = z && this.confirmedChatSession && this.editor != null && "com.kakao.talk".equals(this.editor.packageName) && this.editor.fieldId == editorInfo.fieldId && this.editor.inputType == editorInfo.inputType && this.editor.imeOptions == editorInfo.imeOptions;
        super.onStartInput(editorInfo, z);
        this.session++;
        this.editor = editorInfo;
        this.confirmedChatSession = z2;
        SharedPreferences sharedPreferencesPrefs = ImageStore.prefs(this);
        if ("com.kakao.talk".equals(editorInfo.packageName)) {
            if (sharedPreferencesPrefs.getLong("chat_pending_until", 0L) > System.currentTimeMillis() && sharedPreferencesPrefs.getInt("chat_type", 0) == editorInfo.inputType && sharedPreferencesPrefs.getInt("chat_options", 0) == editorInfo.imeOptions && (sharedPreferencesPrefs.getInt("chat_field", 0) <= 0 || sharedPreferencesPrefs.getInt("chat_field", 0) == editorInfo.fieldId)) {
                this.confirmedChatSession = true;
                sharedPreferencesPrefs.edit().remove("chat_pending_until").apply();
            }
            sharedPreferencesPrefs.edit().putLong("kakao_editor_seen", System.currentTimeMillis()).putInt("kakao_field", editorInfo.fieldId).putInt("kakao_type", editorInfo.inputType).putInt("kakao_options", editorInfo.imeOptions).apply();
        }
        if (this.imageGuard && this.imageEditorLeft && "com.kakao.talk".equals(editorInfo.packageName) && editorInfo.fieldId == this.imageField) {
            this.imageGuard = false;
            this.imageEditorLeft = false;
        }
        SharedPreferences sharedPreferencesPrefs2 = ImageStore.prefs(this);
        if (!getPackageName().equals(editorInfo.packageName)) {
            sharedPreferencesPrefs2.edit().putString("editor_package", editorInfo.packageName == null ? "" : editorInfo.packageName).putString("editor_mimes", TextUtils.join(", ", types(editorInfo))).apply();
        }
        final String string = sharedPreferencesPrefs2.getString("manual_token", "");
        String string2 = sharedPreferencesPrefs2.getString("manual_target", "com.kakao.talk");
        long j = sharedPreferencesPrefs2.getLong("manual_until", 0L);
        if (!string.isEmpty() && System.currentTimeMillis() < j && string2.equals(editorInfo.packageName)) {
            sharedPreferencesPrefs2.edit().remove("manual_token").apply();
            if (arm(string) != null) {
                this.handler.postDelayed(new Runnable() { // from class: com.cyxfssx.warmime.WarmInputMethodService$$ExternalSyntheticLambda2
                    @Override // java.lang.Runnable
                    public final void run() {
                        this.f$0.m17lambda$onStartInput$0$comcyxfssxwarmimeWarmInputMethodService(string);
                    }
                }, 180L);
            }
        }
    }

    @Override // android.inputmethodservice.InputMethodService
    public void onFinishInput() {
        this.session++;
        this.confirmedChatSession = false;
        if (this.imageGuard) {
            this.imageEditorLeft = true;
        }
        this.editor = null;
        super.onFinishInput();
    }

    @Override // android.inputmethodservice.InputMethodService, android.inputmethodservice.AbstractInputMethodService, android.app.Service
    public void onDestroy() {
        if (instance == this) {
            instance = null;
        }
        super.onDestroy();
    }

    static boolean selected(Context context) {
        String string = Settings.Secure.getString(context.getContentResolver(), "default_input_method");
        ComponentName componentName = new ComponentName(context, (Class<?>) WarmInputMethodService.class);
        return componentName.flattenToString().equals(string) || componentName.flattenToShortString().equals(string);
    }

    private static String[] types(EditorInfo editorInfo) {
        if (editorInfo.contentMimeTypes != null && editorInfo.contentMimeTypes.length > 0) {
            return editorInfo.contentMimeTypes;
        }
        if (editorInfo.extras != null) {
            String[] stringArray = editorInfo.extras.getStringArray("androidx.core.view.inputmethod.EditorInfoCompat.CONTENT_MIME_TYPES");
            if (stringArray != null) {
                return stringArray;
            }
            String[] stringArray2 = editorInfo.extras.getStringArray("android.support.v13.view.inputmethod.EditorInfoCompat.CONTENT_MIME_TYPES");
            if (stringArray2 != null) {
                return stringArray2;
            }
        }
        return new String[0];
    }

    private boolean usable() {
        if (!selected(this) || this.editor == null || getCurrentInputConnection() == null || this.editor.packageName == null || this.editor.packageName.equals(getPackageName())) {
            return false;
        }
        int i = this.editor.inputType & 15;
        int i2 = this.editor.inputType & 4080;
        return (i != 1 || i2 == 128 || i2 == 144 || i2 == 224) ? false : true;
    }

    private Arm arm(String str) {
        if (!ImagePolicy.validToken(str) || !usable()) {
            return null;
        }
        if (this.arms.size() > 32) {
            this.arms.clear();
        }
        Arm arm = new Arm();
        arm.session = this.session;
        arm.pkg = this.editor.packageName;
        arm.at = SystemClock.elapsedRealtime();
        this.arms.put(str, arm);
        return arm;
    }

    private void record(String str, String str2) {
        ImageStore.prefs(this).edit().putString("last_result", str).putString("last_detail", str2).putLong("last_time", System.currentTimeMillis()).apply();
    }

    /* JADX INFO: Access modifiers changed from: private */
    /* JADX INFO: renamed from: insert, reason: merged with bridge method [inline-methods] */
    public String m17lambda$onStartInput$0$comcyxfssxwarmimeWarmInputMethodService(String str) {
        Arm arm = this.arms.get(str);
        if (arm == null || !usable() || arm.session != this.session || !arm.pkg.equals(this.editor.packageName) || SystemClock.elapsedRealtime() - arm.at > 30000) {
            if (arm != null) {
                arm.result = "stale";
            }
            record("stale", "输入框已变化或请求过期，未插入图片");
            return "stale";
        }
        if (!arm.result.equals("ready")) {
            return arm.result;
        }
        arm.result = "working";
        try {
            if (!ImageStore.file(this, str, false).isFile()) {
                throw new IllegalStateException("图片尚未保存");
            }
            String strMime = ImageStore.mime(this, str);
            Uri uri = ImageStore.uri(str);
            grantUriPermission(arm.pkg, uri, 1);
            InputContentInfo inputContentInfo = new InputContentInfo(uri, new ClipDescription("推推图片", new String[]{strMime}), null);
            String strJoin = TextUtils.join(", ", types(this.editor));
            InputConnection currentInputConnection = getCurrentInputConnection();
            int i = this.editor.fieldId;
            boolean z = currentInputConnection != null && currentInputConnection.commitContent(inputContentInfo, 1, null);
            if (z && "com.kakao.talk".equals(arm.pkg)) {
                this.imageGuard = true;
                this.imageEditorLeft = false;
                this.imageField = i;
            }
            arm.result = z ? "accepted" : "rejected";
            record(arm.result, z ? "应用已接受图片请求，请检查当前聊天；输入法没有调用发送操作。" : "应用未接受标准图片接口；没有自动点击发送。声明类型：" + strJoin);
            return arm.result;
        } catch (IOException | RuntimeException e) {
            arm.result = "error";
            record("error", e.getClass().getSimpleName() + ": " + e.getMessage());
        }
    }

    static Bundle command(final String str, final String str2) {
        final WarmInputMethodService warmInputMethodService = instance;
        Bundle bundle = new Bundle();
        if (warmInputMethodService == null) {
            bundle.putString("status", "ime_unavailable");
            return bundle;
        }
        final AtomicReference atomicReference = new AtomicReference("pending");
        final Runnable runnable = new Runnable() { // from class: com.cyxfssx.warmime.WarmInputMethodService$$ExternalSyntheticLambda0
            @Override // java.lang.Runnable
            public final void run() {
                WarmInputMethodService.lambda$command$1(str, atomicReference, warmInputMethodService, str2);
            }
        };
        if (Looper.myLooper() == Looper.getMainLooper()) {
            runnable.run();
        } else {
            final CountDownLatch countDownLatch = new CountDownLatch(1);
            warmInputMethodService.handler.post(new Runnable() { // from class: com.cyxfssx.warmime.WarmInputMethodService$$ExternalSyntheticLambda1
                @Override // java.lang.Runnable
                public final void run() {
                    WarmInputMethodService.lambda$command$2(runnable, countDownLatch);
                }
            });
            try {
                countDownLatch.await(2500L, TimeUnit.MILLISECONDS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                atomicReference.set("interrupted");
            }
        }
        bundle.putString("status", (String) atomicReference.get());
        return bundle;
    }

    static /* synthetic */ void lambda$command$1(String str, AtomicReference atomicReference, WarmInputMethodService warmInputMethodService, String str2) {
        if (!str.equals("arm")) {
            if (!str.equals("deliver")) {
                Arm arm = warmInputMethodService.arms.get(str2);
                atomicReference.set(arm == null ? "unknown" : arm.result);
                return;
            } else {
                atomicReference.set(warmInputMethodService.m17lambda$onStartInput$0$comcyxfssxwarmimeWarmInputMethodService(str2));
                return;
            }
        }
        atomicReference.set(warmInputMethodService.arm(str2) != null ? "ready" : "no_active_editor");
    }

    static /* synthetic */ void lambda$command$2(Runnable runnable, CountDownLatch countDownLatch) {
        try {
            runnable.run();
        } finally {
            countDownLatch.countDown();
        }
    }
}
