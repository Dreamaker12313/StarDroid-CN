package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Runs the actual Android importer logic on desktop fixtures. */
public class MusicDataHarness {
    public static void main(String[] args) throws Exception {
        File mpq=new File(args[0]),target=new File(args[1]),temporary=new File(args[1]+".tmp");
        try(FileInputStream in=new FileInputStream(mpq);FileOutputStream out=new FileOutputStream(temporary)) {
            MissionBundle.Result r=MissionBundle.exportMusic(in.getChannel(),MusicData.names(),out,System.out::println);
            if(r.files!=4)throw new AssertionError("Expected four test tracks, including title music");
        }
        MusicData.install(temporary,target);byte[] before=Files.readAllBytes(target.toPath());
        try(ZipFile z=new ZipFile(target)) {
            for(ZipEntry e:Collections.list(z.entries())) {
                if(e.getName().equals("README.txt"))continue;
                try(InputStream a=z.getInputStream(e);InputStream b=CampaignData.open(target,e.getName())) {
                    if(!Arrays.equals(a.readAllBytes(),b.readAllBytes()))throw new AssertionError("Served music mismatch");
                }
            }
        }
        Files.write(temporary.toPath(),new byte[]{1,2,3});
        try{MusicData.install(temporary,target);throw new AssertionError("Invalid replacement accepted");}catch(IOException expected){}
        if(!Arrays.equals(before,Files.readAllBytes(target.toPath())))throw new AssertionError("Existing music damaged");
        temporary.delete();
        try(FileInputStream in=new FileInputStream(args[2]);FileOutputStream out=new FileOutputStream(temporary)) {
            try {MissionBundle.exportMusic(in.getChannel(),MusicData.names(),out,p->{});throw new AssertionError("Music-less archive accepted");}
            catch(IOException expected){System.out.println("Missing-music archive rejected: "+expected.getMessage());}
        }
        temporary.delete();System.out.println("PASS: music export, validated install, local serving, safe replacement, missing-track handling.");
    }
}
