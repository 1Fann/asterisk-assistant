package com.fann.asterisk;

/** Restrict direct recovery to a previously observed engine loss, never a startup guess. */
final class EngineRecovery {
 interface Host {
  default void stage(String name){}
  boolean missing(int oldPid)throws Exception;
  boolean authorized()throws Exception;
  boolean foreground()throws Exception;
  boolean runtimeValid()throws Exception;
  Boolean idle()throws Exception;
  void verifySignature()throws Exception;
  void start()throws Exception;
 }
 static boolean attempt(String observedPid,Host host)throws Exception{
  host.stage(observedPid==null||observedPid.isEmpty()?"no_event":"event");
  if(observedPid==null||!observedPid.matches("[1-9][0-9]*"))return false;
  int pid;try{pid=Integer.parseInt(observedPid);}catch(NumberFormatException invalid){return false;}
  if(pid<=1)return false;
  host.stage("pid_missing");if(!host.missing(pid))return false;
  host.stage("authorization");if(!host.authorized())return false;
  host.stage("foreground");if(!host.foreground())return false;
  host.stage("runtime");if(!host.runtimeValid())return false;
  host.stage("idle");
  if(!Boolean.TRUE.equals(host.idle()))return false;
  host.stage("signature");
  host.verifySignature();
  host.stage("authorization_final");if(!host.authorized())return false;
  host.stage("pid_missing_final");if(!host.missing(pid))return false;
  host.stage("launch");host.start();host.stage("started");return true;
 }
}
