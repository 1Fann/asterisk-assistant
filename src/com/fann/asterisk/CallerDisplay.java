package com.fann.asterisk;

import android.app.AlertDialog;
import android.widget.*;
import org.json.JSONObject;

final class CallerDisplay {
 static void show(MainActivity a){
  if(!a.latest.optBoolean("installed")){a.toast("请先一键部署 Asterisk");return;}
  JSONObject current=a.latest.optJSONObject("callerId");
  LinearLayout form=a.form();Switch enabled=new Switch(a);enabled.setText("来电号码自动分段");
  enabled.setChecked(current==null||current.optBoolean("enabled",true));form.addView(enabled);
  EditText region=a.input(form,"无国家区号时的默认地区",current==null?"CN":current.optString("defaultRegion","CN"),false);
  a.text(form,"CN：中国大陆 · HK：香港 · TW：台湾 · US：美国 · GB：英国。带 + 国家区号的号码会自动识别。",13,false);
  a.text(form,"号码库已内置，手机离线处理。仅调整显示名称，保留真实号码、隐私状态和联系人姓名；短号及无法识别的号码保持原样。",13,false);
  if(current!=null&&current.optBoolean("pending"))a.text(form,"等待空闲时完成自动配置；请稍后刷新。",13,false);
  AlertDialog dialog=new AlertDialog.Builder(a).setTitle("来电号码分段").setView(form).setNegativeButton("取消",null).setPositiveButton("保存",null).create();
  dialog.setOnShowListener(x->dialog.getButton(-1).setOnClickListener(v->{boolean on=enabled.isChecked();String code=region.getText().toString().trim();a.async(()->RootBridge.api("set_callerid",new JSONObject().put("enabled",on).put("defaultRegion",code)).optString("message"),s->{dialog.dismiss();a.toast(s);a.refresh(false);});}));dialog.show();
 }
}
