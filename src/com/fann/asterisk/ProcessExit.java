package com.fann.asterisk;

import java.io.IOException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** Wait for a short root subprocess exit without Android's timed waitFor polling tick. */
final class ProcessExit {
 static int await(Process process,long duration,TimeUnit unit)throws IOException,InterruptedException{
  // Wait on the child, independently of stdout: a descendant can keep its pipe open.
  FutureTask<Integer> exit=new FutureTask<>(()->process.waitFor());
  Thread waiter=new Thread(exit,"asterisk-process-exit");waiter.setDaemon(true);waiter.start();
  boolean completed=false;
  try{int code=exit.get(duration,unit);completed=true;return code;}
  catch(TimeoutException timeout){throw new IOException("操作超时，请刷新查看状态");}
  catch(ExecutionException failure){throw new IOException("无法读取操作退出状态",failure.getCause());}
  finally{
   if(!completed){process.destroyForcibly();exit.cancel(true);}
  }
 }
}
