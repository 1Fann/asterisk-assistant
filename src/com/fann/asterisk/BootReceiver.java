package com.fann.asterisk;
import android.content.*;
public class BootReceiver extends BroadcastReceiver {
 public void onReceive(Context c,Intent i){if(Intent.ACTION_BOOT_COMPLETED.equals(i.getAction())&&c.getSharedPreferences("app",0).getBoolean("autostart",false)){try{c.startForegroundService(new Intent(c,ManagerService.class).putExtra("action","BOOT"));}catch(Exception ignored){}}}
}
