package com.cyxfssx.warmime;

import java.util.HashSet;

/* JADX INFO: loaded from: classes.dex */
public final class EnterRouter {
    private final HashSet<Integer> held = new HashSet<>();

    public interface Actions {
        void empty();

        void newline();

        void send();
    }

    public enum Mode {
        PASS,
        SEND,
        NEWLINE,
        EMPTY
    }

    public boolean down(int i, int i2, Mode mode, Actions actions) {
        if (this.held.contains(Integer.valueOf(i))) {
            return true;
        }
        if (i2 != 0 || mode == Mode.PASS) {
            return false;
        }
        this.held.add(Integer.valueOf(i));
        if (mode == Mode.SEND) {
            actions.send();
        } else if (mode == Mode.NEWLINE) {
            actions.newline();
        } else {
            actions.empty();
        }
        return true;
    }

    public boolean up(int i) {
        return this.held.remove(Integer.valueOf(i));
    }

    public static String reason(String str, int i, int i2, boolean z, boolean z2, boolean z3, boolean z4, boolean z5) {
        if (!z) {
            return "disabled_or_no_connection";
        }
        if (!"com.kakao.talk".equals(str)) {
            return "other_package";
        }
        if ((i & 15) != 1) {
            return "not_text_input";
        }
        if (z2) {
            return "modified_key";
        }
        if (z3) {
            return "android_composing";
        }
        if (z4) {
            return "image_preview_guard";
        }
        int i3 = i & 4080;
        if (i3 != 0 && i3 != 64 && i3 != 80 && (!z5 || i3 != 160)) {
            return "input_variation_0x" + Integer.toHexString(i3);
        }
        int i4 = i2 & 255;
        if (i4 == 0 || i4 == 1 || i4 == 4) {
            return "eligible";
        }
        return (z5 && i4 == 6) ? "eligible" : "ime_action_" + i4;
    }

    public static boolean knownKakaoChat(String str, int i, int i2, int i3) {
        return "com.kakao.talk".equals(str) && i == 2131365282 && i2 == 180225 && i3 == 1375731718;
    }

    public static boolean sameConfirmedEditor(int i, int i2, int i3, int i4, int i5, int i6) {
        return i > 0 && i == i4 && i2 == i5 && i3 == i6;
    }

    public static boolean mayConfirm(int i, int i2) {
        return "eligible".equals(reason("com.kakao.talk", i, i2, true, false, false, false, true));
    }

    public static Mode mode(String str, int i, int i2, boolean z, boolean z2, boolean z3, boolean z4, boolean z5, boolean z6) {
        return mode(str, i, i2, z, z2, z3, z4, z5, z6, false);
    }

    public static Mode mode(String str, int i, int i2, boolean z, boolean z2, boolean z3, boolean z4, boolean z5, boolean z6, boolean z7) {
        if (!"eligible".equals(reason(str, i, i2, z, z3, z4, z5, z7))) {
            return Mode.PASS;
        }
        if (z2) {
            return Mode.NEWLINE;
        }
        return z6 ? Mode.SEND : Mode.EMPTY;
    }
}
