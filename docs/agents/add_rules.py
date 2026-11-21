#!/usr/bin/env python3
"""add_rules.py DECK NAME --at N --rules JSON --note TEXT [--attack JSON] [--groups JSON] [--on DATE]: a candidate that is
a deck's shipped playbook with cast rules added. A session helper.

playbook/variants/DECK-NAME.json: the shipped playbook of playbook/precons/DECK.json, its version plus one, with the rules of
--rules (a JSON list of cast rules, playbook/README.md) put in before the shipped rule number N (1-based, as the rule trace
and the counters number them; N one past the last rule appends). With --attack (a JSON object) those keys are set on the
attack block as well; a playbook that leaves the attack to Forge gets `{"policy": "forge", ...}`, Forge's own attack followed
by what the keys ask for. With --groups (a JSON object of named card lists) those are added to `cast.groups`, for a
`hand:<group>` condition. Nothing else is changed; the notes are the shipped notes with --note at the end, which should say
what the rules are for and what they were tried on.
"""
import argparse, copy, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("name")
    ap.add_argument("--at", type=int, required=True)
    ap.add_argument("--rules", required=True)
    ap.add_argument("--note", required=True)
    ap.add_argument("--attack")
    ap.add_argument("--groups")
    ap.add_argument("--on", default="")
    a = ap.parse_args(argv)
    base = json.load(open(os.path.join(ROOT, "playbook", "precons", f"{a.deck}.json"), encoding="utf-8"))["playbook"]
    new = json.loads(a.rules)
    if not isinstance(new, list) or not new or not all(isinstance(r, dict) for r in new):
        ap.error("--rules is a JSON list of cast rules")
    rules = base["cast"]["rules"]
    if not 1 <= a.at <= len(rules) + 1:
        ap.error(f"--at is between 1 and {len(rules) + 1}")
    pb = copy.deepcopy(base)
    pb["version"] = base["version"] + 1
    pb["cast"]["rules"] = rules[:a.at - 1] + new + rules[a.at - 1:]
    pb.pop("on", None)
    attack_note = ""
    if a.groups:
        groups = json.loads(a.groups)
        if not isinstance(groups, dict) or not groups:
            ap.error("--groups is a JSON object of named card lists")
        pb["cast"] = {"groups": {**(base["cast"].get("groups") or {}), **groups}, **{k: v for k, v in pb["cast"].items() if k != "groups"}}
    if a.attack:
        extra = json.loads(a.attack)
        if not isinstance(extra, dict) or not extra:
            ap.error("--attack is a JSON object of attack keys")
        attack = dict(base.get("attack") or {"policy": "forge"})
        attack.update(extra)
        pb = {"version": pb["version"], "attack": attack, **{k: v for k, v in pb.items() if k not in ("version", "attack")}}
        attack_note = f" and {json.dumps(extra)} set on its attack ({'its own attack' if base.get('attack') else 'Forge\'s own attack'} is declared first)"
    n = len(new)
    pb["notes"] = ((base.get("notes") or "") + f" VERSION {pb['version']} CANDIDATE `{a.name}`{' (' + a.on + ')' if a.on else ''}. Version {base['version']} with "
                   f"{'one cast rule' if n == 1 else str(n) + ' cast rules'} added as rule{'s' if n > 1 else ''} {a.at}{' to ' + str(a.at + n - 1) if n > 1 else ''}"
                   f" (the shipped rules from {a.at} on move down by {n}){attack_note}; nothing else is changed. " + a.note.strip())
    out = {"schema": 1, "deck": a.deck, "variant": a.name, "of": f"playbook/precons/{a.deck}.json (version {base['version']})",
           "about": "A candidate playbook for ab-run (deck@variant) and runner/ab.py --data: the shipped playbook with cast rules added (docs/agents/add_rules.py). Only the playbook object is read.",
           "playbook": pb}
    p = os.path.join(ROOT, "playbook", "variants", f"{a.deck}-{a.name}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"{p}: version {pb['version']}, {len(pb['cast']['rules'])} cast rules, new at {a.at}: {json.dumps(new)}" + (f", attack {json.dumps(pb.get('attack'))}" if a.attack else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
