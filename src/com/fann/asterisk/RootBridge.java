package com.fann.asterisk;

import android.content.Context;
import java.io.*;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;

final class RootBridge {
 static long runtimeStamp(Context c){try{return c.getPackageManager().getPackageInfo(c.getPackageName(),0).lastUpdateTime;}catch(Exception e){return -1;}}
 static String busybox()throws Exception{
  String command="for p in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do if [ -x \"$p\" ]; then echo \"$p\"; exit 0; fi; done; exit 20";
  String path=run(command,null,8);
  if(!path.matches("/data/adb/(magisk|ksu/bin|ap/bin)/busybox"))throw new IOException("需要 Root 管理器提供 BusyBox；请检查 Magisk、KernelSU 或 APatch 安装");
  return path;
 }

 static final String BASE="/data/adb/asterisk-app";
 static final String CERT="b7f7a97088b3860cfbdd1935e82a5409151fdac10057f5c22138091395f8b26d";
 static synchronized String run(String command, JSONObject input, int seconds) throws Exception {
  Process p=(android.os.Process.myUid()==0?new ProcessBuilder("/system/bin/sh","-c",command):new ProcessBuilder("su","-M","-c",command)).redirectErrorStream(true).start();
  ByteArrayOutputStream out=new ByteArrayOutputStream();
  Thread reader=new Thread(()->{try{byte[] b=new byte[8192];int n;while((n=p.getInputStream().read(b))!=-1){if(out.size()<1048576)out.write(b,0,n);}}catch(Exception ignored){}});
  reader.start();
  try(OutputStream stdin=p.getOutputStream()){if(input!=null)stdin.write(input.toString().getBytes("UTF-8"));}
  if(!p.waitFor(seconds,TimeUnit.SECONDS)){p.destroyForcibly();throw new IOException("操作超时，请刷新查看状态");}
  reader.join(3000);
  String value=out.toString("UTF-8").trim();
  if(p.exitValue()!=0){
   JSONObject result=parse(value);
   if(result!=null)throw new IOException(result.optString("error","操作失败"));
   if(value.endsWith("start_failed"))throw new IOException("服务器启动失败，请查看运行日志或重新部署修复");
   if(value.endsWith("wifi_not_ready"))throw new IOException("请连接 Wi-Fi 后重试");
   if(value.endsWith("not_installed"))throw new IOException("请先点击一键部署 Asterisk");
   if(value.endsWith("selftest_required")||value.endsWith("migration_not_verified"))throw new IOException("请先迁移配置并完成回声自检");
   throw new IOException("Root 操作失败，请确认已授权并查看部署进度");
  }
  return value;
 }
 static JSONObject parse(String value){String[] lines=value.split("\n");for(int i=lines.length-1;i>=0;i--){try{return new JSONObject(lines[i]);}catch(Exception ignored){}}return null;}
 static JSONObject api(String action,JSONObject data)throws Exception{
  if(!action.matches("status|logs|accounts|credentials|save_account|delete_account|read_file|save_file|restore_file|set_ports|set_public_ipv6|set_callerid|selftest|migration_verify"))throw new IOException("无效操作");
  JSONObject result=parse(run(BASE+"/control.sh "+(action.equals("status")?"status":"api "+action),data,60));
  if(result==null)throw new IOException("服务器未返回有效状态");
  if(!result.optBoolean("ok"))throw new IOException(result.optString("error","操作失败"));
  return result;
 }
 static void stage(Context context)throws Exception{
  String installedMonitor=run("sha256sum "+BASE+"/health.sh 2>/dev/null | cut -d ' ' -f 1 || true",null,8);

  verifySelf(context);String apkHash=hash(new File(context.getApplicationInfo().sourceDir));
  File directory=new File(context.getFilesDir(),"runtime");directory.mkdirs();
  for(String name:context.getAssets().list("runtime")){
   if(!name.matches("[a-z0-9][a-z0-9-]*\\.(sh|py)")&&!name.equals("phonenumberslite-9.0.42-py2.py3-none-any.whl"))continue;
   try(InputStream in=context.getAssets().open("runtime/"+name);OutputStream out=new FileOutputStream(new File(directory,name))){byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);}
  }
  String source=directory.getAbsolutePath();
  File wheel=new File(directory,"phonenumberslite-9.0.42-py2.py3-none-any.whl");if(!hash(wheel).equals("7ae0a97b12e9f0749e7bed2c9c3da4df43648ea5ba021de86b36088d98a0915e"))throw new IOException("内置号码库校验失败");
  String command="set -eu; umask 077; if [ -e "+BASE+" ] && [ ! -f "+BASE+"/.asterisk-app-owned ]; then exit 21; fi; mkdir -p "+BASE+"; chmod 700 "+BASE+"; touch "+BASE+"/.asterisk-app-owned; cp "+source+"/* "+BASE+"/; chmod 700 "+BASE+"/*.sh; mkdir -p /data/adb/service.d; cp "+BASE+"/97-asterisk-app.sh /data/adb/service.d/97-asterisk-app.sh; chmod 700 /data/adb/service.d/97-asterisk-app.sh; if [ -d "+BASE+"/rootfs/opt/asterisk-app ]; then chmod 755 "+BASE+"/rootfs; cp "+BASE+"/*.py "+BASE+"/*.whl "+BASE+"/run.sh "+BASE+"/rootfs/opt/asterisk-app/; fi; echo ready";
  run(command,null,30);
  // First-install default for tested Android 11-13; preserve an explicit opt-out.
  if(android.os.Build.VERSION.SDK_INT<=33)run("if [ ! -f "+BASE+"/wifi-compat.configured ]; then touch "+BASE+"/wifi-compat.enabled "+BASE+"/wifi-compat.configured; fi",null,8);
  // Retire only our old migration hook. The APK now starts the same owned worker.
  run("if [ -f /data/adb/service.d/98-asterisk-wifi-compat.sh ] && grep -q 'Local Android 13 restore compatibility' /data/adb/service.d/98-asterisk-wifi-compat.sh; then rm /data/adb/service.d/98-asterisk-wifi-compat.sh; fi",null,8);
  run("umask 077; printf '%s\\n' "+apkHash+" > "+BASE+"/health-helper.sha256",null,10);
  syncMonitorWake(context);
  String currentMonitor=run("sha256sum "+BASE+"/health.sh | cut -d ' ' -f 1",null,8);
  if(!installedMonitor.equals(currentMonitor)){
   run("p=$(cat "+BASE+"/health-loop.pid 2>/dev/null); case $p in ''|*[!0-9]*) ;; *) if [ -r /proc/$p/cmdline ] && tr '\\000' ' ' </proc/$p/cmdline | grep -qF '"+BASE+"/health.sh --loop'; then kill -TERM $p; i=0; while kill -0 $p 2>/dev/null && [ $i -lt 10 ]; do sleep 1; i=$((i+1)); done; fi;; esac",null,15);
   if(run("test -f "+BASE+"/health-enabled && echo yes || true",null,8).equals("yes"))healthLaunch();
  }
 }
 static void syncMonitorWake(Context context)throws Exception{
  boolean on=context.getSharedPreferences("app",0).getBoolean("awake",false);
  run(on?"touch "+BASE+"/health-awake":"rm -f "+BASE+"/health-awake; printf '%s\\n' asterisk_monitor > /sys/power/wake_unlock 2>/dev/null || true",null,8);
 }
 static void verifySelf(Context c)throws Exception{
  android.content.pm.PackageInfo p=c.getPackageManager().getPackageInfo("com.fann.asterisk",android.content.pm.PackageManager.GET_SIGNING_CERTIFICATES);
  if(p.signingInfo==null||p.signingInfo.hasMultipleSigners())throw new IOException("助手签名校验失败");
  boolean ok=false;for(android.content.pm.Signature s:p.signingInfo.getApkContentsSigners())if(hex(java.security.MessageDigest.getInstance("SHA-256").digest(s.toByteArray())).equals(CERT))ok=true;
  if(!ok)throw new IOException("助手签名校验失败");
 }
 static String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format(java.util.Locale.ROOT,"%02x",v&255));return s.toString();}
 static String hash(File f)throws Exception{java.security.MessageDigest d=java.security.MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(f)){byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}return hex(d.digest());}
 static void healthConfigure(Context c,boolean on,int minutes)throws Exception{
  HealthPolicy.minutes(Integer.toString(minutes));stage(c);
  run("set -eu; umask 077; printf '%s\\n' "+minutes+" > "+BASE+"/health-minutes.tmp; mv "+BASE+"/health-minutes.tmp "+BASE+"/health-minutes; "+(on?"touch "+BASE+"/health-enabled "+BASE+"/health-now":"rm -f "+BASE+"/health-enabled "+BASE+"/health-now"),null,10);
  if(on)healthLaunch();
 }
 static void healthLaunch()throws Exception{run(busybox()+" setsid /system/bin/sh "+BASE+"/health.sh loop </dev/null >/dev/null 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &",null,10);}
 static void healthNow(Context c)throws Exception{
  stage(c);if(!run("test -f "+BASE+"/health-enabled && echo on || true",null,5).equals("on"))throw new IOException("请先开启自动检查与恢复");
  run("touch "+BASE+"/health-now",null,5);healthLaunch();
 }
 static JSONObject healthStatus()throws Exception{
  String[] lines=run("if [ -f "+BASE+"/health-enabled ]; then echo on; else echo off; fi; cat "+BASE+"/health-minutes 2>/dev/null || echo 5; cat "+BASE+"/health-status.json 2>/dev/null || true",null,8).split("\\n",3);
  JSONObject result=lines.length>2?new JSONObject(lines[2]):new JSONObject();result.put("enabled",lines[0].equals("on"));result.put("minutes",HealthPolicy.minutes(lines[1].trim()));return result;
 }
}
