package org.openbw.androidtest;

import java.io.*;
import java.nio.channels.FileChannel;
import java.util.*;

/** One local import operation installs the campaigns and their presentation. */
final class GameContent {
    interface Names { List<String> forMission(String id) throws IOException; }
    static String install(FileChannel input, File directory, boolean expansion,
                          Names names, MissionBundle.Progress progress) throws IOException {
        File stage = new File(directory, "content-import.tmp");
        int count = 0; List<String> problems = new ArrayList<String>();
        try {
            for (Object[] item : CampaignCatalog.ALL) {
                int code = (Integer)item[0]; if (CampaignCatalog.expansion(code) != expansion) continue;
                String id = CampaignCatalog.id(code);
                try {
                    List<String> paths = names.forMission(id);
                    try (FileOutputStream out = new FileOutputStream(stage)) {
                        MissionBundle.export(input, paths, paths.get(0), out,
                            value -> progress.update(CampaignCatalog.title(code) + " · " + value));
                    }
                    try (FileInputStream bundle = new FileInputStream(stage)) {
                        CampaignData.copy(bundle, new File(directory, CampaignData.filename(id)));
                    }
                    count++;
                } catch (Exception e) { problems.add(CampaignCatalog.title(code) + ": " + e.getMessage()); }
            }
            if (count == 0) throw new IOException("No campaign maps found. Choose the large " + (expansion ? "BroodWar.mpq" : "StarCraft.mpq") + " archive.");
            if (!expansion) {
                try {
                    InterfaceData.importArchive(input, directory, progress);
                    File target = new File(directory, InterfaceData.NAME);
                    if (!InterfaceData.hasCampaignPalette(target))
                        problems.add("Campaign artwork is unavailable in this archive.");
                } catch (Exception e) { problems.add("Interface: " + e.getMessage()); }
            }
            try {
                try (FileOutputStream out = new FileOutputStream(stage)) { MissionBundle.exportMusic(input, MusicData.names(), out, progress); }
                MusicData.install(stage, new File(directory, expansion ? "StarDroid-Music-BroodWar.zip" : MusicData.NAME));
            } catch (Exception e) { problems.add("Music: " + e.getMessage()); }
            try {
                try (FileOutputStream out = new FileOutputStream(stage)) { MissionBundle.exportStory(input, StoryData.names(false), out, progress, false); }
                StoryData.install(stage, new File(directory, expansion ? "StarDroid-Story-BroodWar.zip" : StoryData.NAME), false);
            } catch (Exception e) { problems.add("Mission openings: " + e.getMessage()); }
            {
                try {
                    try (FileOutputStream out = new FileOutputStream(stage)) { MissionBundle.exportStory(input, StoryData.names(true), out, progress, true); }
                    StoryData.install(stage, new File(directory, expansion ? StoryData.EXP_MOVIES : StoryData.MOVIES), true);
                } catch (Exception e) { problems.add("Movies: " + e.getMessage()); }
            }
            return (expansion ? "Brood War" : "StarCraft") + ": " + count + " maps imported."
                + (problems.isEmpty() ? " Music, mission openings and cinematics included." : "\nNeeds attention:\n" + String.join("\n", problems));
        } finally { stage.delete(); }
    }
}
