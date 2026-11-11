#!/usr/bin/env python3
"""Vibefish rollup: turn harness runs (run.json + games/*.events.jsonl) into per-deck statistics.

    runner/rollup.py RUN_DIR [RUN_DIR ...] --out DIR [--run-id ID] [--pod runner/benchmark-pod.json]
                     [--index path/to/index.json] [--max-turn 12]

Several RUN_DIRs are shards of the same run (same decks in the same seats). Writes DIR/rollup.json;
with --index, upserts an entry pointing at it so the dashboard can list runs.
Standard library only.
"""
import argparse
import collections
import datetime as dt
import json
import os
import statistics
import sys

VERSION = "0.3.1"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def iter_events(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.fmean(xs), 2) if xs else None


def wilson(wins, n, z=1.96):
    """95% Wilson score interval for a proportion, as (low, high)."""
    if n == 0:
        return None
    p = wins / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return [round(centre - half, 4), round(centre + half, 4)]


def mc_summary(games_out):
    """Sums Forge's FLATMC-STATS / FLATMC-REASONS lines recorded per game (mc_stats) into one picture of what the
    Monte Carlo layer did: decisions, how many were settled by rollouts, how often it overrode the heuristic, how
    often it ran out of time, rollout failures and time per rollout."""
    import re
    tot = collections.Counter()
    ms = []
    n = 0
    for g in games_out:
        txt = g.get("mc_stats")
        if not txt:
            continue
        n += 1
        for line in txt.splitlines():
            if line.startswith("FLATMC-STATS"):
                for k, v in re.findall(r"(\w+)=([0-9.]+)", line):
                    if k in ("decisions", "byRollouts", "rollouts", "pruned", "failures", "unsimulatableCards"):
                        tot[k] += int(float(v))
                    elif k == "avgMs":
                        ms.append(float(v))
            elif line.startswith("FLATMC-REASONS"):
                for k, v in re.findall(r"([\w-]+)=(\d+)", line):
                    tot["reason:" + k] += int(v)
            elif line.startswith("FLATMC-POINTS"):
                for k, v in re.findall(r"(\w+)=(\d+)", line):
                    if k == "outOfBudget":
                        tot[k] += int(v)
    if not n:
        return None
    dec = tot["decisions"]
    return {
        "games_with_stats": n,
        "decisions": dec,
        "by_rollouts": tot["byRollouts"],
        "overrides": tot["reason:override"],
        "kept_heuristic": tot["reason:kept-heuristic"],
        "too_slow": tot["reason:too-slow"],
        "holds": tot["reason:hold"],
        "out_of_budget_points": tot["outOfBudget"],
        "rollouts": tot["rollouts"],
        "rollout_failures": tot["failures"],
        "unsimulatable_cards": tot["unsimulatableCards"],
        "override_rate": round(tot["reason:override"] / dec, 4) if dec else None,
        "avg_rollout_ms": round(statistics.fmean(ms), 1) if ms else None,
    }


def arm_stats(games_out, decks):
    """Win statistics by AI profile ("arm") when games carry a per-seat profile list.

    Each game has one winner; an arm's game win share is the share of games won by any of its seats, and its expected
    value under equal strength is the share of seats it held. Per-seat win rate (expected 25% in a 4-player pod) and
    per-deck splits are reported too.
    """
    with_profiles = [g for g in games_out if g.get("profiles")]
    if not with_profiles:
        return None
    arms = {}
    for g in with_profiles:
        profs = g["profiles"]
        n = len(profs)
        winner = g.get("winner")
        for seat, prof in enumerate(profs):
            a = arms.setdefault(prof, {"seat_games": 0, "wins": 0, "games": 0, "expected_share": 0.0, "by_deck": {}})
            a["seat_games"] += 1
            a["expected_share"] += 1.0 / n
            d = a["by_deck"].setdefault(decks[seat]["id"] if seat < len(decks) else str(seat), {"games": 0, "wins": 0})
            d["games"] += 1
            if winner == seat:
                a["wins"] += 1
                d["wins"] += 1
        for prof in set(profs):
            arms[prof]["games"] += 1
    out = {}
    for prof, a in arms.items():
        games = a["games"]
        out[prof] = {
            "games": games,
            "seat_games": a["seat_games"],
            "wins": a["wins"],
            "game_win_share": round(a["wins"] / games, 4) if games else None,
            "game_win_share_ci95": wilson(a["wins"], games),
            "expected_game_win_share": round(a["expected_share"] / games, 4) if games else None,
            "seat_win_rate": round(a["wins"] / a["seat_games"], 4) if a["seat_games"] else None,
            "by_deck": {k: {**v, "win_rate": round(v["wins"] / v["games"], 4) if v["games"] else None} for k, v in a["by_deck"].items()},
        }
    return {"games_with_profiles": len(with_profiles), "arms": out}


