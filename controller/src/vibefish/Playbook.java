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
     *  for the creatures it loses ({@code damagePerLoss}), and the swing goes at the opponent it scores best on.
     *  {@code forge}: Forge's own attack, which is also what a playbook without an attack block gets; the block is
     *  then there for {@code finish}. With {@code finish}, whatever the policy declared, an opponent the seat is
     *  sure to kill is killed: enough attackers are put on it that the damage gets through whatever it blocks
     *  (one blocker an attacker, Forge's own rules for who may block whom), the opponent that looks most dangerous
     *  first and then any other the creatures that are left can kill the same way. {@code "finish": "leader"}
     *  takes such a kill only from the most dangerous opponent down: the most dangerous one alive, then the next
     *  if the first is taken, and none past the first opponent that cannot be killed for sure (a weaker opponent
     *  is left alone while a more dangerous one lives). With {@code guard}, after all of that, attackers are taken
     *  back when the attack as declared leaves the seat where one opponent alone is sure to kill it before its
     *  next turn and keeping them home prevents that; a sure kill's attackers are never taken back, and an attack
     *  stands when nothing kept home would save the seat. {@code "guard": "table"} asks the same of the opponents
     *  one after another (what each is sure to get through, summed), and falls back to the one-opponent question
     *  when nothing kept home answers that. With {@code "aim": "danger"} (since 0.4.5), before any of that, the
     *  attackers the policy sent at a player are sent at the opponent that looks most dangerous instead (life and
     *  nonland permanents by the weights of {@code cast.danger}), when that opponent is ahead of the one attacked
     *  by at least {@code aim_margin} and the attack is no worse there by what can be counted on the table: the
     *  damage sure to get through whatever is blocked is at least what it was, no more creatures there could
     *  block the attackers, and no attacker meets a blocker that would kill it unless it met one where it was
     *  sent. An attack that is sure to kill its target stays.
     *  With {@code "open": true} (since 0.4.5), after the aim, the creatures that stayed home attack an opponent
     *  that has no creature that can block, the most dangerous such opponent first: those that deal damage, have
     *  no ability that taps them (or have vigilance) and are not wanted home by Forge's own judgement of the
     *  seat's defence; a weaker opponent is not killed this way while a more dangerous one lives. */
    public static final class Attack {
        public final String policy;        // go_wide | pressure | forge
        public final boolean finish;       // take a kill no block prevents
        public final boolean finishLeader; // ... only from the most dangerous opponent down
        public final boolean finishCommander;  // ... and a kill by a commander's damage that no blocker can stop (0.4.13)
        public final boolean guard;        // take attackers back when the attack leaves the seat dead on board to one opponent
        public final boolean guardTable;   // ... or to the opponents one after another
        public final int guardMargin;      // ... counting the seat as dead this much life early
        public final boolean aimDanger;    // send the declared attack at the most dangerous opponent when it is no worse there
        public final int aimMargin;        // ... and that opponent is ahead of the one attacked by at least this much
        public final boolean open;         // creatures left home attack an opponent that cannot block, when not needed at home
        public final String target;        // lowest_life | weakest_board | highest_life | biggest_board
        public final int minAttackers;     // fewer than this: Forge decides
        public final int safetyMargin;     // life to keep above the strongest opponent's possible attack
        public final int maxReserve;       // creatures kept home at most
        public final boolean spread;       // once a defender is dead through its blockers, the rest attack the next one
        public final int damagePerLoss;    // pressure: damage through that one lost attacker must buy
        public final String enableWith;    // "enable": a permanent of ours whose tap ability wants an attacker: it stays home (null: none)
        public final String enableSend;    // ... and the kind of creature that attacks for it: face_down

        Attack(JsonObject o) {
            policy = str(o, "policy", "go_wide");
            if (!List.of("go_wide", "pressure", "forge").contains(policy)) {
                throw new IllegalArgumentException("playbook attack policy must be go_wide, pressure or forge");
            }
            String fin = null;
            if (o.has("finish") && o.get("finish").isJsonPrimitive()) {
                fin = o.getAsJsonPrimitive("finish").isBoolean() ? (o.get("finish").getAsBoolean() ? "any" : null) : o.get("finish").getAsString();
            }
            if (fin != null && !List.of("any", "leader").contains(fin)) {
                throw new IllegalArgumentException("playbook attack finish must be true, \"any\" or \"leader\"");
            }
            finish = fin != null;
            finishLeader = "leader".equals(fin);
            finishCommander = o.has("finish_commander") && o.get("finish_commander").isJsonPrimitive() && o.get("finish_commander").getAsBoolean();
            if (finishCommander && !finish) {
                throw new IllegalArgumentException("playbook attack finish_commander needs finish (it is a kind of kill the finish hook takes)");
            }
            String grd = null;
            if (o.has("guard") && o.get("guard").isJsonPrimitive()) {
                grd = o.getAsJsonPrimitive("guard").isBoolean() ? (o.get("guard").getAsBoolean() ? "one" : null) : o.get("guard").getAsString();
            }
            if (grd != null && !List.of("one", "table").contains(grd)) {
                throw new IllegalArgumentException("playbook attack guard must be true, \"one\" or \"table\"");
            }
            guard = grd != null;
            guardTable = "table".equals(grd);
            guardMargin = num(o, "guard_margin", 0);
            String aim = str(o, "aim", "");
            if (!aim.isEmpty() && !"danger".equals(aim)) {
                throw new IllegalArgumentException("playbook attack aim must be \"danger\"");
            }
            aimDanger = "danger".equals(aim);
            aimMargin = num(o, "aim_margin", 5);
            open = o.has("open") && o.get("open").isJsonPrimitive() && o.get("open").getAsBoolean();
            JsonObject en = o.has("enable") && o.get("enable").isJsonObject() ? o.getAsJsonObject("enable") : null;
            enableWith = en == null ? null : str(en, "with", null);
            enableSend = en == null ? null : str(en, "send", "face_down");
            if (o.has("enable") && (enableWith == null || !"face_down".equals(enableSend))) {
                throw new IllegalArgumentException("playbook attack enable is {\"with\": a permanent of ours, \"send\": \"face_down\"}");
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

    /**
     * Blocks. {@code "survive": true}: Forge's AI declares the seat's blocks; when they leave at least the seat's
     * life in damage unblocked and blocks exist that would not (one blocker an attacker, by Forge's own rules
     * for who may block whom; an attacker that tramples or needs two blockers is not counted as stopped), blocks
     * are added, the least valuable free creatures in front of the heaviest unblocked attackers and only as many
     * as it takes for the seat to live. When adding to Forge's blocks is not enough and a different set of blocks
     * would be, the seat's blocks are declared anew that way. Everything else about blocking stays Forge's.
     */
    public static final class Block {
        public final boolean survive;

        Block(JsonObject o) {
            survive = o.has("survive") && o.get("survive").isJsonPrimitive() && o.get("survive").getAsBoolean();
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
                "threat", "main", "opp_toughness", "attacking", "unblocked", "attacked", "incoming", "lethal",
                "table_creatures", "table_power");
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
     * and not at all below {@code x_min}; without it X spells are cast only when Forge's own logic would. {@code x} may
     * also name a metric (X is that number), and an X that is paid in life is the rule's to name the same way, never
     * below {@code x_keep_life} life left. With {@code aim} (a kind of permanent) the spell's one target is an
     * opponent's permanent of that kind, worth at least {@code aim_min}: the best one of the opponent that looks most
     * dangerous ({@code aim_at danger}, the default; the weights are {@code cast.danger}) or the best on any
     * opponent's side ({@code any}); a rule takes {@code target} or {@code aim}, not both. With {@code divide}
     * (since 0.4.6; a number, on a rule that has {@code aim}) the spell is one that divides an X among any number
     * of targets (Fire Covenant): the rule chooses up to that many of the opponents' permanents of the aimed kind,
     * gives each the amount that destroys it and pays their sum as X, never more than {@code x} (when the rule
     * gives one) and never below {@code x_keep_life} when the X is paid in life; the targets are the set with the
     * highest total rating the amount pays for, the most dangerous opponent's first ({@code aim_at danger}) or over
     * every opponent's side at once ({@code any}), and the rule casts only for at least {@code divide_min} of them
     * (default 1). With {@code "target_player": "self"} (since 0.4.6) the spell's one target is the seat itself
     * (Pact of the Serpent: the cards are the seat's to draw); anything else such a spell asks as it resolves is
     * Forge's to answer. With {@code "own": "face_down"} (since 0.4.7) the one target is a face-down creature of
     * the seat's own that the spell or ability can target: one that is a creature card face up, an unblocked
     * attacker before a blocked one once blocks are declared, then the greater power face up; with
     * {@code "own": "attacker"} (0.4.8) it is an attacking creature of the seat's own, an unblocked one first, then
     * the greater power, and the rule's {@code x} applies as it does with {@code target}; with
     * {@code "own": "minus_counter"} (0.4.9) a permanent of the seat's own that has -1/-1 counters and no other
     * kind, a creature before anything else. A rule with {@code own} and {@code aim} (0.4.9) is for a spell or
     * ability with two targets, in that order: the first is the seat's own permanent, the second an opponent's
     * (Nesting Grounds: move a counter from the one onto the other). {@code own_except} (0.4.10) lists permanents
     * of the seat's own that an {@code own} selector never takes: a deck that puts counters on some of its own
     * creatures on purpose (Tree of Perdition, whose toughness an opponent's life is exchanged with) does not want
     * them moved off. {@code aim_toughness} (0.4.9) keeps an aim
     * to creatures of at most that toughness, for an effect that kills by a fixed amount. {@code keep} (0.4.8; its
     * value is {@code "mana"}): in the seat's first main phase, while every {@code when} condition holds, the rules
     * below are not read and the seat goes to combat with its mana, for a play written for its combat; they are
     * read in the second main phase. A rule's
     * {@code phase} is {@code main} (either main phase, the default), {@code main1} or {@code main2}, or since
     * 0.4.7 a step of the seat's own combat with an empty stack: {@code attack}, after its attackers are declared,
     * or {@code blocks}, after the blocks. {@code hold}: Forge's
     * own AI may not cast the listed cards, nor use the activated abilities of the listed permanents of ours (all of
     * them, or the one {@code ability} quotes), until every {@code until} condition holds (never, with no
     * {@code until}); a card named by several hold rules is released as soon as one of them is, and a play or
     * activate rule may still make a held play, which is how "only this way" is written.
     * {@code forge} (its value is {@code "unnamed"}): at this place in the order Forge's own AI chooses, among the
     * plays no rule names: the spells of cards no play rule lists and the abilities no activate rule covers, the
     * holds in force left out. When it wants none of them the rules below are read. Without such a rule everything
     * the rules do not name waits until every rule is idle, which starves it behind an engine that always has
     * something to do (DESIGN.md section 30). With {@code "wait": "main2"} the rule also keeps the mana for what
     * Forge's AI casts after combat: in the first main phase, when Forge wants none of the unnamed plays now but
     * says of an unnamed card it could pay for that it is waiting for its second main phase, the rules below are
     * not read and the seat passes; they are read in the second main phase, after Forge has made its choice there.
     * Without it the rules below spend in the first main phase the mana Forge would have used in the second.
     */
    public static final class CastRule {
        public final String kind;           // play | activate | hold | forge | keep | reserve
        public final List<String> cards;
        public final String target;         // play, activate
        public final String ability;        // activate, hold: text the ability's description contains (null: any of them)
        public final int times;             // play: casts of one card name a turn; activate: per permanent a turn (default 1)
        public final List<Cond> when;       // play, activate: when; hold: until
        public final String phase;          // play, activate: main (either main phase) | main1 | main2 | attack | blocks (our own combat) | defend | end (another player's turn)
        public final boolean beforeLand;    // play, activate: tried before the turn's land is played (landfall first)
        public final int x;                 // play, activate: the most X the rule pays (-1: X is Forge's; "max": all the mana left)
        public final int xMin;              // ... and the least X worth casting for (default 1)
        public final String xMetric;        // x given as a metric: X is that number (opp_toughness: a wipe sized to the largest creature)
        public final int xKeepLife;         // an X paid in life: never paid below this much life left (default 10)
        public final boolean waitMain2;     // forge: the rules below wait for main 2 while Forge keeps an unnamed card for it
        public final String aim;            // play, activate: the one target is an opponent's permanent of this kind (null: no aim)
        public final String aimAt;          // danger: of the opponent judged most dangerous first | any: the best on any opponent's side
        public final int aimMin;            // the least worth of a permanent the rule aims at (mana value; a creature's power if more)
        public final boolean targetSelf;    // play: the spell's one target is the seat itself ("target_player": "self")
        public final String own;            // play, activate: a target that is a permanent of ours of this kind (face_down | attacker | minus_counter), chosen by the harness
        public final int aimToughness;      // an aimed creature has at most this toughness (0: any)
        public final List<String> ownExcept; // permanents of ours an "own" selector never takes (the deck wants them as they are)
        public final int divide;            // an aimed spell that divides its X: the most targets (0: not a dividing rule)
        public final int divideMin;         // ... and the fewest worth casting for (default 1)
        public final boolean take;          // play (0.4.14): which counters a "remove any number of counters" spell takes, and how many
        public final int takeKeepLife;      // ... the life the seat keeps once it has paid a life a counter
        public final int takeMax;           // ... the most counters in one cast
        public final int takeMin;           // ... the fewest worth casting for
        public final List<String> takeExcept; // ... permanents of the seat's own whose counters stay where they are
        public final int index;             // 1-based position in the file, for the counters

        /** The kinds of permanent an aim can ask for. */
        public static final List<String> AIM_KINDS = List.of("creature", "permanent", "noncreature", "artifact", "enchantment", "planeswalker", "attacker");

        CastRule(JsonObject o, int index) {
            this.index = index;
            String k = null;
            for (String candidate : List.of("play", "activate", "hold", "forge", "keep", "reserve")) {
                if (o.has(candidate)) {
                    if (k != null) {
                        throw new IllegalArgumentException("playbook cast rule " + index + " needs exactly one of \"play\", \"activate\", \"hold\", \"forge\", \"keep\" and \"reserve\"");
                    }
                    k = candidate;
                }
            }
            if (k == null) {
                throw new IllegalArgumentException("playbook cast rule " + index + " needs one of \"play\", \"activate\", \"hold\", \"forge\", \"keep\" and \"reserve\"");
            }
            kind = k;
            boolean reserve = "reserve".equals(kind);
            if (reserve) {
                for (String key : List.of("target", "ability", "times", "x", "x_min", "before_land", "until", "divide", "divide_min", "target_player", "own", "wait", "phase", "own_except")) {
                    if (o.has(key)) {
                        throw new IllegalArgumentException("playbook cast rule " + index + ": a reserve rule takes only its cards, \"when\", and an \"aim\" (with \"aim_at\", \"aim_min\", \"aim_toughness\") that has to have a target for the mana to be kept");
                    }
                }
            }
            boolean hold = "hold".equals(kind) || reserve;         // a reserve rule is parsed like a hold rule: cards, and conditions of its own
            boolean keep = "keep".equals(kind);
            boolean forge = "forge".equals(kind) || keep;      // a keep rule is parsed like a forge rule: no cards, only conditions
            if (keep) {
                if (!o.get("keep").isJsonPrimitive() || !"mana".equals(o.get("keep").getAsString())) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": \"keep\" takes \"mana\" (the seat passes its first main phase with its mana)");
                }
                for (String key : List.of("target", "ability", "times", "x", "x_min", "before_land", "until", "aim", "aim_at", "aim_min", "divide", "divide_min", "target_player", "own", "wait", "phase")) {
                    if (o.has(key)) {
                        throw new IllegalArgumentException("playbook cast rule " + index + ": a keep rule takes only \"when\"");
                    }
                }
            } else if (forge) {
                if (!o.get("forge").isJsonPrimitive() || !"unnamed".equals(o.get("forge").getAsString())) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": \"forge\" takes \"unnamed\" (Forge's choice among the plays no rule names)");
                }
                for (String key : List.of("target", "ability", "times", "x", "x_min", "before_land", "until", "aim", "aim_at", "aim_min", "divide", "divide_min", "target_player", "own", "aim_toughness", "own_except")) {
                    if (o.has(key)) {
                        throw new IllegalArgumentException("playbook cast rule " + index + ": a forge rule takes only \"when\", \"phase\" and \"wait\"");
                    }
                }
                if (o.has("wait") && (!o.get("wait").isJsonPrimitive() || !"main2".equals(o.get("wait").getAsString()))) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": \"wait\" takes \"main2\" (the rules below wait for the second main phase)");
                }
            } else if (o.has("wait")) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": only a forge rule takes \"wait\"");
            }
            waitMain2 = forge && o.has("wait");
            cards = forge ? Collections.emptyList() : strings(o.get(kind));
            if (cards.isEmpty() && !forge) {
                throw new IllegalArgumentException("playbook cast rule " + index + " names no cards");
            }
            target = hold ? null : str(o, "target", null);
            aim = (hold && !reserve) || forge ? null : str(o, "aim", null);
            aimAt = str(o, "aim_at", "danger");
            aimMin = num(o, "aim_min", 0);
            aimToughness = num(o, "aim_toughness", 0);
            if (aim == null && (o.has("aim") || o.has("aim_at") || o.has("aim_min") || o.has("aim_toughness"))) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": only a play or activate rule takes \"aim\", and \"aim_at\", \"aim_min\" and \"aim_toughness\" need it");
            }
            if (aim != null) {
                if ("attacker".equals(aim) && (reserve || !"defend".equals(str(o, "phase", "main")) || o.has("divide") || o.has("aim_at"))) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": aim \"attacker\" (a creature attacking the seat) needs \"phase\": \"defend\" and takes no \"divide\" or \"aim_at\"");
                }
                if (!AIM_KINDS.contains(aim)) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": aim must be one of " + AIM_KINDS + " (an opponent's permanent of that kind)");
                }
                if (target != null) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": \"target\" names a permanent of the seat's own and \"aim\" an opponent's; a rule takes one of them");
                }
                if (!List.of("danger", "any").contains(aimAt)) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": aim_at must be danger or any");
                }
            }
            String tp = str(o, "target_player", null);
            if (tp != null && (!"self".equals(tp) || !"play".equals(kind) || target != null || aim != null)) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": \"target_player\" takes \"self\", on a play rule without \"target\" or \"aim\"");
            }
            targetSelf = tp != null;
            own = hold || forge ? null : str(o, "own", null);
            if (o.has("own") && (own == null || !List.of("face_down", "attacker", "minus_counter").contains(own) || target != null || tp != null)) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": \"own\" takes \"face_down\", \"attacker\" or \"minus_counter\", on a play or activate rule without \"target\" or \"target_player\"");
            }
            ownExcept = Collections.unmodifiableList(strings(o.get("own_except")));
            if (!ownExcept.isEmpty() && own == null) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": \"own_except\" needs \"own\"");
            }
            if (own != null && aim != null && o.has("divide")) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": a rule with \"own\" and \"aim\" names two targets and takes no \"divide\"");
            }
            divide = num(o, "divide", 0);
            divideMin = num(o, "divide_min", 1);
            if ((o.has("divide") || o.has("divide_min")) && (aim == null || divide < 1 || divideMin < 1 || divideMin > divide)) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": \"divide\" (the most targets, at least 1) needs \"aim\", and \"divide_min\" is between 1 and it");
            }
            JsonObject tk = o.has("take") && o.get("take").isJsonObject() ? o.getAsJsonObject("take") : null;
            if (o.has("take") && (tk == null || !"play".equals(kind))) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": \"take\" is an object on a play rule ({\"keep_life\": 15, \"max\": 8, \"min\": 3, \"own_except\": [...]})");
            }
            take = tk != null;
            takeKeepLife = tk == null ? 0 : num(tk, "keep_life", 15);
            takeMax = tk == null ? 0 : num(tk, "max", 8);
            takeMin = tk == null ? 0 : num(tk, "min", 3);
            takeExcept = tk == null ? Collections.emptyList() : Collections.unmodifiableList(strings(tk.get("own_except")));
            if (take && (takeKeepLife < 1 || takeMax < 1 || takeMin < 1 || takeMin > takeMax)) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": \"take\" needs keep_life of at least 1 and min between 1 and max");
            }
            ability = "play".equals(kind) ? null : str(o, "ability", null);
            times = num(o, "times", 1);
            phase = hold ? null : keep ? "main1" : str(o, "phase", "main");
            beforeLand = !hold && o.has("before_land") && o.get("before_land").isJsonPrimitive() && o.get("before_land").getAsBoolean();
            if (!hold && o.has("x") && o.get("x").isJsonPrimitive()) {
                String xs = o.get("x").getAsString().trim();
                boolean metric = !xs.equals("max") && !xs.matches("\\d+");
                if (metric && !Cond.METRICS.contains(xs)) {
                    throw new IllegalArgumentException("playbook cast rule " + index + ": x must be a number, \"max\" or a metric (" + Cond.METRICS + ")");
                }
                x = xs.equals("max") || metric ? Integer.MAX_VALUE : Integer.parseInt(xs);
                xMetric = metric ? xs : null;
            } else {
                x = -1;
                xMetric = null;
            }
            xKeepLife = num(o, "x_keep_life", 10);
            xMin = num(o, "x_min", 1);
            if (hold && (o.has("x") || o.has("x_min") || o.has("before_land"))) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": a hold rule takes no \"x\", \"x_min\" or \"before_land\"");
            }
            if (!hold && !List.of("main", "main1", "main2", "attack", "blocks", "defend", "end").contains(phase)) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": phase must be main, main1, main2, attack, blocks, defend or end");
            }
            if (forge && (isCombat() || isReact())) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": a forge or keep rule is for the main phases");
            }
            if (isReact() && (beforeLand || own != null)) {
                throw new IllegalArgumentException("playbook cast rule " + index + ": a rule for another player's turn takes no \"before_land\" or \"own\"");
            }
            List<Cond> conds = new ArrayList<>();
            for (String c : strings(o.get(hold && !reserve ? "until" : "when"))) {
                conds.add(new Cond(c));
            }
            when = Collections.unmodifiableList(conds);
            if (hold && !reserve && (o.has("when") || o.has("target"))) {
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

        /** A rule that keeps the mana for one of its cards untapped through the seat's own turn while its conditions hold and the card is in hand. */
        public boolean isReserve() {
            return "reserve".equals(kind);
        }

        /** A rule for another player's turn: when the seat is attacked ({@code defend}), or in the end step before its own turn ({@code end}). */
        public boolean isReact() {
            return "defend".equals(phase) || "end".equals(phase);
        }

        public boolean isForge() {
            return "forge".equals(kind);
        }

        /** A rule that ends the seat's first main phase with its mana unspent while its conditions hold. */
        public boolean isKeep() {
            return "keep".equals(kind);
        }

        /** A rule for the seat's own combat: after its attackers are declared ({@code attack}) or after the blocks ({@code blocks}). */
        public boolean isCombat() {
            return "attack".equals(phase) || "blocks".equals(phase);
        }
    }

    /** The cast rules, in the file's order: the first play rule that can cast something does. */
    public static final class Cast {
        public final List<CastRule> rules;
        public final int maxPerTurn;        // plays by rule in one turn before Forge takes over (runaway guard)
        public final java.util.Map<String, List<String>> groups;   // named lists of cards, for hand:<group> conditions
        public final JsonObject source;     // as written, recorded in run.json
        public final boolean hasBeforeLand; // some rule is tried before the land drop
        public final boolean hasCombat;     // some rule acts in the seat's own combat (phase attack or blocks)
        public final boolean hasReact;      // some rule acts on another player's turn (phase defend or end)
        public final boolean hasReserve;    // some rule keeps mana for a card through the seat's own turn
        public final int dangerLife;        // how dangerous an opponent looks: this times its life ...
        public final int dangerPermanents;  // ... plus this times its nonland permanents (an aim reads it; DESIGN.md section 33)
        public final int keepLife;          // 0.4.15: no spell is cast whose own script takes the seat below this much life (0: not asked)
        public final boolean bounceLands;   // 0.4.16: a land that returns a land is played late in the turn, and when Forge's AI would not play it at all

        Cast(JsonObject o) {
            source = o;
            maxPerTurn = num(o, "max_per_turn", 60);
            keepLife = Math.max(0, num(o, "keep_life", 0));
            bounceLands = o.has("bounce_lands") && o.get("bounce_lands").isJsonPrimitive() && o.get("bounce_lands").getAsBoolean();
            JsonObject danger = o.has("danger") && o.get("danger").isJsonObject() ? o.getAsJsonObject("danger") : new JsonObject();
            dangerLife = num(danger, "life", 1);
            dangerPermanents = num(danger, "permanents", 2);
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
            boolean fight = false;
            for (CastRule rule : rules) {
                fight |= !rule.isHold() && rule.isCombat();
            }
            hasCombat = fight;
            boolean react = false, keeps = false;
            java.util.Set<String> held = new java.util.HashSet<>();
            for (CastRule rule : rules) {
                react |= !rule.isHold() && !rule.isReserve() && rule.isReact();
                keeps |= rule.isReserve();
                if (rule.isHold() && rule.ability == null) {
                    held.addAll(rule.cards);
                }
            }
            hasReact = react;
            hasReserve = keeps;
            for (CastRule rule : rules) {
                // Forge's AI casts an instant in the seat's own turn if it may: a card kept for another player's turn has to
                // be kept from Forge too, or the rule that waits for it finds the hand empty. A typo must not undo that quietly.
                if ((rule.isPlay() && rule.isReact()) || rule.isReserve()) {
                    for (String name : rule.cards) {
                        if (!held.contains(name)) {
                            throw new IllegalArgumentException("playbook cast rule " + rule.index + ": " + name + " is kept for another player's turn and needs a hold rule (\"hold\": [\"" + name + "\"]), or Forge's AI casts it first");
                        }
                    }
                }
            }
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
                names.addAll(rule.ownExcept);           // a misspelt name here would leave the card unprotected
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
        public final int perTurn;           // an accept rule says yes at most this often in one turn (0: no limit)
        public final boolean effect;        // 0.4.15: answers the "you may" an effect of the card asks as it resolves, not its optional trigger
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
            perTurn = num(o, "per_turn", 0);
            if (perTurn < 0 || (perTurn > 0 && !accept)) {
                throw new IllegalArgumentException("playbook trigger rule " + index + ": \"per_turn\" is a positive number on an accept rule");
            }
            effect = o.has("effect") && o.get("effect").isJsonPrimitive() && o.get("effect").getAsBoolean();
            if (effect && perTurn > 0) {
                throw new IllegalArgumentException("playbook trigger rule " + index + ": \"per_turn\" is not for a rule with \"effect\"");
            }
        }
    }

    /**
     * Where the seat's own triggered abilities aim. {@code "triggers": "danger"}: a triggered ability of the seat
     * that removes one permanent an opponent controls (it destroys it, exiles it, or returns it to hand or
     * library) is aimed at the opponent that looks most dangerous (life and nonland permanents by the weights of
     * {@code cast.danger}). Forge's AI chooses its target first; when that target belongs to an opponent that
     * looks less dangerous than another by at least {@code margin} (a close table is left to Forge), and the
     * more dangerous one controls a permanent of the same kind (creature or not) that the ability can target
     * and that is worth at least as much as Forge's choice or at least {@code min} (mana value, or power if
     * higher), the best such permanent is targeted instead. Everything else about the trigger stays Forge's.
     *
     * <p>{@code "counters": {"cards": ["Blowfly Infestation"], "own_per_turn": 5}} (0.4.14) is for a named
     * permanent of the seat whose trigger puts a -1/-1 counter on one target creature. When Forge aims such a
     * trigger at a creature of the seat's own that the counter kills, that is allowed {@code own_per_turn} times
     * a turn (a deck that draws or makes a token for each such counter wants some of them); after that the
     * counter goes on a creature an opponent controls, the most dangerous opponent first and there the creature
     * with the lowest toughness, or, when no opponent's creature can be targeted, on a creature of the seat's
     * own that survives it. It ends a chain in which each death puts the next counter on the next creature.
     */
    public static final class Targets {
        public final boolean triggersByDanger;
        public final int min;
        public final int margin;
        public final List<String> counterCards;
        public final int counterOwnPerTurn;
        public final List<String> typeCards;    // 0.4.17: permanents whose trigger exiles "any number of cards with N card types among them"
        public final List<String> typeLeave;    // ... cards that trigger never brings back

        Targets(JsonObject o) {
            String t = str(o, "triggers", "");
            if (!t.isEmpty() && !"danger".equals(t)) {
                throw new IllegalArgumentException("playbook targets.triggers must be \"danger\"");
            }
            triggersByDanger = "danger".equals(t);
            min = num(o, "min", 4);
            margin = num(o, "margin", 5);
            JsonObject c = o.has("counters") && o.get("counters").isJsonObject() ? o.getAsJsonObject("counters") : null;
            counterCards = c == null || !c.has("cards") ? Collections.emptyList() : strings(c.get("cards"));
            counterOwnPerTurn = c == null ? 0 : Math.max(0, num(c, "own_per_turn", 0));
            if (c != null && counterCards.isEmpty()) {
                throw new IllegalArgumentException("playbook targets.counters needs \"cards\"");
            }
            JsonObject ty = o.has("types") && o.get("types").isJsonObject() ? o.getAsJsonObject("types") : null;
            typeCards = ty == null || !ty.has("cards") ? Collections.emptyList() : strings(ty.get("cards"));
            typeLeave = ty == null || !ty.has("leave") ? Collections.emptyList() : strings(ty.get("leave"));
            if (ty != null && typeCards.isEmpty()) {
                throw new IllegalArgumentException("playbook targets.types needs \"cards\"");
            }
        }
    }

    public final int version;
    public final Attack attack;
    public final Mulligan mulligan;
    public final Cast cast;
    public final Targets targets;               // null when the playbook has none
    public final JsonElement targetsSource;     // as written, recorded in run.json (null when none)
    public final Block block;                   // null when the playbook has none
    public final JsonElement blockSource;       // as written, recorded in run.json (null when none)
    public final List<TriggerRule> triggers;    // empty when the playbook has none
    public final JsonElement triggersSource;    // as written, recorded in run.json (null when none)

    private Playbook(JsonObject o) {
        version = num(o, "version", 1);
        attack = o.has("attack") && o.get("attack").isJsonObject() ? new Attack(o.getAsJsonObject("attack")) : null;
        mulligan = o.has("mulligan") && o.get("mulligan").isJsonObject() ? new Mulligan(o.getAsJsonObject("mulligan")) : null;
        cast = o.has("cast") && o.get("cast").isJsonObject() ? new Cast(o.getAsJsonObject("cast")) : null;
        targets = o.has("targets") && o.get("targets").isJsonObject() ? new Targets(o.getAsJsonObject("targets")) : null;
        targetsSource = targets == null ? null : o.get("targets");
        block = o.has("block") && o.get("block").isJsonObject() ? new Block(o.getAsJsonObject("block")) : null;
        blockSource = block == null ? null : o.get("block");
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
            if ("forge".equals(attack.policy)) {
                sb.append(" attack=forge's own");
            } else {
                sb.append(" attack=").append(attack.policy).append('/').append(attack.target)
                  .append(" min=").append(attack.minAttackers).append(" margin=").append(attack.safetyMargin).append(" reserve<=").append(attack.maxReserve)
                  .append(attack.spread ? " spread" : "").append("pressure".equals(attack.policy) ? " damage/loss>=" + attack.damagePerLoss : "");
            }
            sb.append(attack.aimDanger ? ", aimed at the most dangerous opponent when no worse there (margin " + attack.aimMargin + ")" : "");
            sb.append(attack.open ? ", idle creatures attack an open board" : "");
            sb.append(attack.finish ? (attack.finishLeader ? ", takes a sure kill of the most dangerous opponent" : ", takes a sure kill") : "");
            sb.append(attack.finishCommander ? " (a commander's 21 damage that no blocker can stop counts as one)" : "");
            sb.append(attack.guard ? (attack.guardTable ? ", keeps attackers home against the table's lethal answer" : ", keeps attackers home against one opponent's lethal answer") : "");
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
            if (cast.hasReact) {
                int reacts = 0;
                for (CastRule r : cast.rules) {
                    reacts += !r.isHold() && !r.isReserve() && r.isReact() ? 1 : 0;
                }
                sb.append(", ").append(reacts).append(" for another player's turn").append(cast.hasReserve ? " (mana kept for them)" : "");
            }
            int aims = 0;
            for (CastRule r : cast.rules) {
                aims += r.aim != null ? 1 : 0;
            }
            if (aims > 0) {
                sb.append(", ").append(aims).append(" aimed at an opponent's permanent (danger = ").append(cast.dangerLife).append(" x life + ")
                  .append(cast.dangerPermanents).append(" x nonland permanents)");
            }
            for (CastRule r : cast.rules) {
                if (r.isForge()) {
                    sb.append(", Forge's choice among the unnamed at rule ").append(r.index).append(r.waitMain2 ? " (the rules below wait for main 2)" : "");
                }
            }
        }
        if (!triggers.isEmpty()) {
            sb.append(" triggers=").append(triggers.size()).append(" rule(s)");
        }
        if (block != null && block.survive) {
            sb.append(" block=adds the blocks that keep it alive");
        }
        if (targets != null && targets.triggersByDanger) {
            sb.append(" targets=removal triggers by danger (min ").append(targets.min).append(", margin ").append(targets.margin).append(")");
        }
        if (targets != null && !targets.counterCards.isEmpty()) {
            sb.append(" counters=").append(targets.counterCards).append(" on its own dying creature at most ").append(targets.counterOwnPerTurn).append(" time(s) a turn");
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
