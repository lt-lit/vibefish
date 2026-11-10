package vibefish;

import java.io.IOException;
import java.io.Writer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.common.collect.Multimap;
import com.google.common.eventbus.Subscribe;
import com.google.gson.Gson;

import forge.game.Game;
import forge.game.GameEndReason;
import forge.game.GameEntityView;
import forge.game.card.Card;
import forge.game.card.CardView;
import forge.game.event.GameEvent;
import forge.game.event.GameEventAttackersDeclared;
import forge.game.event.GameEventBlockersDeclared;
import forge.game.event.GameEventCardChangeZone;
import forge.game.event.GameEventGameOutcome;
import forge.game.event.GameEventGameStarted;
import forge.game.event.GameEventLandPlayed;
import forge.game.event.GameEventMulligan;
import forge.game.event.GameEventPlayerDamaged;
import forge.game.event.GameEventPlayerLivesChanged;
import forge.game.event.GameEventPlayerPoisoned;
import forge.game.event.GameEventSpellAbilityCast;
import forge.game.event.GameEventSpellResolved;
import forge.game.event.GameEventTurnBegan;
import forge.game.player.Player;
import forge.game.player.PlayerOutcome;
import forge.game.player.PlayerView;
import forge.game.spellability.SpellAbilityView;
import forge.game.spellability.StackItemView;
import forge.game.zone.ZoneType;
import forge.game.zone.ZoneView;

/**
 * Subscribes to a Forge game's event bus and writes one JSON object per line.
 *
 * Every line has "e" (event type) and "t" (Forge's global turn number, 0 before the first turn).
 * Seats are indices into the deck list the harness was given. At the start of every turn a
 * snapshot of all players (life, hand, lands, zone sizes, commanders in the command zone) is
 * written, read straight from the live game, so the rollup never has to reconstruct state.
 *
 * Also enforces the turn cap: when a turn beyond the cap begins, the game is declared a draw.
 */
public final class JsonGameLogger {
    private final Game game;
    private final Writer out;
    private final Gson gson;
    private final Map<Integer, Integer> seatByPlayerId;
    private final int turnCap;

    private int turn = 0;
    private final Map<Integer, Integer> ownTurn = new HashMap<>();
    private final Map<Integer, Integer> turnLost = new HashMap<>();
    private final Map<Integer, ZoneType> zoneByCard = new HashMap<>();
    private final Map<Integer, ZoneType> prevZoneByCard = new HashMap<>();
    private Integer firstSeat = null;
    private String capReason = null;
    private int events = 0;
    private int errors = 0;

    public JsonGameLogger(Game game, Writer out, Gson gson, Map<Integer, Integer> seatByPlayerId, int turnCap) {
        this.game = game;
        this.out = out;
        this.gson = gson;
        this.seatByPlayerId = seatByPlayerId;
        this.turnCap = turnCap;
    }

    public int turn() { return turn; }
    public Integer firstSeat() { return firstSeat; }
    public String capReason() { return capReason; }
    public Integer turnLost(int seat) { return turnLost.get(seat); }
    public int eventCount() { return events; }
    public int errorCount() { return errors; }

    @Subscribe
    public void onEvent(GameEvent ev) {
        try {
            handle(ev);
            checkLosses();
        } catch (Exception | AssertionError e) {
            errors++;
            if (errors <= 5) {
                System.err.println("[logger] " + ev.getClass().getSimpleName() + ": " + e);
                e.printStackTrace();
            }
        }
    }

