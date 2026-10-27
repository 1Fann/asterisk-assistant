package com.fann.asterisk;

import android.content.Context;
import java.io.*;
import java.util.concurrent.TimeUnit;
import org.json.JSONObject;

final class RootBridge {
 static final String BASE="/data/adb/asterisk-app";
 static synchronized String run(String command, JSONObject input, int seconds) throws Exception {
  Process p=new ProcessBuilder("su","-M","-c",command).redirectErrorStream(true).start();
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
  if(!action.matches("status|logs|accounts|credentials|save_account|delete_account|read_file|save_file|restore_file|set_ports|selftest|migration_verify"))throw new IOException("无效操作");
  JSONObject result=parse(run(BASE+"/control.sh "+(action.equals("status")?"status":"api "+action),data,60));
  if(result==null)throw new IOException("服务器未返回有效状态");
  if(!result.optBoolean("ok"))throw new IOException(result.optString("error","操作失败"));
  return result;
 }
 static void stage(Context context)throws Exception{
  File directory=new File(context.getFilesDir(),"runtime");directory.mkdirs();
  for(String name:context.getAssets().list("runtime")){
   try(InputStream in=context.getAssets().open("runtime/"+name);OutputStream out=new FileOutputStream(new File(directory,name))){byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);}
  }
  String source=directory.getAbsolutePath();
  String command="set -eu; umask 077; if [ -e "+BASE+" ] && [ ! -f "+BASE+"/.asterisk-app-owned ]; then exit 21; fi; mkdir -p "+BASE+"; chmod 700 "+BASE+"; touch "+BASE+"/.asterisk-app-owned; cp "+source+"/* "+BASE+"/; chmod 700 "+BASE+"/*.sh; mkdir -p /data/adb/service.d; cp "+BASE+"/97-asterisk-app.sh /data/adb/service.d/97-asterisk-app.sh; chmod 700 /data/adb/service.d/97-asterisk-app.sh; if [ -d "+BASE+"/rootfs/opt/asterisk-app ]; then chmod 755 "+BASE+"/rootfs; cp "+BASE+"/*.py "+BASE+"/run.sh "+BASE+"/rootfs/opt/asterisk-app/; fi; echo ready";
  run(command,null,30);
 }
}
