#!/usr/bin/env python3
"""add_finish.py DECK [DECK ...] [--name NAME] [--finish true|leader|none] [--guard one|table] [--targets danger] [--block survive]: a
candidate that is a deck's shipped playbook with a hook on its attack, its triggers' targets or its blocks. A session helper.

For each deck, playbook/variants/DECK-NAME.json: the shipped playbook of playbook/precons/DECK.json, its version plus one,
with the hooks asked for on its attack block; a playbook that leaves the attack to Forge (no attack block) gets
`{"policy": "forge", ...}`, which is Forge's own attack followed by the hooks (playbook/README.md). `--finish true` (the default)
is the kill no block prevents, of any opponent (harness 0.4.0); `--finish leader` takes it only from the most dangerous opponent
down (0.4.1); `--finish none` leaves it out. `--guard one` adds the guard against dying tapped out to one opponent, `--guard table`
the same against the opponents one after another (0.4.1). NAME defaults to `finish`, `leader`, `guard`, `table`, `leaderguard` or
`leadertable` by what is asked. `--targets danger` adds `"targets": {"triggers": "danger"}`: the seat's removal triggers are aimed
at the opponent that looks most dangerous (0.4.2); with `--finish none` and no guard the attack is left as it is and NAME defaults
to `aim`. `--block survive` adds `"block": {"survive": true}`: blocks are added to Forge's own when those leave the seat dead
and blocks exist that would not (0.4.3); alone its NAME defaults to `block`. Nothing else is changed, and the notes are the shipped notes with
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
    ap.add_argument("--targets", choices=["danger"])
    ap.add_argument("--block", choices=["survive"])
    ap.add_argument("--on", default="")
    a = ap.parse_args(argv)
    if a.finish == "none" and not a.guard and not a.targets and not a.block:
        ap.error("nothing to add: --finish none without --guard, --targets or --block")
    if not a.name:
        a.name = {"true": "finish", "leader": "leader", "none": ""}[a.finish] + {"one": "guard", "table": "table", None: ""}[a.guard] + ("aim" if a.targets else "") + ("block" if a.block else "")
    for deck in a.decks:
        base = json.load(open(os.path.join(ROOT, "playbook", "precons", f"{deck}.json"), encoding="utf-8"))["playbook"]
        pb = copy.deepcopy(base)
        attack = dict(pb.get("attack") or {"policy": "forge"})
        if (attack.get("finish") and a.finish != "none") or (attack.get("guard") and a.guard) or (pb.get("targets") and a.targets) or (pb.get("block") and a.block):
            print(f"{deck}: the shipped playbook already has that hook (attack {json.dumps(attack)}, targets {json.dumps(pb.get('targets'))}); nothing written")
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
        if a.targets:
            what.append("a triggered ability of the seat that removes one permanent of an opponent (destroys it, exiles it, returns it to hand or library) is aimed at the "
                        "opponent that looks most dangerous, when that opponent looks more dangerous than the one Forge aimed at by five or more and has a permanent of the "
                        "same kind worth at least as much as Forge's choice or at least 4 (`\"targets\": {\"triggers\": \"danger\"}`)")
        if a.block:
            what.append("when Forge's blocks leave at least the seat's life in damage unblocked and blocks exist that would not, blocks are added, the least valuable free "
                        "creatures in front of the heaviest unblocked attackers and only as many as it takes for the seat to live (`\"block\": {\"survive\": true}`)")
        # the attack block goes where a reader looks for it: after the version
        touches_attack = a.finish != "none" or bool(a.guard)
        out_pb = {"version": base["version"] + 1}
        if touches_attack or base.get("attack"):
            out_pb["attack"] = attack if touches_attack else base["attack"]
        if a.targets:
            out_pb["targets"] = {"triggers": a.targets}
        if a.block:
            out_pb["block"] = {"survive": True}
        out_pb.update({k: v for k, v in pb.items() if k not in ("version", "attack", "targets", "block", "on", "notes")})
        was = "its own attack (" + base["attack"].get("policy", "go_wide") + ")" if base.get("attack") else "Forge's own attack"
        out_pb["notes"] = ((base.get("notes") or "") + f" VERSION {out_pb['version']} CANDIDATE `{a.name}`{' (' + a.on + ')' if a.on else ''}. Version {base['version']} with "
                           f"{['', 'one change', 'two changes', 'three changes', 'four changes'][len(what)]}: " + (f"after {was} has been declared, " if touches_attack else "")
                           + f"{'; and then '.join(what)}. No cast or trigger rule is changed.")
        out = {"schema": 1, "deck": deck, "variant": a.name, "of": f"playbook/precons/{deck}.json (version {base['version']})",
               "about": "A candidate playbook for ab-run (deck@variant) and runner/ab.py --data: the shipped playbook with a hook on its attack (docs/agents/add_finish.py; DESIGN.md section 34). Only the playbook object is read.",
               "playbook": out_pb}
        p = os.path.join(ROOT, "playbook", "variants", f"{deck}-{a.name}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"{p}: version {out_pb['version']}, attack {json.dumps(out_pb.get('attack'))}, targets {json.dumps(out_pb.get('targets'))}, block {json.dumps(out_pb.get('block'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
