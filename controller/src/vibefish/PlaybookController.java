package vibefish;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import forge.LobbyPlayer;
import forge.ai.AiPlayDecision;
import forge.ai.ComputerUtilAbility;
import forge.ai.ComputerUtilCard;
import forge.ai.ComputerUtilCombat;
import forge.ai.ComputerUtilCost;
import forge.ai.ComputerUtilMana;
import forge.ai.PlayerControllerAi;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.card.CardCollection;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.cost.Cost;
import forge.game.phase.PhaseHandler;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.spellability.SpellAbility;
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

    public static synchronized void resetStats() {
        STATS.clear();
    }

    private static synchronized void count(String key, int by) {
        STATS.merge(key, by, Integer::sum);
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
        try {
            if ("pressure".equals(policy.policy) ? pressure(attacker, combat, policy) : goWide(attacker, combat, policy)) {
                count("attack_policy", 1);
                return;
            }
        } catch (RuntimeException e) {
            count("attack_errors", 1);
            for (Card c : new ArrayList<>(combat.getAttackers())) {
                combat.removeFromCombat(c);
            }
        }
        count("attack_fallback", 1);
        super.declareAttackers(attacker, combat);
    }

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
            forge = forgeChoice(cast);                  // the land drop first: every rule below wants the mana
            asked = true;
            if (forge != null && !forge.isEmpty() && forge.get(0).isLandAbility()) {
                return forge;
            }
        }
        count("cast_decisions", 1);
        SpellAbility pick = null;
        castRetargeted = false;
        try {
            pick = castByRule(cast, ph);
        } catch (RuntimeException e) {
            count("cast_errors", 1);
        }
        if (pick != null) {
            count("cast_policy", 1);
            List<SpellAbility> one = new ArrayList<>();
            one.add(pick);
            return one;
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

    /** The first play rule that has something to cast right now, or null. */
    private SpellAbility castByRule(Playbook.Cast cast, PhaseHandler ph) {
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
            if (rule.isHold() || !phaseFits(rule, ph) || !allHold(rule.when)) {
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
                        SpellAbility sa = activatable(c, rule.ability, target);
                        if (sa != null) {
                            castActivations.merge(c.getId(), 1, Integer::sum);
                            castPlays++;
                            count("cast_rule_" + rule.index, 1);
                            trace("rule " + rule.index + " activates " + name + ": " + sa);
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
                    SpellAbility sa = playable(c, target);
                    if (sa != null) {
                        castPendingId = c.getId();
                        castPendingSpells = spells;
                        castByName.merge(playKey, 1, Integer::sum);
                        castPlays++;
                        count("cast_rule_" + rule.index, 1);
                        trace("rule " + rule.index + " casts " + name + (target == null ? "" : " at " + target.getName()));
                        return sa;
                    }
                }
            }
        }
        return null;
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
    private SpellAbility playable(Card card, Card target) {
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
            if (sa.isSpell() && sa.getAlternativeCost() == null && ready(sa, target)) {
                return sa;
            }
        }
        return null;
    }

    /** An activated ability of the permanent that can be used now (mana abilities are Forge's to tap), or null. */
    private SpellAbility activatable(Card card, String text, Card target) {
        String want = text == null ? null : text.toLowerCase();
        for (SpellAbility sa : card.getAllPossibleAbilities(player, true)) {
            if (!sa.isActivatedAbility() || sa.isManaAbility()) {
                continue;
            }
            String d = sa.getDescription();
            if (want != null && (d == null || !d.toLowerCase().contains(want))) {
                continue;
            }
            if (ready(sa, target)) {
                return sa;
            }
        }
        return null;
    }

    /** Legal now, aimed (by the rule's target, or by Forge's own logic when the ability needs choices) and affordable. */
    private boolean ready(SpellAbility sa, Card target) {
        sa.setActivatingPlayer(player);
        if (!sa.canPlay()) {
            return false;
        }
        SpellAbility aimed = null;
        if (target != null) {
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
        } else if (sa.usesTargeting() || subTargets(sa) || sa.costHasManaX()) {
            castRetargeted = true;                      // Forge's logic chooses the targets afresh
            if (getAi().canPlaySa(sa) != AiPlayDecision.WillPlay) {
                count("cast_forge_declined", 1);
                return false;
            }
        }
        if (!ComputerUtilCost.canPayCost(sa, player, false)) {
            if (aimed != null) {
                aimed.resetTargets();
            }
            return false;
        }
        return true;
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
