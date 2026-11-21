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
     * given a blocker if the ones already placed can be moved to make room, which finds the heaviest set.
     * A block counts as stopping all of an attacker's damage (trample is not credited to the attacker).
     * With a {@code defender} given, an attacker that one creature alone may not block (menace) counts as one
     * that cannot be stopped, and so does an attacker with trample, whose damage a block does not stop whole
     * (since 0.4.1): that is the reading for "could its blocks have saved it", where a block that was not
     * possible, or would not have been enough, must not be counted. Without one, such an attacker counts as
     * stoppable by a single blocker, which is the careful reading for "is this damage sure to get through". {@code untapped} asks the question
     * as if every blocker were untapped (what the defender's creatures could have done had they stayed home).
     */
    static int mostStopped(List<Card> attackers, List<Card> blockers, Player defender, boolean untapped) {
        List<Card> order = new ArrayList<>(attackers);
        order.sort((x, y) -> Integer.compare(hits(y), hits(x)));
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
        int stopped = 0;
        for (int i = 0; i < n; i++) {
            if (hits(order.get(i)) > 0 && place(i, can, heldBy, new boolean[blockers.size()])) {
                stopped += hits(order.get(i));
            }
        }
        return stopped;
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
