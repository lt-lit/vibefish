#!/usr/bin/env python3
"""add_finish.py DECK [DECK ...] [--name finish]: a candidate that is a deck's shipped playbook with `finish` on its attack. A session helper.

For each deck, playbook/variants/DECK-NAME.json: the shipped playbook of playbook/precons/DECK.json, its version plus one,
with `"finish": true` on its attack block; a playbook that leaves the attack to Forge (no attack block) gets
`{"policy": "forge", "finish": true}`, which is Forge's own attack followed by the kill (harness 0.4.0, playbook/README.md).
Nothing else is changed, and the notes are the shipped notes with what the candidate is at the end.
"""
import argparse, copy, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("decks", nargs="+")
    ap.add_argument("--name", default="finish")
    ap.add_argument("--on", default="")
    a = ap.parse_args(argv)
    for deck in a.decks:
        base = json.load(open(os.path.join(ROOT, "playbook", "precons", f"{deck}.json"), encoding="utf-8"))["playbook"]
        pb = copy.deepcopy(base)
        attack = dict(pb.get("attack") or {"policy": "forge"})
        if attack.get("finish"):
            print(f"{deck}: the shipped playbook already takes the kill; nothing written")
            continue
        attack["finish"] = True
        # the attack block goes where a reader looks for it: after the version
        out_pb = {"version": base["version"] + 1, "attack": attack}
        out_pb.update({k: v for k, v in pb.items() if k not in ("version", "attack", "on", "notes")})
        was = "its own attack (" + base["attack"].get("policy", "go_wide") + ")" if base.get("attack") else "Forge's own attack"
        out_pb["notes"] = ((base.get("notes") or "") + f" VERSION {out_pb['version']} CANDIDATE `{a.name}`{' (' + a.on + ')' if a.on else ''}. Version {base['version']} with one change: "
                           f"after {was} has been declared, an opponent the seat is sure to kill is killed (`finish`: enough attackers are put on it that the damage reaches its "
                           f"life whatever it blocks, the opponent that looks most dangerous first). No cast or trigger rule is changed.")
        out = {"schema": 1, "deck": deck, "variant": a.name, "of": f"playbook/precons/{deck}.json (version {base['version']})",
               "about": "A candidate playbook for ab-run (deck@variant) and runner/ab.py --data: the shipped playbook with `finish` on its attack (docs/agents/add_finish.py; DESIGN.md section 34). Only the playbook object is read.",
               "playbook": out_pb}
        p = os.path.join(ROOT, "playbook", "variants", f"{deck}-{a.name}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"{p}: version {out_pb['version']}, attack {json.dumps(attack)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
