#!/usr/bin/env python3
"""add_react.py DECK --cards "A,B,..." [--name react] [--lands 3] [--big 6] [--worth 3] [--aim permanent]: a candidate that
plays a deck's instant removal on other players' turns (harness 0.4.12). A session helper.

playbook/variants/DECK-NAME.json: the shipped playbook of playbook/precons/DECK.json, its version plus one, in which the
cards named are
  - taken out of every main-phase `play` rule that names them (a rule left without cards is dropped; each change is printed,
    with the rule it was, so that what the shipped playbook did with the card can be read),
  - held from Forge's AI (`hold`),
  - given their mana through the seat's own turn from LANDS lands on, while the card has a target of the end-step rule's aim on
    the table (`reserve` with that `aim`), so that from then on a card with something to hit is cast within one round of the
    table and no mana is kept for a card with nothing to hit,
  - cast at a creature attacking the seat when the attack is lethal and one removal changes that, or when one removal takes
    BIG damage or more away (`"phase": "defend"`, `"aim": "attacker"`),
  - cast in the end step before the seat's own turn at the most dangerous opponent's best permanent worth WORTH or more that
    the spell can hit (`"phase": "end"`).
Two earlier forms were tried on ten tables each and dropped (DESIGN.md section 39): a main-phase rule for the early game at
the bottom of the rules starved (the cards cast in 71% of the games they were held, the shipped pilots' 93%), and leaving the
early game to Forge left little for the rules (29% of the casts on another player's turn).
Cards have to be single-target instants that can hit a creature (Terminate, Swords to Plowshares, Putrefy, Generous Gift);
a charm, a spell with two targets or an X is not for these rules. Nothing else is changed.
"""
import argparse, copy, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--cards", required=True)
    ap.add_argument("--name", default="react")
    ap.add_argument("--lands", type=int, default=3)
    ap.add_argument("--big", type=int, default=6)
    ap.add_argument("--worth", type=int, default=3)
    ap.add_argument("--aim", default="permanent", help="the kind of permanent the end-step rule aims at")
    a = ap.parse_args(argv)
    cards = [c.strip() for c in a.cards.split(",") if c.strip()]
    src = json.load(open(os.path.join(ROOT, "playbook", "precons", f"{a.deck}.json"), encoding="utf-8"))
    pb = copy.deepcopy(src["playbook"])
    rules = pb["cast"]["rules"]
    kept = []
    for i, r in enumerate(rules, 1):
        if "hold" in r and set(r["hold"]) & set(cards):
            raise SystemExit(f"rule {i} already holds one of the cards: {json.dumps(r)}")
        if "play" in r and set(r["play"]) & set(cards):
            left = [c for c in r["play"] if c not in cards]
            print(f"  rule {i} named {sorted(set(r['play']) & set(cards))}: {json.dumps(r, ensure_ascii=False)[:300]}")
            if not left:
                print("    -> dropped (it named nothing else)")
                continue
            r = dict(r, play=left)
            print(f"    -> kept for {left}")
        kept.append(r)
    kept += [
        {"hold": cards},
        {"reserve": cards, "aim": a.aim, "aim_min": a.worth, "when": [f"lands >= {a.lands}"]},
        {"play": cards, "phase": "defend", "aim": "attacker", "when": ["lethal == 1"]},
        {"play": cards, "phase": "defend", "aim": "attacker", "aim_min": a.big},
        {"play": cards, "phase": "end", "aim": a.aim, "aim_min": a.worth},
    ]
    pb["cast"]["rules"] = kept
    pb["version"] = src["playbook"]["version"] + 1
    pb["notes"] = (src["playbook"].get("notes", "") + f" CANDIDATE {a.name} (harness 0.4.12, docs/agents/add_react.py): version {src['playbook']['version']} with "
                   f"{', '.join(cards)} kept from Forge's AI and played by rules on other players' turns: at a creature attacking the seat when the attack "
                   f"ends its game through its best blocks and one removal changes that, or when one removal takes {a.big} damage or more away; otherwise in the end step before "
                   f"the seat's own turn at the most dangerous opponent's best {a.aim} worth {a.worth} or more that the spell can hit. From {a.lands} lands the mana for one of "
                   f"them is kept through the seat's own turn while it has such a target.")
    out = {"schema": 1, "deck": a.deck, "variant": a.name, "of": f"playbook/precons/{a.deck}.json (version {src['playbook']['version']})",
           "about": "A candidate with rules for other players' turns (docs/agents/add_react.py). Only the playbook object is read.", "playbook": pb}
    p = os.path.join(ROOT, "playbook", "variants", f"{a.deck}-{a.name}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"{p}: version {pb['version']}, {len(kept)} cast rules ({len(rules)} before), cards {cards}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
