#!/usr/bin/env python3
"""Ship the next version of a playbook that is already shipped: the mechanical part. A session helper, not pipeline code.

    python3 -I docs/agents/ship_version.py DECK NAME --tables demo-data/ab/<dir>/DECK-join.json --old-arm shipped --new-arm NAME
            --run "ab-run #33: ..." --status "shipped (v2, ...)" [--summary-add "version 2 also ..."] --note "appended to the notes"
            [--on 2026-11-14] [--dry-run]

For a candidate that was judged against the shipped playbook of its own deck on the same tables (playbook arms only:
`docs/agents/exam_summary.py` writes that join), where `ship_candidate.py` is for a first playbook judged against the
stock pilot. What it does:
  1. reads playbook/variants/DECK-NAME.json and refuses it unless its version is the shipped version plus one and it has
     the same attack block as the shipped playbook (the tables played the candidate as it is; an attack is not changed
     on the way in), unless --attack-changes says the attack block is the change that was examined (a `finish`
     candidate, 2026-11-20);
  2. writes that playbook, with `on` and the note, as the `playbook` object of playbook/precons/DECK.json;
  3. in the deck's row of playbook/bots.json: the new status, the summary with --summary-add appended, and the tables of
     this exam under `version_tables` (file, old arm, new arm, run). The row's `tables` stay: they are the last
     measurement against the stock pilot, of the earlier version, and the status has to say so;
  4. checks that the tables file is this deck's, has the two arms, and prints their wins.

It decides nothing and writes no prose of its own. Afterwards: `python3 -I runner/bots.py`, the candidate's row in
playbook/variants/README.md, DESIGN, CLAUDE.md.
"""
import argparse
import datetime as dt
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


def rules(pb):
    c = pb.get("cast") or []
    return c["rules"] if isinstance(c, dict) else c


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("name")
    ap.add_argument("--tables", required=True)
    ap.add_argument("--old-arm", default="shipped")
    ap.add_argument("--new-arm")
    ap.add_argument("--run", required=True)
    ap.add_argument("--status", required=True)
    ap.add_argument("--summary-add")
    ap.add_argument("--note", required=True)
    ap.add_argument("--on", default=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--attack-changes", action="store_true",
                    help="the candidate's attack block is the change (a `finish` candidate): do not refuse it for differing from the shipped one")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    new_arm = a.new_arm or a.name

    dpath = os.path.join(ROOT, "playbook", "precons", f"{a.deck}.json")
    data = load(dpath)
    old = data.get("playbook")
    if not old:
        raise SystemExit(f"{a.deck} has no shipped playbook: ship_candidate.py is the tool for a first one")
    var = load(os.path.join(ROOT, "playbook", "variants", f"{a.deck}-{a.name}.json"))
    pb = dict(var["playbook"])
    if pb.get("version") != old.get("version", 0) + 1:
        raise SystemExit(f"the candidate is version {pb.get('version')}, the shipped playbook version {old.get('version')}")
    if pb.get("attack") != old.get("attack") and not a.attack_changes:
        raise SystemExit("the candidate's attack block is not the shipped one (--attack-changes when that is the change)")
    notes = pb.get("notes")
    notes = (notes + [a.note]) if isinstance(notes, list) else ((notes + " " if notes else "") + a.note)
    shipped = {k: v for k, v in pb.items() if k not in ("notes", "on")}
    shipped["notes"] = notes
    shipped["on"] = a.on

    tpath = a.tables if os.path.isabs(a.tables) else os.path.join(ROOT, a.tables)
    t = load(tpath)
    if t.get("deck") != a.deck:
        raise SystemExit(f"{a.tables} is a run of {t.get('deck')}, not of {a.deck}")
    for arm in (a.old_arm, new_arm):
        if arm not in t["arm_stats"]:
            raise SystemExit(f"{a.tables} has no arm {arm} (it has {list(t['arm_stats'])})")
    ot, nt = t["arm_stats"][a.old_arm], t["arm_stats"][new_arm]
    pair = (t.get("paired") or {}).get(f"{new_arm}_vs_{a.old_arm}") or {}
    print(f"{a.deck}: {new_arm} {nt['wins']} of {nt['games']} against {a.old_arm} {ot['wins']} of {ot['games']}"
          + (f"; {pair['difference'] * 100:+.1f} points ({pair['difference_ci95'][0] * 100:+.0f} to {pair['difference_ci95'][1] * 100:+.0f}), exact test {pair['exact_p']:.4f}" if pair else ""))

    bots_path = os.path.join(ROOT, "playbook", "bots.json")
    bots = load(bots_path)
    idx = [i for i, r in enumerate(bots["bots"]) if r["deck"] == a.deck]
    if not idx:
        raise SystemExit(f"playbook/bots.json has no row for {a.deck}")
    row = bots["bots"][idx[0]]
    row["status"] = a.status
    if a.summary_add:
        row["summary"] = row["summary"].rstrip() + " " + a.summary_add
    row["version_tables"] = {"file": os.path.relpath(tpath, ROOT), "stock": a.old_arm, "bot": new_arm, "run": a.run}
    kept = [r for r in rules(old) if r in rules(shipped)]
    print(f"playbook/precons/{a.deck}.json: playbook version {shipped['version']} (was {old.get('version')}), {len(rules(shipped))} cast rules "
          f"({len(kept)} of the {len(rules(old))} shipped rules kept as they were), {len(shipped.get('triggers') or [])} trigger rules, "
          f"attack {json.dumps(shipped.get('attack')) if shipped.get('attack') else 'left to Forge'}, on {a.on}")
    if a.dry_run:
        print("dry run: nothing written")
        return 0
    data["playbook"] = shipped
    dump(dpath, data)
    dump(bots_path, bots)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
