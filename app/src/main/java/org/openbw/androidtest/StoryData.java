package org.openbw.androidtest;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import org.json.*;

/** Small establishing shots and optional original movies, selected locally. */
final class StoryData {
    static final String NAME="StarDroid-Story.zip", MOVIES="StarDroid-Cinematics.zip", EXP_MOVIES="StarDroid-Cinematics-BroodWar.zip";
    static Set<String> installedMovies(File directory) {
        Set<String> result = new HashSet<String>();
        for (String name : new String[] {MOVIES, EXP_MOVIES}) {
            File file = ProjectFiles.existing(directory, name);
            if (!file.isFile()) continue;
            try (ZipFile zip = new ZipFile(file)) {
                ZipEntry entry = zip.getEntry("manifest.json");
                if (entry == null) continue;
                JSONObject manifest;
                try (InputStream in = zip.getInputStream(entry)) {
                    manifest = new JSONObject(new String(NativeData.read(in, 131072), "UTF-8"));
                }
                if (!"openbw-cinematic-bundle-v1".equals(manifest.optString("format"))) continue;
                JSONArray entries = manifest.getJSONArray("entries");
                for (int i = 0; i < entries.length(); i++) {
                    JSONObject movie = entries.getJSONObject(i);
                    if (zip.getEntry("blocks/" + movie.getInt("block") + ".bin") != null)
                        result.add(movie.getString("name").replace('\\', '/').toLowerCase(Locale.ROOT));
                }
            } catch (IOException | JSONException ignored) { }
        }
        return result;
    }
    static List<String> names(boolean movies) {
        if(movies)return CinematicCatalog.names();
        return Arrays.asList("rez\\estp01.txt","rez\\estp01x.txt","rez\\estp02.txt","rez\\estp02x.txt","rez\\estp03.txt","rez\\estp03x.txt","rez\\estp04.txt","rez\\estp04x.txt","rez\\estp05.txt","rez\\estp05x.txt","rez\\estp06.txt","rez\\estp06x.txt","rez\\estp07.txt","rez\\estp07x.txt","rez\\estp08.txt","rez\\estp08x.txt","rez\\estp09.txt","rez\\estp0t.txt","rez\\estp10.txt","rez\\estt01.txt","rez\\estt01x.txt","rez\\estt02.txt","rez\\estt02x.txt","rez\\estt03.txt","rez\\estt03x.txt","rez\\estt04.txt","rez\\estt04x.txt","rez\\estt05.txt","rez\\estt05ax.txt","rez\\estt05bx.txt","rez\\estt06.txt","rez\\estt06x.txt","rez\\estt07.txt","rez\\estt07x.txt","rez\\estt08.txt","rez\\estt08x.txt","rez\\estt09.txt","rez\\estt0t.txt","rez\\estt10.txt","rez\\estt11.txt","rez\\estt12.txt","rez\\estz01.txt","rez\\estz01x.txt","rez\\estz02.txt","rez\\estz02x.txt","rez\\estz03.txt","rez\\estz03x.txt","rez\\estz04.txt","rez\\estz04x.txt","rez\\estz05.txt","rez\\estz05x.txt","rez\\estz06.txt","rez\\estz06x.txt","rez\\estz07.txt","rez\\estz07x.txt","rez\\estz08.txt","rez\\estz08x.txt","rez\\estz09.txt","rez\\estz09bx.txt","rez\\estz09x.txt","rez\\estz0t.txt","rez\\estz10.txt","rez\\estz10x.txt","glue\\palpa\\blank.pcx","glue\\palpa\\protossa.pcx","glue\\palpa\\tfont.pcx","glue\\palpax\\blank.pcx","glue\\palpax\\tfont.pcx","glue\\palpax\\xprotosa.pcx","glue\\palpb\\blank.pcx","glue\\palpb\\protossb.pcx","glue\\palpb\\tfont.pcx","glue\\palpbx\\blank.pcx","glue\\palpbx\\tfont.pcx","glue\\palpbx\\xprotosb.pcx","glue\\palpc\\blank.pcx","glue\\palpc\\protossc.pcx","glue\\palpc\\tfont.pcx","glue\\palpcx\\blank.pcx","glue\\palpcx\\tfont.pcx","glue\\palpcx\\xprotosc.pcx","glue\\palta\\blank.pcx","glue\\palta\\terrana.pcx","glue\\palta\\tfont.pcx","glue\\paltax\\blank.pcx","glue\\paltax\\tfont.pcx","glue\\paltax\\xterrana.pcx","glue\\paltb\\blank.pcx","glue\\paltb\\terranb.pcx","glue\\paltb\\tfont.pcx","glue\\paltbx\\blank.pcx","glue\\paltbx\\tfont.pcx","glue\\paltbx\\xterranb.pcx","glue\\paltc\\blank.pcx","glue\\paltc\\terranc.pcx","glue\\paltc\\tfont.pcx","glue\\paltcx\\blank.pcx","glue\\paltcx\\tfont.pcx","glue\\paltcx\\xterranc.pcx","glue\\palza\\blank.pcx","glue\\palza\\tfont.pcx","glue\\palza\\zerga.pcx","glue\\palzax\\blank.pcx","glue\\palzax\\tfont.pcx","glue\\palzax\\xzerga.pcx","glue\\palzb\\blank.pcx","glue\\palzb\\tfont.pcx","glue\\palzb\\zergb.pcx","glue\\palzbx\\blank.pcx","glue\\palzbx\\tfont.pcx","glue\\palzbx\\xzergb.pcx","glue\\palzc\\blank.pcx","glue\\palzc\\tfont.pcx","glue\\palzc\\zergc.pcx","glue\\palzcx\\blank.pcx","glue\\palzcx\\tfont.pcx","glue\\palzcx\\xzergc.pcx");
    }
    static void install(File temporary,File target,boolean movies)throws IOException {
        validate(temporary,movies);
        Files.move(temporary.toPath(),target.toPath(),StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
    }
    static void validate(File file,boolean movies)throws IOException {
        long limit=(movies?768L:16L)*1024*1024;
        try(ZipFile zip=new ZipFile(file)) {
            if(file.length()>limit||zip.size()>264)throw new IOException("Import is too large.");
            ZipEntry me=zip.getEntry("manifest.json");if(me==null||me.getSize()<1||me.getSize()>131072)throw new IOException("Missing manifest.");
            ByteArrayOutputStream out=new ByteArrayOutputStream();
            try(InputStream in=zip.getInputStream(me)){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>131072)throw new IOException("Manifest too large.");out.write(b,0,n);}}
            JSONObject m=new JSONObject(new String(out.toByteArray(),"UTF-8"));
            if(!("openbw-"+(movies?"cinematic":"story")+"-bundle-v1").equals(m.getString("format")))throw new IOException("Wrong content import.");
            for(String n:new String[]{"header.bin","hash-table.bin","block-table.bin"}){ZipEntry e=zip.getEntry(n);if(e==null||e.getSize()<1||e.getSize()>8*1024*1024||(n.equals("header.bin")&&e.getSize()!=32))throw new IOException("Missing MPQ metadata.");}
            Set<String> remaining=new HashSet<String>(names(movies));Set<Integer> blocks=new HashSet<Integer>();long total=0;JSONArray entries=m.getJSONArray("entries");
            if(entries.length()<1 || entries.length()>remaining.size())throw new IOException("Incomplete import. Choose the large original StarCraft.mpq.");
            for(int i=0;i<entries.length();i++){
                JSONObject e=entries.getJSONObject(i);String name=e.getString("name").toLowerCase(Locale.ROOT);int block=e.getInt("block");
                if(!remaining.remove(name)||block<0||block>524287||!blocks.add(block))throw new IOException("Unexpected content entry.");
                long size=e.getLong("packedSize"),unpacked=e.getLong("size"),max=(movies?128L*1024*1024:1048576L);ZipEntry payload=zip.getEntry("blocks/"+block+".bin");
                if(size<1||size>max||unpacked<1||unpacked>max||payload==null||payload.getSize()!=size)throw new IOException("Damaged content entry.");
                total+=size;if(total>limit)throw new IOException("Content import is too large.");
            }
        }catch(JSONException e){throw new IOException("Invalid content manifest.",e);}
    }
}
