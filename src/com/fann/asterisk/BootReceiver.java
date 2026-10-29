package com.fann.asterisk;
import android.content.*;
public class BootReceiver extends BroadcastReceiver {
 public void onReceive(Context c,Intent i){
  String action=i.getAction();
  if(Intent.ACTION_MY_PACKAGE_REPLACED.equals(action)){
   try{c.startForegroundService(new Intent(c,ManagerService.class).putExtra("action","UPDATE"));}catch(Exception ignored){}
  }else if(Intent.ACTION_BOOT_COMPLETED.equals(action)&&c.getSharedPreferences("app",0).getBoolean("autostart",false)){
   try{c.startForegroundService(new Intent(c,ManagerService.class).putExtra("action","BOOT"));}catch(Exception ignored){}
  }
 }
}