class DeckStats:
    def __init__(self, seat, info, max_turn):
        self.seat = seat
        self.info = info
        self.max_turn = max_turn
        self.games = 0
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.loss_reasons = collections.Counter()
        self.turns_played = []
        self.turn_lost_own = []
        self.mulligans = []
        self.opening_hand_lands = []
        self.land_drop_games = [set() for _ in range(max_turn + 1)]   # k -> set of game keys with a land drop on own turn k
        self.turn_games = [set() for _ in range(max_turn + 1)]        # k -> set of game keys that reached own turn k
        self.lands_by_turn = [[] for _ in range(max_turn + 1)]
        self.hand_by_turn = [[] for _ in range(max_turn + 1)]
        self.life_by_turn = [[] for _ in range(max_turn + 1)]
        self.first_cast = []          # own turn of first commander cast, per game (None if never)
        self.commander_casts = []     # casts from the command zone per game
        self.damage_dealt = []
        self.damage_taken = []
        self.commander_damage_dealt = []
        self.cards = {}
        for c in info.get("cards", []):
            self.cards[c["name"]] = {
                "name": c["name"], "count": c.get("count", 1), "type": c.get("type"), "cmc": c.get("cmc"),
                "land": bool(c.get("land")), "drawn": 0, "cast": 0, "played": 0, "games_drawn": set(), "games_cast": set(),
            }

    def card(self, name):
        if name not in self.cards:
            self.cards[name] = {"name": name, "count": 0, "type": None, "cmc": None, "land": False, "drawn": 0,
                                "cast": 0, "played": 0, "games_drawn": set(), "games_cast": set(), "extra": True}
        return self.cards[name]

    def summary(self):
        games = self.games or 1
        cards = []
        for c in self.cards.values():
            d = dict(c)
            d["games_drawn"] = len(c["games_drawn"])
            d["games_cast"] = len(c["games_cast"])
            cards.append(d)
        cards.sort(key=lambda c: (-c["cast"], -c["played"], c["name"]))
        never_cast = sorted(c["name"] for c in cards if not c["land"] and c["cast"] == 0 and c["played"] == 0
                            and not c.get("extra"))
        drawn_never_cast = sorted(c["name"] for c in cards if not c["land"] and c["cast"] == 0 and c["drawn"] > 0
                                  and not c.get("extra"))
        rng = range(1, self.max_turn + 1)
        return {
            "seat": self.seat,
            "id": self.info.get("id"),
            "name": self.info.get("name"),
            "commanders": self.info.get("commanders", []),
            "profile": self.info.get("profile"),
            "games": self.games,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "win_rate": round(self.wins / games, 4),
            "loss_reasons": dict(self.loss_reasons.most_common()),
            "avg_turns_played": mean(self.turns_played),
            "turns_played": self.turns_played,
            "avg_turn_lost": mean(self.turn_lost_own),
            "mulligan_rate": round(sum(1 for m in self.mulligans if m > 0) / games, 4),
            "avg_mulligans": mean(self.mulligans),
            "opening_hand_lands_avg": mean(self.opening_hand_lands),
            "opening_hand_lands": self.opening_hand_lands,
            "land_drop_rate": [round(len(self.land_drop_games[k]) / len(self.turn_games[k]), 3) if self.turn_games[k] else None for k in rng],
            "lands_by_turn": [mean(self.lands_by_turn[k]) for k in rng],
            "hand_by_turn": [mean(self.hand_by_turn[k]) for k in rng],
            "life_by_turn": [mean(self.life_by_turn[k]) for k in rng],
            "games_reaching_turn": [len(self.turn_games[k]) for k in rng],
            "commander": {
                "first_cast_turns": self.first_cast,
                "avg_first_cast_turn": mean([t for t in self.first_cast if t is not None]),
                "never_cast_games": sum(1 for t in self.first_cast if t is None),
                "casts_per_game": mean(self.commander_casts),
            },
            "damage": {
                "dealt_per_game": mean(self.damage_dealt),
                "taken_per_game": mean(self.damage_taken),
                "commander_dealt_per_game": mean(self.commander_damage_dealt),
            },
            "never_cast": never_cast,
            "drawn_never_cast": drawn_never_cast,
            "cards": cards,
        }


