package com.fann.asterisk;
/** Host checks for decisions that must never interrupt a call or accept shell input. */
public class HealthPolicyChecks {
 static int passed;
 static void require(boolean value){if(!value)throw new AssertionError();passed++;}
 public static void main(String[] args)throws Exception{
  require(HealthPolicy.minutes("1")==1);require(HealthPolicy.minutes("1440")==1440);
  for(String value:new String[]{null,"0","1441","-1","1.5","5; id","$(id)","99999",""}){
   try{HealthPolicy.minutes(value);throw new AssertionError("accepted invalid interval");}catch(java.io.IOException expected){passed++;}
  }
  String idle="    mCallState=0\n    mCallState=0\n";
  require(HealthPolicy.idle(idle,"0 active calls\n",true));
  require(!HealthPolicy.idle("mCallState=0\nmCallState=1\n","0 active calls\n",true));
  require(!HealthPolicy.idle("mCallState=2\n","0 active calls\n",true));
  require(!HealthPolicy.idle("", "0 active calls\n",true));
  require(!HealthPolicy.idle(idle,"1 active calls\n",true));
  require(!HealthPolicy.idle(idle,"",true));
  require(HealthPolicy.idle(idle,"",false));
  require(!HealthPolicy.healthy("ready=false shizuku=CONNECTED audioReady=true sip=ready"));
  require(!HealthPolicy.healthy("ready=true shizuku=BINDING audioReady=false sip=down"));
  require(HealthPolicy.healthy("ready=true shizuku=CONNECTED audioReady=true sip=ready"));
  System.out.println("PASS: "+passed+" monitor policy checks");
 }
}