    private void handle(GameEvent ev) throws IOException {
        if (ev instanceof GameEventGameStarted e) {
            firstSeat = seat(e.firstTurn());
            emit(obj("e", "game_start", "t", 0, "first_seat", firstSeat));
        } else if (ev instanceof GameEventTurnBegan e) {
            turn = e.turnNumber();
            Integer s = seat(e.turnOwner());
            int own = 0;
            if (s != null) {
                own = ownTurn.merge(s, 1, Integer::sum);
            }
            emit(obj("e", "turn", "t", turn, "seat", s, "own_turn", own, "state", snapshot()));
            if (turnCap > 0 && turn > turnCap && !game.isGameOver()) {
                capReason = "TurnCap";
                emit(obj("e", "cap", "t", turn, "turn_cap", turnCap));
                game.setGameOver(GameEndReason.Draw);
            }
        } else if (ev instanceof GameEventMulligan e) {
            emit(obj("e", "mulligan", "t", turn, "seat", seat(e.player())));
        } else if (ev instanceof GameEventLandPlayed e) {
            emit(obj("e", "land", "t", turn, "seat", seat(e.player()), "card", name(e.land()), "id", id(e.land())));
        } else if (ev instanceof GameEventSpellAbilityCast e) {
            SpellAbilityView sa = e.sa();
            CardView host = sa != null ? sa.getHostCard() : null;
            if (host == null) {
                return;
            }
            boolean spell = sa.isSpell();
            Map<String, Object> m = obj("e", "cast", "t", turn, "seat", seat(host.getController()),
                    "card", name(host), "id", host.getId(), "spell", spell, "commander", host.isCommander());
            ZoneType from = zoneByCard.get(host.getId()) == ZoneType.Stack ? prevZoneByCard.get(host.getId()) : zoneByCard.get(host.getId());
            m.put("from", from != null ? from.name() : null);
            if (spell && from == null) {
                m.put("copy", true);            // a copy of a spell was never in a zone: not a card played from hand
            }
            StackItemView si = e.si();
            if (si != null) {
                // The target can sit on a sub-ability (Fists of Flame draws first, then pumps its target).
                List<String> targets = new ArrayList<>();
                List<Integer> targetSeats = new ArrayList<>();
                int depth = 0;
                for (StackItemView part = si; part != null && depth < 8; part = part.getSubInstance(), depth++) {
                    if (part.getTargetCards() != null) {
                        for (CardView t : part.getTargetCards()) {
                            targets.add(name(t));
                        }
                    }
                    if (part.getTargetPlayers() != null) {
                        for (PlayerView t : part.getTargetPlayers()) {
                            targetSeats.add(seat(t));
                        }
                    }
                }
                if (!targets.isEmpty()) {
                    m.put("targets", targets);
                }
                if (!targetSeats.isEmpty()) {
                    m.put("target_seats", targetSeats);
                }
            }
            if (!spell) {
                String d = sa.getDescription();
                m.put("ability", d != null && d.length() > 120 ? d.substring(0, 120) : d);
            }
            emit(m);
        } else if (ev instanceof GameEventSpellResolved e) {
            SpellAbilityView sa = e.spell();
            if (sa != null && sa.isSpell() && sa.getHostCard() != null) {
                emit(obj("e", "resolve", "t", turn, "card", name(sa.getHostCard()), "id", sa.getHostCard().getId(),
                        "fizzled", e.hasFizzled()));
            }
        } else if (ev instanceof GameEventCardChangeZone e) {
            CardView c = e.card();
            if (c == null) {
                return;
            }
            ZoneView from = e.from();
            ZoneView to = e.to();
            ZoneType fromType = from != null ? from.zoneType() : null;
            ZoneType toType = to != null ? to.zoneType() : null;
            if (toType != null) {
                prevZoneByCard.put(c.getId(), fromType != null ? fromType : zoneByCard.get(c.getId()));
                zoneByCard.put(c.getId(), toType);
            }
            PlayerView owner = to != null && to.player() != null ? to.player() : (from != null ? from.player() : null);
            emit(obj("e", "zone", "t", turn, "seat", seat(owner), "card", name(c), "id", c.getId(),
                    "from", fromType != null ? fromType.name() : null, "to", toType != null ? toType.name() : null,
                    "token", c.isToken()));
        } else if (ev instanceof GameEventPlayerLivesChanged e) {
            emit(obj("e", "life", "t", turn, "seat", seat(e.player()), "from", e.oldLives(), "to", e.newLives()));
        } else if (ev instanceof GameEventPlayerDamaged e) {
            CardView src = e.source();
            emit(obj("e", "damage", "t", turn, "seat", seat(e.target()), "amount", e.amount(), "combat", e.combat(),
                    "infect", e.infect(), "source", src != null ? name(src) : null,
                    "source_seat", src != null ? seat(src.getController()) : null,
                    "source_commander", src != null && src.isCommander()));
        } else if (ev instanceof GameEventPlayerPoisoned e) {
            emit(obj("e", "poison", "t", turn, "seat", seat(e.receiver()), "from", e.oldValue(), "amount", e.amount(),
                    "source_seat", seat(e.source())));
        } else if (ev instanceof GameEventAttackersDeclared e) {
            List<Map<String, Object>> attacks = new ArrayList<>();
            Multimap<GameEntityView, CardView> map = e.attackersMap();
            if (map != null) {
                for (Map.Entry<GameEntityView, CardView> en : map.entries()) {
                    GameEntityView def = en.getKey();
                    attacks.add(obj("attacker", name(en.getValue()), "defender", def != null ? def.getName() : null,
                            "defender_seat", defenderSeat(def), "planeswalker", def instanceof CardView));
                }
            }
            if (!attacks.isEmpty()) {
                emit(obj("e", "attack", "t", turn, "seat", seat(e.player()), "attacks", attacks));
            }
        } else if (ev instanceof GameEventBlockersDeclared e) {
            List<Map<String, Object>> blocks = new ArrayList<>();
            Map<GameEntityView, Multimap<CardView, CardView>> map = e.blockers();
            if (map != null) {
                for (Map.Entry<GameEntityView, Multimap<CardView, CardView>> en : map.entrySet()) {
                    Multimap<CardView, CardView> byAttacker = en.getValue();
                    if (byAttacker == null) {
                        continue;
                    }
                    for (CardView attacker : byAttacker.keySet()) {
                        List<String> blockers = new ArrayList<>();
                        for (CardView b : byAttacker.get(attacker)) {
                            if (b == null || b.getId() == attacker.getId()) {
                                continue; // Forge lists an unblocked attacker as its own blocker
                            }
                            blockers.add(name(b));
                        }
                        blocks.add(obj("attacker", name(attacker), "blockers", blockers));
                    }
                }
            }
            if (!blocks.isEmpty()) {
                emit(obj("e", "block", "t", turn, "seat", seat(e.defendingPlayer()), "blocks", blocks));
            }
        } else if (ev instanceof GameEventGameOutcome e) {
            emit(obj("e", "outcome", "t", e.lastTurnNumber(), "winner_name", e.winningPlayerName(), "lines", e.outcomeStrings()));
        }
    }

