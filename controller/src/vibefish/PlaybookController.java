package vibefish;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import forge.LobbyPlayer;
import forge.ai.AiPlayDecision;
import forge.ai.ComputerUtil;
import forge.ai.ComputerUtilAbility;
import forge.ai.ComputerUtilCard;
import forge.ai.ComputerUtilCombat;
import forge.ai.ComputerUtilCost;
import forge.ai.ComputerUtilMana;
import forge.ai.PlayerControllerAi;
import forge.ai.SpellApiToAi;
import forge.game.Game;
import forge.game.GameEntity;
import forge.game.ability.ApiType;
import forge.game.card.Card;
import forge.game.card.CardCollection;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.cost.Cost;
import forge.game.cost.CostPart;
import forge.game.cost.CostPayLife;
import forge.game.keyword.Keyword;
import forge.game.phase.PhaseHandler;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
import forge.game.trigger.WrappedAbility;
import forge.game.zone.ZoneType;

/**
 * Forge's AI controller with a deck's playbook on top (Phase 4). Only the decisions the playbook covers are taken
 * here; everything else, and every case the policy declines, is Forge's own AI. One instance per seat; Forge itself
 * is untouched (public hooks only, DESIGN.md §3.1).
 */
public class PlaybookController extends PlayerControllerAi {

    /** Counters for the game being played, read into run.json by the harness. */
    public static final Map<String, Integer> STATS = new LinkedHashMap<>();

    /** {@code -Dvibefish.trace=true} (FORGE_JAVA_OPTS): one stderr line per decision a rule takes, for tuning a playbook. */
    private static final boolean TRACE = Boolean.getBoolean("vibefish.trace");

    private void trace(String what) {
        if (TRACE) {
            System.err.printf("[playbook] turn %d %s: %s%n", getGame().getPhaseHandler().getTurn(), player.getName(), what);
        }
    }

    private final Playbook playbook;

    public PlaybookController(Game game, Player p, LobbyPlayer lp, Playbook playbook) {
        super(game, p, lp);
        this.playbook = playbook;
    }

    /** The same counters for each playbook seat by itself, keyed by the seat's name, which is its deck id (0.4.0). */
    private static final Map<String, Map<String, Integer>> BY_SEAT = new LinkedHashMap<>();

    public static synchronized void resetStats() {
        STATS.clear();
        BY_SEAT.clear();
    }

    private static synchronized void add(String seat, String key, int by) {
        STATS.merge(key, by, Integer::sum);
        BY_SEAT.computeIfAbsent(seat, k -> new LinkedHashMap<>()).merge(key, by, Integer::sum);
    }

    private void count(String key, int by) {
        add(player.getName(), key, by);
    }

    public static synchronized Map<String, Map<String, Integer>> statsBySeatSnapshot() {
        Map<String, Map<String, Integer>> copy = new LinkedHashMap<>();
        for (Map.Entry<String, Map<String, Integer>> e : BY_SEAT.entrySet()) {
            copy.put(e.getKey(), new LinkedHashMap<>(e.getValue()));
        }
        return copy;
    }

    public static synchronized Map<String, Integer> statsSnapshot() {
        return new LinkedHashMap<>(STATS);
    }

    // ------------------------------------------------------------------ attack

    @Override
    public void declareAttackers(Player attacker, Combat combat) {
        Playbook.Attack policy = playbook == null ? null : playbook.attack;
        if (policy == null || attacker != player) {
            super.declareAttackers(attacker, combat);
            return;
        }
        count("attack_decisions", 1);
        boolean declared = false;
        if ("forge".equals(policy.policy)) {
            super.declareAttackers(attacker, combat);   // Forge's own attack; the block is there for what follows it
            declared = true;
        } else {
            try {
                if ("pressure".equals(policy.policy) ? pressure(attacker, combat, policy) : goWide(attacker, combat, policy)) {
                    count("attack_policy", 1);
                    declared = true;
                }
            } catch (RuntimeException e) {
                count("attack_errors", 1);
                for (Card c : new ArrayList<>(combat.getAttackers())) {
                    combat.removeFromCombat(c);
                }
            }
            if (!declared) {
                count("attack_fallback", 1);
                super.declareAttackers(attacker, combat);
            }
        }
        if (policy.finish) {
            try {
                finish(attacker, combat);
            } catch (RuntimeException e) {
                count("attack_kill_errors", 1);
            }
        }
        if (policy.guard) {
            try {
                guard(attacker, combat);
            } catch (RuntimeException e) {
                count("attack_guard_errors", 1);
            }
        }
    }

    /**
     * Take a kill no block prevents. After the policy has declared its attack, each opponent the seat is sure to
     * kill gets enough attackers that the damage reaches its life whatever it blocks: the opponent that looks most
     * dangerous first, then any other that the creatures still unassigned can kill the same way. Creatures the
     * policy sent elsewhere are moved; everything else stays as declared. If the changed attack is not a legal
     * one the policy's own declaration is put back. With {@code "finish": "leader"} the kills are taken only from
     * the most dangerous opponent down: the walk stops at the first opponent that cannot be killed for sure, so a
     * weaker opponent is left alone while a more dangerous one lives (DESIGN §34: at 2,000 tables the kill of
     * the most dangerous opponent won games and the kill of a lesser one lost them).
     */
    private void finish(Player attacker, Combat combat) {
        List<Player> opps = new ArrayList<>();
        for (Player opp : attacker.getOpponents()) {
            if (!opp.hasLost() && opp.getLife() > 0) {
                opps.add(opp);
            }
        }
        opps.sort((a, b) -> Integer.compare(danger(b), danger(a)));
        Map<Card, Player> plan = new LinkedHashMap<>();
        StringBuilder what = new StringBuilder();
        for (Player d : opps) {
            List<Card> can = new ArrayList<>();
            for (Card c : CombatMath.freeAttackers(getGame(), attacker, d)) {
                if (!plan.containsKey(c)) {
                    can.add(c);
                }
            }
            can.sort((x, y) -> Integer.compare(CombatMath.hits(y), CombatMath.hits(x)));
            List<Card> blockers = CombatMath.ableBlockers(d);
            if (CombatMath.through(can, blockers) < d.getLife()) {
                if (playbook.attack.finishLeader) {
                    for (Player lesser : opps.subList(opps.indexOf(d) + 1, opps.size())) {     // for the count and the trace only
                        List<Card> left = new ArrayList<>();
                        for (Card c : CombatMath.freeAttackers(getGame(), attacker, lesser)) {
                            if (!plan.containsKey(c)) {
                                left.add(c);
                            }
                        }
                        if (CombatMath.through(left, CombatMath.ableBlockers(lesser)) >= lesser.getLife()) {
                            count("attack_kill_left", 1);
                            trace("leaves " + lesser.getName() + " alive (life " + lesser.getLife() + ", danger " + danger(lesser) + "): "
                                    + d.getName() + " is more dangerous (" + danger(d) + ") and cannot be killed for sure");
                            break;
                        }
                    }
                    break;                              // nothing below an opponent that lives
                }
                continue;
            }
            List<Card> chosen = new ArrayList<>();
            for (Card c : can) {                        // the heaviest first, until what is sure to get through is enough
                chosen.add(c);
                if (CombatMath.through(chosen, blockers) >= d.getLife()) {
                    break;
                }
            }
            for (Card c : chosen) {
                plan.put(c, d);
            }
            what.append(what.length() == 0 ? "" : "; ").append(chosen.size()).append(" at ").append(d.getName())
                .append(" (life ").append(d.getLife()).append(", ").append(CombatMath.through(chosen, blockers)).append(" sure through ")
                .append(blockers.size()).append(" blockers)");
        }
        if (plan.isEmpty()) {
            return;
        }
        count("attack_kill_seen", 1);
        Map<Card, GameEntity> before = new LinkedHashMap<>();
        for (Card c : combat.getAttackers()) {
            before.put(c, combat.getDefenderByAttacker(c));
        }
        int moved = 0;
        for (Map.Entry<Card, Player> e : plan.entrySet()) {
            GameEntity now = before.get(e.getKey());
            if (now == e.getValue()) {
                continue;
            }
            if (now != null) {
                combat.removeFromCombat(e.getKey());
            }
            combat.addAttacker(e.getKey(), e.getValue());
            moved++;
        }
        if (moved == 0) {
            count("attack_kill_already", 1);            // the policy's own attack had them there
            return;
        }
        if (!CombatUtil.validateAttackers(combat)) {
            for (Card c : new ArrayList<>(combat.getAttackers())) {
                combat.removeFromCombat(c);
            }
            for (Map.Entry<Card, GameEntity> e : before.entrySet()) {
                combat.addAttacker(e.getKey(), e.getValue());
            }
            count("attack_kill_invalid", 1);
            return;
        }
        count("attack_kill", 1);
        count("attack_kill_moved", moved);
        trace("takes the kill: " + what + " (" + moved + " attacker(s) added or moved)");
    }

    // ------------------------------------------------------------------ blocks

    /**
     * Forge's AI blocks; with {@code block.survive} the seat does not die to an attack it could have blocked.
     * When Forge's blocks leave at least the seat's life unblocked, blocks are added to them: the heaviest
     * unblocked attackers that one creature may stop get the least valuable creatures that are not blocking yet,
     * and only as many as it takes for the unblocked damage to fall under the seat's life. If adding is not
     * enough but another set of blocks would be, the seat's blocks are declared anew that way. A set of blocks
     * Forge's rules refuse is taken back and Forge's own stand.
     */
    @Override
    public void declareBlockers(Player defender, Combat combat) {
        super.declareBlockers(defender, combat);
        if (playbook == null || playbook.block == null || !playbook.block.survive || defender != player) {
            return;
        }
        try {
            survive(combat);
        } catch (RuntimeException e) {
            count("block_survive_errors", 1);
        }
    }

