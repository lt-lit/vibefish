#!/usr/bin/env python3
"""A variant of a playbook with a `{"forge": "unnamed"}` rule put in mechanically. A session helper.

    python3 -I docs/agents/add_forge_rule.py DECK [--base playbook/variants/DECK-NAME.json] [--name forge]
                                             [--after commander|top|N] [--print]

The base is the deck's shipped playbook (playbook/precons/DECK.json) unless --base names a candidate file. The rule
goes after the first play rule that lists the deck's commander (--after commander, the default; at the top when no
rule does), at the top (--after top) or after rule N of the base. Writes playbook/variants/DECK-<name>.json with the
version one higher and a line in the notes; a base that already has a forge rule is refused.

This is the mechanical remedy for what engine rules crowd out (DESIGN.md section 30): everything the rules do not
name is Forge's to choose at that place instead of after every rule. Where the place should be is a judgement about
the deck; "after the commander" is the uniform choice for trying the remedy on many decks at once.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--base")
    ap.add_argument("--name", default="forge")
    ap.add_argument("--after", default="commander")
    ap.add_argument("--print", action="store_true", help="say where the rule would go and write nothing")
    a = ap.parse_args(argv)
    precon = json.load(open(os.path.join(ROOT, "playbook", "precons", a.deck + ".json"), encoding="utf-8"))
    base_path = a.base or os.path.join("playbook", "precons", a.deck + ".json")
    base = json.load(open(os.path.join(ROOT, base_path) if not os.path.isabs(base_path) else base_path, encoding="utf-8"))
    pb = json.loads(json.dumps(base["playbook"]))
    cast = pb.get("cast")
    if cast is None:
        raise SystemExit(f"{base_path} has no cast rules")
    rules = cast["rules"] if isinstance(cast, dict) else cast
    if any("forge" in r for r in rules):
        raise SystemExit(f"{base_path} already has a forge rule")
    commanders = precon.get("commanders") or []
    if a.after == "top":
        at = 0
    elif a.after == "commander":
        hits = [i for i, r in enumerate(rules) if any(c in (r.get("play") or []) for c in commanders)]
        at = hits[0] + 1 if hits else 0
    else:
        at = int(a.after)
        if not 0 <= at <= len(rules):
            raise SystemExit(f"--after {a.after}: the base has {len(rules)} rules")
    where = "at the top" if at == 0 else f"after rule {at} ({json.dumps(rules[at - 1])[:90]})"
    print(f"{a.deck}: {len(rules)} rules in {base_path}; the forge rule goes {where}")
    if a.print:
        return 0
    rules.insert(at, {"forge": "unnamed"})
    pb["version"] = int(pb.get("version") or 1) + 1
    pb.pop("on", None)
    line = (f"Variant {a.name} (not shipped): the rules of {base_path} unchanged and in their order, with one rule added {where}: "
            "{\"forge\": \"unnamed\"}, Forge's own choice among the plays no rule names, at that place instead of after every rule "
            "(DESIGN.md section 30: engine rules crowd out the cards they do not name). Put in mechanically by docs/agents/add_forge_rule.py; "
            "its place was not chosen for this deck.")
    notes = pb.get("notes")
    pb["notes"] = (notes + [line]) if isinstance(notes, list) else ((notes + " " if notes else "") + line)
    out = {"schema": base.get("schema"), "deck": a.deck, "variant": a.name, "of": base_path,
           "about": f"{base_path} with a forge rule {where}: what the rules do not name is Forge's choice there, not last.",
           "playbook": pb}
    path = os.path.join(ROOT, "playbook", "variants", f"{a.deck}-{a.name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("wrote", os.path.relpath(path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
