package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
public final class GameContentHarness {
 public static void main(String[] args) throws Exception {
  File dir=new File(args[1]);dir.mkdirs();boolean expected=Boolean.parseBoolean(args[2]);
  try(RandomAccessFile f=new RandomAccessFile(args[0],"r")){
   if(MissionBundle.expansionArchive(f.getChannel())!=expected)throw new AssertionError("Wrong game detected");
   String result=GameContent.install(f.getChannel(),dir,expected,id->Files.readAllLines(Paths.get(args[3],id+"-files.txt")),message->{});
   System.out.println(result);if(result.contains("Needs attention"))throw new AssertionError(result);
  }
  int count=0;
  for(Object[] row:CampaignCatalog.ALL)if((Boolean)row[4]==expected){String id=(String)row[1];File zip=new File(dir,CampaignData.filename(id));if(!zip.isFile())throw new AssertionError(id);try(ZipFile z=new ZipFile(zip)){String manifest=new String(z.getInputStream(z.getEntry("manifest.json")).readAllBytes(),"UTF-8");if(!manifest.contains("\"mission\":\""+id+"\""))throw new AssertionError(id+" manifest identity");}count++;}
  if(count!=(expected?33:31))throw new AssertionError("Catalog count "+count);
  System.out.println("Validated "+count+" maps, each imported through the app validator.");
 }
}