    private void survive(Combat combat) {
        List<Card> attackers = new ArrayList<>(combat.getAttackersOf(player));
        int life = player.getLife();
        List<Card> open = new ArrayList<>();
        int incoming = 0;
        boolean cmd = false;                            // a commander's lethal damage is unblocked
        Map<Card, List<Card>> before = new LinkedHashMap<>();
        for (Card a : attackers) {
            List<Card> bs = new ArrayList<>(combat.getBlockers(a));
            before.put(a, bs);
            if (bs.isEmpty()) {
                open.add(a);
                incoming += CombatMath.strikes(a);
                cmd |= CombatMath.lethalCommander(a, player);
            }
        }
        if (attackers.isEmpty() || life <= 0 || (incoming < life && !cmd)) {
            return;
        }
        count("block_lethal_seen", 1);
        List<Card> blocking = new ArrayList<>(combat.getAllBlockers());
        List<Card> able = new ArrayList<>();
        for (Card c : player.getCreaturesInPlay()) {
            if (CombatUtil.canBlock(c, combat)) {
                able.add(c);
            }
        }
        able.sort((x, y) -> Integer.compare(ComputerUtilCard.evaluateCreature(x), ComputerUtilCard.evaluateCreature(y)));
        List<Card> free = new ArrayList<>(able);
        free.removeAll(blocking);
        // add to Forge's blocks: a commander's lethal damage first, then the heaviest unblocked attackers, until the seat lives
        List<Card[]> use = new ArrayList<>();
        int left = chosen(CombatMath.blocks(open, free, player), incoming, life, use);
        if (left < life && !commanderLeft(open, use)) {
            for (Card[] pair : use) {
                combat.addBlocker(pair[0], pair[1]);
            }
            if (CombatUtil.validateBlocks(combat, player) != null) {
                for (Card[] pair : use) {
                    combat.removeBlockAssignment(pair[0], pair[1]);
                }
                count("block_survive_invalid", 1);
                return;
            }
            count("block_survive", 1);
            count("block_survive_added", use.size());
            trace("blocks to live: " + use.size() + " block(s) added, " + incoming + " unblocked at " + life + " life" + (cmd ? " and a commander's lethal damage" : "") + ", now " + left);
            return;
        }
        // adding is not enough: would other blocks be?
        int total = 0;
        for (Card a : attackers) {
            total += CombatMath.strikes(a);
        }
        List<Card[]> anew = new ArrayList<>();
        left = chosen(CombatMath.blocks(attackers, able, player), total, life, anew);
        if (left >= life || commanderLeft(attackers, anew)) {
            count("block_lethal_hopeless", 1);          // no blocks of one creature an attacker keep the seat alive
            return;
        }
        for (Card b : blocking) {
            if (b.getController() == player) {
                combat.undoBlockingAssignment(b);
            }
        }
        for (Card[] pair : anew) {
            combat.addBlocker(pair[0], pair[1]);
        }
        if (CombatUtil.validateBlocks(combat, player) != null) {
            for (Card[] pair : anew) {
                combat.removeBlockAssignment(pair[0], pair[1]);
            }
            for (Map.Entry<Card, List<Card>> e : before.entrySet()) {
                for (Card b : e.getValue()) {
                    combat.addBlocker(e.getKey(), b);
                }
            }
            count("block_survive_invalid", 1);
            return;
        }
        count("block_survive", 1);
        count("block_survive_reblocked", 1);
        trace("blocks to live: its blocks declared anew, " + anew.size() + " block(s), " + incoming + " unblocked at " + life + " life" + (cmd ? " and a commander's lethal damage" : "") + ", now " + left);
    }

    /**
     * From the blocks that could be made (a commander's lethal damage first, then the heaviest attacker), take those
     * the seat needs: every block of a lethal commander, and others only while the unblocked damage is still at
     * least its life. Returns the unblocked damage left.
     */
    private int chosen(Map<Card, Card> pairs, int unblocked, int life, List<Card[]> use) {
        int left = unblocked;
        for (Map.Entry<Card, Card> e : pairs.entrySet()) {
            if (left < life && !CombatMath.lethalCommander(e.getKey(), player)) {
                continue;
            }
            use.add(new Card[] {e.getKey(), e.getValue()});
            left -= CombatMath.strikes(e.getKey());
        }
        return left;
    }

    /** Whether one of these attackers is a commander with lethal damage that the chosen blocks do not stop. */
    private boolean commanderLeft(List<Card> attackers, List<Card[]> use) {
        for (Card a : attackers) {
            if (!CombatMath.lethalCommander(a, player)) {
                continue;
            }
            boolean stopped = false;
            for (Card[] pair : use) {
                stopped |= pair[0] == a;
            }
            if (!stopped) {
                return true;
            }
        }
        return false;
    }

    /**
     * Do not tap out into a lethal answer. After the attack is declared (and after {@code finish}), look at each
     * opponent the attack is not sure to kill: with the creatures that would stay untapped at home, is the damage
     * it could send on its next turn sure to reach the seat's life, whatever the seat blocks? If so for any of
     * them, and if keeping attackers home changes that, attackers are taken back until no single opponent is sure
     * to kill the seat: each time the one whose staying home lowers the threat most, and among equals the one
     * that deals least. With {@code "guard": "table"} the question is asked of the opponents one after another
     * first (what each is sure to get through the same blockers, summed: a seat hit by one opponent is finished
     * by the next), and of the worst single opponent when nothing kept home answers that. The attackers of a kill
     * the attack is sure of are never taken back, and an attack that leaves the seat dead on board whatever stays
     * home stands as declared (a race). The arithmetic is the logger's ({@code CombatMath.through}: one blocker
     * an attacker, no trample credited), so "sure" errs to the side of not acting. If what is left is not a legal
     * attack the declaration is put back.
     */
    private void guard(Player me, Combat combat) {
        List<Card> tapping = new ArrayList<>();         // attackers that will be tapped during the opponents' turns
        for (Card c : combat.getAttackers()) {
            if (c.getController() == me && !c.hasKeyword(Keyword.VIGILANCE)) {
                tapping.add(c);
            }
        }
        if (tapping.isEmpty()) {
            return;
        }
        List<Player> threats = new ArrayList<>();
        List<Card> locked = new ArrayList<>();          // the attackers of a kill the attack is sure of
        for (Player opp : me.getOpponents()) {
            if (opp.hasLost() || opp.getLife() <= 0) {
                continue;
            }
            List<Card> at = new ArrayList<>(combat.getAttackersOf(opp));
            if (!at.isEmpty() && CombatMath.through(at, CombatMath.ableBlockers(opp)) >= opp.getLife()) {
                locked.addAll(at);                      // it will not be there to answer
            } else {
                threats.add(opp);
            }
        }
        if (threats.isEmpty()) {
            return;                                     // the attack takes out everyone who is left
        }
        List<Card> home = new ArrayList<>();
        for (Card c : me.getCreaturesInPlay()) {
            if (!c.isTapped() && !tapping.contains(c) && CombatUtil.canBlock(c)) {
                home.add(c);
            }
        }
        Map<Player, List<Card>> theirs = new LinkedHashMap<>();
        for (Player opp : threats) {
            theirs.put(opp, CombatMath.nextTurnAttackers(opp, me));
        }
        int life = me.getLife() - Math.max(0, playbook.attack.guardMargin);   // dead this much early: life falls between an attack and the answer
        boolean table = playbook.attack.guardTable;
        if (answer(theirs, home, table) < life) {
            return;                                     // nobody (or, for the table, not all of them together) is sure to kill the seat
        }
        count("attack_guard_seen", 1);
        List<Card> cand = new ArrayList<>();
        for (Card c : tapping) {
            if (!locked.contains(c) && CombatUtil.canBlock(c)) {
                cand.add(c);
            }
        }
        List<Card> all = new ArrayList<>(home);
        all.addAll(cand);
        boolean sum = table;
        if (sum && (cand.isEmpty() || answer(theirs, all, true) >= life)) {
            sum = false;                                // the table cannot be held off: at least no single opponent
            if (answer(theirs, home, false) < life) {
                count("attack_guard_hopeless", 1);      // and none is sure to kill it alone as things are: the attack stands
                return;
            }
        }
        if (cand.isEmpty() || answer(theirs, all, sum) >= life) {
            count("attack_guard_hopeless", 1);          // dead on board whatever stays home: the attack stands
            return;
        }
        int was = answer(theirs, home, sum);
        int now = was;
        List<Card> back = new ArrayList<>();
        while (now >= life && !cand.isEmpty()) {
            Card best = null;
            int bestNow = Integer.MAX_VALUE;
            for (Card c : cand) {
                List<Card> h = new ArrayList<>(home);
                h.add(c);
                int w = answer(theirs, h, sum);
                if (best == null || w < bestNow || (w == bestNow && CombatMath.hits(c) < CombatMath.hits(best))) {
                    best = c;
                    bestNow = w;
                }
            }
            home.add(best);
            cand.remove(best);
            back.add(best);
            now = bestNow;
        }
        Map<Card, GameEntity> before = new LinkedHashMap<>();
        for (Card c : combat.getAttackers()) {
            before.put(c, combat.getDefenderByAttacker(c));
        }
        for (Card c : back) {
            combat.removeFromCombat(c);
        }
        if (!CombatUtil.validateAttackers(combat)) {
            for (Card c : new ArrayList<>(combat.getAttackers())) {
                combat.removeFromCombat(c);
            }
            for (Map.Entry<Card, GameEntity> e : before.entrySet()) {
                combat.addAttacker(e.getKey(), e.getValue());
            }
            count("attack_guard_invalid", 1);
            return;
        }
        count("attack_guard", 1);
        count("attack_guard_back", back.size());
        if (table && !sum) {
            count("attack_guard_single", 1);            // asked for the table, could only hold off the worst single opponent
        }
        if (combat.getAttackers().isEmpty()) {
            count("attack_guard_all", 1);               // nothing attacks after all
        }
        trace("keeps " + back.size() + " of " + before.size() + " attacker(s) home: at " + me.getLife() + " life"
                + (playbook.attack.guardMargin > 0 ? " (less a margin of " + playbook.attack.guardMargin + ")" : "") + ", "
                + (sum ? "the opponents in turn" : "one opponent") + " would get " + (was >= LETHAL ? "a commander's lethal damage" : String.valueOf(was))
                + " through what stayed home, now " + now);
    }

