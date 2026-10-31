package com.fann.asterisk;

import android.app.*;
import android.content.*;
import android.os.*;
import android.net.wifi.WifiManager;
import java.io.*;
import java.net.*;
import javax.net.ssl.HttpsURLConnection;
import java.security.MessageDigest;
import java.util.concurrent.Executors;
import org.json.JSONObject;

public class ManagerService extends Service {
 static volatile String message="就绪";
 static volatile boolean busy=false;
 static final String SHA="a91d5a93010193712d346d761372b7c9db6dfcf093893161c64ca107f05914f2";
 final java.util.concurrent.ExecutorService worker=Executors.newSingleThreadExecutor();
 PowerManager.WakeLock wake;
 WifiManager.MulticastLock multicast;
 WifiManager.WifiLock receiveLock;
 void multicast(boolean enabled){
  if(multicast==null){WifiManager wifi=getApplicationContext().getSystemService(WifiManager.class);if(wifi==null)return;multicast=wifi.createMulticastLock("asterisk:ipv6-neighbor");multicast.setReferenceCounted(false);}
  if(receiveLock==null){receiveLock=getApplicationContext().getSystemService(WifiManager.class).createWifiLock(WifiManager.WIFI_MODE_FULL_HIGH_PERF,"asterisk:receive");receiveLock.setReferenceCounted(false);}
  if(enabled&&!receiveLock.isHeld())receiveLock.acquire();
  if(!enabled&&receiveLock.isHeld())receiveLock.release();
  if(enabled&&!multicast.isHeld())multicast.acquire();
  if(!enabled&&multicast.isHeld())multicast.release();
 }
 void syncNetworkLock()throws Exception{
  JSONObject s=RootBridge.api("status",null),p=s.optJSONObject("publicIpv6");
  multicast(s.optBoolean("running")&&p!=null&&p.optBoolean("enabled"));
 }
 String recoveryOwnerState()throws Exception{
  return RootBridge.run("if [ ! -f "+RootBridge.BASE+"/installed ] || [ -f "+RootBridge.BASE+"/disabled ]; then echo stopped; elif [ ! -f "+RootBridge.BASE+"/health-enabled ]; then echo paused; else "+RootBridge.BASE+"/control.sh state; fi",null,10);
 }
 void syncAfterRecovery(int startId)throws Exception{
  String state=recoveryOwnerState();
  if(state.equals("paused"))return; // Disabling monitoring alone must not stop a running server.
  if(state.equals("running")){
   awake(getSharedPreferences("app",0).getBoolean("awake",false));syncNetworkLock();
   state=recoveryOwnerState();
  }
  if(state.equals("stopped")){awake(false);multicast(false);stopForeground(STOP_FOREGROUND_REMOVE);stopSelf(startId);}
 }
 public void onCreate(){super.onCreate();NotificationManager manager=getSystemService(NotificationManager.class);manager.createNotificationChannel(new NotificationChannel("server","SIP 服务器",NotificationManager.IMPORTANCE_LOW));notice("服务器管理已启动");}
 void notice(String text){Intent intent=new Intent(this,MainActivity.class);PendingIntent pending=PendingIntent.getActivity(this,0,intent,PendingIntent.FLAG_IMMUTABLE|PendingIntent.FLAG_UPDATE_CURRENT);Notification n=new Notification.Builder(this,"server").setSmallIcon(android.R.drawable.stat_notify_sync).setContentTitle("Asterisk 助手").setContentText(text).setContentIntent(pending).setOngoing(true).build();startForeground(10,n);}
 void report(String text){message=text;getSharedPreferences("app",0).edit().putString("message",text).apply();notice(text);}
 void awake(boolean enabled){if(wake==null){wake=((PowerManager)getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,"asterisk:server");wake.setReferenceCounted(false);}if(enabled&&!wake.isHeld())wake.acquire();if(!enabled&&wake.isHeld())wake.release();}
 public int onStartCommand(Intent intent,int flags,int startId){
  String action=intent==null?"BOOT":intent.getStringExtra("action");if(action==null)action="BOOT";
  final String task=action;
  final boolean healthEnabled=intent!=null&&intent.getBooleanExtra("healthEnabled",false);
  final String healthMinutes=intent==null?null:intent.getStringExtra("healthMinutes");
  if(task.equals("WAKE")){awake(getSharedPreferences("app",0).getBoolean("awake",false));worker.submit(()->{try{RootBridge.syncMonitorWake(this);}catch(Exception e){report("唤醒设置未同步，请重试");}});return START_STICKY;}
  if(task.equals("SYNC_RUNTIME")){
   // The verified root monitor already restored the engine. This request may only
   // synchronize existing locks; a delayed request must never clear manual STOP.
   worker.submit(()->{try{syncAfterRecovery(startId);}catch(Exception ignored){message="运行锁状态同步未完成，请刷新检查";}});
   return START_STICKY;
  }
  if(busy){message="正在处理上一项操作";return START_STICKY;}
  busy=true;
  worker.submit(()->{try{
   report("正在准备…");if(task.equals("START")||task.equals("BOOT"))RootBridge.ensureStaged(this);else RootBridge.stage(this);
   if(task.equals("UPDATE")){
    RootBridge.api("status",null);
    if(RootBridge.run("test -f "+RootBridge.BASE+"/health-enabled && echo yes || true",null,5).equals("yes"))RootBridge.healthLaunch();
    if(RootBridge.run(RootBridge.BASE+"/control.sh state",null,8).equals("running"))RootBridge.run(RootBridge.BASE+"/control.sh start",null,30);
    report("运行组件与号码分段已更新；通话中的变更会延后生效");
    getSharedPreferences("app",0).edit().putLong("runtimeStamp",RootBridge.runtimeStamp(this)).apply();
    if(!RootBridge.run(RootBridge.BASE+"/control.sh state",null,8).equals("running")){stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}
   }else if(task.equals("DEPLOY")){
    awake(true);report("正在下载并验证 Ubuntu ARM64 运行环境…");File archive=download();report("正在安装 Asterisk，首次部署可能需要数分钟…");
    RootBridge.run(RootBridge.BASE+"/install.sh "+archive.getAbsolutePath()+" "+android.os.Process.myUid(),null,1800);
    RootBridge.run(RootBridge.BASE+"/control.sh start",null,40);getSharedPreferences("app",0).edit().putBoolean("autostart",true).apply();report("部署完成，服务器已启动");
   }else if(task.equals("IMPORT")){
    report("正在迁移现有账号与拨号配置…");RootBridge.run(RootBridge.BASE+"/migrate.sh",null,120);report("正在验证账号认证与语音回声…");JSONObject result=RootBridge.api("selftest",null);report("迁移成功，回声包 "+result.optInt("echoPackets")+"；旧部署保留待清理");
   }else if(task.equals("CLEANUP")){
    report("正在核对并删除旧部署…");RootBridge.run(RootBridge.BASE+"/cleanup-legacy.sh",null,90);report("旧部署已清理，当前由本 App 管理");
   }else if(task.equals("SELFTEST")){
    JSONObject result=RootBridge.api("selftest",null);report("自检通过：账号 "+result.optJSONArray("testedAccounts")+"，回声包 "+result.optInt("echoPackets"));
   }else if(task.equals("HEALTH_CONFIG")){
    RootBridge.healthConfigure(this,healthEnabled,HealthPolicy.minutes(healthMinutes));report(healthEnabled?"已启用服务器自动检查":"已关闭服务器自动检查");
   }else if(task.equals("STOP")){
    RootBridge.run(RootBridge.BASE+"/control.sh stop",null,35);report("服务器已停止");awake(false);stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();
   }else if(task.equals("BOOT")){
    boolean manuallyStopped=RootBridge.run("test -f "+RootBridge.BASE+"/disabled && echo yes || true",null,8).equals("yes");
    if(getSharedPreferences("app",0).getBoolean("autostart",true)&&!manuallyStopped){RootBridge.run(RootBridge.BASE+"/control.sh start",null,40);report("服务器已自动启动");}else{stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}
   }else if(task.equals("START")||task.equals("RESTART")){
    RootBridge.run(RootBridge.BASE+"/control.sh "+(task.equals("START")?"start":"restart"),null,65);report("服务器运行中");
   }else throw new IOException("未知操作");
  }catch(Exception error){report(error.getMessage()==null?"操作失败，请刷新查看":error.getMessage());}
  finally{busy=false;if(task.equals("STOP"))multicast(false);else{awake(getSharedPreferences("app",0).getBoolean("awake",false));try{syncNetworkLock();}catch(Exception e){report("IPv6 Wi-Fi 接收锁未就绪，请刷新并重启服务");}}}});
  return START_STICKY;
 }
 File download()throws Exception{
  File target=new File(getFilesDir(),"ubuntu-base.tar.gz");if(target.exists()&&digest(target).equals(SHA))return target;
  File partial=new File(getFilesDir(),"ubuntu-base.part");
  HttpsURLConnection connection=(HttpsURLConnection)new URL("https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/ubuntu-base-24.04.5-base-arm64.tar.gz").openConnection();
  connection.setConnectTimeout(30000);connection.setReadTimeout(45000);connection.setInstanceFollowRedirects(true);
  try{if(connection.getResponseCode()!=200)throw new IOException("运行环境下载失败，请检查网络后重试");long length=connection.getContentLengthLong(),total=0;int last=-1;
   try(InputStream in=connection.getInputStream();OutputStream out=new FileOutputStream(partial)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){out.write(b,0,n);total+=n;int percent=length>0?(int)(total*100/length):0;if(percent/10!=last){last=percent/10;report("下载运行环境 "+percent+"%");}}}
  }finally{connection.disconnect();}
  if(!digest(partial).equals(SHA)){partial.delete();throw new IOException("下载校验失败，请重试");}
  if(target.exists()&&!target.delete())throw new IOException("无法更新下载文件");if(!partial.renameTo(target))throw new IOException("无法保存下载文件");return target;
 }
 String digest(File file)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=new FileInputStream(file)){byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)d.update(b,0,n);}StringBuilder s=new StringBuilder();for(byte b:d.digest())s.append(String.format("%02x",b&255));return s.toString();}
 public void onDestroy(){awake(false);multicast(false);worker.shutdown();super.onDestroy();}
 public IBinder onBind(Intent intent){return null;}
}
