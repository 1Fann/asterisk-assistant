package com.fann.asterisk;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import java.io.File;
import java.io.IOException;

/** Explicit user consent for background access; limited to this assistant's signed components. */
final class BackgroundAccess {
 static String run(String s)throws Exception{return RootBridge.run(s,null,12);}
 static String[] packages(Context c)throws Exception{return new String[]{c.getPackageName()};}
 static String missing(Context c)throws Exception{
  StringBuilder result=new StringBuilder();String white=run("cmd deviceidle whitelist");
  for(String p:packages(c)){
   if(HealthPolicy.backgroundBlocked(run("cmd appops get "+p))||!white.contains(","+p+",")){
    if(result.length()>0)result.append("、");result.append(p.equals(c.getPackageName())?"本助手":"Voice SIP 网关");
   }
  }
  return result.toString();
 }
 static void allow(Context c)throws Exception{
  // Called only after the user accepts the visible background-access explanation.
  RootBridge.stage(c);
  apply(c);
  run("umask 077; touch "+BASE+"/background-authorized");
 }
 static void setting(String command,String label)throws Exception{
  try{run(command);}catch(Exception e){throw new IOException(label+"未完成，请在系统应用信息中手动允许；这不代表 Root 未授权");}
 }
 static void apply(Context c)throws Exception{
  for(String p:packages(c)){
   setting("cmd appops set "+p+" RUN_IN_BACKGROUND allow","后台运行设置");
   setting("cmd appops set "+p+" RUN_ANY_IN_BACKGROUND allow","后台限制设置");
   setting("cmd deviceidle whitelist +"+p+" >/dev/null","电池优化设置");
   if(!run("getprop ro.miui.ui.version.name").isEmpty()){
    // Tested MIUI framework exposes OP_AUTO_START=10008, but its shell rejects AUTO_START.
    // Require that named vendor operation in the actual ROM output before using its numeric ID.
    String ops=run("cmd appops get "+p);
    if(!ops.contains("MIUIOP(10008):"))throw new IOException("当前小米系统未提供可识别的自启动设置，请到应用信息中手动允许自启动");
    setting("cmd appops set "+p+" 10008 allow","小米自启动设置");
   }
  }
  if(!missing(c).isEmpty())throw new IOException("系统仍限制后台运行，请在应用信息中设为不限制，并允许自启动");
 }
 static boolean repairAuthorized(Context c)throws Exception{
  if(missing(c).isEmpty())return true;
  if(!new File(BASE,"background-authorized").isFile())return false;
  apply(c);return true;
 }
 static final String BASE=RootBridge.BASE;
 static void explain(Activity a,Runnable accepted){
  new AlertDialog.Builder(a).setTitle("允许持续后台运行")
   .setMessage("为避免清后台或息屏后断开，需要允许相关应用在后台运行、加入电池优化白名单，并在小米系统允许自启动。点击允许后，由已获 Root 授权的助手完成这些设置。可能增加耗电；不锁定最近任务，也不授予电话、麦克风或通知权限。自动恢复仅在你启用检查且未手动停用服务时执行。")
   .setPositiveButton("允许后台运行",(d,w)->accepted.run()).setNegativeButton("稍后",null).show();
 }
}
