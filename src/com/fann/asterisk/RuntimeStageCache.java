package com.fann.asterisk;

import java.io.IOException;
import java.util.Map;
import java.util.TreeMap;

/** A private, APK-stamped manifest; every cache hit still checks the actual root files. */
final class RuntimeStageCache {
 static boolean eligible(long installed,long saved,String manifest){return installed>0&&installed==saved&&manifest!=null&&!manifest.isEmpty();}
 static boolean assetName(String name){return name.matches("[a-z0-9][a-z0-9-]*\\.(sh|py)")||name.equals("phonenumberslite-9.0.42-py2.py3-none-any.whl");}
 static String manifest(Map<String,String> hashes,boolean rootfs)throws IOException{
  // A terminal newline causes Android's XML serializer to append closing-tag
  // indentation to this String when it is loaded by the next process.
  StringBuilder result=new StringBuilder(rootfs?"rootfs":"host");
  for(Map.Entry<String,String> entry:new TreeMap<>(hashes).entrySet())result.append('\n').append(entry.getValue()).append("  ").append(entry.getKey());
  parse(result.toString());return result.toString();
 }
 static TreeMap<String,String> parse(String manifest)throws IOException{
  if(manifest==null||manifest.length()>32768)throw new IOException("Invalid runtime manifest");
  String[] lines=manifest.split("\n",-1);int end=lines.length;
  // Accept only terminal whitespace-only lines introduced by XML formatting.
  // Interior blank lines, padded entries, malformed hashes and paths remain invalid.
  while(end>0&&lines[end-1].matches("[ \\t\\r]*"))end--;
  for(int i=0;i<end;i++)if(lines[i].endsWith("\r"))lines[i]=lines[i].substring(0,lines[i].length()-1);
  if(end<2||!(lines[0].equals("rootfs")||lines[0].equals("host")))throw new IOException("Invalid runtime manifest");
  TreeMap<String,String> hashes=new TreeMap<>();
  for(int i=1;i<end;i++){
   if(lines[i].length()<67||!lines[i].substring(0,64).matches("[0-9a-f]{64}")||!lines[i].substring(64,66).equals("  "))throw new IOException("Invalid runtime hash");
   String name=lines[i].substring(66);
   if((!assetName(name)&&!name.equals("health-helper.sha256"))||hashes.put(name,lines[i].substring(0,64))!=null)throw new IOException("Invalid runtime file");
  }
  for(String name:new String[]{"control.sh","run.sh","enter.sh","api.py","health.sh","97-asterisk-app.sh","health-helper.sha256"})if(!hashes.containsKey(name))throw new IOException("Incomplete runtime manifest");
  return hashes;
 }
 static String verificationCommand(String base,String hook,String manifest)throws IOException{
  if(!base.matches("/[a-zA-Z0-9/_-]+")||!hook.matches("/[a-zA-Z0-9/_.-]+"))throw new IOException("Invalid runtime path");
  TreeMap<String,String> hashes=parse(manifest),files=new TreeMap<>();
  boolean rootfs=manifest.startsWith("rootfs\n")||manifest.startsWith("rootfs\r\n");
  for(Map.Entry<String,String> entry:hashes.entrySet()){
   String name=entry.getKey();files.put(base+"/"+name,entry.getValue());
   if(rootfs&&(name.endsWith(".py")||name.endsWith(".whl")||name.equals("run.sh")))files.put(base+"/rootfs/opt/asterisk-app/"+name,entry.getValue());
  }
  files.put(hook,hashes.get("97-asterisk-app.sh"));
  StringBuilder command=new StringBuilder("set -eu\ntest -d "+base+"\ntest -f "+base+"/.asterisk-app-owned\n");
  command.append(rootfs?"test -d "+base+"/rootfs/opt/asterisk-app\n":"test ! -d "+base+"/rootfs/opt/asterisk-app\ntest ! -f "+base+"/installed\n");
  // One stat process checks all owners; no per-file su or process launch.
  command.append("owners=$(stat -c %u ").append(base).append(' ').append(base).append("/.asterisk-app-owned");
  if(rootfs)command.append(' ').append(base).append("/rootfs/opt/asterisk-app");
  for(String path:files.keySet())command.append(' ').append(path);
  command.append(") || exit 1\ntest -n \"$owners\"\nfor owner in $owners; do test \"$owner\" = 0 || exit 1; done\n");
  for(String path:files.keySet())if(path.endsWith(".sh")&&!path.startsWith(base+"/rootfs/"))command.append("test -x ").append(path).append('\n');
  command.append("sha256sum -c <<'ASTERISK_RUNTIME_HASHES' >/dev/null 2>&1\n");
  for(Map.Entry<String,String> entry:files.entrySet())command.append(entry.getValue()).append("  ").append(entry.getKey()).append('\n');
  return command.append("ASTERISK_RUNTIME_HASHES\necho valid\n").toString();
 }
}