def process_game(game, events_path, stats, game_key, max_turn):
    seats = list(stats.keys())
    own_turn = {s: 0 for s in seats}
    land_drop_turns = {s: set() for s in seats}
    first_cast = {s: None for s in seats}
    cmd_casts = {s: 0 for s in seats}
    dealt = {s: 0 for s in seats}
    taken = {s: 0 for s in seats}
    cmd_dealt = {s: 0 for s in seats}
    mulls = {s: 0 for s in seats}
    lost_own = {s: None for s in seats}
    drawn_cards = {s: collections.Counter() for s in seats}
    cast_cards = {s: collections.Counter() for s in seats}
    played_cards = {s: collections.Counter() for s in seats}

    for ev in iter_events(events_path):
        e = ev.get("e")
        if e == "turn":
            s = ev.get("seat")
            if s is None or s not in stats:
                continue
            k = ev.get("own_turn") or 0
            own_turn[s] = k
            if 1 <= k <= max_turn:
                st = stats[s]
                st.turn_games[k].add(game_key)
                for ps in ev.get("state", []):
                    if ps.get("seat") == s:
                        st.lands_by_turn[k].append(ps.get("lands"))
                        st.hand_by_turn[k].append(len(ps.get("hand", [])))
                        st.life_by_turn[k].append(ps.get("life"))
                        if k == 1 and ps.get("hand_lands") is not None:
                            st.opening_hand_lands.append(ps.get("hand_lands"))
        elif e == "land":
            s = ev.get("seat")
            if s in own_turn:
                k = own_turn[s]
                if 1 <= k <= max_turn:
                    land_drop_turns[s].add(k)
                played_cards[s][ev.get("card")] += 1
        elif e == "cast":
            s = ev.get("seat")
            if s not in own_turn:
                continue
            if ev.get("spell") and not (ev.get("copy") or ev.get("from") is None):   # a copy of a spell is not a card cast
                cast_cards[s][ev.get("card")] += 1
            if ev.get("commander") and ev.get("from") == "Command":
                cmd_casts[s] += 1
                if first_cast[s] is None:
                    first_cast[s] = max(own_turn[s], 1)
        elif e == "zone":
            if ev.get("from") == "Library" and ev.get("to") == "Hand" and ev.get("seat") in own_turn:
                drawn_cards[ev["seat"]][ev.get("card")] += 1
        elif e == "mulligan":
            s = ev.get("seat")
            if s in mulls:
                mulls[s] += 1
        elif e == "damage":
            s = ev.get("seat")
            src = ev.get("source_seat")
            amt = ev.get("amount") or 0
            if s in taken:
                taken[s] += amt
            if src in dealt and src != s:
                dealt[src] += amt
                if ev.get("source_commander"):
                    cmd_dealt[src] += amt
        elif e == "lost":
            s = ev.get("seat")
            if s in lost_own:
                lost_own[s] = own_turn[s]

    winner = game.get("winner")
    reason = game.get("reason")
    by_seat = {p.get("seat"): p for p in game.get("players", [])}
    for s, st in stats.items():
        st.games += 1
        p = by_seat.get(s, {})
        if winner == s:
            st.wins += 1
        elif p.get("lost"):
            st.losses += 1
            st.loss_reasons[p.get("reason") or "Unknown"] += 1
        else:
            st.draws += 1
        st.turns_played.append(p.get("turns_played"))
        if lost_own[s] is not None:
            st.turn_lost_own.append(lost_own[s])
        st.mulligans.append(p.get("mulligans") if p.get("mulligans") is not None else mulls[s])
        for k in land_drop_turns[s]:
            st.land_drop_games[k].add(game_key)
        st.first_cast.append(first_cast[s])
        st.commander_casts.append(cmd_casts[s])
        st.damage_dealt.append(dealt[s])
        st.damage_taken.append(taken[s])
        st.commander_damage_dealt.append(cmd_dealt[s])
        for name, n in drawn_cards[s].items():
            c = st.card(name)
            c["drawn"] += n
            c["games_drawn"].add(game_key)
        for name, n in cast_cards[s].items():
            c = st.card(name)
            c["cast"] += n
            c["games_cast"].add(game_key)
        for name, n in played_cards[s].items():
            st.card(name)["played"] += n


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--run-id")
    ap.add_argument("--pod")
    ap.add_argument("--index")
    ap.add_argument("--max-turn", type=int, default=12)
    args = ap.parse_args(argv)

    runs = []
    for d in args.run_dirs:
        rj = os.path.join(d, "run.json")
        if not os.path.isfile(rj):
            print(f"skipping {d}: no run.json", file=sys.stderr)
            continue
        run = load_json(rj)
        run["_dir"] = d
        runs.append(run)
    if not runs:
        print("no runs found", file=sys.stderr)
        return 1

    decks = runs[0]["decks"]
    ids = [d["id"] for d in decks]
    for run in runs[1:]:
        if [d["id"] for d in run["decks"]] != ids:
            print(f"deck mismatch in {run['_dir']}: {[d['id'] for d in run['decks']]} vs {ids}", file=sys.stderr)
            return 1

    stats = {d["seat"]: DeckStats(d["seat"], d, args.max_turn) for d in decks}
    games_out = []
    seeds = []
    for run in runs:
        shard = os.path.basename(os.path.normpath(run["_dir"]))
        seeds.append(run.get("seed_base"))
        for g in run.get("games", []):
            ev_rel = g.get("events")
            ev_path = os.path.join(run["_dir"], ev_rel) if ev_rel else None
            key = f"{shard}:{g.get('index')}"
            if ev_path and os.path.isfile(ev_path):
                process_game(g, ev_path, stats, key, args.max_turn)
            else:
                print(f"missing events for {key}", file=sys.stderr)
            out = dict(g)
            out["shard"] = shard
            out["events"] = f"{shard}/{ev_rel}" if ev_rel else None
            games_out.append(out)

    games_out.sort(key=lambda g: (g["shard"], g.get("index", 0)))
    deck_summaries = [stats[s].summary() for s in sorted(stats)]
    pod_name = None
    if args.pod and os.path.isfile(args.pod):
        pod_name = load_json(args.pod).get("name")
    run_id = args.run_id or os.path.basename(os.path.normpath(args.out))
    rollup = {
        "vibefish": VERSION,
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": run_id,
        "forge_version": runs[0].get("forge_version"),
        "forge_build": runs[0].get("forge_build"),
        "format": runs[0].get("format"),
        "pod": pod_name,
        "games": len(games_out),
        "completed_games": sum(1 for g in games_out if g.get("winner") is not None),
        "drawn_games": sum(1 for g in games_out if g.get("winner") is None),
        "shards": len(runs),
        "seeds": seeds,
        "clock_s": runs[0].get("clock_s"),
        "turn_cap": runs[0].get("turn_cap"),
        "max_turn": args.max_turn,
        "avg_game_turns": mean([g.get("turns") for g in games_out]),
        "avg_game_seconds": mean([g.get("duration_ms", 0) / 1000 for g in games_out]),
        "decks": [{k: v for k, v in d.items() if k != "cards"} | {"card_count": len(d.get("cards", []))} for d in decks],
        "mc": runs[0].get("mc"),
        "mc_available": runs[0].get("mc_available"),
        "rotate_profiles": runs[0].get("rotate_profiles"),
        "arms": arm_stats(games_out, decks),
        "mc_summary": mc_summary(games_out),
        "deck_stats": deck_summaries,
        "game_summaries": games_out,
    }
    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "rollup.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rollup, f, indent=1, ensure_ascii=False)
    print(f"rollup: {len(games_out)} games, {len(deck_summaries)} decks -> {out_path}", file=sys.stderr)
    for d in deck_summaries:
        print(f"  {d['id']:<18} games {d['games']:>3}  wins {d['wins']:>3}  win% {d['win_rate']*100:5.1f}  "
              f"mull% {d['mulligan_rate']*100:5.1f}  cmdr T{d['commander']['avg_first_cast_turn']}  "
              f"lands@T4 {d['lands_by_turn'][3] if len(d['lands_by_turn']) > 3 else None}", file=sys.stderr)
    if rollup["mc_summary"]:
        m = rollup["mc_summary"]
        print(f"  monte carlo: {m['decisions']} decisions in {m['games_with_stats']} games, {m['by_rollouts']} by rollouts, "
              f"{m['overrides']} overrides ({(m['override_rate'] or 0)*100:.1f}%), {m['too_slow']} too slow, "
              f"{m['rollout_failures']} failures, {m['avg_rollout_ms']} ms per rollout", file=sys.stderr)
    if rollup["arms"]:
        for prof, a in rollup["arms"]["arms"].items():
            ci = a["game_win_share_ci95"] or [None, None]
            print(f"  arm {prof:<20} games {a['games']:>3}  wins {a['wins']:>3}  game win share {a['game_win_share']*100:5.1f}% "
                  f"(95% {ci[0]*100:.0f}–{ci[1]*100:.0f}%, even = {a['expected_game_win_share']*100:.0f}%)  per seat {a['seat_win_rate']*100:.1f}%",
                  file=sys.stderr)

    if args.index:
        index = load_json(args.index) if os.path.isfile(args.index) else {"runs": []}
        rel = os.path.relpath(out_path, os.path.dirname(os.path.abspath(args.index))).replace(os.sep, "/")
        entry = {"id": run_id, "generated": rollup["generated"], "forge_version": rollup["forge_version"],
                 "pod": pod_name, "games": rollup["games"], "path": rel}
        index["runs"] = [r for r in index.get("runs", []) if r.get("id") != run_id] + [entry]
        index["runs"].sort(key=lambda r: r.get("generated", ""), reverse=True)
        os.makedirs(os.path.dirname(os.path.abspath(args.index)), exist_ok=True)
        with open(args.index, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=1)
        print(f"index: {len(index['runs'])} run(s) -> {args.index}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
