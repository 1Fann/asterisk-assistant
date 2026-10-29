package com.fann.asterisk;

import java.io.IOException;
import java.util.regex.*;

/** Shared, fail-closed decisions; no Android dependencies. */
final class HealthPolicy {
 static int minutes(String input)throws IOException {
  if(input==null||!input.matches("[0-9]{1,4}"))throw new IOException("检查间隔请输入 1–1440 分钟");
  int value=Integer.parseInt(input);
  if(value<1||value>1440)throw new IOException("检查间隔请输入 1–1440 分钟");
  return value;
 }
 static boolean backgroundBlocked(String value){
  for(String line:value.split("\n"))if(line.matches(".*(?:RUN_ANY_IN_BACKGROUND|RUN_IN_BACKGROUND|MIUIOP\\(10008\\)):\\s*(?:ignore|deny|errored).*"))return true;
  return false;
 }
 static boolean healthy(String status){return status.contains("ready=true")&&status.contains("shizuku=CONNECTED")&&status.contains("audioReady=true")&&status.contains("sip=ready");}
 static boolean idle(String registry,String pbx,boolean serverExpected){
  Matcher m=Pattern.compile("(?m)^\\s*mCallState=([0-9]+)\\s*$").matcher(registry);
  boolean found=false;while(m.find()){found=true;if(!m.group(1).equals("0"))return false;}
  if(!found)return false;
  if(serverExpected){Matcher c=Pattern.compile("(?m)^([0-9]+) active calls\\s*$").matcher(pbx);return c.find()&&c.group(1).equals("0");}
  return true;
 }
}
