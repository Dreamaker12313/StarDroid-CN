package org.openbw.androidtest;
import java.io.*;
public final class NativeDataHarness {
 public static void main(String[] args)throws Exception{
  File dir=new File(args[1]);int count=0;
  for(File zip:new File(args[0]).listFiles())if(zip.getName().endsWith(".zip")){
   File out=NativeData.prepare(zip,dir,zip.getName().replace(".zip",""));
   if(out==null||!out.isFile())throw new AssertionError(zip);
   if(!out.equals(NativeData.prepare(zip,dir,zip.getName().replace(".zip",""))))throw new AssertionError("Cache mismatch");
   count++;
  }
  System.out.println("Reconstructed and cached "+count+" imported bundles");
 }
}
