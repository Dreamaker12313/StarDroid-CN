import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import org.openbw.androidtest.MissionBundle;

public class ExportHarness {
    public static void main(String[] args) throws Exception {
        List<String> names = Files.readAllLines(Paths.get(args[2]), StandardCharsets.UTF_8);
        try (FileInputStream in = new FileInputStream(args[0]); FileOutputStream out = new FileOutputStream(args[1])) {
            MissionBundle.Result r = MissionBundle.export(in.getChannel(), names, names.get(0), out, message -> {});
            System.out.println("Exported " + r.files + " entries, " + r.packedBytes + " payload bytes, missing=" + r.missing.size());
        }
    }
}