    /**
     * What these opponents get through these blockers on their next turns under a blocking plan the seat could
     * carry out ({@code CombatMath.plannedLeft}, since 0.4.4; before that what they were sure to get through
     * whatever the seat blocked, which left trample, menace and commander damage out and saw one death in twelve
     * coming): the most any one of them does, or with {@code sum} all of them one after another (each against
     * the same blockers).
     */
    private int answer(Map<Player, List<Card>> theirs, List<Card> home, boolean sum) {
        int worst = 0;
        int total = 0;
        for (List<Card> at : theirs.values()) {
            int[] plan = CombatMath.plannedLeft(at, home, player);
            int t = plan[1] != 0 ? LETHAL : plan[0];    // a commander's lethal damage is lethal whatever the life
            worst = Math.max(worst, t);
            total = Math.min(LETHAL, total + t);
        }
        return sum ? total : worst;
    }

    private static final int LETHAL = 1_000_000;

    /** Attack the chosen opponent with every creature the reserve does not need. True when the policy declared. */
    private boolean goWide(Player attacker, Combat combat, Playbook.Attack policy) {
        CardCollection possible = CombatUtil.getPossibleAttackers(attacker);
        if (possible.isEmpty()) {
            count("attack_no_attackers", 1);
            return false;
        }
        Player defender = chooseDefender(attacker, possible, policy);
        if (defender == null) {
            count("attack_no_defender", 1);
            return false;
        }
        List<Card> candidates = new ArrayList<>();
        for (Card c : possible) {
            if (!CombatUtil.canAttack(c, defender)) {
                continue;
            }
            Cost cost = CombatUtil.getAttackCost(getGame(), c, defender);
            if (cost != null && !cost.isFree()) {
                continue;                       // attack taxes: let Forge weigh those
            }
            candidates.add(c);
        }
        List<Card> reserve = reserve(attacker, candidates, policy);
        List<Card> going = new ArrayList<>(candidates);
        going.removeAll(reserve);
        if (going.size() < policy.minAttackers) {
            count("attack_below_min", 1);
            return false;
        }
        Map<Card, Player> plan = policy.spread ? spread(attacker, going, defender, policy) : null;
        Set<Player> attacked = new HashSet<>();
        for (Card c : going) {
            Player d = plan == null ? defender : plan.getOrDefault(c, defender);
            combat.addAttacker(c, d);
            attacked.add(d);
        }
        if (attacked.size() > 1) {
            count("attack_spread", 1);
        }
        if (!CombatUtil.validateAttackers(combat)) {
            for (Card c : new ArrayList<>(combat.getAttackers())) {
                combat.removeFromCombat(c);
            }
            count("attack_invalid", 1);
            return false;
        }
        count("attackers_declared", going.size());
        count("attackers_reserved", reserve.size());
        return true;
    }

    // ------------------------------------------------------------------ attack: pressure

    /** One opponent's share of a pressure attack. */
    private static final class Swing {
        final Player defender;
        final List<Card> attackers = new ArrayList<>();
        int through;            // damage expected to reach the player
        int losses;             // attackers the defender can kill by blocking
        Swing(Player defender) {
            this.defender = defender;
        }
    }

    /**
     * The pressure policy. First the kills: in the playbook's target order, an opponent that is dead even if each of
     * its blockers stops one of our biggest attackers gets the attackers that takes. Then, with what is left, the
     * opponent the swing scores best on (the damage that gets through, less {@code damagePerLoss} for every attacker
     * a blocker can kill; the target order breaks near ties). Against that opponent the attackers no blocker can kill
     * always go; the others go only together and only if the damage they add is worth the ones that die. Whether a
     * blocker can block and kill is Forge's own combat arithmetic. True when the policy declared (possibly nobody).
     */
    private boolean pressure(Player attacker, Combat combat, Playbook.Attack policy) {
        CardCollection possible = CombatUtil.getPossibleAttackers(attacker);
        if (possible.isEmpty()) {
            count("attack_no_attackers", 1);
            return false;
        }
        killMemo.clear();
        List<Card> left = new ArrayList<>();
        for (Card c : possible) {
            left.add(c);
        }
        List<Card> reserve = reserve(attacker, left, policy);
        left.removeAll(reserve);
        List<Player> order = new ArrayList<>();
        for (Player opp : attacker.getOpponents()) {
            order.add(opp);
        }
        order.sort(Comparator.comparingInt((Player opp) -> defenderScore(opp, policy)));

        Map<Card, Player> plan = new LinkedHashMap<>();
        Set<Player> dead = new HashSet<>();
        for (Player d : order) {
            List<Card> killers = lethalOn(left, d, combat);
            if (killers != null) {
                for (Card c : killers) {
                    plan.put(c, d);
                }
                left.removeAll(killers);
                dead.add(d);
            }
        }
        Swing best = null;
        double bestScore = 0;
        for (Player d : order) {
            if (dead.contains(d)) {
                continue;
            }
            Swing s = swing(attacker, left, d, combat, policy);
            double score = s.through - (double) policy.damagePerLoss * s.losses;
            if (s.attackers.isEmpty() || score <= 0) {
                continue;
            }
            // an opponent later in the playbook's order has to be clearly the better swing to be preferred
            if (best == null || score > bestScore * 1.2 + 1) {
                best = s;
                bestScore = score;
            }
        }
        if (best != null) {
            for (Card c : best.attackers) {
                plan.put(c, best.defender);
            }
            count("attack_expected_losses", best.losses);
        }
        // Whoever is still home goes wherever no blocker can kill it: at a living opponent first, else as insurance
        // on a kill. Nothing safe to attack is the only reason to stay back.
        if (!plan.isEmpty()) {
            List<Player> anywhere = new ArrayList<>();
            for (Player d : order) {
                if (!dead.contains(d)) {
                    anywhere.add(d);
                }
            }
            for (Player d : order) {
                if (dead.contains(d)) {
                    anywhere.add(d);
                }
            }
            for (Card c : left) {
                if (plan.containsKey(c)) {
                    continue;
                }
                for (Player d : anywhere) {
                    if (canSwingAt(c, d) && safeFrom(attacker, c, blockersOf(d), combat)) {
                        plan.put(c, d);
                        break;
                    }
                }
            }
        }
        if (plan.size() < policy.minAttackers) {
            if (!CombatUtil.validateAttackers(combat)) {
                count("attack_forced", 1);
                return false;                           // a creature has to attack: Forge declares, it knows the requirement
            }
            count("attack_held", possible.size());
            count("attack_none", 1);
            return true;                                // nothing worth sending: nobody attacks
        }
        Set<Player> attacked = new HashSet<>();
        for (Map.Entry<Card, Player> e : plan.entrySet()) {
            combat.addAttacker(e.getKey(), e.getValue());
            attacked.add(e.getValue());
        }
        if (!CombatUtil.validateAttackers(combat)) {
            for (Card c : new ArrayList<>(combat.getAttackers())) {
                combat.removeFromCombat(c);
            }
            count("attack_invalid", 1);
            return false;
        }
        if (attacked.size() > 1) {
            count("attack_spread", 1);
        }
        if (!dead.isEmpty()) {
            count("attack_lethal", dead.size());
        }
        count("attackers_declared", plan.size());
        count("attackers_reserved", reserve.size());
        count("attack_held", possible.size() - reserve.size() - plan.size());
        return true;
    }

    private static List<Card> blockersOf(Player d) {
        List<Card> blockers = new ArrayList<>();
        for (Card b : d.getCreaturesInPlay()) {
            if (CombatUtil.canBlock(b)) {
                blockers.add(b);
            }
        }
        return blockers;
    }

    /** No blocker in the list can both block this attacker and kill it. */
    private boolean safeFrom(Player ai, Card a, List<Card> blockers, Combat combat) {
        for (Card b : blockers) {
            if (kills(ai, a, b, combat)) {
                return false;
            }
        }
        return true;
    }

    /** Answers of {@link #kills} for the declaration being made: a board of tokens asks the same question many times. */
    private final Map<String, Boolean> killMemo = new LinkedHashMap<>();

    /**
     * Whether this blocker can block this attacker and destroy it, by Forge's combat arithmetic on what is on the
     * battlefield now (power, toughness, first strike, deathtouch, indestructible, protection and the like). Abilities
     * either side might activate during combat are left out: asking Forge to weigh those costs a mana-payment search
     * for every pair, which is minutes on a wide board.
     */
    private boolean kills(Player ai, Card a, Card b, Combat combat) {
        String key = a.getName() + "|" + a.getNetPower() + "|" + a.getNetToughness() + "|" + a.getDamage() + "|" + b.getId();
        Boolean known = killMemo.get(key);
        if (known == null) {
            known = CombatUtil.canBlock(a, b) && ComputerUtilCombat.canDestroyAttacker(ai, a, b, combat, true);
            killMemo.put(key, known);
        }
        return known;
    }

    private boolean canSwingAt(Card c, Player d) {
        if (!CombatUtil.canAttack(c, d)) {
            return false;
        }
        Cost cost = CombatUtil.getAttackCost(getGame(), c, d);
        return cost == null || cost.isFree();           // attack taxes: not this policy's to pay
    }

