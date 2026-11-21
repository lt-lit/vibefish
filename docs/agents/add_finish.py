#!/usr/bin/env python3
"""add_finish.py DECK [DECK ...] [--name NAME] [--finish true|leader|none] [--guard one|table]: a candidate that is a deck's shipped
playbook with a hook on its attack. A session helper.

For each deck, playbook/variants/DECK-NAME.json: the shipped playbook of playbook/precons/DECK.json, its version plus one,
with the hooks asked for on its attack block; a playbook that leaves the attack to Forge (no attack block) gets
`{"policy": "forge", ...}`, which is Forge's own attack followed by the hooks (playbook/README.md). `--finish true` (the default)
is the kill no block prevents, of any opponent (harness 0.4.0); `--finish leader` takes it only from the most dangerous opponent
down (0.4.1); `--finish none` leaves it out. `--guard one` adds the guard against dying tapped out to one opponent, `--guard table`
the same against the opponents one after another (0.4.1). NAME defaults to `finish`, `leader`, `guard`, `table`, `leaderguard` or
`leadertable` by what is asked. Nothing else is changed, and the notes are the shipped notes with
what the candidate is at the end.
"""
import argparse, copy, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("decks", nargs="+")
    ap.add_argument("--name")
    ap.add_argument("--finish", choices=["true", "leader", "none"], default="true")
    ap.add_argument("--guard", choices=["one", "table"])
    ap.add_argument("--on", default="")
    a = ap.parse_args(argv)
    if a.finish == "none" and not a.guard:
        ap.error("nothing to add: --finish none without --guard")
    if not a.name:
        a.name = {"true": "finish", "leader": "leader", "none": ""}[a.finish] + {"one": "guard", "table": "table", None: ""}[a.guard]
    for deck in a.decks:
        base = json.load(open(os.path.join(ROOT, "playbook", "precons", f"{deck}.json"), encoding="utf-8"))["playbook"]
        pb = copy.deepcopy(base)
        attack = dict(pb.get("attack") or {"policy": "forge"})
        if attack.get("finish") or attack.get("guard"):
            print(f"{deck}: the shipped playbook already has a hook on its attack ({json.dumps(attack)}); nothing written")
            continue
        if a.finish != "none":
            attack["finish"] = True if a.finish == "true" else "leader"
        if a.guard:
            attack["guard"] = True if a.guard == "one" else "table"
        what = []
        if a.finish == "true":
            what.append("an opponent the seat is sure to kill is killed (`finish`: enough attackers are put on it that the damage reaches its life whatever it blocks, "
                        "the opponent that looks most dangerous first)")
        elif a.finish == "leader":
            what.append("a sure kill is taken from the most dangerous opponent down (`\"finish\": \"leader\"`: enough attackers are put on the opponent that looks most dangerous "
                        "that the damage reaches its life whatever it blocks, then on the next one, and no weaker opponent is killed while a more dangerous one lives)")
        if a.guard == "one":
            what.append("attackers are taken back when the attack leaves the seat where one opponent alone is sure to kill it before its next turn and keeping them home "
                        "prevents that (`guard`; a sure kill's attackers stay, and an attack stands when nothing kept home would save the seat)")
        elif a.guard == "table":
            what.append("attackers are taken back when the attack leaves the seat where the opponents one after another are sure to kill it before its next turn and keeping "
                        "them home prevents that, or, when nothing kept home does, where one opponent alone is (`\"guard\": \"table\"`; a sure kill's attackers stay, and an "
                        "attack stands when nothing kept home would save the seat)")
        # the attack block goes where a reader looks for it: after the version
        out_pb = {"version": base["version"] + 1, "attack": attack}
        out_pb.update({k: v for k, v in pb.items() if k not in ("version", "attack", "on", "notes")})
        was = "its own attack (" + base["attack"].get("policy", "go_wide") + ")" if base.get("attack") else "Forge's own attack"
        out_pb["notes"] = ((base.get("notes") or "") + f" VERSION {out_pb['version']} CANDIDATE `{a.name}`{' (' + a.on + ')' if a.on else ''}. Version {base['version']} with "
                           f"{'one change' if len(what) == 1 else 'two changes'}: after {was} has been declared, {'; and then '.join(what)}. No cast or trigger rule is changed.")
        out = {"schema": 1, "deck": deck, "variant": a.name, "of": f"playbook/precons/{deck}.json (version {base['version']})",
               "about": "A candidate playbook for ab-run (deck@variant) and runner/ab.py --data: the shipped playbook with a hook on its attack (docs/agents/add_finish.py; DESIGN.md section 34). Only the playbook object is read.",
               "playbook": out_pb}
        p = os.path.join(ROOT, "playbook", "variants", f"{deck}-{a.name}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"{p}: version {out_pb['version']}, attack {json.dumps(attack)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
