import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Paths;
import vibefish.Playbook;

/** Parses every playbook file given on the command line with the harness's own loader; prints the failures. */
public class PbCheck {
    public static void main(String[] args) throws Exception {
        int ok = 0, none = 0, bad = 0;
        for (String a : args) {
            try {
                Playbook p = Playbook.fromDeckFile(JsonParser.parseString(Files.readString(Paths.get(a))).getAsJsonObject());
                if (p == null) { none++; } else { ok++; }
            } catch (Exception e) {
                bad++;
                System.out.println("FAILED " + a + ": " + e.getMessage());
            }
        }
        System.out.println(ok + " playbooks parsed, " + none + " files without a playbook, " + bad + " failed");
    }
}
