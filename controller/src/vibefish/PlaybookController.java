package vibefish;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import forge.LobbyPlayer;
import forge.ai.PlayerControllerAi;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.card.CardCollection;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.cost.Cost;
import forge.game.player.Player;
import forge.game.zone.ZoneType;

/**
 * Forge's AI controller with a deck's playbook on top (Phase 4). Only the decisions the playbook covers are taken
 * here; everything else, and every case the policy declines, is Forge's own AI. One instance per seat; Forge itself
 * is untouched (public hooks only, DESIGN.md §3.1).
 */
public class PlaybookController extends PlayerControllerAi {

    /** Counters for the game being played, read into run.json by the harness. */
    public static final Map<String, Integer> STATS = new LinkedHashMap<>();

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
        if (policy == null || !"go_wide".equals(policy.policy) || attacker != player) {
            super.declareAttackers(attacker, combat);
            return;
        }
        count("attack_decisions", 1);
        try {
            if (goWide(attacker, combat, policy)) {
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
        for (Card c : going) {
            combat.addAttacker(c, defender);
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
            int score = "weakest_board".equals(policy.target) ? untappedCreatures(opp) * 100 + opp.getLife() : opp.getLife() * 100 + untappedCreatures(opp);
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