    /**
     * The attackers that kill this opponent even if each of its blockers stops one of the biggest of them, or null
     * when the creatures at hand cannot. Evasion and trample are not counted, so a kill is never claimed too early.
     */
    private List<Card> lethalOn(List<Card> left, Player d, Combat combat) {
        List<Card> able = new ArrayList<>();
        for (Card c : left) {
            if (canSwingAt(c, d)) {
                able.add(c);
            }
        }
        able.sort(Comparator.comparingInt((Card c) -> ComputerUtilCombat.damageIfUnblocked(c, d, combat, false)).reversed());
        int blockers = blockersOf(d).size();
        List<Card> sent = new ArrayList<>();
        int unblocked = 0;
        for (Card c : able) {
            sent.add(c);
            if (sent.size() > blockers) {
                unblocked += Math.max(0, ComputerUtilCombat.damageIfUnblocked(c, d, combat, false));
            }
            if (unblocked >= d.getLife()) {
                return sent;
            }
        }
        return null;
    }

    /** What attacking this opponent with the creatures at hand looks like: who goes, what gets through, what dies. */
    private Swing swing(Player ai, List<Card> left, Player d, Combat combat, Playbook.Attack policy) {
        Swing s = new Swing(d);
        List<Card> blockers = blockersOf(d);
        List<Card> safe = new ArrayList<>();
        List<Card> risky = new ArrayList<>();
        Map<Card, List<Card>> killers = new LinkedHashMap<>();
        for (Card a : left) {
            if (!canSwingAt(a, d)) {
                continue;
            }
            List<Card> k = new ArrayList<>();
            for (Card b : blockers) {
                if (kills(ai, a, b, combat)) {
                    k.add(b);
                }
            }
            if (k.isEmpty()) {
                safe.add(a);
            } else {
                risky.add(a);
                killers.put(a, k);
            }
        }
        int safeDamage = 0;
        for (Card a : safe) {
            safeDamage += Math.max(0, ComputerUtilCombat.damageIfUnblocked(a, d, combat, false));
        }
        // The defender kills what it can, the most valuable attacker first, each blocker once.
        risky.sort(Comparator.comparingInt((Card a) -> ComputerUtilCard.evaluateCreature(a)).reversed());
        Set<Card> used = new HashSet<>();
        int crowdDamage = 0;
        int victims = 0;
        for (Card a : risky) {
            Card killer = null;
            for (Card b : killers.get(a)) {
                if (!used.contains(b)) {
                    killer = b;
                    break;
                }
            }
            if (killer != null) {
                used.add(killer);
                victims++;
            } else {
                crowdDamage += Math.max(0, ComputerUtilCombat.damageIfUnblocked(a, d, combat, false));
            }
        }
        s.attackers.addAll(safe);
        s.through = safeDamage;
        if (victims < risky.size() && crowdDamage >= policy.damagePerLoss * victims) {
            s.attackers.addAll(risky);                  // the crowd goes: what gets through is worth what dies
            s.through += crowdDamage;
            s.losses = victims;
        }
        return s;
    }

    /**
     * The attack split over opponents: the first defender gets the biggest attackers until it is dead even if every
     * untapped creature it has blocks the biggest of them, and what is left over goes to the next opponent by the same
     * rule; an opponent that cannot be killed this turn takes everything that is left. Evasion and trample are not
     * counted, so the estimate is on the careful side.
     */
    private Map<Card, Player> spread(Player attacker, List<Card> going, Player first, Playbook.Attack policy) {
        Map<Card, Player> plan = new LinkedHashMap<>();
        List<Player> order = new ArrayList<>();
        order.add(first);
        List<Player> rest = new ArrayList<>();
        for (Player opp : attacker.getOpponents()) {
            if (opp != first) {
                rest.add(opp);
            }
        }
        rest.sort(Comparator.comparingInt((Player opp) -> defenderScore(opp, policy)));
        order.addAll(rest);
        List<Card> left = new ArrayList<>(going);
        left.sort(Comparator.comparingInt(Card::getNetPower).reversed());
        for (Player d : order) {
            if (left.isEmpty()) {
                break;
            }
            int blockers = untappedCreatures(d);
            List<Card> sent = new ArrayList<>();
            int unblocked = 0;
            boolean dead = false;
            for (Card c : left) {
                if (!CombatUtil.canAttack(c, d)) {
                    continue;
                }
                Cost cost = CombatUtil.getAttackCost(getGame(), c, d);
                if (cost != null && !cost.isFree()) {
                    continue;
                }
                sent.add(c);
                if (sent.size() > blockers) {           // the biggest ones are the ones that get blocked
                    unblocked += Math.max(0, c.getNetPower());
                }
                if (unblocked >= d.getLife()) {
                    dead = true;
                    break;
                }
            }
            for (Card c : sent) {
                plan.put(c, d);
            }
            if (!dead) {
                break;                                  // not dead this turn: it takes everything that can reach it
            }
            left.removeAll(sent);
        }
        return plan;
    }

    /** Lower is attacked first. */
    private static int defenderScore(Player opp, Playbook.Attack policy) {
        switch (policy.target) {
            case "weakest_board":
                return untappedCreatures(opp) * 100 + opp.getLife();
            case "highest_life":
                return -opp.getLife() * 100 + untappedCreatures(opp);
            case "biggest_board":
                return -boardPower(opp) * 100 - opp.getLife();
            default:
                return opp.getLife() * 100 + untappedCreatures(opp);
        }
    }

    private static int boardPower(Player p) {
        int n = 0;
        for (Card c : p.getCreaturesInPlay()) {
            n += Math.max(0, c.getNetPower());
        }
        return n;
    }

    /** The opponent to attack: lowest life, or the weakest board, among those at least one candidate can attack. */
    private Player chooseDefender(Player attacker, CardCollection possible, Playbook.Attack policy) {
        Player best = null;
        int bestScore = Integer.MAX_VALUE;
        for (Player opp : attacker.getOpponents()) {
            boolean reachable = false;
            for (Card c : possible) {
                if (CombatUtil.canAttack(c, opp)) {
                    reachable = true;
                    break;
                }
            }
            if (!reachable) {
                continue;
            }
            int score = defenderScore(opp, policy);
            if (score < bestScore) {
                bestScore = score;
                best = opp;
            }
        }
        return best;
    }

    private static int untappedCreatures(Player p) {
        int n = 0;
        for (Card c : p.getCreaturesInPlay()) {
            if (c.isUntapped()) {
                n++;
            }
        }
        return n;
    }

    /**
     * Creatures to keep home: enough of the toughest candidates that the strongest single opponent's possible attack
     * next turn, with each kept blocker absorbing its biggest remaining attacker, stays below our life minus the
     * safety margin. Nothing is kept when no opponent threatens that.
     */
    private List<Card> reserve(Player attacker, List<Card> candidates, Playbook.Attack policy) {
        List<Card> reserve = new ArrayList<>();
        List<Integer> threat = biggestThreat(attacker);
        int incoming = 0;
        for (int p : threat) {
            incoming += p;
        }
        int limit = attacker.getLife() - policy.safetyMargin;
        if (incoming < limit) {
            return reserve;
        }
        List<Card> byToughness = new ArrayList<>(candidates);
        byToughness.sort(Comparator.comparingInt(Card::getNetToughness).thenComparingInt(Card::getNetPower).reversed());
        for (Card c : byToughness) {
            if (reserve.size() >= policy.maxReserve || incoming < limit || threat.isEmpty()) {
                break;
            }
            reserve.add(c);
            incoming -= threat.remove(0);           // the kept blocker takes the biggest remaining attacker
        }
        return reserve;
    }

    /** Powers, biggest first, of the creatures of the single opponent whose possible attack next turn is largest. */
    private List<Integer> biggestThreat(Player attacker) {
        List<Integer> best = new ArrayList<>();
        int bestTotal = -1;
        for (Player opp : attacker.getOpponents()) {
            List<Integer> powers = new ArrayList<>();
            int total = 0;
            for (Card c : opp.getCreaturesInPlay()) {
                if (CombatUtil.canAttackNextTurn(c, attacker)) {
                    int p = Math.max(0, c.getNetPower());
                    powers.add(p);
                    total += p;
                }
            }
            if (total > bestTotal) {
                bestTotal = total;
                best = powers;
            }
        }
        best.sort(Comparator.reverseOrder());
        return best;
    }

    // ------------------------------------------------------------------ cast

    /** Per-turn state of the cast rules: what a rule already tried this turn, so a cast that fails cannot loop. */
    private int castTurn = -1;
    private int castPlays;
    private int castPendingId = -1;
    private int castPendingSpells = -1;
    private final Set<Integer> castTried = new HashSet<>();
    private final Map<Integer, Integer> castActivations = new LinkedHashMap<>();
    private final Map<String, Integer> castByName = new LinkedHashMap<>();
    private boolean castRetargeted;
    private Card castAimed;                 // the opponent's permanent the last aimed rule chose (for the trace and the counters)
    private boolean castWaiting;            // a forge rule with "wait" stopped the rules for this decision: the seat passes
    private int castWaitCard = -1;          // the card the rules waited for this turn, until Forge has chosen in main 2
    private int castWaitTurn = -1;
    private final Set<Integer> castWaitDeclined = new HashSet<>();   // cards waited for that Forge then did not cast: not waited for again

