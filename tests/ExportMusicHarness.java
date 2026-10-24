package org.openbw.androidtest;
import java.io.*;

/** Exercise the production importer with a locally supplied original archive. */
public class ExportMusicHarness {
    public static void main(String[] args) throws Exception {
        File target = new File(args[1]);
        try (FileInputStream in = new FileInputStream(args[0]); FileOutputStream out = new FileOutputStream(target)) {
            MissionBundle.Result result = MissionBundle.exportMusic(in.getChannel(), MusicData.names(), out, message -> {});
            System.out.println("Exported " + result.files + " tracks; missing=" + result.missing);
        }
        MusicData.validate(target);
        System.out.println("PASS: production music import validation");
    }
}
