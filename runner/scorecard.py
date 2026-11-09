#!/usr/bin/env python3
"""Calibration scorecard: how human-like a run's games look, against the Playgroup.gg references.

    runner/scorecard.py RUN_DIR/rollup.json [--reference runner/reference/playgroup-commander.json] [--out scorecard.json]

Compares, where the run has the data: stock-precon win rates and their rank order, the first-seat advantage,
how often decks mulligan, lands in the kept opening hand, and game length in rounds. These are sanity metrics for
"does the AI play precons the way people do", not a measure of play strength on their own. Works for a pod rollup
(runner/rollup.py, four decks) and a league rollup (runner/league.py, many decks). Standard library only.
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


def ranks(v, descending=False):
    """Average ranks for ties; 1 is the smallest value (or the largest with descending)."""
    key = (lambda i: -v[i]) if descending else (lambda i: v[i])
    order = sorted(range(len(v)), key=key)
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


def pearson(xs, ys):
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
    return round(num / den, 3) if den else None


def spearman(xs, ys):
    """Spearman rank correlation (average ranks for ties)."""
    if len(xs) < 3:
        return None
    return pearson(ranks(xs), ranks(ys))


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
    seats = rollup.get("seats_per_game") or len(decks) or 4
    league = rollup.get("league")
    card = {"run_id": rollup.get("run_id"), "kind": rollup.get("kind", "pod"), "games": len(games), "reference": ref.get("source"),
            "reference_retrieved": ref.get("retrieved"), "metrics": {}}

    # 1. precon win rates against the human table
    rows = []
    for d in decks:
        name = d.get("reference_name") or short_name(d.get("name"))
        h = ref["precon_win_rate"].get(name)
        row = {"deck": name, "id": d.get("id"), "sim_win_rate": d.get("win_rate"), "sim_games": d.get("games")}
        if d.get("win_rate_ci95"):
            row["sim_win_rate_ci95"] = d["win_rate_ci95"]
        if h:
            row["human_win_rate"] = h["win_rate"]
            row["human_games"] = h["games"]
            row["difference"] = round(d["win_rate"] - h["win_rate"], 4)
            if h.get("tier"):
                row["human_tier"] = h["tier"]
        rows.append(row)
    matched = [r for r in rows if "human_win_rate" in r]
    sim_rates = [r["sim_win_rate"] for r in matched]
    human_rates = [r["human_win_rate"] for r in matched]
    if matched:
        for r, sr, hr in zip(matched, ranks(sim_rates, descending=True), ranks(human_rates, descending=True)):
            r["sim_rank"] = sr
            r["human_rank"] = hr
    rows.sort(key=lambda r: (-(r.get("human_win_rate") if r.get("human_win_rate") is not None else -1), r["deck"]))
    pw = {"rows": rows, "decks_compared": len(matched),
          "spearman_rank_correlation": spearman(sim_rates, human_rates),
          "pearson_correlation": pearson(sim_rates, human_rates),
          "mean_abs_difference": round(statistics.fmean(abs(r["difference"]) for r in matched), 4) if matched else None,
          "sim_sd": round(statistics.pstdev(sim_rates), 4) if len(matched) > 1 else None,
          "human_sd": round(statistics.pstdev(human_rates), 4) if len(matched) > 1 else None,
          "note": "human rates are stock precons against mixed tables, normalised to a 25% baseline; sim rates are inside this "
                  + ("league" if league else "pod") + ", so compare the ordering more than the levels"}
    well = [r for r in matched if r["human_games"] >= 100]
    if len(well) >= 3:
        pw["well_measured"] = {"min_human_games": 100, "decks_compared": len(well),
                               "spearman_rank_correlation": spearman([r["sim_win_rate"] for r in well], [r["human_win_rate"] for r in well]),
                               "pearson_correlation": pearson([r["sim_win_rate"] for r in well], [r["human_win_rate"] for r in well])}
    card["metrics"]["precon_win_rate"] = pw

    # 2. first-seat advantage
    first = [g for g in games if g.get("first_seat") is not None and g.get("winner") is not None]
    if first:
        fw = sum(1 for g in first if g["winner"] == g["first_seat"])
        card["metrics"]["first_seat_win_rate"] = {"sim": round(fw / len(first), 4), "sim_games": len(first),
                                                  "human": ref["seat_win_rate"][0], "even": round(1 / seats, 4)}
        if rollup.get("seat_win_rate"):
            card["metrics"]["first_seat_win_rate"]["sim_by_seat"] = rollup["seat_win_rate"]
            card["metrics"]["first_seat_win_rate"]["human_by_seat"] = ref["seat_win_rate"]

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
    shown = m["precon_win_rate"]["rows"] if len(rows) <= 12 else [r for r in rows if "human_win_rate" in r][:6]
    for r in shown:
        print(f"  {r['deck']:<24} sim {r['sim_win_rate']*100:5.1f}%  human {r.get('human_win_rate', float('nan'))*100:5.1f}%", file=sys.stderr)
    if len(rows) > 12:
        print(f"  ... {len(rows) - len(shown)} more decks", file=sys.stderr)
    print(f"  rank correlation {pw['spearman_rank_correlation']} (pearson {pw['pearson_correlation']}, mean |diff| {pw['mean_abs_difference']}) over {pw['decks_compared']} decks"
          + (f"; {pw['well_measured']['spearman_rank_correlation']} over the {pw['well_measured']['decks_compared']} with 100+ human games" if "well_measured" in pw else ""), file=sys.stderr)
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