    /**
     * The seat's next play. Hold rules bind Forge's own choice on every call; play rules run on the seat's own main
     * phases with an empty stack, after Forge has had the chance to make its land drop. Whatever no rule covers is
     * Forge's choice, as before.
     */
    @Override
    public List<SpellAbility> chooseSpellAbilityToPlay() {
        Playbook.Cast cast = playbook == null ? null : playbook.cast;
        if (cast == null) {
            return super.chooseSpellAbilityToPlay();
        }
        Game game = getGame();
        PhaseHandler ph = game.getPhaseHandler();
        boolean ownMain = ph.isPlayerTurn(player) && (ph.is(PhaseType.MAIN1) || ph.is(PhaseType.MAIN2)) && game.getStack().isEmpty();
        if (!ownMain) {
            return forgeChoice(cast);
        }
        List<SpellAbility> forge = null;
        boolean asked = false;
        CardCollection lands = ComputerUtilAbility.getAvailableLandsToPlay(game, player);
        if (lands != null && !lands.isEmpty()) {
            if (cast.hasBeforeLand) {
                // A landfall deck's payoffs go down before the land that would trigger them.
                SpellAbility early = null;
                castRetargeted = false;
                try {
                    early = castByRule(cast, ph, true);
                } catch (RuntimeException e) {
                    count("cast_errors", 1);
                }
                if (early != null) {
                    count("cast_decisions", 1);
                    count("cast_policy", 1);
                    count("cast_before_land", 1);
                    List<SpellAbility> one = new ArrayList<>();
                    one.add(early);
                    return one;
                }
            }
            forge = forgeChoice(cast);                  // the land drop first: every rule below wants the mana
            asked = true;
            if (forge != null && !forge.isEmpty() && forge.get(0).isLandAbility()) {
                return forge;
            }
        }
        count("cast_decisions", 1);
        SpellAbility pick = null;
        castRetargeted = false;
        castWaiting = false;
        try {
            pick = castByRule(cast, ph, false);
        } catch (RuntimeException e) {
            count("cast_errors", 1);
        }
        if (pick != null) {
            count("cast_policy", 1);
            List<SpellAbility> one = new ArrayList<>();
            one.add(pick);
            return one;
        }
        if (castWaiting) {
            return null;                                // pass: the mana is kept for what Forge casts after combat
        }
        // Forge's earlier answer stands unless a rule tried a spell and changed its targets on the way to giving up.
        return asked && !castRetargeted ? forge : forgeChoice(cast);
    }

    /**
     * Forge's own choice with the held plays left out. Forge drops abilities flagged {@code skip} from its candidates
     * for one decision, remembers which ones it dropped and clears their flags at the start of its next decision, so
     * a flag set here is sometimes cleared before it is read. When that lets a held play through, one unflagged call
     * empties Forge's memory of dropped abilities and the flags of the call after it all stand. A choice that is not
     * held is the same choice Forge would have made with the held plays removed (it takes the first acceptable
     * candidate in its own order), so the extra calls are only spent when a hold actually bites.
     */
    private List<SpellAbility> forgeChoice(Playbook.Cast cast) {
        List<Playbook.CastRule> holds = holdsInForce(cast);
        if (holds.isEmpty()) {
            return super.chooseSpellAbilityToPlay();
        }
        List<SpellAbility> flagged = new ArrayList<>();
        try {
            flagHeld(holds, flagged);
            List<SpellAbility> choice = super.chooseSpellAbilityToPlay();
            if (choice == null || choice.isEmpty() || !isHeld(choice.get(0), holds)) {
                return choice;
            }
            count("cast_hold_vetoes", 1);
            trace("held " + choice.get(0).getHostCard().getName() + " back from Forge: " + choice.get(0));
            unflag(flagged);
            super.chooseSpellAbilityToPlay();           // result unused: this call only resets Forge's skip memory
            flagHeld(holds, flagged);
            choice = super.chooseSpellAbilityToPlay();
            if (choice == null || choice.isEmpty() || !isHeld(choice.get(0), holds)) {
                return choice;
            }
            count("cast_hold_stuck", 1);
            trace("hold did not bind on " + choice.get(0).getHostCard().getName() + ", passing instead");
            return null;                                // pass rather than let a held play go
        } finally {
            unflag(flagged);
        }
    }

    private static void unflag(List<SpellAbility> flagged) {
        for (SpellAbility sa : flagged) {
            sa.setSkip(false);
        }
        flagged.clear();
    }

    /**
     * The hold rules in force now. A hold is on a card (its spell, and every ability of the permanent) or on one
     * ability of a permanent; when several rules hold the same thing it is released as soon as the conditions of one
     * of them are met.
     */
    private List<Playbook.CastRule> holdsInForce(Playbook.Cast cast) {
        Set<String> released = new HashSet<>();
        List<Playbook.CastRule> holds = new ArrayList<>();
        for (Playbook.CastRule rule : cast.rules) {
            if (!rule.isHold()) {
                continue;
            }
            if (!rule.when.isEmpty() && allHold(rule.when)) {
                for (String name : rule.cards) {
                    released.add(holdKey(name, rule.ability));
                }
            } else {
                holds.add(rule);
            }
        }
        heldReleased = released;
        return holds;
    }

    private Set<String> heldReleased = new HashSet<>();

    private static String holdKey(String name, String ability) {
        return name + "\u0000" + (ability == null ? "" : ability.toLowerCase());
    }

    /**
     * Whether a hold rule keeps Forge from this play: the card's spell from wherever it can be cast, or, for a
     * permanent of ours on the battlefield, its activated abilities (all of them, or the one whose text the rule
     * quotes in {@code ability}). Mana abilities are never held.
     */
    private boolean isHeld(SpellAbility sa, List<Playbook.CastRule> holds) {
        Card host = sa.getHostCard();
        if (host == null) {
            return false;
        }
        boolean onBattlefield = host.isInZone(ZoneType.Battlefield);
        if (onBattlefield ? !sa.isActivatedAbility() || sa.isManaAbility() : !sa.isSpell()) {
            return false;
        }
        String d = sa.getDescription();
        for (Playbook.CastRule rule : holds) {
            if (!rule.cards.contains(host.getName()) || heldReleased.contains(holdKey(host.getName(), rule.ability))) {
                continue;
            }
            if (rule.ability == null) {
                return true;                            // the card as a whole
            }
            if (onBattlefield && d != null && d.toLowerCase().contains(rule.ability.toLowerCase())) {
                return true;                            // this one ability of the permanent
            }
        }
        return false;
    }

    /**
     * Flags the held plays wherever Forge could make them from (hand, command zone, graveyard, exile, the top of the
     * library, the battlefield). A card's own spell abilities carry the flag into the alternative-cost copies Forge
     * derives from them (flashback, harmonize, a card it may play from exile).
     */
    private void flagHeld(List<Playbook.CastRule> holds, List<SpellAbility> flagged) {
        Set<String> names = new HashSet<>();
        for (Playbook.CastRule rule : holds) {
            names.addAll(rule.cards);
        }
        for (Card c : ComputerUtilAbility.getAvailableCards(getGame(), player)) {
            if (!names.contains(c.getName()) || (c.isInZone(ZoneType.Battlefield) && c.getController() != player)) {
                continue;
            }
            List<SpellAbility> all = new ArrayList<>();
            for (SpellAbility sa : c.getSpellAbilities()) {
                all.add(sa);
            }
            all.addAll(c.getAllPossibleAbilities(player, false));
            for (SpellAbility sa : all) {
                if (!sa.isSkip() && isHeld(sa, holds)) {
                    sa.setSkip(true);
                    flagged.add(sa);
                }
            }
        }
    }

    /**
     * Whether a play or activate rule names this play: the spell of a card some play rule lists, or, for a permanent
     * of ours on the battlefield, an activated ability some activate rule covers (all of the permanent's, or the one
     * whose text the rule quotes). Mana abilities and lands are never named.
     */
    private boolean isNamed(SpellAbility sa, Playbook.Cast cast) {
        Card host = sa.getHostCard();
        if (host == null || sa.isLandAbility()) {
            return false;
        }
        boolean onBattlefield = host.isInZone(ZoneType.Battlefield);
        if (onBattlefield ? !sa.isActivatedAbility() || sa.isManaAbility() : !sa.isSpell()) {
            return false;
        }
        String d = sa.getDescription();
        for (Playbook.CastRule rule : cast.rules) {
            if (!rule.cards.contains(host.getName())) {
                continue;
            }
            if (onBattlefield) {
                if (rule.isActivate() && (rule.ability == null || (d != null && d.toLowerCase().contains(rule.ability.toLowerCase())))) {
                    return true;
                }
            } else if (rule.isPlay()) {
                return true;
            }
        }
        return false;
    }

    /** Flags, for Forge's next decision, every play a rule names and every held play (see {@link #flagHeld}). */
    private void flagNamed(Playbook.Cast cast, List<Playbook.CastRule> holds, List<SpellAbility> flagged) {
        for (Card c : ComputerUtilAbility.getAvailableCards(getGame(), player)) {
            if (c.isInZone(ZoneType.Battlefield) && c.getController() != player) {
                continue;
            }
            List<SpellAbility> all = new ArrayList<>();
            for (SpellAbility sa : c.getSpellAbilities()) {
                all.add(sa);
            }
            all.addAll(c.getAllPossibleAbilities(player, false));
            for (SpellAbility sa : all) {
                if (!sa.isSkip() && (isNamed(sa, cast) || isHeld(sa, holds))) {
                    sa.setSkip(true);
                    flagged.add(sa);
                }
            }
        }
    }

    /**
     * A {@code forge} rule: Forge's own choice with the plays the rules name, and the held ones, left out; null when
     * it wants none of what is left. The flags work as in {@link #forgeChoice}: when Forge's memory of dropped
     * abilities lets a flagged play through, one unflagged call empties it and the flags of the call after stand.
     * Forge is asked afresh after this, so its earlier answer of the turn is not reused ({@code castRetargeted}).
     */
    private SpellAbility forgeUnnamed(Playbook.Cast cast) {
        List<Playbook.CastRule> holds = holdsInForce(cast);
        List<SpellAbility> flagged = new ArrayList<>();
        castRetargeted = true;
        try {
            flagNamed(cast, holds, flagged);
            List<SpellAbility> choice = super.chooseSpellAbilityToPlay();
            if (choice != null && !choice.isEmpty() && (isNamed(choice.get(0), cast) || isHeld(choice.get(0), holds))) {
                unflag(flagged);
                super.chooseSpellAbilityToPlay();       // result unused: this call only resets Forge's skip memory
                flagNamed(cast, holds, flagged);
                choice = super.chooseSpellAbilityToPlay();
                if (choice != null && !choice.isEmpty() && (isNamed(choice.get(0), cast) || isHeld(choice.get(0), holds))) {
                    count("cast_forge_stuck", 1);
                    trace("Forge kept choosing a named play (" + choice.get(0).getHostCard().getName() + "); the rules below decide");
                    return null;
                }
            }
            return choice == null || choice.isEmpty() ? null : choice.get(0);
        } finally {
            unflag(flagged);
        }
    }

