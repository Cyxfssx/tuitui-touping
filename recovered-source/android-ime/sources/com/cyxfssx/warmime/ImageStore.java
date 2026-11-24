package com.cyxfssx.warmime;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.UUID;

/* JADX INFO: loaded from: classes.dex */
final class ImageStore {
    static final String AUTHORITY = "com.cyxfssx.warmime.images";

    ImageStore() {
    }

    static SharedPreferences prefs(Context context) {
        return context.getSharedPreferences("local", 0);
    }

    static File directory(Context context) throws IOException {
        File file = new File(context.getFilesDir(), "images");
        if (file.isDirectory() || file.mkdirs()) {
            return file;
        }
        throw new IOException("无法创建图片缓存");
    }

    static File file(Context context, String str, boolean z) throws IOException {
        if (ImagePolicy.validToken(str)) {
            return new File(directory(context), str + (z ? ".part" : ".img"));
        }
        throw new IOException("无效图片标识");
    }

    static Uri uri(String str) {
        return new Uri.Builder().scheme("content").authority(AUTHORITY).appendPath("image").appendPath(str).build();
    }

    static synchronized String importUri(Context context, Uri uri) throws IOException {
        long length;
        String string;
        File[] fileArrListFiles = directory(context).listFiles();
        long j = 0;
        if (fileArrListFiles != null) {
            length = 0;
            for (File file : fileArrListFiles) {
                length += file.length();
            }
        } else {
            length = 0;
        }
        if (length >= ImagePolicy.MAX_CACHE) {
            throw new IOException("缓存已满，请先完成发送，再到设置清理缓存");
        }
        string = UUID.randomUUID().toString();
        File file2 = file(context, string, true);
        try {
            InputStream inputStreamOpenInputStream = context.getContentResolver().openInputStream(uri);
            try {
                FileOutputStream fileOutputStream = new FileOutputStream(file2);
                try {
                    if (inputStreamOpenInputStream == null) {
                        throw new IOException("无法打开图片");
                    }
                    byte[] bArr = new byte[65536];
                    while (true) {
                        int i = inputStreamOpenInputStream.read(bArr);
                        if (i != -1) {
                            j += (long) i;
                            if (j > ImagePolicy.MAX_FILE) {
                                throw new IOException("图片超过 32 MB");
                            }
                            fileOutputStream.write(bArr, 0, i);
                        } else {
                            fileOutputStream.close();
                            if (inputStreamOpenInputStream != null) {
                                inputStreamOpenInputStream.close();
                            }
                            try {
                                finish(context, string);
                            } catch (Throwable th) {
                                file2.delete();
                                throw th;
                            }
                        }
                    }
                } catch (Throwable th2) {
                    try {
                        fileOutputStream.close();
                    } catch (Throwable th3) {
                        th2.addSuppressed(th3);
                    }
                    throw th2;
                }
            } catch (Throwable th4) {
                if (inputStreamOpenInputStream != null) {
                    try {
                        inputStreamOpenInputStream.close();
                    } catch (Throwable th5) {
                        th4.addSuppressed(th5);
                    }
                }
                throw th4;
            }
        } catch (IOException e) {
            file2.delete();
            throw e;
        }
        return string;
    }

    static synchronized String finish(Context context, String str) throws IOException {
        String strDetect;
        File file = file(context, str, true);
        strDetect = ImagePolicy.detect(file);
        File[] fileArrListFiles = directory(context).listFiles();
        long length = 0;
        if (fileArrListFiles != null) {
            for (File file2 : fileArrListFiles) {
                length += file2.length();
            }
        }
        if (length > ImagePolicy.MAX_CACHE) {
            file.delete();
            throw new IOException("图片缓存已满，请完成发送后清理缓存");
        }
        File file3 = file(context, str, false);
        if (file3.exists() || !file.renameTo(file3)) {
            throw new IOException("无法保存图片");
        }
        prefs(context).edit().putString("mime_" + str, strDetect).putString("pending", str).apply();
        return strDetect;
    }

    static String mime(Context context, String str) {
        return prefs(context).getString("mime_" + str, "image/png");
    }

    static synchronized void clear(Context context) throws IOException {
        File[] fileArrListFiles = directory(context).listFiles();
        if (fileArrListFiles != null) {
            for (File file : fileArrListFiles) {
                String strReplaceFirst = file.getName().replaceFirst("\\.(img|part)$", "");
                if (ImagePolicy.validToken(strReplaceFirst)) {
                    context.revokeUriPermission(uri(strReplaceFirst), 1);
                    file.delete();
                }
            }
        }
        prefs(context).edit().remove("pending").remove("manual_token").apply();
    }
}
