#!/usr/bin/env python3
"""keep_before.py DECK [DECK ...] [--name before] [--on DATE]: the shipped playbook kept as a candidate file, before a next
version replaces it. A session helper.

playbook/variants/DECK-NAME.json: the playbook object of playbook/precons/DECK.json exactly as it is shipped now, so that a
confirming run can play the version before beside the next one on the same tables (`deck@before` and `deck` in an ab-run
request). Run it before the next version is shipped; it refuses to overwrite a file of another version.
"""
import argparse, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("decks", nargs="+")
    ap.add_argument("--name", default="before")
    ap.add_argument("--on", default="")
    a = ap.parse_args(argv)
    for deck in a.decks:
        pb = json.load(open(os.path.join(ROOT, "playbook", "precons", f"{deck}.json"), encoding="utf-8"))["playbook"]
        p = os.path.join(ROOT, "playbook", "variants", f"{deck}-{a.name}.json")
        if os.path.exists(p):
            old = json.load(open(p, encoding="utf-8"))["playbook"]
            if old.get("version") != pb.get("version"):
                raise SystemExit(f"{p} holds version {old.get('version')}; the shipped playbook is version {pb.get('version')}")
        out = {"schema": 1, "deck": deck, "variant": a.name, "of": f"playbook/precons/{deck}.json (version {pb['version']})",
               "about": f"The playbook as it was shipped until {a.on or 'the next version'} (version {pb['version']}), kept so that a confirming run can play it beside the next version on the same tables (docs/agents/keep_before.py). Only the playbook object is read.",
               "playbook": pb}
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"{p}: version {pb['version']}, {len(pb['cast']['rules'])} cast rules, attack {json.dumps(pb.get('attack')) if pb.get('attack') else 'left to Forge'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
