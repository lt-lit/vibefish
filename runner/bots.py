#!/usr/bin/env python3
"""The per-deck bots in one file for the dashboard.

    runner/bots.py [--manifest playbook/bots.json] [--out demo-data/bots.json]

Reads the manifest (which decks have a bot or a candidate, and which measurement files are theirs) and writes
demo-data/bots.json: for each deck its human win rate (runner/reference/playgroup-commander.json), the paired table
result (wins of the stock arm and of the bot's arm on the same tables, Wilson intervals, the paired difference and
the exact test, from an ab.py rollup or join) and the goldfish kill turns (hands.py compare --out). Numbers are
copied from those files, never typed. Standard library only.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import league as lg  # noqa: E402  (load_json, dump_json, now)
import rollup as rl  # noqa: E402  (VERSION)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", default=os.path.join(ROOT, "playbook", "bots.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "demo-data", "bots.json"))
    ap.add_argument("--league", default=os.path.join(HERE, "precon-league.json"))
    ap.add_argument("--reference", default=os.path.join(HERE, "reference", "playgroup-commander.json"))
    args = ap.parse_args(argv)
    manifest = lg.load_json(args.manifest)
    decks = {d["id"]: d for d in lg.load_json(args.league)["decks"]}
    ref = lg.load_json(args.reference)
    out = []
    for b in manifest["bots"]:
        deck = decks.get(b["deck"])
        if deck is None:
            sys.exit(f"bots.py: {b['deck']} is not a league deck")
        human = ref["precon_win_rate"].get(deck.get("reference_name") or deck["name"]) or {}
        row = {"deck": b["deck"], "name": deck["name"], "commanders": deck.get("commanders", []), "status": b.get("status"),
               "playbook": b.get("playbook"), "summary": b.get("summary"),
               "human": {"win_rate": human.get("win_rate"), "games": human.get("games")} if human else None,
               "tables": None, "goldfish": None}
        t = b.get("tables")
        if t:
            r = lg.load_json(os.path.join(ROOT, t["file"]))
            stock, bot = r["arm_stats"][t["stock"]], r["arm_stats"][t["bot"]]
            pair = r["paired"][f"{t['bot']}_vs_{t['stock']}"]
            row["tables"] = {"run": t.get("run"), "seed": r.get("seed"), "forge_version": r.get("forge_version"), "source": t["file"],
                             "stock": {k: stock[k] for k in ("games", "wins", "win_rate", "win_rate_ci95")},
                             "bot": {k: bot[k] for k in ("games", "wins", "win_rate", "win_rate_ci95")},
                             "difference": pair["difference"], "difference_ci95": pair["difference_ci95"],
                             "bot_only": pair[f"{t['bot']}_only"], "stock_only": pair[f"{t['stock']}_only"], "exact_p": pair.get("exact_p")}
        g = b.get("goldfish")
        if g:
            p = lg.load_json(os.path.join(ROOT, g))
            row["goldfish"] = {"source": g, "games": p["a"]["games"], "stock_kill_turn": p["a"].get("kill_turn_mean"),
                               "bot_kill_turn": p["b"].get("kill_turn_mean"), "faster_by": p["paired"]["a_minus_b_turns"],
                               "faster_by_ci95": p["paired"]["ci95"], "seeds_paired": p["paired"]["seeds"]}
        out.append(row)
    result = {"vibefish": rl.VERSION, "generated": lg.now(), "kind": "bots",
              "reference": {"source": "Playgroup.gg", "retrieved": ref.get("retrieved"), "license": (ref.get("precon_table") or {}).get("license")},
              "bots": out}
    lg.dump_json(args.out, result)
    for r in out:
        t, g = r["tables"], r["goldfish"]
        print(f"{r['name']:<16} {r['status']:<32} "
              + (f"tables {t['bot']['wins']}/{t['bot']['games']} vs stock {t['stock']['wins']}/{t['stock']['games']} ({t['difference'] * 100:+.1f}, p {t['exact_p']})  " if t else "tables -  ")
              + (f"goldfish {g['bot_kill_turn']} vs {g['stock_kill_turn']}" if g else ""), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
