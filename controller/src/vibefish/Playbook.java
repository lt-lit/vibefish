package vibefish;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

/**
 * A deck's playbook (Phase 4): the decisions Vibefish makes for the seat that plays this deck instead of Forge's
 * AI. Read from the {@code playbook} object of playbook/precons/<id>.json. Everything absent stays Forge's.
 */
public final class Playbook {

    /** Attack policy. {@code go_wide}: attack the chosen opponent with every creature not needed to survive the
     *  strongest opponent's counter-attack, as long as at least {@code minAttackers} can go. */
    public static final class Attack {
        public final String policy;        // go_wide
        public final String target;        // lowest_life | weakest_board
        public final int minAttackers;     // fewer than this: Forge decides
        public final int safetyMargin;     // life to keep above the strongest opponent's possible attack
        public final int maxReserve;       // creatures kept home at most

        Attack(JsonObject o) {
            policy = str(o, "policy", "go_wide");
            target = str(o, "target", "lowest_life");
            minAttackers = num(o, "min_attackers", 3);
            safetyMargin = num(o, "safety_margin", 5);
            maxReserve = num(o, "max_reserve", 3);
        }
    }

    /** Mulligan rule: keep a hand whose land count is within the range; never mulligan past {@code maxMulligans}. */
    public static final class Mulligan {
        public final int minLands;
        public final int maxLands;
        public final int maxMulligans;

        Mulligan(JsonObject o) {
            minLands = num(o, "min_lands", 2);
            maxLands = num(o, "max_lands", 5);
            maxMulligans = num(o, "max_mulligans", 2);
        }
    }

    public final int version;
    public final Attack attack;
    public final Mulligan mulligan;

    private Playbook(JsonObject o) {
        version = num(o, "version", 1);
        attack = o.has("attack") && o.get("attack").isJsonObject() ? new Attack(o.getAsJsonObject("attack")) : null;
        mulligan = o.has("mulligan") && o.get("mulligan").isJsonObject() ? new Mulligan(o.getAsJsonObject("mulligan")) : null;
    }

    /** The playbook in a deck data file, or null when the file has none. */
    public static Playbook fromDeckFile(JsonObject file) {
        JsonElement pb = file.get("playbook");
        if (pb == null || !pb.isJsonObject()) {
            return null;
        }
        return new Playbook(pb.getAsJsonObject());
    }

    public String describe() {
        StringBuilder sb = new StringBuilder("v" + version);
        if (attack != null) {
            sb.append(" attack=").append(attack.policy).append('/').append(attack.target)
              .append(" min=").append(attack.minAttackers).append(" margin=").append(attack.safetyMargin).append(" reserve<=").append(attack.maxReserve);
        }
        if (mulligan != null) {
            sb.append(" mulligan=lands ").append(mulligan.minLands).append('-').append(mulligan.maxLands).append(" max ").append(mulligan.maxMulligans);
        }
        return sb.toString();
    }

    static String str(JsonObject o, String k, String d) {
        return o.has(k) && o.get(k).isJsonPrimitive() ? o.get(k).getAsString() : d;
    }

    static int num(JsonObject o, String k, int d) {
        return o.has(k) && o.get(k).isJsonPrimitive() ? o.get(k).getAsInt() : d;
    }
}
