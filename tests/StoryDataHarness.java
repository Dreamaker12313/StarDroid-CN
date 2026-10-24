package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;
public class StoryDataHarness {
 public static void main(String[] args)throws Exception{
  for(boolean movies:new boolean[]{false,true}){
   File target=new File(args[1],movies?StoryData.MOVIES:StoryData.NAME),stage=new File(target+".tmp");
   try(FileInputStream in=new FileInputStream(args[0]);FileOutputStream out=new FileOutputStream(stage)){
    MissionBundle.Result r=MissionBundle.exportStory(in.getChannel(),StoryData.names(movies),out,p->{},movies);
    if(!r.missing.isEmpty()||r.files!=StoryData.names(movies).size())throw new AssertionError("Incomplete original fixture");
   }
   StoryData.install(stage,target,movies);byte[] before=Files.readAllBytes(target.toPath());
   try(InputStream in=CampaignData.open(target,"manifest.json")){if(in.read()<0)throw new AssertionError("Empty served manifest");}
   Files.write(stage.toPath(),new byte[]{1,2,3});
   try{StoryData.install(stage,target,movies);throw new AssertionError("Bad replacement accepted");}catch(IOException expected){}
   if(!Arrays.equals(before,Files.readAllBytes(target.toPath())))throw new AssertionError("Existing content lost");stage.delete();
   try{StoryData.validate(target,!movies);throw new AssertionError("Wrong bundle accepted");}catch(IOException expected){}
   System.out.println("PASS "+target.getName()+": original entries, validated atomic install, local serving, corrupt/wrong-format rejection");
  }
 }
}
