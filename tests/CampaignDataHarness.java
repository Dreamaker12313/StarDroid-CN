package org.openbw.androidtest;
import java.io.*;
import java.util.zip.*;
import java.util.Arrays;
public class CampaignDataHarness {
    public static void main(String[] args) throws Exception {
        File source = new File(args[0]), target = new File(args[1]);
        byte[] before = target.exists() ? java.nio.file.Files.readAllBytes(target.toPath()) : null;
        if (args.length > 2) {
            try (InputStream in = new FileInputStream(source)) {
                try { CampaignData.copy(in, target); throw new AssertionError("Invalid bundle accepted"); }
                catch (IOException expected) { System.out.println("Rejected: " + expected.getMessage()); }
            }
            if (!Arrays.equals(before, java.nio.file.Files.readAllBytes(target.toPath()))) throw new AssertionError("Invalid import damaged existing mission");
            return;
        }
        try (InputStream in = new FileInputStream(source)) { CampaignData.copy(in,target); }
        if (!Arrays.equals(java.nio.file.Files.readAllBytes(source.toPath()), java.nio.file.Files.readAllBytes(target.toPath()))) throw new AssertionError("Copy mismatch");
        try (ZipFile z = new ZipFile(target)) {
            java.util.Enumeration<? extends ZipEntry> entries = z.entries();
            while(entries.hasMoreElements()) {
                ZipEntry e = entries.nextElement(); if (e.getName().equals("README.txt")) continue;
                try(InputStream a=z.getInputStream(e); InputStream b=CampaignData.open(target,e.getName())) {
                    if(!Arrays.equals(a.readAllBytes(),b.readAllBytes())) throw new AssertionError("Read mismatch");
                }
            }
        }
        try { CampaignData.open(target,"../manifest.json"); throw new AssertionError("Unsafe path accepted"); }
        catch(IOException expected) {}
        System.out.println("Mission import and every served entry match uploaded ZIP; unsafe path rejected.");
    }
}
