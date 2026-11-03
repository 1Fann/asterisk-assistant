package com.fann.asterisk;

import android.app.AlertDialog;
import android.content.Context;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;

/** Explicit device-level fallback for already enabled companion supervisors. */
final class SuiteFallbackSettings {
    private static final String BUSYBOX = "/data/adb/magisk/busybox";

    static void show(MainActivity activity) {
        activity.async(() -> apply(activity, "status"), status -> {
            AlertDialog.Builder dialog = new AlertDialog.Builder(activity)
                .setTitle("配套服务备用守护")
                .setMessage(describe(status) + "\n\n电话、短信、推送或 DDNS 的两层守护都退出后，此功能会拉起该组件原有的守护。只处理已启用的服务。启用时也会检查 DDNS 管理应用的后台权限。")
                .setNegativeButton("返回", null);
            if (!status.equals("conflict") && !status.equals("no_magisk")) {
                dialog.setPositiveButton("启用 / 修复", (d,w) -> change(activity,"enable"));
                if (!status.equals("off")) dialog.setNeutralButton("关闭备用守护", (d,w) -> change(activity,"disable"));
            }
            dialog.show();
        });
    }

    private static void change(MainActivity activity, String action) {
        activity.async(() -> apply(activity,action), state -> activity.toast(describe(state)));
    }

    private static String describe(String state) {
        switch (state) {
            case "off": return "备用守护已关闭";
            case "running": return "备用守护正在运行";
            case "started": return "已启用，正在启动备用守护";
            case "updated": return "已更新，备用守护下次启动时载入新版";
            case "waiting": return "备用守护已启用，当前未运行";
            case "needs_repair": return "备用守护文件不完整，可点修复";
            case "no_magisk": return "此功能需要 Magisk 和 Root 授权";
            case "conflict": return "检测到其他程序的文件，无法安全接管";
            case "busy": return "正在更改备用守护，请稍后再试";
            default: return "未能确认备用守护状态";
        }
    }

    private static String read(Context context, String asset) throws Exception {
        try (InputStream input=context.getAssets().open("runtime/"+asset);
             ByteArrayOutputStream output=new ByteArrayOutputStream()) {
            byte[] block=new byte[4096]; int count;
            while ((count=input.read(block))!=-1) output.write(block,0,count);
            return new String(output.toByteArray(),StandardCharsets.UTF_8).replace("\r\n","\n");
        }
    }
    private static String quote(String value) { return "'"+value.replace("'","'\\''")+"'"; }
    private static String apply(Context context, String action) throws Exception {
        RootBridge.verifySelf(context);
        String command="if [ ! -x "+BUSYBOX+" ]; then echo no_magisk; else "+BUSYBOX+" ash -c "+
            quote(read(context,"suite-fallback-config.sh"))+" suite "+action;
        if (action.equals("enable")) {
            String worker=read(context,"suite-fallback.sh");
            byte[] hash=MessageDigest.getInstance("SHA-256").digest(worker.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex=new StringBuilder();
            for (byte b: hash) hex.append(String.format(Locale.ROOT,"%02x",b & 255));
            command+=" "+quote(worker)+" "+hex;
        }
        return RootBridge.run(command+"; fi",null,15);
    }
}
