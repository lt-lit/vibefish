package vibefish;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

/**
 * A deck's playbook (Phase 4): the decisions Vibefish makes for the seat that plays this deck instead of Forge's
 * AI. Read from the {@code playbook} object of playbook/precons/<id>.json. Everything absent stays Forge's.
 */
public final class Playbook {

    /** Attack policy. {@code go_wide}: attack the chosen opponent with every creature not needed to survive the
     *  strongest opponent's counter-attack, as long as at least {@code minAttackers} can go. {@code pressure}: the
     *  same reserve, but an attacker a blocker would kill stays home unless the damage the swing gets through pays
     *  for the creatures it loses ({@code damagePerLoss}), and the swing goes at the opponent it scores best on. */
    public static final class Attack {
        public final String policy;        // go_wide | pressure
        public final String target;        // lowest_life | weakest_board | highest_life | biggest_board
        public final int minAttackers;     // fewer than this: Forge decides
        public final int safetyMargin;     // life to keep above the strongest opponent's possible attack
        public final int maxReserve;       // creatures kept home at most
        public final boolean spread;       // once a defender is dead through its blockers, the rest attack the next one
        public final int damagePerLoss;    // pressure: damage through that one lost attacker must buy

        Attack(JsonObject o) {
            policy = str(o, "policy", "go_wide");
            if (!List.of("go_wide", "pressure").contains(policy)) {
                throw new IllegalArgumentException("playbook attack policy must be go_wide or pressure");
            }
            target = str(o, "target", "lowest_life");
            if (!List.of("lowest_life", "weakest_board", "highest_life", "biggest_board").contains(target)) {
                throw new IllegalArgumentException("playbook attack target must be lowest_life, weakest_board, highest_life or biggest_board");
            }
            minAttackers = num(o, "min_attackers", "pressure".equals(policy) ? 1 : 3);
            damagePerLoss = num(o, "damage_per_loss", 3);
            safetyMargin = num(o, "safety_margin", 5);
            maxReserve = num(o, "max_reserve", 3);
            spread = o.has("spread") && o.get("spread").isJsonPrimitive() && o.get("spread").getAsBoolean();
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

    /**
     * A condition on the seat's own side of the game, written as text so the file stays greppable:
     * {@code "creatures >= 3"}, {@code "storm >= 4"}, {@code "type:Goblin >= 5"}, {@code "controls Zada, Hedron Grinder"},
     * {@code "not controls Krenko, Mob Boss"}. The metrics are evaluated by {@link PlaybookController}.
     */
    public static final class Cond {
        /** Everything a comparison may be made on; anything else is a mistake in the file and stops the run. */
        public static final List<String> METRICS = List.of("creatures", "tokens", "attackers", "lands", "hand", "library",
                "storm", "drawn", "turn", "life", "mana", "opponents", "power", "opp_creatures", "opp_power", "opp_life",
                "threat", "main");
        private static final Pattern CONTROLS = Pattern.compile("^(not\\s+)?controls\\s+(.+)$");
        private static final Pattern COMPARE = Pattern.compile(
                "^([a-z_]+|type:[A-Za-z' -]+?|hand:[A-Za-z0-9_]+)\\s*(>=|<=|==|!=|>|<)\\s*(-?\\d+|[a-z_]+)$");

        public final String text;
        public final String metric;     // null for a controls condition
        public final String op;
        public final int value;
        public final String other;      // the metric on the right-hand side, when the comparison is with one, else null
        public final String card;       // controls / not controls: the permanent's name
        public final boolean negate;

        Cond(String raw) {
            text = raw.trim();
            Matcher c = CONTROLS.matcher(text);
            Matcher m = COMPARE.matcher(text);
            if (c.matches()) {
                negate = c.group(1) != null;
                card = c.group(2).trim();
                metric = null;
                op = null;
                value = 0;
                other = null;
            } else if (m.matches() && known(m.group(1)) && (m.group(3).matches("-?\\d+") || METRICS.contains(m.group(3)))) {
                metric = m.group(1).trim();
                op = m.group(2);
                boolean number = m.group(3).matches("-?\\d+");
                value = number ? Integer.parseInt(m.group(3)) : 0;
                other = number ? null : m.group(3);
                card = null;
                negate = false;
            } else {
                throw new IllegalArgumentException("playbook condition not understood: \"" + raw + "\" (use \"<metric> <op> <number or metric>\" with "
                        + METRICS + ", type:<CreatureType> or hand:<group>, or \"[not] controls <card name>\")");
            }
        }

        private static boolean known(String metric) {
            return METRICS.contains(metric) || metric.startsWith("type:") || metric.startsWith("hand:");
        }

        /** The group a {@code hand:<group>} metric counts, or null. */
        public String group() {
            return metric != null && metric.startsWith("hand:") ? metric.substring(5) : null;
        }

        public boolean compare(int actual) {
            return compare(actual, value);
        }

        public boolean compare(int actual, int value) {
            switch (op) {
                case ">=": return actual >= value;
                case "<=": return actual <= value;
                case ">": return actual > value;
                case "<": return actual < value;
                case "==": return actual == value;
                default: return actual != value;
            }
        }
    }

    /**
     * One cast rule. {@code play}: on the seat's own main phase with an empty stack, cast the first listed card that
     * is in hand (or the command zone) and affordable, when every {@code when} condition holds; with {@code target}
     * the spell is aimed at that permanent of ours, without it Forge picks the targets of a spell that needs any; a
     * card that returns to hand (buyback) is cast at most {@code times} a turn by the rule.
     * {@code activate}: the same for an activated ability of a listed permanent of ours ({@code ability}: a piece of
     * its text, when the card has several), at most {@code times} a turn for each permanent. A play or activate rule
     * marked {@code before_land} is also tried before the turn's land is played, when a land could still be played,
     * which is how a landfall deck says "the payoff first, then the land". With {@code x} a rule casts an untargeted
     * spell that has X in its cost for as much as the mana left pays for ({@code "max"}) or at most the number given,
     * and not at all below {@code x_min}; without it X spells are cast only when Forge's own logic would. {@code hold}: Forge's
     * own AI may not cast the listed cards, nor use the activated abilities of the listed permanents of ours (all of
     * them, or the one {@code ability} quotes), until every {@code until} condition holds (never, with no
     * {@code until}); a card named by several hold rules is released as soon as one of them is, and a play or
     * activate rule may still make a held play, which is how "only this way" is written.
     */
    public static final class CastRule {
        public final String kind;           // play | activate | hold
        public final List<String> cards;
        public final String target;         // play, activate
        public final String ability;        // activate, hold: text the ability's description contains (null: any of them)
        public final int times;             // play: casts of one card name a turn; activate: per permanent a turn (default 1)
        public final List<Cond> when;       // play, activate: when; hold: until
        public final String phase;          // play, activate: main (either main phase) | main1 | main2
        public final boolean beforeLand;    // play, activate: tried before the turn's land is played (landfall first)
        public final int x;                 // play, activate: the most X the rule pays (-1: X is Forge's; "max": all the mana left)
        public final int xMin;              // ... and the least X worth casting for (default 1)
        public final int index;             // 1-based position in the file, for the counters

        CastRule(JsonObject o, int index) {
            this.index = index;
            String k = null;
            for (String candidate : List.of("play", "activate", "hold")) {
                if (o.has(candidate)) {
                    if (k != null) {
                        throw new IllegalArgumentException("playbook cast rule " + index + " needs exactly one of \"play\", \"activate\" and \"hold\"");
                    }
                    k = candidate;
                }
            }
            if (k == null) {
                throw new IllegalArgumentException("playbook cast rule " + index + " needs one of \"play\", \"activate\" and \"hold\"");
            }
            kind = k;
            boolean hold = "hold".equals(kind);
            cards = strings(o.get(kind));
            if (cards.isEmpty()) {
                throw new IllegalArgumentException("playbook cast rule " + index + " names no cards");
            }
            target = hold ? null : str(o, "target", null);
            ability = "play".equals(kind) ? null : str(o, "ability", null);
            times = num(o, "times", 1);
            phase = hold ? null : str(o, "phase", "main");
            beforeLand = !hold && o.has("before_land") && o.get("before_land").isJsonPrimitive() && o.get("before_land").getAsBoolean();
            if (!hold && o.has("x") && o.get("x").isJsonPrimitive()) {
                String xs = o.get("x").getAsString().trim();
                if (!xs.equals("max") && !xs.matches("\\d+")) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": x must be a number or \"max\"");
                }
                x = xs.equals("max") ? Integer.MAX_VALUE : Integer.parseInt(xs);
            } else {
                x = -1;
            }
            xMin = num(o, "x_min", 1);
            if (hold && (o.has("x") || o.has("x_min") || o.has("before_land"))) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": a hold rule takes no \"x\", \"x_min\" or \"before_land\"");
            }
            if (!hold && !List.of("main", "main1", "main2").contains(phase)) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": phase must be main, main1 or main2");
            }
            List<Cond> conds = new ArrayList<>();
            for (String c : strings(o.get(hold ? "until" : "when"))) {
                conds.add(new Cond(c));
            }
            when = Collections.unmodifiableList(conds);
            if (hold && (o.has("when") || o.has("target"))) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": a hold rule takes \"until\", not \"when\" or \"target\"");
            }
            if (!hold && o.has("until")) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": a " + kind + " rule takes \"when\", not \"until\"");
            }
        }

        public boolean isPlay() {
            return "play".equals(kind);
        }

        public boolean isActivate() {
            return "activate".equals(kind);
        }

        public boolean isHold() {
            return "hold".equals(kind);
        }
    }

    /** The cast rules, in the file's order: the first play rule that can cast something does. */
    public static final class Cast {
        public final List<CastRule> rules;
        public final int maxPerTurn;        // plays by rule in one turn before Forge takes over (runaway guard)
        public final java.util.Map<String, List<String>> groups;   // named lists of cards, for hand:<group> conditions
        public final JsonObject source;     // as written, recorded in run.json
        public final boolean hasBeforeLand; // some rule is tried before the land drop

        Cast(JsonObject o) {
            source = o;
            maxPerTurn = num(o, "max_per_turn", 60);
            java.util.Map<String, List<String>> g = new java.util.LinkedHashMap<>();
            if (o.has("groups") && o.get("groups").isJsonObject()) {
                for (java.util.Map.Entry<String, JsonElement> e : o.getAsJsonObject("groups").entrySet()) {
                    g.put(e.getKey(), Collections.unmodifiableList(strings(e.getValue())));
                }
            }
            groups = Collections.unmodifiableMap(g);
            List<CastRule> list = new ArrayList<>();
            JsonElement r = o.get("rules");
            if (r != null && r.isJsonArray()) {
                JsonArray arr = r.getAsJsonArray();
                for (int i = 0; i < arr.size(); i++) {
                    list.add(new CastRule(arr.get(i).getAsJsonObject(), i + 1));
                }
            }
            rules = Collections.unmodifiableList(list);
            boolean early = false;
            for (CastRule rule : rules) {
                early |= rule.beforeLand;
            }
            hasBeforeLand = early;
            for (CastRule rule : rules) {
                for (Cond c : rule.when) {
                    if (c.group() != null && !groups.containsKey(c.group())) {
                        throw new IllegalArgumentException("playbook cast rule " + rule.index + ": no group \"" + c.group() + "\" in cast.groups");
                    }
                }
            }
        }

        /** Every card a rule names (to cast, to hold or to aim at), for checking against the decklist. */
        public List<String> namedCards() {
            List<String> names = new ArrayList<>();
            for (CastRule rule : rules) {
                names.addAll(rule.cards);
                if (rule.target != null) {
                    names.add(rule.target);
                }
                for (Cond c : rule.when) {
                    if (c.card != null) {
                        names.add(c.card);
                    }
                }
            }
            for (List<String> g : groups.values()) {
                names.addAll(g);
            }
            return names;
        }
    }

    /**
     * One trigger rule: the seat's answer when Forge asks whether to use an optional ("you may") trigger of a listed
     * card of ours. {@code accept}: yes, {@code decline}: no, when every {@code when} condition holds; the first rule
     * that names the card and whose conditions hold answers, and Forge's own AI answers when none does.
     * {@code ability} narrows a rule to the trigger whose text contains it, for a card with several. What an accepted
     * trigger then costs and does (what is sacrificed, the modes, the targets) is still chosen by Forge.
     */
    public static final class TriggerRule {
        public final boolean accept;
        public final List<String> cards;
        public final String ability;        // text the trigger's description contains (null: any trigger of the card)
        public final List<Cond> when;
        public final int index;             // 1-based position in the file, for the counters

        TriggerRule(JsonObject o, int index) {
            this.index = index;
            if (o.has("accept") == o.has("decline")) {
                throw new IllegalArgumentException("playbook trigger rule " + index + " needs exactly one of \"accept\" and \"decline\"");
            }
            accept = o.has("accept");
            cards = strings(o.get(accept ? "accept" : "decline"));
            if (cards.isEmpty()) {
                throw new IllegalArgumentException("playbook trigger rule " + index + " names no cards");
            }
            ability = str(o, "ability", null);
            List<Cond> conds = new ArrayList<>();
            for (String c : strings(o.get("when"))) {
                conds.add(new Cond(c));
            }
            when = Collections.unmodifiableList(conds);
        }
    }

    public final int version;
    public final Attack attack;
    public final Mulligan mulligan;
    public final Cast cast;
    public final List<TriggerRule> triggers;    // empty when the playbook has none
    public final JsonElement triggersSource;    // as written, recorded in run.json (null when none)

    private Playbook(JsonObject o) {
        version = num(o, "version", 1);
        attack = o.has("attack") && o.get("attack").isJsonObject() ? new Attack(o.getAsJsonObject("attack")) : null;
        mulligan = o.has("mulligan") && o.get("mulligan").isJsonObject() ? new Mulligan(o.getAsJsonObject("mulligan")) : null;
        cast = o.has("cast") && o.get("cast").isJsonObject() ? new Cast(o.getAsJsonObject("cast")) : null;
        List<TriggerRule> list = new ArrayList<>();
        if (o.has("triggers") && o.get("triggers").isJsonArray()) {
            JsonArray arr = o.getAsJsonArray("triggers");
            for (int i = 0; i < arr.size(); i++) {
                list.add(new TriggerRule(arr.get(i).getAsJsonObject(), i + 1));
            }
        }
        triggers = Collections.unmodifiableList(list);
        triggersSource = list.isEmpty() ? null : o.get("triggers");
        for (TriggerRule rule : triggers) {
            for (Cond c : rule.when) {
                if (c.group() != null && (cast == null || !cast.groups.containsKey(c.group()))) {
                    throw new IllegalArgumentException("playbook trigger rule " + rule.index + ": no group \"" + c.group() + "\" in cast.groups");
                }
            }
        }
    }

    /** Every card the rules name (to cast, hold, aim at, or answer a trigger for), for checking against the decklist. */
    public List<String> namedCards() {
        List<String> names = new ArrayList<>();
        if (cast != null) {
            names.addAll(cast.namedCards());
        }
        for (TriggerRule rule : triggers) {
            names.addAll(rule.cards);
            for (Cond c : rule.when) {
                if (c.card != null) {
                    names.add(c.card);
                }
            }
        }
        return names;
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
              .append(" min=").append(attack.minAttackers).append(" margin=").append(attack.safetyMargin).append(" reserve<=").append(attack.maxReserve)
              .append(attack.spread ? " spread" : "").append("pressure".equals(attack.policy) ? " damage/loss>=" + attack.damagePerLoss : "");
        }
        if (mulligan != null) {
            sb.append(" mulligan=lands ").append(mulligan.minLands).append('-').append(mulligan.maxLands).append(" max ").append(mulligan.maxMulligans);
        }
        if (cast != null) {
            int plays = 0, activations = 0, holds = 0;
            for (CastRule r : cast.rules) {
                plays += r.isPlay() ? 1 : 0;
                activations += r.isActivate() ? 1 : 0;
                holds += r.isHold() ? 1 : 0;
            }
            sb.append(" cast=").append(plays).append(" play, ").append(activations).append(" activate, ").append(holds).append(" hold rule(s)");
        }
        if (!triggers.isEmpty()) {
            sb.append(" triggers=").append(triggers.size()).append(" rule(s)");
        }
        return sb.toString();
    }

    static List<String> strings(JsonElement e) {
        List<String> out = new ArrayList<>();
        if (e == null || e.isJsonNull()) {
            return out;
        }
        if (e.isJsonArray()) {
            for (JsonElement x : e.getAsJsonArray()) {
                out.add(x.getAsString());
            }
        } else {
            out.add(e.getAsString());
        }
        return out;
    }

    static String str(JsonObject o, String k, String d) {
        return o.has(k) && o.get(k).isJsonPrimitive() ? o.get(k).getAsString() : d;
    }

    static int num(JsonObject o, String k, int d) {
        return o.has(k) && o.get(k).isJsonPrimitive() ? o.get(k).getAsInt() : d;
    }
}
