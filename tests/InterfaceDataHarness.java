package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Runs the actual Android importer logic on desktop fixtures. */
public class InterfaceDataHarness {
    public static void main(String[] args) throws Exception {
        File mpq=new File(args[0]),target=new File(args[1]),temporary=new File(args[1]+".tmp");
        try(FileInputStream in=new FileInputStream(mpq);FileOutputStream out=new FileOutputStream(temporary)) {
            MissionBundle.Result r=MissionBundle.exportInterface(in.getChannel(),InterfaceData.names(),out,System.out::println);
            if(r.files!=16)throw new AssertionError("Expected eight original fonts, five campaign palette files and three custom-menu panels");
        }
        InterfaceData.install(temporary,target);byte[] before=Files.readAllBytes(target.toPath());
        try(ZipFile z=new ZipFile(target)) {
            for(ZipEntry e:Collections.list(z.entries())) {
                if(e.getName().equals("README.txt"))continue;
                try(InputStream a=z.getInputStream(e);InputStream b=CampaignData.open(target,e.getName())) {
                    if(!Arrays.equals(a.readAllBytes(),b.readAllBytes()))throw new AssertionError("Served fonts mismatch");
                }
            }
        }
        Files.write(temporary.toPath(),new byte[]{1,2,3});
        try{InterfaceData.install(temporary,target);throw new AssertionError("Invalid replacement accepted");}catch(IOException expected){}
        if(!Arrays.equals(before,Files.readAllBytes(target.toPath())))throw new AssertionError("Existing fonts damaged");
        temporary.delete();
        // A palette-only/partial import must not be reported as original fonts
        // ready, and must never replace the working interface bundle.
        try(ZipFile original=new ZipFile(target);ZipOutputStream out=new ZipOutputStream(new FileOutputStream(temporary))) {
            for(ZipEntry entry:Collections.list(original.entries())) {
                byte[] data;try(InputStream in=original.getInputStream(entry)){data=in.readAllBytes();}
                if(entry.getName().equals("manifest.json")) {
                    org.json.JSONObject manifest=new org.json.JSONObject(new String(data,"UTF-8"));
                    org.json.JSONArray entries=manifest.getJSONArray("entries");entries.remove(0);
                    data=manifest.toString().getBytes("UTF-8");
                }
                out.putNextEntry(new ZipEntry(entry.getName()));out.write(data);out.closeEntry();
            }
        }
        try{InterfaceData.install(temporary,target);throw new AssertionError("Incomplete fonts accepted");}catch(IOException expected){
            if(!expected.getMessage().contains("font set is incomplete"))throw expected;
        }
        if(!Arrays.equals(before,Files.readAllBytes(target.toPath())))throw new AssertionError("Partial import damaged working fonts");
        temporary.delete();
        try(FileInputStream in=new FileInputStream(args[2]);FileOutputStream out=new FileOutputStream(temporary)) {
            try {MissionBundle.exportInterface(in.getChannel(),InterfaceData.names(),out,p->{});throw new AssertionError("Fonts-less archive accepted");}
            catch(IOException expected){System.out.println("Missing-fonts archive rejected: "+expected.getMessage());}
        }
        temporary.delete();System.out.println("PASS: eight-font export, validated install, local serving, safe replacement, incomplete/missing-font rejection.");
    }
}
