package com.cyxfssx.warmime;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.TextView;
import android.widget.Toast;

/* JADX INFO: loaded from: classes.dex */
public final class PickImageActivity extends Activity {
    private boolean busy;

    @Override // android.app.Activity
    public void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        TextView textView = new TextView(this);
        textView.setText("正在选择测试图片……");
        textView.setPadding(32, 80, 32, 32);
        setContentView(textView);
        if (bundle == null) {
            Intent intent = new Intent("android.intent.action.OPEN_DOCUMENT");
            intent.addCategory("android.intent.category.OPENABLE");
            intent.setType("image/*");
            intent.addFlags(1);
            startActivityForResult(intent, 1);
        }
    }

    @Override // android.app.Activity
    protected void onActivityResult(int i, int i2, Intent intent) {
        super.onActivityResult(i, i2, intent);
        if (i != 1) {
            return;
        }
        if (i2 != -1 || intent == null || intent.getData() == null) {
            finish();
            return;
        }
        this.busy = true;
        final Uri data = intent.getData();
        ((TextView) ((ViewGroup) findViewById(android.R.id.content)).getChildAt(0)).setText("正在准备图片，请稍候……");
        new Thread(new Runnable() { // from class: com.cyxfssx.warmime.PickImageActivity$$ExternalSyntheticLambda2
            @Override // java.lang.Runnable
            public final void run() {
                this.f$0.m16lambda$onActivityResult$2$comcyxfssxwarmimePickImageActivity(data);
            }
        }, "warm-image-import").start();
    }

    /* JADX INFO: renamed from: lambda$onActivityResult$2$com-cyxfssx-warmime-PickImageActivity, reason: not valid java name */
    /* synthetic */ void m16lambda$onActivityResult$2$comcyxfssxwarmimePickImageActivity(Uri uri) {
        String str = "com.kakao.talk";
        try {
            String strImportUri = ImageStore.importUri(this, uri);
            String string = ImageStore.prefs(this).getString("editor_package", "com.kakao.talk");
            if (!string.isEmpty() && !string.equals(getPackageName())) {
                str = string;
            }
            ImageStore.prefs(this).edit().putString("manual_token", strImportUri).putString("manual_target", str).putLong("manual_until", System.currentTimeMillis() + 60000).putString("last_result", "armed_manual").putString("last_detail", "图片已准备，请返回目标聊天，点击输入框。目标：" + str).apply();
            runOnUiThread(new Runnable() { // from class: com.cyxfssx.warmime.PickImageActivity$$ExternalSyntheticLambda0
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.m14lambda$onActivityResult$0$comcyxfssxwarmimePickImageActivity();
                }
            });
        } catch (Exception e) {
            runOnUiThread(new Runnable() { // from class: com.cyxfssx.warmime.PickImageActivity$$ExternalSyntheticLambda1
                @Override // java.lang.Runnable
                public final void run() {
                    this.f$0.m15lambda$onActivityResult$1$comcyxfssxwarmimePickImageActivity(e);
                }
            });
        }
    }

    /* JADX INFO: renamed from: lambda$onActivityResult$0$com-cyxfssx-warmime-PickImageActivity, reason: not valid java name */
    /* synthetic */ void m14lambda$onActivityResult$0$comcyxfssxwarmimePickImageActivity() {
        this.busy = false;
        Toast.makeText(this, "图片已准备，请返回聊天并点击输入框", 1).show();
        finish();
    }

    /* JADX INFO: renamed from: lambda$onActivityResult$1$com-cyxfssx-warmime-PickImageActivity, reason: not valid java name */
    /* synthetic */ void m15lambda$onActivityResult$1$comcyxfssxwarmimePickImageActivity(Exception exc) {
        this.busy = false;
        Toast.makeText(this, exc.getMessage(), 1).show();
        finish();
    }

    @Override // android.app.Activity
    public void onBackPressed() {
        if (this.busy) {
            return;
        }
        super.onBackPressed();
    }
}