    /**
     * For a {@code forge} rule with {@code "wait": "main2"}, in the first main phase: a permanent card no rule names
     * or holds that Forge's AI keeps for its second main phase and that can be paid for now, or null. Forge's AI
     * casts most permanents after combat; asked in the first main phase it declines them, and unless the rules below
     * wait, they spend the mana before Forge is asked again. Forge's general answer ({@code AiController.canPlaySa})
     * says only that the AI will not play the card; the reason is the answer of the card's own AI class, which is
     * {@link AiPlayDecision#MissingPhaseRestrictions} for a permanent it wants in another phase and something else
     * for a card it does not want at all (snapshot 2026-11-10: every permanent kept for after combat read so, and
     * a wipe with nothing to destroy read {@code CantPlayAi}).
     */
    private Card forgeKeepsForMain2(Playbook.Cast cast) {
        List<Playbook.CastRule> holds = holdsInForce(cast);
        for (Card c : castable()) {
            if (c.isLand() || !c.isPermanent() || castWaitDeclined.contains(c.getId())) {
                continue;                               // an instant Forge keeps is kept for another turn, not for main 2
            }
            List<SpellAbility> spells = new ArrayList<>();
            for (SpellAbility sa : c.getAllPossibleAbilities(player, true)) {
                if (sa.isSpell() && sa.getAlternativeCost() == null) {
                    spells.add(sa);
                }
            }
            if (spells.isEmpty()) {
                continue;
            }
            for (SpellAbility sa : ComputerUtilAbility.getOriginalAndAltCostAbilities(spells, player)) {
                if (!sa.isSpell() || sa.getAlternativeCost() != null || isNamed(sa, cast) || isHeld(sa, holds)) {
                    continue;
                }
                sa.setActivatingPlayer(player);
                if (!sa.canPlay()) {
                    continue;
                }
                castRetargeted = true;                  // Forge's logic may choose targets while it judges the spell
                AiPlayDecision api;
                try {
                    api = SpellApiToAi.Converter.get(sa).canPlayWithSubs(player, sa).decision();
                } catch (RuntimeException e) {
                    continue;
                }
                if ((api == AiPlayDecision.MissingPhaseRestrictions || api == AiPlayDecision.WaitForMain2)
                        && ComputerUtilCost.canPayCost(sa, player, false)) {
                    return c;
                }
            }
        }
        return null;
    }

