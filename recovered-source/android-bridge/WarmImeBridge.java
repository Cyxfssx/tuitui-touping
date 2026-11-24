package com.genymobile.scrcpy;

import android.content.ContentProviderClient;
import android.content.ContentResolver;
import android.net.Uri;
import android.os.Bundle;
import android.os.Looper;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.io.FileInputStream;

/* JADX INFO: loaded from: classes.dex */
public final class WarmImeBridge {
    private static final Uri BASE = Uri.parse("content://com.cyxfssx.warmime.images");

    private WarmImeBridge() {
    }

    private static String call(ContentResolver contentResolver, String str, String str2) {
        Bundle bundleCall = contentResolver.call(BASE, str, str2, (Bundle) null);
        return bundleCall == null ? "unavailable" : bundleCall.getString("status", "unavailable");
    }

    private static int run(String[] strArr) throws Exception {
        if (strArr.length < 2 || !strArr[1].matches("[A-Za-z0-9_-]{8,100}")) {
            return 2;
        }
        ContentResolver contentResolver = FakeContext.get().getContentResolver();
        String str = strArr[1];
        if (strArr.length == 2 && strArr[0].equals("arm")) {
            return call(contentResolver, "arm", str).equals("ready") ? 0 : 20;
        }
        if (strArr.length != 3 || !strArr[0].equals("deliver") || !strArr[2].equals("/data/local/tmp/warm-image-" + str + ".tmp")) {
            return 2;
        }
        File file = new File(strArr[2]);
        if (file.isFile()) {
            long j = 0;
            if (file.length() > 0) {
                long j2 = 33554432;
                if (file.length() <= 33554432) {
                    ContentProviderClient contentProviderClientAcquireContentProviderClient = contentResolver.acquireContentProviderClient(BASE);
                    if (contentProviderClientAcquireContentProviderClient == null) {
                        if (contentProviderClientAcquireContentProviderClient != null) {
                            contentProviderClientAcquireContentProviderClient.release();
                        }
                        return 21;
                    }
                    try {
                        ParcelFileDescriptor parcelFileDescriptorOpenFile = contentProviderClientAcquireContentProviderClient.openFile(BASE.buildUpon().appendPath("upload").appendPath(str).build(), "w");
                        if (parcelFileDescriptorOpenFile == null) {
                            if (contentProviderClientAcquireContentProviderClient != null) {
                                contentProviderClientAcquireContentProviderClient.release();
                            }
                            return 21;
                        }
                        FileInputStream fileInputStream = new FileInputStream(file);
                        try {
                            ParcelFileDescriptor.AutoCloseOutputStream autoCloseOutputStream = new ParcelFileDescriptor.AutoCloseOutputStream(parcelFileDescriptorOpenFile);
                            try {
                                byte[] bArr = new byte[65536];
                                while (true) {
                                    int i = fileInputStream.read(bArr);
                                    if (i == -1) {
                                        autoCloseOutputStream.close();
                                        fileInputStream.close();
                                        if (contentProviderClientAcquireContentProviderClient != null) {
                                            contentProviderClientAcquireContentProviderClient.release();
                                        }
                                        String strCall = call(contentResolver, "deliver", str);
                                        for (int i2 = 0; i2 < 20 && (strCall.equals("pending") || strCall.equals("working")); i2++) {
                                            Thread.sleep(100L);
                                            strCall = call(contentResolver, "result", str);
                                        }
                                        System.out.println("Warm IME: " + strCall);
                                        return strCall.equals("accepted") ? 0 : 22;
                                    }
                                    long j3 = j2;
                                    j += (long) i;
                                    if (j > j3) {
                                        autoCloseOutputStream.close();
                                        fileInputStream.close();
                                        if (contentProviderClientAcquireContentProviderClient != null) {
                                            contentProviderClientAcquireContentProviderClient.release();
                                        }
                                        return 2;
                                    }
                                    autoCloseOutputStream.write(bArr, 0, i);
                                    j2 = j3;
                                    try {
                                        fileInputStream.close();
                                        throw th;
                                    } catch (Throwable th) {
                                        Throwable.class.getDeclaredMethod("addSuppressed", Throwable.class).invoke(th, th);
                                        throw th;
                                    }
                                }
                            } catch (Throwable th2) {
                                try {
                                    autoCloseOutputStream.close();
                                    throw th2;
                                } catch (Throwable th3) {
                                    Throwable.class.getDeclaredMethod("addSuppressed", Throwable.class).invoke(th2, th3);
                                    throw th2;
                                }
                            }
                        } catch (Throwable th4) {
                            fileInputStream.close();
                            throw th4;
                        }
                    } catch (Throwable th5) {
                        if (contentProviderClientAcquireContentProviderClient == null) {
                            throw th5;
                        }
                        try {
                            contentProviderClientAcquireContentProviderClient.release();
                            throw th5;
                        } catch (Throwable th6) {
                            Throwable.class.getDeclaredMethod("addSuppressed", Throwable.class).invoke(th5, th6);
                            throw th5;
                        }
                    }
                }
            }
        }
        return 2;
    }

    public static void main(final String... strArr) {
        try {
            Looper.prepareMainLooper();
            Workarounds.apply();
            new Thread(new Runnable() { // from class: com.genymobile.scrcpy.WarmImeBridge$$ExternalSyntheticLambda1
                @Override // java.lang.Runnable
                public final void run() {
                    WarmImeBridge.lambda$main$0(strArr);
                }
            }, "warm-ime-adapter").start();
            Looper.loop();
        } catch (Throwable th) {
            System.err.println("Warm IME adapter unavailable");
            System.exit(20);
        }
    }

    static /* synthetic */ void lambda$main$0(String[] strArr) {
        try {
            System.exit(run(strArr));
        } catch (Throwable th) {
            System.err.println("Warm IME unavailable: " + th.getClass().getSimpleName());
            System.exit(20);
        }
    }
}
