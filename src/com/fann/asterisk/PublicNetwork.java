package com.fann.asterisk;

import android.app.AlertDialog;
import android.widget.*;
import org.json.JSONObject;

/** Public IPv6 is explicit opt-in; credentials and the loopback gateway are preserved. */
final class PublicNetwork {
 static void show(MainActivity a){
  if(!a.latest.optBoolean("installed")){a.toast("请先部署 Asterisk 并刷新状态");return;}
  JSONObject state=a.latest.optJSONObject("publicIpv6");
  LinearLayout form=a.form();Switch enabled=new Switch(a);enabled.setText("启用公网 IPv6 客户端");
  enabled.setChecked(state!=null&&state.optBoolean("enabled"));form.addView(enabled);
  EditText domain=a.input(form,"DDNS 域名（不含端口）",state==null?"":state.optString("domain"),false);
  a.text(form,"客户端改用域名连接，信令和语音均使用 Wi-Fi 非临时公网 IPv6。本机网关继续连接 127.0.0.1。",13,false);
  a.text(form,"Cloudflare 保持仅 DNS；需要客户端网络支持 IPv6、沿途防火墙允许 SIP / RTP。DDNS 由原助手管理。",13,false);
  a.text(form,"IPv6 地址变化由自动检查发现，空闲时重启服务器更新。没有公网 IPv6 时回退局域网配置；请保持自动检查开启。",13,false);
  a.text(form,"公网模式会持有 Wi-Fi 组播接收锁，避免部分 ROM 息屏时过滤 IPv6 邻居发现，会增加耗电。关闭公网模式或停止服务后释放。",13,false);
  AlertDialog dialog=new AlertDialog.Builder(a).setTitle("公网 IPv6 / DDNS").setView(form).setNegativeButton("取消",null).setPositiveButton("保存并重启",null).create();
  dialog.setOnShowListener(x->dialog.getButton(-1).setOnClickListener(v->{
   boolean on=enabled.isChecked();String host=domain.getText().toString().trim();
   a.async(()->{RootBridge.run(RootBridge.BASE+"/control.sh network-state",null,10);return RootBridge.api("set_public_ipv6",new JSONObject().put("enabled",on).put("domain",host)).optString("message");},s->{dialog.dismiss();a.toast(s);a.service("RESTART");});
  }));dialog.show();
 }
}