    /** Whether the card is still in hand (or the command zone) with a spell that is legal and can be paid for now. */
    private boolean stillPayable(int cardId) {
        for (Card c : castable()) {
            if (c.getId() != cardId) {
                continue;
            }
            for (SpellAbility sa : c.getAllPossibleAbilities(player, true)) {
                if (sa.isSpell() && sa.getAlternativeCost() == null) {
                    sa.setActivatingPlayer(player);
                    if (sa.canPlay() && ComputerUtilCost.canPayCost(sa, player, false)) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    /** The cards a rule can cast: the hand and the commanders in the command zone. */
    private List<Card> castable() {
        List<Card> cards = new ArrayList<>();
        for (Card c : player.getCardsIn(ZoneType.Hand)) {
            cards.add(c);
        }
        for (Card c : player.getCardsIn(ZoneType.Command)) {
            if (c.isCommander()) {
                cards.add(c);
            }
        }
        return cards;
    }

    /** The first play rule that has something to cast right now, or null; with {@code beforeLandOnly}, among the rules marked before_land. */
    private SpellAbility castByRule(Playbook.Cast cast, PhaseHandler ph, boolean beforeLandOnly) {
        int turn = ph.getTurn();
        int spells = player.getSpellsCastThisTurn();
        if (turn != castTurn) {
            castTurn = turn;
            castPlays = 0;
            castTried.clear();
            castActivations.clear();
            castByName.clear();
            castPendingId = -1;
        }
        if (castPendingId >= 0) {
            // The last pick should have left its zone and counted as a spell; if neither happened the cast failed.
            if (spells <= castPendingSpells && stillCastable(castPendingId)) {
                castTried.add(castPendingId);
                count("cast_failed", 1);
                trace("the last cast did not happen (card " + castPendingId + "); not trying it again this turn");
            }
            castPendingId = -1;
        }
        if (castPlays >= cast.maxPerTurn) {
            count("cast_turn_limit", 1);
            return null;
        }
        List<Card> cards = castable();
        for (Playbook.CastRule rule : cast.rules) {
            if (rule.isHold() || (beforeLandOnly && !rule.beforeLand) || !phaseFits(rule, ph) || !allHold(rule.when)) {
                continue;
            }
            if (rule.isForge()) {
                // Forge's own pick among the plays no rule names, at this place in the order instead of after every rule.
                SpellAbility sa = forgeUnnamed(cast);
                if (sa != null) {
                    castPlays++;
                    count("cast_rule_" + rule.index, 1);
                    count("cast_forge_unnamed", 1);
                    if (ph.is(PhaseType.MAIN2)) {
                        count("cast_forge_unnamed_main2", 1);
                    }
                    trace("rule " + rule.index + " leaves the choice to Forge among the unnamed: " + sa.getHostCard().getName() + ": " + sa);
                    return sa;
                }
                if (rule.waitMain2 && !beforeLandOnly && ph.is(PhaseType.MAIN1)) {
                    Card kept = forgeKeepsForMain2(cast);
                    if (kept != null) {
                        count("cast_forge_wait", 1);
                        trace("rule " + rule.index + ": Forge keeps " + kept.getName() + " for its second main phase; the rules below wait for it");
                        castWaitCard = kept.getId();
                        castWaitTurn = turn;
                        castWaiting = true;
                        return null;
                    }
                } else if (rule.waitMain2 && castWaitCard >= 0 && castWaitTurn == turn && ph.is(PhaseType.MAIN2)) {
                    // Forge has made its choices after combat. A card the rules waited for that it could still pay for
                    // and did not cast is one it does not want after all: the rules do not wait for it again.
                    if (stillPayable(castWaitCard)) {
                        castWaitDeclined.add(castWaitCard);
                        count("cast_forge_wait_unused", 1);
                        trace("rule " + rule.index + ": Forge did not cast the card the rules waited for (card " + castWaitCard + "); not waiting for it again");
                    }
                    castWaitCard = -1;
                }
                continue;
            }
            Card target = null;
            if (rule.target != null) {
                target = controlled(rule.target);
                if (target == null) {
                    continue;
                }
            }
            for (String name : rule.cards) {
                if (rule.isActivate()) {
                    for (Card c : player.getCardsIn(ZoneType.Battlefield)) {
                        if (!c.getName().equals(name) || castActivations.getOrDefault(c.getId(), 0) >= rule.times) {
                            continue;
                        }
                        castAimed = null;
                        SpellAbility sa = activatable(c, rule.ability, target, rule);
                        if (sa != null) {
                            castActivations.merge(c.getId(), 1, Integer::sum);
                            castPlays++;
                            count("cast_rule_" + rule.index, 1);
                            countAim(rule);
                            trace("rule " + rule.index + " activates " + name + ": " + sa + aimText());
                            return sa;
                        }
                    }
                    continue;
                }
                String playKey = rule.index + ":" + name;
                if (castByName.getOrDefault(playKey, 0) >= rule.times) {
                    continue;                           // a card that comes back to hand (buyback) is not cast without end
                }
                for (Card c : cards) {
                    if (!c.getName().equals(name) || castTried.contains(c.getId())) {
                        continue;
                    }
                    castAimed = null;
                    SpellAbility sa = playable(c, target, rule);
                    if (sa != null) {
                        castPendingId = c.getId();
                        castPendingSpells = spells;
                        castByName.merge(playKey, 1, Integer::sum);
                        castPlays++;
                        count("cast_rule_" + rule.index, 1);
                        countAim(rule);
                        trace("rule " + rule.index + " casts " + name + (target == null ? "" : " at " + target.getName()) + aimText());
                        return sa;
                    }
                }
            }
        }
        return null;
    }

    /** An aimed rule fired: counted, and whether the permanent it chose belongs to the opponent that looks most dangerous. */
    private void countAim(Playbook.CastRule rule) {
        if (rule.aim == null || castAimed == null) {
            return;
        }
        count("cast_aim", 1);
        Player owner = castAimed.getController();
        boolean top = true;
        for (Player opp : player.getOpponents()) {
            top &= opp == owner || danger(opp) <= danger(owner);
        }
        count(top ? "cast_aim_most_dangerous" : "cast_aim_next", 1);
    }

    private String aimText() {
        return castAimed == null ? "" : " aimed at " + castAimed.getName() + " of " + castAimed.getController().getName()
                + " (danger " + danger(castAimed.getController()) + ")";
    }

    private boolean stillCastable(int cardId) {
        for (Card c : castable()) {
            if (c.getId() == cardId) {
                return true;
            }
        }
        return false;
    }

    private static boolean phaseFits(Playbook.CastRule rule, PhaseHandler ph) {
        return "main".equals(rule.phase) || ("main1".equals(rule.phase) ? ph.is(PhaseType.MAIN1) : ph.is(PhaseType.MAIN2));
    }

    /**
     * A way to cast the card now, or null: legal, affordable and aimed. With a target the spell is pointed at it and
     * nothing else; without one, a spell that needs no choices is cast as it is, and one that needs targets or an X
     * is cast only if Forge's own logic will play it, since that logic is what chooses them.
     */
    private SpellAbility playable(Card card, Card target, Playbook.CastRule rule) {
        List<SpellAbility> spells = new ArrayList<>();
        for (SpellAbility sa : card.getAllPossibleAbilities(player, true)) {
            if (sa.isSpell() && sa.getAlternativeCost() == null) {
                spells.add(sa);
            }
        }
        if (spells.isEmpty()) {
            return null;
        }
        for (SpellAbility sa : ComputerUtilAbility.getOriginalAndAltCostAbilities(spells, player)) {
            if (sa.isSpell() && sa.getAlternativeCost() == null && ready(sa, target, rule)) {
                return sa;
            }
        }
        return null;
    }

    /** An activated ability of the permanent that can be used now (mana abilities are Forge's to tap), or null. */
    private SpellAbility activatable(Card card, String text, Card target, Playbook.CastRule rule) {
        String want = text == null ? null : text.toLowerCase();
        for (SpellAbility sa : card.getAllPossibleAbilities(player, true)) {
            if (!sa.isActivatedAbility() || sa.isManaAbility()) {
                continue;
            }
            String d = sa.getDescription();
            if (want != null && (d == null || !d.toLowerCase().contains(want))) {
                continue;
            }
            if (ready(sa, target, rule)) {
                return sa;
            }
        }
        return null;
    }

    /** Legal now, aimed (by the rule's target, or by Forge's own logic when the ability needs choices) and affordable. */
    private boolean ready(SpellAbility sa, Card target, Playbook.CastRule rule) {
        sa.setActivatingPlayer(player);
        if (!sa.canPlay()) {
            return false;
        }
        SpellAbility aimed = null;
        SpellAbility paidX = null;
        if (target == null && rule.aim != null) {
            // The rule aims at an opponent's permanent: the one part of the spell that takes a target says which are legal.
            SpellAbility part = null;
            int parts = 0;
            for (SpellAbility p = sa; p != null; p = p.getSubAbility()) {
                if (p.usesTargeting()) {
                    part = p;
                    parts++;
                }
            }
            if (parts != 1) {
                return false;
            }
            part.setActivatingPlayer(player);
            castRetargeted = true;
            part.resetTargets();
            target = aimTarget(part, rule);
            if (target == null) {
                count("cast_aim_none", 1);
                return false;
            }
            castAimed = target;
        }
        if (target != null) {
            // An Equip aimed at the creature that already wears the equipment attaches nothing and costs the mana
            // (Limit Break, 2026-11-12: 308 of 429 firings of its equip rule re-attached what Cloud already wore).
            Card host = sa.getHostCard();
            if (sa.isEquip() && host != null && host.isAttachedToEntity(target)) {
                return false;
            }
            // The rule aims at one permanent, so the spell must have exactly one part that takes a target (the spell
            // itself, or the sub-ability that does: Fists of Flame draws first and pumps its target second).
            int parts = 0;
            for (SpellAbility part = sa; part != null; part = part.getSubAbility()) {
                if (part.usesTargeting()) {
                    aimed = part;
                    parts++;
                }
            }
            if (parts != 1) {
                return false;
            }
            aimed.setActivatingPlayer(player);
            castRetargeted = true;
            aimed.resetTargets();
            if (!aimed.canTarget(target)) {
                return false;
            }
            aimed.getTargets().add(target);
            if (!aimed.isTargetNumberValid()) {
                aimed.resetTargets();
                return false;
            }
        }
        boolean manaX = sa.costHasManaX();
        boolean lifeX = !manaX && paysXLife(sa);
        boolean hasX = manaX || lifeX;
        if (hasX && rule.x >= 0 && (target != null || (!sa.usesTargeting() && !subTargets(sa)))) {
            // The rule names X: all the mana the rest of the cost leaves (Forge's own count) or, for an X paid in life,
            // the life above what the rule keeps; capped by the rule's number or set by its metric.
            castRetargeted = true;
            SpellAbility root = sa.getRootAbility();
            int want = rule.xMetric == null ? rule.x : metric(rule.xMetric);
            int most = manaX ? ComputerUtilCost.setMaxXValue(sa, player, false) : player.getLife() - rule.xKeepLife;
            int x = Math.min(most, want);
            if (x < Math.max(rule.xMin, 0)) {
                root.setXManaCostPaid(null);
                if (aimed != null) {
                    aimed.resetTargets();
                }
                return false;
            }
            root.setXManaCostPaid(x);
            paidX = root;
        } else if (target == null && (sa.usesTargeting() || subTargets(sa) || hasX)) {
            castRetargeted = true;                      // Forge's logic chooses the targets (and X) afresh
            if (getAi().canPlaySa(sa) != AiPlayDecision.WillPlay) {
                count("cast_forge_declined", 1);
                return false;
            }
        } else if (hasX) {
            aimed.resetTargets();                       // aimed by the rule, but X is nobody's choice: not cast for nothing
            return false;
        }
        if (!ComputerUtilCost.canPayCost(sa, player, false)) {
            if (aimed != null) {
                aimed.resetTargets();
            }
            if (paidX != null) {
                paidX.setXManaCostPaid(null);
            }
            return false;
        }
        return true;
    }

    /** An X in the cost that is paid in life (Toxic Deluge), which the card's script reads back as the X of its effect. */
    private static boolean paysXLife(SpellAbility sa) {
        if (sa.getPayCosts() == null || !sa.getPayCosts().hasXInAnyCostPart()) {
            return false;
        }
        for (CostPart part : sa.getPayCosts().getCostParts()) {
            if (part instanceof CostPayLife && "X".equals(part.getAmount())) {
                return true;
            }
        }
        return false;
    }

    /** How dangerous an opponent looks to this seat: the playbook's weights on its life and its nonland permanents. */
    private int danger(Player opp) {
        int permanents = 0;
        for (Card c : opp.getCardsIn(ZoneType.Battlefield)) {
            permanents += c.isLand() ? 0 : 1;
        }
        int life = playbook.cast == null ? 1 : playbook.cast.dangerLife;
        int perms = playbook.cast == null ? 2 : playbook.cast.dangerPermanents;
        return life * opp.getLife() + perms * permanents;
    }

    private static boolean aimKind(Card c, String kind) {
        switch (kind) {
            case "creature": return c.isCreature();
            case "noncreature": return !c.isCreature();
            case "artifact": return c.isArtifact();
            case "enchantment": return c.isEnchantment();
            case "planeswalker": return c.isPlaneswalker();
            default: return true;
        }
    }

    /**
     * The opponent's permanent an aimed rule hits: of the rule's kind, a legal target of the spell, worth at least the
     * rule's floor (mana value, or a creature's power when that is more). With {@code aim_at danger} the opponents are
     * taken in the order of how dangerous they look and the first that has such a permanent gives its best one, by
     * Forge's own rating of cards; with {@code any} the best one on any opponent's side. Null when there is none.
     */
    private Card aimTarget(SpellAbility part, Playbook.CastRule rule) {
        List<Player> opps = new ArrayList<>(player.getOpponents());
        boolean byDanger = "danger".equals(rule.aimAt);
        if (byDanger) {
            opps.sort((a, b) -> Integer.compare(danger(b), danger(a)));
        }
        boolean destroys = part.getApi() == ApiType.Destroy;
        List<Card> pool = new ArrayList<>();
        for (Player opp : opps) {
            List<Card> theirs = new ArrayList<>();
            for (Card c : opp.getCardsIn(ZoneType.Battlefield)) {
                if (c.isLand() || !aimKind(c, rule.aim)) {
                    continue;
                }
                int worth = Math.max(c.getCMC(), c.isCreature() ? c.getNetPower() : 0);
                if (worth < rule.aimMin || (destroys && c.hasKeyword(Keyword.INDESTRUCTIBLE)) || !part.canTarget(c)) {
                    continue;
                }
                theirs.add(c);
            }
            if (byDanger && !theirs.isEmpty()) {
                return ComputerUtilCard.getBestAI(theirs);
            }
            pool.addAll(theirs);
        }
        return pool.isEmpty() ? null : ComputerUtilCard.getBestAI(pool);
    }

    private static boolean subTargets(SpellAbility sa) {
        for (SpellAbility sub = sa.getSubAbility(); sub != null; sub = sub.getSubAbility()) {
            if (sub.usesTargeting()) {
                return true;
            }
        }
        return false;
    }

    private Card controlled(String name) {
        for (Card c : player.getCardsIn(ZoneType.Battlefield)) {
            if (c.getName().equals(name)) {
                return c;
            }
        }
        return null;
    }

    private boolean allHold(List<Playbook.Cond> conds) {
        for (Playbook.Cond c : conds) {
            if (!holds(c)) {
                return false;
            }
        }
        return true;
    }

    private boolean holds(Playbook.Cond c) {
        if (c.card != null) {
            return (controlled(c.card) != null) != c.negate;
        }
        return c.other == null ? c.compare(metric(c.metric)) : c.compare(metric(c.metric), metric(c.other));
    }

    /** Both sides of the game as numbers (playbook/README.md lists them). */
    private int metric(String name) {
        if (name.startsWith("hand:")) {
            List<String> group = playbook.cast.groups.get(name.substring(5));
            int n = 0;
            for (Card c : player.getCardsIn(ZoneType.Hand)) {
                n += group != null && group.contains(c.getName()) ? 1 : 0;
            }
            return n;
        }
        if (name.startsWith("type:")) {
            String type = name.substring(5).trim();
            int n = 0;
            for (Card c : player.getCreaturesInPlay()) {
                if (c.getType().hasCreatureType(type)) {
                    n++;
                }
            }
            return n;
        }
        switch (name) {
            case "creatures":
                return player.getCreaturesInPlay().size();
            case "tokens": {
                int n = 0;
                for (Card c : player.getCreaturesInPlay()) {
                    n += c.isToken() ? 1 : 0;
                }
                return n;
            }
            case "attackers": {
                int n = 0;
                for (Card c : player.getCreaturesInPlay()) {
                    n += c.isUntapped() && !c.isSick() ? 1 : 0;
                }
                return n;
            }
            case "lands":
                return player.getLandsInPlay().size();
            case "hand":
                return player.getCardsIn(ZoneType.Hand).size();
            case "library":
                return player.getCardsIn(ZoneType.Library).size();
            case "storm":
                return player.getSpellsCastThisTurn();
            case "drawn":
                return player.getNumDrawnThisTurn();
            case "turn":
                return player.getTurn();
            case "life":
                return player.getLife();
            case "mana":
                return ComputerUtilMana.getAvailableManaEstimate(player);
            case "opponents":
                return player.getOpponents().size();
            case "main": {                              // 1 in our first main phase, 2 in our second, 0 at any other time
                PhaseHandler ph = getGame().getPhaseHandler();
                if (!ph.isPlayerTurn(player)) {
                    return 0;
                }
                return ph.is(PhaseType.MAIN1) ? 1 : ph.is(PhaseType.MAIN2) ? 2 : 0;
            }
            case "power":
                return boardPower(player);
            case "opp_creatures": {                     // the most creatures any one opponent controls
                int n = 0;
                for (Player opp : player.getOpponents()) {
                    n = Math.max(n, opp.getCreaturesInPlay().size());
                }
                return n;
            }
            case "opp_power": {                         // the most power any one opponent has on the battlefield
                int n = 0;
                for (Player opp : player.getOpponents()) {
                    n = Math.max(n, boardPower(opp));
                }
                return n;
            }
            case "opp_life": {                          // the highest life total among the opponents
                int n = 0;
                for (Player opp : player.getOpponents()) {
                    n = Math.max(n, opp.getLife());
                }
                return n;
            }
            case "opp_toughness": {                     // the largest toughness among the opponents' creatures
                int n = 0;
                for (Player opp : player.getOpponents()) {
                    for (Card c : opp.getCreaturesInPlay()) {
                        n = Math.max(n, c.getNetToughness());
                    }
                }
                return n;
            }
            case "threat": {                            // the most damage one opponent could attack us with next turn
                int n = 0;
                for (int p : biggestThreat(player)) {
                    n += p;
                }
                return n;
            }
            default:
                throw new IllegalArgumentException("unknown playbook metric " + name);
        }
    }

    // ------------------------------------------------------------------ triggers

    /**
     * The seat's triggered abilities go on the stack here, and for Forge's AI this is where their targets are
     * chosen ({@code prepareSingleSa}, then {@code ComputerUtil.playStack}). With {@code targets.triggers} set
     * the same two steps are taken for the seat's own plain triggers with the aim in between; a copied spell, a
     * charm, a trigger another player aims and anything a teammate plays go through Forge's method unchanged,
     * one at a time and in the order Forge gave them.
     */
    @Override
    public void orderAndPlaySimultaneousSa(List<SpellAbility> activePlayerSAs) {
        if (playbook == null || playbook.targets == null || !playbook.targets.triggersByDanger) {
            super.orderAndPlaySimultaneousSa(activePlayerSAs);
            return;
        }
        for (SpellAbility sa : orderSimultaneousSa(activePlayerSAs)) {
            boolean plain = sa.getActivatingPlayer() == player && sa.isTrigger() && !sa.isCopied()
                    && sa.getApi() != ApiType.Charm && !sa.hasParam("TargetingPlayer");
            if (!plain) {
                super.orderAndPlaySimultaneousSa(Collections.singletonList(sa));
                continue;
            }
            if (getAi().doTrigger(sa, true)) {
                try {
                    aimTrigger(sa);
                } catch (RuntimeException e) {
                    count("trigger_aim_errors", 1);
                }
                ComputerUtil.playStack(sa, player, getGame());
            }
        }
    }

    /**
     * Aim a removal trigger by the judgement of danger. Each part of the trigger that has exactly one target, a
     * permanent an opponent controls, and that destroys it, exiles it or returns it to hand or library: when
     * another opponent looks more dangerous than that one by {@code targets.margin} or more, those are asked in turn for
     * a permanent of the same kind (creature or not) the part can target, not indestructible if it is to be
     * destroyed, and worth at least as much as Forge's choice or at least {@code targets.min}; the best of the
     * first opponent that has one becomes the target. Otherwise Forge's target stands.
     */
    private void aimTrigger(SpellAbility sa) {
        for (SpellAbility part = sa; part != null; part = part.getSubAbility()) {
            if (!part.usesTargeting() || part.getTargets().size() != 1 || !removesOne(part)) {
                continue;
            }
            Card now = part.getTargets().getFirstTargetedCard();
            if (now == null || !now.isInPlay() || now.getController() == player || !player.isOpponentOf(now.getController())) {
                continue;
            }
            count("trigger_aim_seen", 1);
            Player owner = now.getController();
            List<Player> opps = new ArrayList<>();
            for (Player opp : player.getOpponents()) {
                if (!opp.hasLost() && danger(opp) >= danger(owner) + Math.max(1, playbook.targets.margin)) {
                    opps.add(opp);
                }
            }
            if (opps.isEmpty()) {
                count("trigger_aim_already", 1);        // Forge aimed at the most dangerous opponent, or at one that looks nearly as dangerous
                continue;
            }
            opps.sort((x, y) -> Integer.compare(danger(y), danger(x)));
            boolean destroys = part.getApi() == ApiType.Destroy;
            int floor = Math.min(worth(now), playbook.targets.min);
            Card best = null;
            for (Player opp : opps) {
                List<Card> theirs = new ArrayList<>();
                for (Card c : opp.getCardsIn(ZoneType.Battlefield)) {
                    if (c.isLand() || c.isCreature() != now.isCreature() || worth(c) < floor
                            || (destroys && c.hasKeyword(Keyword.INDESTRUCTIBLE)) || !part.canTarget(c)) {
                        continue;
                    }
                    theirs.add(c);
                }
                if (!theirs.isEmpty()) {
                    best = ComputerUtilCard.getBestAI(theirs);
                    break;
                }
            }
            if (best == null) {
                count("trigger_aim_kept", 1);           // nothing worth it on a more dangerous opponent's side
                continue;
            }
            part.resetTargets();
            part.getTargets().add(best);
            count("trigger_aim_moved", 1);
            trace("aims the trigger of " + sa.getHostCard().getName() + " at " + best.getName() + " of " + best.getController().getName()
                    + " (danger " + danger(best.getController()) + ") instead of " + now.getName() + " of " + owner.getName() + " (" + danger(owner) + ")");
        }
    }

    /** Destroys its target, or moves it from the battlefield to exile, a hand, a library or a graveyard. */
    private static boolean removesOne(SpellAbility part) {
        ApiType api = part.getApi();
        if (api == ApiType.Destroy) {
            return true;
        }
        if (api != ApiType.ChangeZone) {
            return false;
        }
        String to = part.hasParam("Destination") ? part.getParam("Destination") : "";
        return "Battlefield".equals(part.hasParam("Origin") ? part.getParam("Origin") : "") && !to.isEmpty() && !"Battlefield".equals(to);
    }

    private static int worth(Card c) {
        return Math.max(c.getCMC(), c.isCreature() ? c.getNetPower() : 0);
    }

    /**
     * An optional trigger of ours: the first trigger rule that names the card and whose conditions hold answers; with
     * none, Forge's AI does. Forge asks at resolution, after the trigger's targets are chosen, and pays the cost of an
     * accepted trigger itself (it sacrifices its lowest-rated creature, for one), so a rule's conditions should make
     * sure the price is one the deck wants to pay.
     */
    @Override
    public boolean confirmTrigger(WrappedAbility wrapper) {
        Playbook.TriggerRule rule = null;
        try {
            rule = triggerRule(wrapper);
        } catch (RuntimeException e) {
            count("trigger_errors", 1);
            System.err.println("[vibefish] playbook trigger rule failed, Forge answers: " + e);
        }
        if (rule == null) {
            boolean forge = super.confirmTrigger(wrapper);
            if (TRACE && !forge && !wrapper.isMandatory() && wrapper.getHostCard() != null) {
                trace("Forge declines the optional trigger of " + wrapper.getHostCard().getName());    // a candidate for a trigger rule
            }
            return forge;
        }
        count("trigger_decisions", 1);
        count(rule.accept ? "trigger_accepted" : "trigger_declined", 1);
        count("trigger_rule_" + rule.index, 1);
        trace("trigger rule " + rule.index + (rule.accept ? " accepts " : " declines ") + wrapper.getHostCard().getName());
        return rule.accept;
    }

    private Playbook.TriggerRule triggerRule(WrappedAbility wrapper) {
        if (playbook == null || playbook.triggers.isEmpty() || wrapper.getHostCard() == null || wrapper.isMandatory()) {
            return null;
        }
        String name = wrapper.getHostCard().getName();
        String text = null;
        for (Playbook.TriggerRule rule : playbook.triggers) {
            if (!rule.cards.contains(name)) {
                continue;
            }
            if (rule.ability != null) {
                if (text == null) {
                    text = String.valueOf(wrapper.getStackDescription()) + " " + String.valueOf(wrapper.getDescription());
                    text = text.toLowerCase(java.util.Locale.ROOT);
                }
                if (!text.contains(rule.ability.toLowerCase(java.util.Locale.ROOT))) {
                    continue;
                }
            }
            if (allHold(rule.when)) {
                return rule;
            }
        }
        return null;
    }

    // ------------------------------------------------------------------ mulligan

    @Override
    public boolean mulliganKeepHand(Player firstPlayer, int cardsToReturn) {
        Playbook.Mulligan rule = playbook == null ? null : playbook.mulligan;
        if (rule == null) {
            return super.mulliganKeepHand(firstPlayer, cardsToReturn);
        }
        count("mulligan_decisions", 1);
        if (cardsToReturn >= rule.maxMulligans) {
            return true;
        }
        int lands = 0;
        for (Card c : player.getCardsIn(ZoneType.Hand)) {
            if (c.isLand()) {
                lands++;
            }
        }
        boolean keep = lands >= rule.minLands && lands <= rule.maxLands;
        if (!keep) {
            count("mulligans_taken", 1);
        }
        return keep;
    }
}
