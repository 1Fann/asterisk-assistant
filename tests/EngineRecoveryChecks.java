package com.fann.asterisk;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public final class EngineRecoveryChecks {
 static int passed;
 static void require(boolean value){if(!value)throw new AssertionError();passed++;}
 static final class Host implements EngineRecovery.Host {
  boolean missing=true,authorized=true,foreground=true,runtime=true,signed=true,started;
  Boolean idle=Boolean.TRUE;String revoke="";List<String> order=new ArrayList<>();
  public boolean missing(int pid){order.add("missing");return missing;}
  public boolean authorized(){order.add("authorized");return authorized;}
  public boolean foreground(){order.add("foreground");return foreground;}
  public boolean runtimeValid(){order.add("runtime");return runtime&&signed;}
  public Boolean idle(){order.add("idle");if(revoke.equals("pid"))missing=false;if(revoke.equals("stop"))authorized=false;if(revoke.equals("signature"))signed=false;return idle;}
  public void verifySignature()throws IOException{order.add("signature");if(!signed)throw new IOException("changed");}
  public void start(){order.add("start");started=true;}
 }
 public static void main(String[] args)throws Exception{
  for(String value:new String[]{null,"","0","1","-4","2 3","12;id","2147483648"}){
   Host h=new Host();require(!EngineRecovery.attempt(value,h));require(!h.started&&h.order.isEmpty());
  }
  Host healthy=new Host();require(EngineRecovery.attempt("4321",healthy));
  require(healthy.started&&String.join(",",healthy.order).equals("missing,authorized,foreground,runtime,idle,signature,authorized,missing,start"));
  for(String rejected:new String[]{"alive","authorization","foreground","runtime","signature","call","unknown"}){
   Host h=new Host();
   switch(rejected){case "alive":h.missing=false;break;case "authorization":h.authorized=false;break;case "foreground":h.foreground=false;break;case "runtime":h.runtime=false;break;case "signature":h.signed=false;break;case "call":h.idle=false;break;case "unknown":h.idle=null;break;}
   require(!EngineRecovery.attempt("4321",h));require(!h.started);
  }
  for(String revoke:new String[]{"pid","stop","signature"}){
   Host h=new Host();h.revoke=revoke;
   try{require(!EngineRecovery.attempt("4321",h));}catch(IOException expected){require(revoke.equals("signature"));}
   require(!h.started);
  }
  System.out.println("PASS: "+passed+" restricted engine recovery checks");
 }
}
