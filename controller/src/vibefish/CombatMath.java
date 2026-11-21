package vibefish;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import forge.game.Game;
import forge.game.card.Card;
import forge.game.combat.CombatUtil;
import forge.game.cost.Cost;
import forge.game.keyword.Keyword;
import forge.game.player.Player;

/**
 * The arithmetic of an attack that both the logger and a playbook's attack read: what is sure to get through.
 * Who may attack and block whom is Forge's ({@code CombatUtil}); this only counts.
 */
final class CombatMath {
    private CombatMath() {
    }

    /** The combat damage a creature would deal to a player's life: nothing for infect, never negative. */
    static int hits(Card c) {
        return c.hasKeyword(Keyword.INFECT) ? 0 : Math.max(0, c.getNetCombatDamage());
    }

    static int hits(List<Card> cards) {
        int n = 0;
        for (Card c : cards) {
            n += hits(c);
        }
        return n;
    }

    /** The attacker's creatures that may attack this opponent now without paying anything for it. */
    static List<Card> freeAttackers(Game game, Player attacker, Player defender) {
        List<Card> l = new ArrayList<>();
        for (Card c : attacker.getCreaturesInPlay()) {
            if (!CombatUtil.canAttack(c, defender)) {
                continue;
            }
            Cost cost = CombatUtil.getAttackCost(game, c, defender);
            if (cost == null || cost.isFree()) {
                l.add(c);
            }
        }
        return l;
    }

    /** The player's creatures that may block now. */
    static List<Card> ableBlockers(Player p) {
        List<Card> l = new ArrayList<>();
        for (Card c : p.getCreaturesInPlay()) {
            if (CombatUtil.canBlock(c)) {
                l.add(c);
            }
        }
        return l;
    }

    /**
     * The most damage a defender can stop by putting one blocker in front of an attacker, each blocker used once:
     * the heaviest set of attackers that can all be blocked at the same time. Who may block whom is Forge's
     * {@code CombatUtil.canBlock(attacker, blocker)}. Attackers are taken from the heaviest down and each is
     * given a blocker if the ones already placed can be moved to make room, which finds the heaviest set; with a
     * defender given, an attacking commander whose damage would be lethal by itself is taken before the rest
     * (since 0.4.3), so the set found stops every such attacker that can be stopped.
     * A block counts as stopping all of an attacker's damage (trample is not credited to the attacker).
     * With a {@code defender} given, an attacker that one creature alone may not block (menace) counts as one
     * that cannot be stopped, and so does an attacker with trample, whose damage a block does not stop whole
     * (since 0.4.1): that is the reading for "could its blocks have saved it", where a block that was not
     * possible, or would not have been enough, must not be counted. Without one, such an attacker counts as
     * stoppable by a single blocker, which is the careful reading for "is this damage sure to get through". {@code untapped} asks the question
     * as if every blocker were untapped (what the defender's creatures could have done had they stayed home).
     */
    static int mostStopped(List<Card> attackers, List<Card> blockers, Player defender, boolean untapped) {
        List<Card> order = ordered(attackers, defender, false);
        int[] heldBy = match(order, blockers, defender, untapped);
        int stopped = 0;
        for (int j = 0; j < heldBy.length; j++) {
            if (heldBy[j] >= 0) {
                stopped += hits(order.get(heldBy[j]));
            }
        }
        return stopped;
    }

    /**
     * A commander attacking this player whose damage would bring what it has dealt to the player to 21 or more:
     * unblocked it ends the player's game whatever the player's life is.
     */
    static boolean lethalCommander(Card a, Player defender) {
        return defender != null && a.isCommander() && defender.getCommanderDamage(a) + strikes(a) >= 21;
    }

    /**
     * Whether the best blocks leave a {@link #lethalCommander} unblocked: the matching stops those attackers
     * first, so this is true only when no set of blocks stops all of them.
     */
    static boolean commanderOpen(List<Card> attackers, List<Card> blockers, Player defender, boolean untapped) {
        List<Card> order = ordered(attackers, defender, false);
        int[] heldBy = match(order, blockers, defender, untapped);
        for (int i = 0; i < order.size(); i++) {
            if (!lethalCommander(order.get(i), defender)) {
                continue;
            }
            boolean held = false;
            for (int h : heldBy) {
                held |= h == i;
            }
            if (!held) {
                return true;
            }
        }
        return false;
    }

