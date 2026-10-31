package com.fann.asterisk;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.util.Map;
import java.util.TreeMap;

/** Pure policy tests and commands consumed by the isolated filesystem fixture. */
public class RuntimeStageCacheChecks {
 static int passed;
 static void require(boolean value){if(!value)throw new AssertionError();passed++;}
 static String digest(String text)throws Exception{
  StringBuilder value=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8)))value.append(String.format("%02x",b&255));return value.toString();
 }
 public static void main(String[] args)throws Exception{
  Map<String,String> hashes=new TreeMap<>();
  for(String name:new String[]{"control.sh","run.sh","enter.sh","api.py","health.sh","network-cache.sh","97-asterisk-app.sh","health-helper.sha256","phonenumberslite-9.0.42-py2.py3-none-any.whl"})hashes.put(name,digest("#!/bin/sh\n# fixture:"+name+"\n"));
  String host=RuntimeStageCache.manifest(hashes,false),rootfs=RuntimeStageCache.manifest(hashes,true);
  require(RuntimeStageCache.eligible(42,42,host));
  require(!RuntimeStageCache.eligible(43,42,host));
  require(!RuntimeStageCache.eligible(-1,-1,host));
  require(!RuntimeStageCache.eligible(0,0,host));
  require(!RuntimeStageCache.eligible(42,42,""));
  require(!RuntimeStageCache.eligible(42,42,null));
  require(RuntimeStageCache.parse(host).equals(hashes));
  require(RuntimeStageCache.parse(rootfs).equals(hashes));
  require(!host.endsWith("\n")&&!rootfs.endsWith("\n"));
  // Exact on-device failure: Android indented </string> after a terminal newline.
  require(RuntimeStageCache.parse(rootfs+"\n    ").equals(hashes));
  require(RuntimeStageCache.parse(rootfs+"\n\t  \n\n").equals(hashes));
  String windowsRootfs=rootfs.replace("\n","\r\n")+"\r\n    ";
  require(RuntimeStageCache.parse(windowsRootfs).equals(hashes));
  require(RuntimeStageCache.verificationCommand("/fixture","/hook.sh",windowsRootfs).contains("test -d /fixture/rootfs/opt/asterisk-app\n"));
  require(RuntimeStageCache.verificationCommand("/fixture","/hook.sh",rootfs).equals(RuntimeStageCache.verificationCommand("/fixture","/hook.sh",windowsRootfs)));
  for(String invalid:new String[]{"",host.replace("control.sh","../control.sh"),host.replace("health.sh","health.sh;id"),host.replace("host\n","wrong\n"),host+"\n"+host.substring(host.indexOf('\n')+1),host.replace("control.sh","missing.sh"),host.replaceFirst("[a-f0-9]{64}","invalid"),host.replaceFirst("\n","\n    \n"),host.replaceFirst("\n","\n\n"),host+" ",host+"\n  not-an-entry\n    ",host.replace("control.sh","control\r.sh")}){
   try{RuntimeStageCache.parse(invalid);throw new AssertionError("accepted invalid manifest");}catch(IOException expected){passed++;}
  }
  if(args.length==3){
   Files.write(Paths.get(args[2],"host.sh"),RuntimeStageCache.verificationCommand(args[0],args[1],host).getBytes(StandardCharsets.UTF_8));
   Files.write(Paths.get(args[2],"rootfs.sh"),RuntimeStageCache.verificationCommand(args[0],args[1],rootfs).getBytes(StandardCharsets.UTF_8));
  }
  System.out.println("PASS: "+passed+" runtime stage policy checks");
 }
}
