package com.chatmirror.ime;

import android.app.Service;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.inputmethodservice.InputMethodService;
import android.os.Build;
import android.util.Base64;
import android.view.View;
import android.view.inputmethod.InputConnection;
import android.widget.TextView;
import java.nio.charset.StandardCharsets;

public final class BridgeIme extends InputMethodService {
    private static final String ACTION = "com.chatmirror.ime.COMMIT_TEXT";
    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            if (!ACTION.equals(intent.getAction())) return;
            String encoded = intent.getStringExtra("text64");
            if (encoded == null || encoded.length() > 131072) { setResultCode(2); setResultData("invalid payload"); return; }
            InputConnection connection = getCurrentInputConnection();
            if (connection == null || !isInputStarted()) { setResultCode(3); setResultData("no focused editor"); return; }
            try {
                String text = new String(Base64.decode(encoded, Base64.NO_WRAP), StandardCharsets.UTF_8);
                boolean ok = connection.commitText(text, 1);
                setResultCode(ok ? 1 : 4); setResultData(ok ? "accepted" : "editor rejected");
            } catch (IllegalArgumentException e) { setResultCode(2); setResultData("invalid payload"); }
        }
    };
    @Override public void onCreate() {
        super.onCreate();
        IntentFilter filter = new IntentFilter(ACTION);
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(receiver, filter, "android.permission.DUMP", null, Context.RECEIVER_EXPORTED);
        else registerReceiver(receiver, filter, "android.permission.DUMP", null);
    }
    @Override public void onDestroy() { unregisterReceiver(receiver); super.onDestroy(); }
    @Override public View onCreateInputView() {
        TextView view = new TextView(this);
        view.setText("ChatMirror 输入法已启用 · 请在电脑端输入");
        view.setPadding(24, 24, 24, 24);
        return view;
    }
}
