package com.fann.asterisk;

import java.io.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Deterministic exit notification, error, timeout and cancellation semantics. */
public final class ProcessExitChecks {
 static final class Child extends Process {
  final CountDownLatch entered=new CountDownLatch(1),finished=new CountDownLatch(1);
  volatile boolean destroyed,fail;final int code;
  Child(int code){this.code=code;}
  public int waitFor()throws InterruptedException{entered.countDown();if(fail)throw new IllegalStateException();finished.await();return code;}
  public boolean waitFor(long n,TimeUnit unit){throw new AssertionError("timed polling must not be used");}
  public int exitValue(){throw new AssertionError("no exitValue polling");}
  public void destroy(){destroyed=true;finished.countDown();}
  public Process destroyForcibly(){destroy();return this;}
  public InputStream getInputStream(){throw new AssertionError("exit must not depend on stdout EOF");}
  public InputStream getErrorStream(){throw new AssertionError();}
  public OutputStream getOutputStream(){throw new AssertionError();}
 }
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args)throws Exception{
  Child quick=new Child(7);quick.finished.countDown();
  check(ProcessExit.await(quick,2,TimeUnit.SECONDS)==7&&!quick.destroyed);
  Child later=new Child(0);
  Thread completes=new Thread(()->{try{later.entered.await();later.finished.countDown();}catch(InterruptedException e){throw new AssertionError(e);}});
  completes.start();check(ProcessExit.await(later,2,TimeUnit.SECONDS)==0&&!later.destroyed);completes.join();
  Child timeout=new Child(0);
  try{ProcessExit.await(timeout,25,TimeUnit.MILLISECONDS);throw new AssertionError();}catch(IOException expected){check(timeout.destroyed);}
  Child cancelled=new Child(0);AtomicBoolean interrupted=new AtomicBoolean();
  Thread caller=new Thread(()->{try{ProcessExit.await(cancelled,30,TimeUnit.SECONDS);}catch(InterruptedException expected){interrupted.set(true);}catch(IOException e){throw new AssertionError(e);}});
  caller.start();check(cancelled.entered.await(2,TimeUnit.SECONDS));caller.interrupt();caller.join(2000);
  check(!caller.isAlive()&&interrupted.get()&&cancelled.destroyed);
  Child failed=new Child(0);failed.fail=true;
  try{ProcessExit.await(failed,2,TimeUnit.SECONDS);throw new AssertionError();}catch(IOException expected){check(failed.destroyed&&expected.getCause() instanceof IllegalStateException);}
  System.out.println("PASS: 5 notification-based subprocess exit cases");
 }
}