    /** The attackers a commander's lethal damage first (with a defender given), then the heaviest first. */
    private static List<Card> ordered(List<Card> attackers, Player defender, boolean twice) {
        List<Card> order = new ArrayList<>(attackers);
        order.sort((x, y) -> {
            int c = Boolean.compare(lethalCommander(y, defender), lethalCommander(x, defender));
            return c != 0 ? c : Integer.compare(twice ? strikes(y) : hits(y), twice ? strikes(x) : hits(x));
        });
        return order;
    }

    /** Each blocker's attacker (an index into {@code order}, or -1): attackers are given a blocker in the order they come. */
    private static int[] match(List<Card> order, List<Card> blockers, Player defender, boolean untapped) {
        int n = order.size();
        boolean[][] can = new boolean[n][blockers.size()];
        for (int i = 0; i < n; i++) {
            boolean single = defender == null
                    || (CombatUtil.canAttackerBeBlockedWithAmount(order.get(i), 1, defender) && !order.get(i).hasKeyword(Keyword.TRAMPLE));
            for (int j = 0; j < blockers.size(); j++) {
                can[i][j] = single && CombatUtil.canBlock(order.get(i), blockers.get(j), untapped);
            }
        }
        int[] heldBy = new int[blockers.size()];        // blocker -> the attacker it stands in front of
        Arrays.fill(heldBy, -1);
        for (int i = 0; i < n; i++) {
            if (hits(order.get(i)) > 0) {
                place(i, can, heldBy, new boolean[blockers.size()]);
            }
        }
        return heldBy;
    }

    private static boolean place(int attacker, boolean[][] can, int[] heldBy, boolean[] seen) {
        for (int j = 0; j < heldBy.length; j++) {
            if (can[attacker][j] && !seen[j]) {
                seen[j] = true;
                if (heldBy[j] < 0 || place(heldBy[j], can, heldBy, seen)) {
                    heldBy[j] = attacker;
                    return true;
                }
            }
        }
        return false;
    }

    /** What an unblocked attacker deals to a player's life in one combat: {@link #hits(Card)}, twice with double strike. */
    static int strikes(Card c) {
        return hits(c) * (c.hasKeyword(Keyword.DOUBLE_STRIKE) ? 2 : 1);
    }

    /**
     * Which blocker stops which attacker when as much damage as possible is to be stopped with one blocker an
     * attacker: the pairs of the heaviest set of these attackers that these blockers can block at the same time
     * (weights by {@link #strikes(Card)}), an attacking commander whose damage would be lethal by itself
     * ({@link #lethalCommander}) before any other. Blockers earlier in the list are tried first, so a caller that
     * lists its least valuable creatures first gets them used first. An attacker that one creature alone may
     * not block, or that tramples, is given no blocker: a block there would not be sure to stop it.
     */
    static java.util.Map<Card, Card> blocks(List<Card> attackers, List<Card> blockers, Player defender) {
        List<Card> order = ordered(attackers, defender, true);
        int[] heldBy = match(order, blockers, defender, false);
        java.util.Map<Card, Card> pairs = new java.util.LinkedHashMap<>();
        for (int i = 0; i < order.size(); i++) {        // a commander's lethal damage first, then the heaviest attacker
            for (int j = 0; j < heldBy.length; j++) {
                if (heldBy[j] == i) {
                    pairs.put(order.get(i), blockers.get(j));
                }
            }
        }
        return pairs;
    }

