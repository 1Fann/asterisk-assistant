package com.fann.asterisk;
import android.content.Context;
import android.os.Looper;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.UUID;
import org.json.JSONObject;
/** Server-only health and recovery. Never starts or changes the cellular gateway. */
public final class HealthMain {
 static final String BASE=RootBridge.BASE;
 static String message="检查尚未完成",phase="initialize",error="",observedPid="";static boolean repaired,retrySoon,fastStarted;
 static String fastGate="not_checked",fastRuntime="not_checked",fastError="";static long fastStartedAt,fastElapsedMs;
 static final java.util.Map<String,Long> fastStages=new java.util.LinkedHashMap<>();
 static Context context;
 static boolean enabled(){return new File(BASE,"health-enabled").isFile();}
 static boolean wanted(){return new File(BASE,"installed").isFile()&&!new File(BASE,"disabled").exists();}
 static boolean idle()throws Exception{
  boolean running=RootBridge.run(BASE+"/control.sh state",null,8).equals("running");
  String channels=running?RootBridge.run(BASE+"/control.sh cli core show channels count",null,10):"0 active calls\n";
  return HealthPolicy.idle(RootBridge.run("dumpsys telephony.registry",null,12),channels,true);
 }
 static void guard()throws Exception{if(!enabled()||!wanted()||!idle())throw new IOException("paused_or_busy");}
 public static void main(String[] args){
  if(android.os.Process.myUid()!=0)throw new SecurityException();
  if(args.length==1)observedPid=args[0];
  try{
   Looper.prepareMainLooper();Class<?> at=Class.forName("android.app.ActivityThread");Object thread=at.getMethod("systemMain").invoke(null);
   Context system=(Context)at.getMethod("getSystemContext").invoke(thread);
   context=system.createPackageContext("com.fann.asterisk",Context.CONTEXT_INCLUDE_CODE|Context.CONTEXT_IGNORE_SECURITY);
   RootBridge.verifySelf(context);if(!enabled())return;
   check();
  }catch(Exception e){retrySoon=enabled()&&!"paused_or_busy".equals(e.getMessage());error=e.getClass().getSimpleName();if(e.getStackTrace().length>0){StackTraceElement f=e.getStackTrace()[0];error+=":"+f.getMethodName()+":"+f.getLineNumber();}message="服务器检查或恢复未完成，下轮重试";}
  finally{save();if(retrySoon)System.exit(75);}
 }
 static void check()throws Exception{
  phase="server_check";
  if(!new File(BASE,"installed").isFile()){message="尚未部署 Asterisk";return;}
  if(!wanted()){message="服务器已手动停止，暂停自动恢复";return;}
  fastStarted=tryEngineRecovery();
  if(!idle()){message="正在通话或无法确认通话状态，本轮跳过恢复";return;}
  String ip=RootBridge.run("ip -4 -o addr show wlan0",null,8);
  if(ip.isEmpty()){retrySoon=true;message="等待 Wi-Fi，本轮不重启服务器";return;}
  if(!BackgroundAccess.repairAuthorized(context)){message="后台运行受限，请打开助手允许后台运行与自启动";return;}
  String owner=RootBridge.run("dumpsys activity services com.fann.asterisk",null,10);
  boolean running=RootBridge.run(BASE+"/control.sh state",null,10).equals("running");
  if(!running||!owner.contains("isForeground=true")){
   guard();phase="server_foreground";
   try{RootBridge.run("am start-foreground-service --user 0 -n com.fann.asterisk/.ManagerService --es action START",null,15);}catch(IOException ignored){}
   repaired=true;awaitForegroundAndEngine(4000);
   owner=RootBridge.run("dumpsys activity services com.fann.asterisk",null,10);
   if(!owner.contains("isForeground=true")){
    guard();RootBridge.run("am start -n com.fann.asterisk/.MainActivity",null,15);Thread.sleep(2000);
    guard();RootBridge.run("am start-foreground-service --user 0 -n com.fann.asterisk/.ManagerService --es action START",null,15);Thread.sleep(2000);
   }
  }
  JSONObject snapshot=new JSONObject(RootBridge.run(BASE+"/control.sh status",null,15));
  if(!snapshot.optBoolean("running")){retrySoon=true;message="服务器启动尚未完成，下轮重试";return;}
  int port=snapshot.getJSONObject("ports").getInt("localPort");
  String address=snapshot.optString("ip");boolean changed=!address.isEmpty()&&!ip.contains(" "+address+"/");
  JSONObject publicNetwork=snapshot.optJSONObject("publicIpv6");
  String publicAddress="";int publicPort=snapshot.getJSONObject("ports").getInt("lanPort");
  if(publicNetwork!=null&&publicNetwork.optBoolean("enabled")){
   String current6=RootBridge.run(BASE+"/control.sh ipv6",null,8);
   publicAddress=current6;
   changed|=!current6.equals(snapshot.optString("ipv6"));
  }
  if(changed||(!sipAlive(port)&&!sipAlive(port))||(!publicAddress.isEmpty()&&!sipAlive(publicAddress,publicPort))){
   guard();phase="server_restart";RootBridge.run(BASE+"/control.sh restart",null,40);repaired=true;
  }
  owner=RootBridge.run("dumpsys activity services com.fann.asterisk",null,10);
  boolean ok=RootBridge.run(BASE+"/control.sh state",null,8).equals("running")&&owner.contains("isForeground=true")&&sipAlive(port)&&(publicAddress.isEmpty()||sipAlive(publicAddress,publicPort));
  retrySoon=!ok;
  message=ok?(repaired?"已恢复 Asterisk，后台网络与 SIP 响应正常":"Asterisk、后台网络服务与 SIP 响应正常"):"服务器恢复尚未完成，下轮重试";
 }
 static boolean tryEngineRecovery(){fastStartedAt=android.os.SystemClock.elapsedRealtime();try{
  return EngineRecovery.attempt(observedPid,new EngineRecovery.Host(){
   public void stage(String name){fastGate=name;fastStages.put(name,android.os.SystemClock.elapsedRealtime()-fastStartedAt);}
   public boolean missing(int oldPid)throws Exception{
    return RootBridge.run("if kill -0 "+oldPid+" 2>/dev/null; then echo alive; elif [ -d /proc/"+oldPid+" ]; then echo unknown; elif [ -r /proc/1/stat ]; then echo absent; else echo unknown; fi",null,5).equals("absent");
   }
   public boolean authorized()throws Exception{return enabled()&&wanted()&&new File(BASE,"background-authorized").isFile()&&!RootBridge.run("ip -4 -o addr show wlan0",null,8).isEmpty();}
   public boolean foreground()throws Exception{return RootBridge.run("dumpsys activity services com.fann.asterisk",null,10).contains("isForeground=true");}
   public boolean runtimeValid()throws Exception{fastRuntime=RootBridge.stagedRuntimeStatus(context);return fastRuntime.equals("valid");}
   public Boolean idle()throws Exception{return HealthMain.idle();}
   public void verifySignature()throws Exception{RootBridge.verifySelf(context);}
   public void start()throws Exception{
    phase="engine_fast_start";RootBridge.run(BASE+"/control.sh recover",null,40);repaired=true;
    // Preserve the manager's CPU/Wi-Fi lock synchronization after native launch,
    // without a START action that could clear a newly requested manual stop.
    RootBridge.run("am start-foreground-service --user 0 -n com.fann.asterisk/.ManagerService --es action SYNC_RUNTIME",null,15);
   }
  });
 }catch(Exception failure){fastError=failure.getClass().getSimpleName();return false;}
 finally{fastElapsedMs=android.os.SystemClock.elapsedRealtime()-fastStartedAt;}}
 static void awaitForegroundAndEngine(long budgetMillis)throws Exception{
  long deadline=android.os.SystemClock.elapsedRealtime()+budgetMillis;
  while(enabled()&&wanted()&&android.os.SystemClock.elapsedRealtime()<deadline){
   try{
    if(RootBridge.run("dumpsys activity services com.fann.asterisk",null,1).contains("isForeground=true")
      &&android.os.SystemClock.elapsedRealtime()<deadline
      &&RootBridge.run(BASE+"/control.sh state",null,1).equals("running"))return;
   }catch(IOException ignored){} // Keep the existing fallback and SIP validation after the wait.
   long left=deadline-android.os.SystemClock.elapsedRealtime();if(left>0)Thread.sleep(Math.min(250,left));
  }
 }
 static boolean sipAlive(int port){
  return sipAlive("127.0.0.1",port);
 }
 static boolean sipAlive(String host,int port){
  if(port<1024||port>65535)return false;
  try(DatagramSocket socket=new DatagramSocket()){
   socket.connect(InetAddress.getByName(host),port);
   String target=host.contains(":")?"["+host+"]":host;
   String local=socket.getLocalAddress().getHostAddress();if(local.contains(":"))local="["+local+"]";
   socket.setSoTimeout(2000);String id=UUID.randomUUID().toString();
   String request="OPTIONS sip:health@"+target+":"+port+" SIP/2.0\r\nVia: SIP/2.0/UDP "+local+":"+socket.getLocalPort()+";branch=z9hG4bK"+id+";rport\r\nFrom: <sip:health@localhost>;tag="+id+"\r\nTo: <sip:health@localhost>\r\nCall-ID: "+id+"\r\nCSeq: 1 OPTIONS\r\nMax-Forwards: 0\r\nContent-Length: 0\r\n\r\n";
   byte[] b=request.getBytes(StandardCharsets.US_ASCII);socket.send(new DatagramPacket(b,b.length,InetAddress.getByName(host),port));
   byte[] out=new byte[8192];DatagramPacket packet=new DatagramPacket(out,out.length);socket.receive(packet);
   String reply=new String(out,0,packet.getLength(),StandardCharsets.US_ASCII);return reply.startsWith("SIP/2.0 ")&&reply.contains("Call-ID: "+id);
  }catch(Exception e){return false;}
 }
 static void save(){try{
  JSONObject j=new JSONObject();j.put("checkedAt",System.currentTimeMillis());j.put("message",message);j.put("repaired",repaired);j.put("phase",phase);j.put("error",error);j.put("fastStarted",fastStarted);
  j.put("fastGate",fastGate);j.put("fastRuntime",fastRuntime);j.put("fastError",fastError);j.put("fastElapsedMs",fastElapsedMs);j.put("fastStagesMs",new JSONObject(fastStages));
  File temp=new File(BASE,"health-status.tmp");try(FileOutputStream out=new FileOutputStream(temp)){out.write(j.toString().getBytes(StandardCharsets.UTF_8));}
  if(!temp.renameTo(new File(BASE,"health-status.json")))temp.delete();
 }catch(Exception ignored){}}
}