    /** Emits a "lost" line the first time a player is seen to have lost. */
    private void checkLosses() throws IOException {
        for (Player p : game.getRegisteredPlayers()) {
            Integer s = seatByPlayerId.get(p.getView().getId());
            if (s == null || turnLost.containsKey(s) || !p.hasLost()) {
                continue;
            }
            PlayerOutcome po = p.getOutcome();
            turnLost.put(s, turn);
            emit(obj("e", "lost", "t", turn, "seat", s, "reason", po != null && po.lossState != null ? po.lossState.name() : null,
                    "life", p.getLife()));
        }
    }

    private List<Map<String, Object>> snapshot() {
        List<Map<String, Object>> state = new ArrayList<>();
        for (Player p : game.getRegisteredPlayers()) {
            Integer s = seatByPlayerId.get(p.getView().getId());
            int lands = 0;
            for (Card c : p.getCardsIn(ZoneType.Battlefield)) {
                if (c.isLand()) {
                    lands++;
                }
            }
            int handLands = 0;
            for (Card c : p.getCardsIn(ZoneType.Hand)) {
                if (c.isLand()) {
                    handLands++;
                }
            }
            List<String> commanders = new ArrayList<>();
            for (Card c : p.getCardsIn(ZoneType.Command)) {
                if (c.isCommander()) {
                    commanders.add(c.getName());
                }
            }
            state.add(obj("seat", s, "alive", !p.hasLost(), "life", p.getLife(), "poison", p.getPoisonCounters(),
                    "hand", names(p.getCardsIn(ZoneType.Hand)), "hand_lands", handLands, "lands", lands,
                    "bf", p.getCardsIn(ZoneType.Battlefield).size(), "lib", p.getCardsIn(ZoneType.Library).size(),
                    "gy", p.getCardsIn(ZoneType.Graveyard).size(), "cmd", commanders));
        }
        return state;
    }

    private Integer defenderSeat(GameEntityView def) {
        if (def instanceof PlayerView pv) {
            return seat(pv);
        }
        if (def instanceof CardView cv) {
            return seat(cv.getController());
        }
        return null;
    }

    private Integer seat(PlayerView pv) {
        return pv == null ? null : seatByPlayerId.get(pv.getId());
    }

    private static String name(CardView c) {
        return c == null ? null : c.getName();
    }

    private static Integer id(CardView c) {
        return c == null ? null : c.getId();
    }

    private static List<String> names(Iterable<Card> cards) {
        List<String> l = new ArrayList<>();
        for (Card c : cards) {
            l.add(c.getName());
        }
        return l;
    }

    static Map<String, Object> obj(Object... kv) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) {
            m.put(String.valueOf(kv[i]), kv[i + 1]);
        }
        return m;
    }

    public void emit(Map<String, Object> m) throws IOException {
        out.write(gson.toJson(m));
        out.write('\n');
        out.flush();
        events++;
    }
}
