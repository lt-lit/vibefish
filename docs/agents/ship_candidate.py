#!/usr/bin/env python3
"""Ship a candidate playbook: the mechanical part. A session helper, not pipeline code.

    python3 -I docs/agents/ship_candidate.py DECK NAME --attack gowide|forge --tables demo-data/ab/<dir>/DECK-join.json
            --bot-arm gowide|forgeattack|playbook|<arm> [--stock-arm stock] --run "ab-run #27: ..." --status "shipped (v1); ..."
            --summary "what the bot does" [--note "appended to the playbook's notes"] [--goldfish FILE] [--on 2026-11-14]
            [--dry-run]

What it does:
  1. reads playbook/variants/DECK-NAME.json; with --attack forge the `attack` block is dropped (the candidate's
     -forgeattack sibling must then hold exactly that playbook), with --attack gowide it is kept;
  2. writes that playbook, with `on` and the note, as the `playbook` object of playbook/precons/DECK.json
     (replacing one that is there: say so in --note);
  3. adds or replaces the deck's row in playbook/bots.json (deck, status, playbook, summary, tables, goldfish);
  4. checks that the tables file has the two arms named and prints their wins.

It decides nothing and writes no prose of its own: the status, summary and note are the session's, from the exam.
Afterwards: `python3 -I runner/bots.py` (demo-data/bots.json), the candidate's row in playbook/variants/README.md,
DESIGN, CLAUDE.md.
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(p, obj):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("name")
    ap.add_argument("--attack", required=True, choices=["gowide", "forge"])
    ap.add_argument("--tables", required=True)
    ap.add_argument("--bot-arm", required=True)
    ap.add_argument("--stock-arm", default="stock")
    ap.add_argument("--run", required=True)
    ap.add_argument("--status", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--note")
    ap.add_argument("--goldfish")
    ap.add_argument("--on", default=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    vpath = os.path.join(ROOT, "playbook", "variants", f"{a.deck}-{a.name}.json")
    var = load(vpath)
    pb = dict(var["playbook"])
    if a.attack == "forge":
        pb.pop("attack", None)
        sib = os.path.join(ROOT, "playbook", "variants", f"{a.deck}-{a.name}-forgeattack.json")
        if os.path.isfile(sib):
            s = dict(load(sib)["playbook"])
            if {k: v for k, v in s.items() if k != "notes"} != {k: v for k, v in pb.items() if k != "notes"}:
                raise SystemExit(f"{sib} is not {vpath} without its attack block: the tables did not play what would ship")
    elif not pb.get("attack"):
        raise SystemExit(f"{vpath} has no attack block")
    notes = pb.get("notes")
    if a.note:
        notes = (notes + [a.note]) if isinstance(notes, list) else ((notes + " " if notes else "") + a.note)
    shipped = {k: v for k, v in pb.items() if k != "notes"}
    shipped["notes"] = notes
    shipped["on"] = a.on

    tpath = os.path.join(ROOT, a.tables) if not os.path.isabs(a.tables) else a.tables
    t = load(tpath)
    if t.get("deck") != a.deck:
        raise SystemExit(f"{a.tables} is a run of {t.get('deck')}, not of {a.deck}")
    for arm in (a.stock_arm, a.bot_arm):
        if arm not in t["arm_stats"]:
            raise SystemExit(f"{a.tables} has no arm {arm} (it has {list(t['arm_stats'])})")
    st, bt = t["arm_stats"][a.stock_arm], t["arm_stats"][a.bot_arm]
    pair = (t.get("paired") or {}).get(f"{a.bot_arm}_vs_{a.stock_arm}") or {}
    print(f"{a.deck}: {a.bot_arm} {bt['wins']} of {bt['games']} against {a.stock_arm} {st['wins']} of {st['games']}"
          + (f"; {pair['difference'] * 100:+.1f} points ({pair['difference_ci95'][0] * 100:+.0f} to {pair['difference_ci95'][1] * 100:+.0f}), exact test {pair['exact_p']:.4f}" if pair else ""))

    gf = a.goldfish
    if not gf:
        found = sorted(p for p in glob.glob(os.path.join(ROOT, "demo-data", "goldfish", "*", f"{a.deck}-seeds-*.json")))
        gf = os.path.relpath(found[-1], ROOT) if found else None
    dpath = os.path.join(ROOT, "playbook", "precons", f"{a.deck}.json")
    data = load(dpath)
    was = (data.get("playbook") or {}).get("version")
    data["playbook"] = shipped
    bots_path = os.path.join(ROOT, "playbook", "bots.json")
    bots = load(bots_path)
    row = {"deck": a.deck, "status": a.status, "playbook": f"playbook/precons/{a.deck}.json", "summary": a.summary,
           "tables": {"file": os.path.relpath(tpath, ROOT), "stock": a.stock_arm, "bot": a.bot_arm, "run": a.run},
           "goldfish": gf}
    old = [i for i, r in enumerate(bots["bots"]) if r["deck"] == a.deck]
    if old:
        keep = {k: v for k, v in bots["bots"][old[0]].items() if k not in row}      # earlier tables of the deck stay on its row
        bots["bots"][old[0]] = {**row, **keep}
    else:
        bots["bots"].append(row)
    rules = shipped["cast"]["rules"] if isinstance(shipped.get("cast"), dict) else shipped.get("cast") or []
    print(f"playbook/precons/{a.deck}.json: playbook version {shipped.get('version')}{' (was ' + str(was) + ')' if was else ''}, {len(rules)} cast rules, "
          f"{len(shipped.get('triggers') or [])} trigger rules, attack {json.dumps(shipped.get('attack')) if shipped.get('attack') else 'left to Forge'}, on {a.on}")
    print(f"playbook/bots.json: {'replaced' if old else 'added'} the row; goldfish {gf}")
    if a.dry_run:
        print("dry run: nothing written")
        return 0
    dump(dpath, data)
    dump(bots_path, bots)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
