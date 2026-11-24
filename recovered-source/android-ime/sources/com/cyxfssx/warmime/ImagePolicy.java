package com.cyxfssx.warmime;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/* JADX INFO: loaded from: classes.dex */
public final class ImagePolicy {
    public static final long MAX_CACHE = 134217728;
    public static final long MAX_FILE = 33554432;

    private ImagePolicy() {
    }

    public static boolean validToken(String str) {
        return str != null && str.matches("[A-Za-z0-9_-]{8,100}");
    }

    public static String detect(File file) throws IOException {
        if (!file.isFile() || file.length() == 0 || file.length() > MAX_FILE) {
            throw new IOException("图片为空或超过 32 MB");
        }
        byte[] bArr = new byte[64];
        FileInputStream fileInputStream = new FileInputStream(file);
        try {
            int i = fileInputStream.read(bArr);
            fileInputStream.close();
            if (i >= 24 && bArr[0] == -119 && bArr[1] == 80 && bArr[2] == 78 && bArr[3] == 71) {
                return "image/png";
            }
            if (i >= 3 && bArr[0] == -1 && bArr[1] == -40 && bArr[2] == -1) {
                return "image/jpeg";
            }
            if (i >= 6 && bArr[0] == 71 && bArr[1] == 73 && bArr[2] == 70 && bArr[3] == 56) {
                return "image/gif";
            }
            if (i >= 12 && bArr[0] == 82 && bArr[1] == 73 && bArr[2] == 70 && bArr[8] == 87 && bArr[9] == 69 && bArr[10] == 66 && bArr[11] == 80) {
                return "image/webp";
            }
            if (i >= 14 && bArr[0] == 66 && bArr[1] == 77) {
                return "image/bmp";
            }
            if (i >= 16 && bArr[4] == 102 && bArr[5] == 116 && bArr[6] == 121 && bArr[7] == 112) {
                String str = new String(bArr, 8, 4, StandardCharsets.US_ASCII);
                if (str.equals("avif") || str.equals("avis")) {
                    return "image/avif";
                }
                if (str.equals("heic") || str.equals("heix") || str.equals("mif1") || str.equals("msf1")) {
                    return "image/heic";
                }
            }
            throw new IOException("暂不支持此图片格式，请先测试 JPG 或 PNG");
        } catch (Throwable th) {
            try {
                fileInputStream.close();
            } catch (Throwable th2) {
                th.addSuppressed(th2);
            }
            throw th;
        }
    }

    public static boolean accepts(String[] strArr, String str) {
        if (strArr == null || str == null) {
            return false;
        }
        String lowerCase = str.toLowerCase(Locale.ROOT);
        for (String str2 : strArr) {
            if (str2 != null) {
                String lowerCase2 = str2.toLowerCase(Locale.ROOT);
                if (lowerCase2.equals(lowerCase) || lowerCase2.equals("*/*")) {
                    return true;
                }
                if (lowerCase2.equals("image/*") && lowerCase.startsWith("image/")) {
                    return true;
                }
            }
        }
        return false;
    }
}
