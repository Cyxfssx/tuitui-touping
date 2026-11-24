package com.cyxfssx.warmime;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.Binder;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.os.Process;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.List;

/* JADX INFO: loaded from: classes.dex */
public final class WarmImageProvider extends ContentProvider {
    @Override // android.content.ContentProvider
    public boolean onCreate() {
        return true;
    }

    private void transport() {
        if (Binder.getCallingUid() != Process.myUid() && getContext().checkCallingPermission("android.permission.DUMP") != 0) {
            throw new SecurityException("Only the explicitly authorized ADB shell transport may upload images");
        }
    }

    private String token(Uri uri, String str) throws FileNotFoundException {
        List<String> pathSegments = uri.getPathSegments();
        if (pathSegments.size() == 2 && str.equals(pathSegments.get(0)) && ImagePolicy.validToken(pathSegments.get(1))) {
            return pathSegments.get(1);
        }
        throw new FileNotFoundException("Invalid image URI");
    }

    @Override // android.content.ContentProvider
    public ParcelFileDescriptor openFile(Uri uri, String str) throws FileNotFoundException {
        try {
            if (str.equals("r")) {
                return ParcelFileDescriptor.open(ImageStore.file(getContext(), token(uri, "image"), false), 268435456);
            }
            transport();
            if (!str.equals("w") && !str.equals("wt")) {
                throw new FileNotFoundException("Read-only image grants");
            }
            String str2 = token(uri, "upload");
            if (ImageStore.file(getContext(), str2, false).exists()) {
                throw new FileNotFoundException("An imported image cannot be overwritten");
            }
            File[] fileArrListFiles = ImageStore.directory(getContext()).listFiles();
            long length = 0;
            if (fileArrListFiles != null) {
                for (File file : fileArrListFiles) {
                    length += file.length();
                }
            }
            if (length >= ImagePolicy.MAX_CACHE) {
                throw new FileNotFoundException("Image cache full");
            }
            if (!"ready".equals(WarmInputMethodService.command("result", str2).getString("status"))) {
                throw new FileNotFoundException("No active armed editor for upload");
            }
            return ParcelFileDescriptor.open(ImageStore.file(getContext(), str2, true), 738197504);
        } catch (IOException e) {
            throw new FileNotFoundException(e.getMessage());
        }
    }

    @Override // android.content.ContentProvider
    public String getType(Uri uri) {
        try {
            return ImageStore.mime(getContext(), token(uri, "image"));
        } catch (IOException e) {
            return null;
        }
    }

    @Override // android.content.ContentProvider
    public Cursor query(Uri uri, String[] strArr, String str, String[] strArr2, String str2) {
        try {
            File file = ImageStore.file(getContext(), token(uri, "image"), false);
            if (!file.isFile()) {
                return null;
            }
            if (strArr == null) {
                strArr = new String[]{"_display_name", "_size"};
            }
            MatrixCursor matrixCursor = new MatrixCursor(strArr);
            Object[] objArr = new Object[strArr.length];
            for (int i = 0; i < strArr.length; i++) {
                if ("_display_name".equals(strArr[i])) {
                    objArr[i] = "推推图片";
                } else if ("_size".equals(strArr[i])) {
                    objArr[i] = Long.valueOf(file.length());
                }
            }
            matrixCursor.addRow(objArr);
            return matrixCursor;
        } catch (IOException e) {
            return null;
        }
    }

    @Override // android.content.ContentProvider
    public Bundle call(String str, String str2, Bundle bundle) {
        transport();
        Bundle bundle2 = new Bundle();
        if (!ImagePolicy.validToken(str2)) {
            bundle2.putString("status", "invalid_token");
            return bundle2;
        }
        try {
            if (!str.equals("arm") && !str.equals("result")) {
                if (str.equals("deliver")) {
                    if (!ImageStore.file(getContext(), str2, false).exists()) {
                        ImageStore.finish(getContext(), str2);
                    }
                    return WarmInputMethodService.command("deliver", str2);
                }
                if (!str.equals("cancel")) {
                    bundle2.putString("status", "unknown_method");
                    return bundle2;
                }
                ImageStore.file(getContext(), str2, true).delete();
                bundle2.putString("status", "cancelled");
                return bundle2;
            }
            return WarmInputMethodService.command(str, str2);
        } catch (IOException | RuntimeException e) {
            bundle2.putString("status", "error");
            bundle2.putString("detail", e.getMessage());
        }
    }

    @Override // android.content.ContentProvider
    public Uri insert(Uri uri, ContentValues contentValues) {
        throw new UnsupportedOperationException();
    }

    @Override // android.content.ContentProvider
    public int update(Uri uri, ContentValues contentValues, String str, String[] strArr) {
        throw new UnsupportedOperationException();
    }

    @Override // android.content.ContentProvider
    public int delete(Uri uri, String str, String[] strArr) {
        throw new UnsupportedOperationException();
    }
}
