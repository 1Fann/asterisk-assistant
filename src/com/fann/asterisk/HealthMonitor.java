package com.fann.asterisk;
import android.widget.*;
import android.text.InputType;
import java.text.DateFormat;
import java.util.Date;
import org.json.JSONObject;
/** The server monitor has its own settings and status, independent of Voice SIP Assistant. */
final class HealthMonitor {
 final MainActivity a;Switch enabled;EditText minutes;TextView status;Button save,now;boolean updating,busy,initialized;JSONObject last=new JSONObject();
 HealthMonitor(MainActivity activity){
  a=activity;LinearLayout card=a.card();a.text(card,"自动检查与恢复",18,true);
  a.text(card,"每秒检查服务器与守护进程是否退出，异常退出时优先快速恢复；每 10 秒确认前台服务，按下方间隔完整检查后台网络与实际 SIP 响应。清理助手后台仍有效，开机首次解锁后恢复检查；通话中或状态不明时暂停修复，手动停止后不拉起。必要时可能打开管理页，深度休眠或网络异常可能延后恢复。",13,false);
  enabled=new Switch(a);enabled.setText("开启服务器自动检查与恢复");card.addView(enabled);
  enabled.setOnCheckedChangeListener((b,on)->{if(updating)return;updating=true;enabled.setChecked(!on);updating=false;configure(on);});
  a.text(card,"检查间隔（分钟，1–1440）",14,false);minutes=new EditText(a);minutes.setInputType(InputType.TYPE_CLASS_NUMBER);minutes.setSingleLine(true);minutes.setText("5");card.addView(minutes);
  save=a.button(card,"保存检查间隔",()->configure(last.optBoolean("enabled")));
  now=a.button(card,"立即检查并恢复",()->{if(busy)return;working(true);a.async(()->{try{RootBridge.healthNow(a);return "已提交立即检查";}finally{a.runOnUiThread(()->working(false));}},s->{a.toast(s);refresh();});});
  status=a.text(card,"正在读取检查设置…",13,false);
 }
 void working(boolean value){busy=value;save.setEnabled(!value);now.setEnabled(!value);enabled.setEnabled(!value);minutes.setEnabled(!value);}
 void configure(boolean on){
  if(busy)return;final int value;try{value=HealthPolicy.minutes(minutes.getText().toString().trim());}catch(Exception e){minutes.setError(e.getMessage());return;}
  working(true);a.async(()->{try{RootBridge.healthConfigure(a,on,value);return RootBridge.healthStatus().toString();}finally{a.runOnUiThread(()->working(false));}},s->{try{render(new JSONObject(s),true);}catch(Exception ignored){}a.toast(on?"已开启服务器自动恢复":"已关闭自动检查，服务器继续运行");});
 }
 void refresh(){if(busy)return;a.async(()->RootBridge.healthStatus().toString(),s->{try{render(new JSONObject(s),false);}catch(Exception ignored){}});}
 void render(JSONObject data,boolean saved){last=data;updating=true;enabled.setChecked(data.optBoolean("enabled"));updating=false;if(!initialized||saved||!minutes.hasFocus())minutes.setText(Integer.toString(data.optInt("minutes",5)));initialized=true;
  String text=data.optBoolean("enabled")?"每秒检查进程 · 每 "+data.optInt("minutes",5)+" 分钟完整检查":"自动检查已关闭";long time=data.optLong("checkedAt");if(time>0)text+="\n上次检查："+DateFormat.getDateTimeInstance(DateFormat.SHORT,DateFormat.MEDIUM).format(new Date(time))+"\n"+data.optString("message");status.setText(text);
 }
}
