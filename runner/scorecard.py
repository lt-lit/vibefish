#!/usr/bin/env python3
"""Calibration scorecard: how human-like a run's games look, against the Playgroup.gg references.

    runner/scorecard.py RUN_DIR/rollup.json [--reference runner/reference/playgroup-commander.json] [--out scorecard.json]

Compares, where the run has the data: stock-precon win rates and their rank order, the first-seat advantage,
how often decks mulligan, lands in the kept opening hand, and game length in rounds. These are sanity metrics for
"does the AI play precons the way people do", not a measure of play strength on their own. Standard library only.
"""
import argparse
import collections
import json
import os
import statistics
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def short_name(name):
    import re
    return re.sub(r"\s*\[[^\]]*\]", "", name or "").strip()


def spearman(xs, ys):
    """Spearman rank correlation (average ranks for ties)."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    if len(xs) < 3:
        return None
    rx, ry = ranks(xs), ranks(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 3) if den else None


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rollup")
    ap.add_argument("--reference", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference", "playgroup-commander.json"))
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    rollup = load(args.rollup)
    ref = load(args.reference)
    games = rollup.get("game_summaries", [])
    decks = rollup.get("deck_stats", [])
    seats = len(decks) or 4
    card = {"run_id": rollup.get("run_id"), "games": len(games), "reference": ref.get("source"), "reference_retrieved": ref.get("retrieved"), "metrics": {}}

    # 1. precon win rates against the human table
    rows, sim_rates, human_rates = [], [], []
    for d in decks:
        name = short_name(d.get("name"))
        h = ref["precon_win_rate"].get(name)
        row = {"deck": name, "sim_win_rate": d.get("win_rate"), "sim_games": d.get("games")}
        if h:
            row["human_win_rate"] = h["win_rate"]
            row["human_games"] = h["games"]
            row["difference"] = round(d["win_rate"] - h["win_rate"], 4)
            sim_rates.append(d["win_rate"])
            human_rates.append(h["win_rate"])
        rows.append(row)
    card["metrics"]["precon_win_rate"] = {"rows": rows, "spearman_rank_correlation": spearman(sim_rates, human_rates),
                                          "decks_compared": len(sim_rates),
                                          "note": "human rates are stock precons against mixed tables; sim rates are inside this pod, so compare the ordering more than the levels"}

    # 2. first-seat advantage
    first = [g for g in games if g.get("first_seat") is not None and g.get("winner") is not None]
    if first:
        fw = sum(1 for g in first if g["winner"] == g["first_seat"])
        card["metrics"]["first_seat_win_rate"] = {"sim": round(fw / len(first), 4), "sim_games": len(first),
                                                  "human": ref["seat_win_rate"][0], "even": round(1 / seats, 4)}

    # 3. mulligans per seat-game
    mulls = collections.Counter()
    n_seat_games = 0
    for g in games:
        for p in g.get("players", []):
            m = p.get("mulligans")
            if m is None:
                continue
            n_seat_games += 1
            mulls["3+" if m >= 3 else str(m)] += 1
    if n_seat_games:
        dist = {k: round(mulls.get(k, 0) / n_seat_games, 4) for k in ("0", "1", "2", "3+")}
        card["metrics"]["mulligans_taken"] = {"sim": dist, "human": ref["mulligans_taken"], "sim_seat_games": n_seat_games,
                                              "sim_any_mulligan": round(1 - dist["0"], 4), "human_any_mulligan": round(1 - ref["mulligans_taken"]["0"], 4)}

    # 4. lands in the kept opening hand
    lands = collections.Counter()
    n_hands = 0
    for d in decks:
        for v in d.get("opening_hand_lands") or []:
            n_hands += 1
            lands[str(min(max(int(v), 0), 7))] += 1
    if n_hands:
        dist = {k: round(lands.get(k, 0) / n_hands, 4) for k in ("0", "1", "2", "3", "4", "5", "6", "7")}
        human = ref["opening_hand_lands"]
        card["metrics"]["opening_hand_lands"] = {"sim": dist, "human": human, "sim_hands": n_hands,
                                                 "sim_mean": round(sum(int(k) * v for k, v in dist.items()), 2),
                                                 "human_mean": round(sum(int(k) * v for k, v in human.items()), 2)}

    # 5. game length in rounds
    turns = [g.get("turns") for g in games if g.get("turns")]
    if turns:
        rounds = [t / seats for t in turns]
        card["metrics"]["rounds_per_game"] = {"sim_mean": round(statistics.fmean(rounds), 2), "sim_median": round(statistics.median(rounds), 1),
                                              "human_mean": ref["rounds_per_game"]["mean"], "human_median": ref["rounds_per_game"]["median"]}

    out = args.out or os.path.join(os.path.dirname(os.path.abspath(args.rollup)), "scorecard.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=1)
    m = card["metrics"]
    print(f"scorecard for {card['run_id']} ({card['games']} games) vs Playgroup ({ref.get('retrieved')}):", file=sys.stderr)
    for r in m["precon_win_rate"]["rows"]:
        print(f"  {r['deck']:<18} sim {r['sim_win_rate']*100:5.1f}%  human {r.get('human_win_rate', float('nan'))*100:5.1f}%", file=sys.stderr)
    print(f"  rank correlation {m['precon_win_rate']['spearman_rank_correlation']} over {m['precon_win_rate']['decks_compared']} decks", file=sys.stderr)
    if "first_seat_win_rate" in m:
        print(f"  first seat wins {m['first_seat_win_rate']['sim']*100:.1f}% (human {m['first_seat_win_rate']['human']*100:.1f}%, even {m['first_seat_win_rate']['even']*100:.0f}%)", file=sys.stderr)
    if "mulligans_taken" in m:
        print(f"  any mulligan {m['mulligans_taken']['sim_any_mulligan']*100:.1f}% (human {m['mulligans_taken']['human_any_mulligan']*100:.0f}%)  distribution {m['mulligans_taken']['sim']}", file=sys.stderr)
    if "opening_hand_lands" in m:
        print(f"  opening-hand lands mean {m['opening_hand_lands']['sim_mean']} (human {m['opening_hand_lands']['human_mean']})  distribution {m['opening_hand_lands']['sim']}", file=sys.stderr)
    if "rounds_per_game" in m:
        print(f"  rounds per game {m['rounds_per_game']['sim_mean']} (human {m['rounds_per_game']['human_mean']})", file=sys.stderr)
    print(f"  -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