    /**
     * What a defender is left to take from these attackers under a blocking plan it could carry out: not the
     * least that is sure to be stopped ({@link #through}) and not the most ({@code mostStopped} with a defender),
     * but a plan. An attacker one creature may stop is stopped whole by one blocker; one that needs two blockers
     * by two; a trampler loses the toughness of each creature put in front of it (one damage a blocker if it has
     * deathtouch). Blockers are handed out one at a time to wherever a blocker prevents most, a commander whose
     * damage would be lethal by itself before anything else, and a blocker few attackers can be blocked by is
     * kept for those. The plan need not be the best one, so the damage returned can be more than the defender
     * would have to take, never less than a real set of blocks leaves. The second element is 1 when a commander
     * is left dealing lethal commander damage under the plan.
     */
    static int[] plannedLeft(List<Card> attackers, List<Card> blockers, Player defender) {
        int n = attackers.size();
        int[] left = new int[n];
        boolean[] single = new boolean[n];
        boolean[] dbl = new boolean[n];
        boolean[] trample = new boolean[n];
        for (int i = 0; i < n; i++) {
            Card a = attackers.get(i);
            left[i] = strikes(a);
            trample[i] = a.hasKeyword(Keyword.TRAMPLE);
            single[i] = CombatUtil.canAttackerBeBlockedWithAmount(a, 1, defender);
            dbl[i] = !single[i] && CombatUtil.canAttackerBeBlockedWithAmount(a, 2, defender);
        }
        List<Card> spare = new ArrayList<>(blockers);
        boolean[][] can = new boolean[n][blockers.size()];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < blockers.size(); j++) {
                can[i][j] = CombatUtil.canBlock(attackers.get(i), blockers.get(j), false);
            }
        }
        boolean[] used = new boolean[blockers.size()];
        while (true) {
            double bestRatio = 0;
            int bestA = -1;
            int b1 = -1;
            int b2 = -1;
            int bestGain = 0;
            for (int i = 0; i < n; i++) {
                if (left[i] <= 0) {
                    continue;
                }
                Card a = attackers.get(i);
                boolean lethalCmd = a.isCommander() && defender.getCommanderDamage(a) + left[i] >= 21;
                // the free blockers that may block it, the one fewest other attackers need first
                int first = -1;
                int second = -1;
                int firstUse = Integer.MAX_VALUE;
                int secondUse = Integer.MAX_VALUE;
                for (int j = 0; j < blockers.size(); j++) {
                    if (used[j] || !can[i][j]) {
                        continue;
                    }
                    int use = 0;
                    for (int k = 0; k < n; k++) {
                        use += k != i && left[k] > 0 && can[k][j] ? 1 : 0;
                    }
                    if (trample[i]) {                   // a trampler wants the toughest blocker, not the least needed
                        use = -soak(a, blockers.get(j));
                    }
                    if (use < firstUse) {
                        second = first;
                        secondUse = firstUse;
                        first = j;
                        firstUse = use;
                    } else if (use < secondUse) {
                        second = j;
                        secondUse = use;
                    }
                }
                if (first < 0) {
                    continue;
                }
                int gain;
                int cost;
                int two = -1;
                if (trample[i]) {
                    gain = Math.min(left[i], soak(a, blockers.get(first)));
                    cost = 1;
                } else if (single[i]) {
                    gain = left[i];
                    cost = 1;
                } else if (dbl[i] && second >= 0) {
                    gain = left[i];
                    cost = 2;
                    two = second;
                } else {
                    continue;
                }
                double ratio = (double) gain / cost + (lethalCmd ? 1e6 : 0);
                if (gain > 0 && ratio > bestRatio) {
                    bestRatio = ratio;
                    bestA = i;
                    b1 = first;
                    b2 = two;
                    bestGain = gain;
                }
            }
            if (bestA < 0) {
                break;
            }
            used[b1] = true;
            if (b2 >= 0) {
                used[b2] = true;
            }
            left[bestA] -= bestGain;
        }
        int total = 0;
        int cmd = 0;
        for (int i = 0; i < n; i++) {
            total += left[i];
            Card a = attackers.get(i);
            if (left[i] > 0 && a.isCommander() && defender.getCommanderDamage(a) + left[i] >= 21) {
                cmd = 1;
            }
        }
        return new int[] {total, cmd};
    }

    /** The trample damage a blocker takes off an attacker: its toughness less the damage on it, one if the attacker has deathtouch. */
    private static int soak(Card attacker, Card blocker) {
        if (attacker.hasKeyword(Keyword.DEATHTOUCH)) {
            return 1;
        }
        return Math.max(1, blocker.getNetToughness() - blocker.getDamage());
    }

    /** The creatures of {@code o} that may attack {@code target} on {@code o}'s next turn (Forge's own rule for it). */
    static List<Card> nextTurnAttackers(Player o, Player target) {
        List<Card> l = new ArrayList<>();
        for (Card c : o.getCreaturesInPlay()) {
            if (CombatUtil.canAttackNextTurn(c, target)) {
                l.add(c);
            }
        }
        return l;
    }

    /** A player's permanents that are not lands. */
    static int nonlandPermanents(Player p) {
        int n = 0;
        for (Card c : p.getCardsIn(forge.game.zone.ZoneType.Battlefield)) {
            n += c.isLand() ? 0 : 1;
        }
        return n;
    }

    /** The damage of these attackers that gets through whatever these blockers do (one blocker an attacker). */
    static int through(List<Card> attackers, List<Card> blockers) {
        return hits(attackers) - mostStopped(attackers, blockers, null, false);
    }
}
