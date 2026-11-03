package com.fann.asterisk;

import android.app.AlertDialog;
import android.content.Context;
import android.os.Build;
import android.util.Base64;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/** Explicit control of one reviewed, code-free Redmi Wi-Fi resource overlay. */
final class RedmiWifiModule {
 private static final String MODULE_SHA="2e6c42e2c62807ba47ebacd4d0ac700d1f2a7d72cb46bb755a2d3c91fd0d4d80";
 private static final String BB="/data/adb/magisk/busybox";
 private static final String LOCK="/data/adb/.interlink-wifi-app.lock";

 static void show(MainActivity activity){
  activity.async(()->run(activity,"status"),value->display(activity,value));
 }
 private static void display(MainActivity activity,String value){
  AlertDialog.Builder dialog=new AlertDialog.Builder(activity).setTitle("红米息屏 Wi-Fi 模块")
      .setMessage(message(value)+"\n\n适用红米 Note 10 Pro（chopin）、Android 13 和 Magisk。此选项变更整机的 Wi-Fi 息屏策略，拔掉电源或停止 PBX 后也会继续生效，可能增加耗电。安装或停用后，请在方便时自行重启手机。")
      .setNegativeButton("返回",null);
  if(value.equals("absent")||value.equals("disabled")||value.equals("pending-disable")||value.equals("mixed"))
   dialog.setPositiveButton("安装／启用",(d,w)->change(activity,true));
  if(value.equals("active")||value.equals("pending-enable")||value.equals("not-effective")||value.equals("mixed"))
   dialog.setNeutralButton("停用",(d,w)->change(activity,false));
  dialog.show();
 }
 private static void change(MainActivity activity,boolean enable){
  String title=enable?"启用红米 Wi-Fi 模块？":"停用红米 Wi-Fi 模块？";
  String prompt=enable?"将通过 Magisk 安装或启用随助手提供的模块。整机重启后生效。":
      "将只停用本助手的红米 Wi-Fi 模块。重启后，Wi-Fi 恢复系统策略。";
  activity.confirm(title,prompt,()->activity.async(()->run(activity,enable?"enable":"disable"),v->display(activity,v)));
 }
 private static String message(String state){
  switch(state){
   case "unsupported":return "此手机型号或 Android 版本不受支持。";
   case "no-magisk":return "需要 Magisk 和已授予的 Root 权限。";
   case "no-target":return "此系统的 Wi-Fi 资源不兼容，无法安装。";
   case "absent":return "尚未安装。";
   case "pending-enable":return "模块已准备启用。请重启后回来确认生效状态。";
   case "active":return "已生效。系统已加载本模块，Wi-Fi 服务报告息屏优化已关闭。";
   case "pending-disable":return "已设置停用。本次开机仍加载着模块，重启后恢复系统策略。";
   case "disabled":return "已停用，当前系统未加载本模块。";
   case "mixed":return "当前模块与待更新副本的开关不同。请重新选择启用或停用。";
   case "not-effective":return "模块已加载，但尚未确认 Wi-Fi 服务已采用设置。重启后再次查看。";
   case "removing":return "Magisk 已安排移除此模块。重启后再查看。";
   case "conflict":return "发现同名模块或覆盖包与内置版本不一致。请在 Magisk 中核对来源。";
   case "bad-asset":return "内置模块校验失败，请重新安装正式签名的助手。";
   case "install-failed":return "Magisk 未完成模块安装，请查看 Magisk 日志后重试。";
   default:return "无法核实模块状态，请刷新后重试。";
  }
 }
 private static String run(Context context,String action)throws Exception{
  if(!Build.DEVICE.equals("chopin")||Build.VERSION.SDK_INT!=33)return "unsupported";
  RootBridge.verifySelf(context);
  String script=new String(asset(context,"redmi-wifi-control.sh"),StandardCharsets.UTF_8);
  String payload="";
  if(action.equals("enable")){
   byte[] zip=asset(context,"redmi-wifi-module.zip");
   if(!MODULE_SHA.equals(RootBridge.hex(MessageDigest.getInstance("SHA-256").digest(zip))))return "bad-asset";
   payload=Base64.encodeToString(zip,Base64.NO_WRAP);
  }
  String launch=BB+" ash -c "+quote(script)+" redmi-wifi "+action+" "+quote(payload);
  if(!action.equals("status"))launch="if [ -L "+LOCK+" ]; then echo conflict; else "+BB+" flock -n "+LOCK+" "+launch+"; fi";
  return RootBridge.run("if [ ! -x "+BB+" ]; then echo no-magisk; else "+launch+"; fi",null,60);
 }
 private static String quote(String value){return "'"+value.replace("'","'\"'\"'")+"'";}
 private static byte[] asset(Context context,String name)throws IOException{
  try(InputStream in=context.getAssets().open("compat/"+name);ByteArrayOutputStream out=new ByteArrayOutputStream()){
   byte[] chunk=new byte[4096];int count;
   while((count=in.read(chunk))!=-1){if(out.size()+count>65536)throw new IOException("内置模块文件大小不符");out.write(chunk,0,count);}
   return out.toByteArray();
  }
 }
 private RedmiWifiModule(){}
}
