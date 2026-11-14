#!/usr/bin/env python3
"""pool_check.py DECK VARIANT OUT_DIR [--base-commit REV]: three pilots of one deck, card by card. A session helper.

For a candidate (playbook/variants/DECK-VARIANT.json) that extends the deck's shipped playbook and was examined against it
as playbook arms on the same tables: the cards the candidate's rules newly name, with the games cast of the games drawn
under stock AI (demo-data/playtest/2026-11-14/DECK-stock.json: the stock arm of ab-run #26, other tables of the same
pool), under the shipped playbook and under the candidate (OUT_DIR/DECK-shipped.json and OUT_DIR/DECK-VARIANT.json,
`runner/playtest.py --arm playbook --json` reports of the two run directories), then what the candidate casts fifteen
points less or more often than the shipped playbook and than stock AI. Once the candidate has shipped, the playbook it
extended is read from git: --base-commit names a revision that still has it (default: the working tree)."""
import json, os, subprocess, sys
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
args = [a for a in sys.argv[1:] if not a.startswith("--base-commit")]
base_commit = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--base-commit=")), None)
deck, v, out = args[:3]
def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)
def rules(pb):
    c = pb.get("cast") or []
    return c["rules"] if isinstance(c, dict) else c
def named(pb, kinds=("play",)):
    s = []
    for r in rules(pb):
        for k in kinds:
            for c in r.get(k) or []:
                if c not in s:
                    s.append(c)
    return s
shipped_pb = (json.loads(subprocess.run(["git", "-C", R, "show", f"{base_commit}:playbook/precons/{deck}.json"], capture_output=True, text=True, check=True).stdout)
              if base_commit else load(f"{R}/playbook/precons/{deck}.json"))["playbook"]
cand_pb = load(f"{R}/playbook/variants/{deck}-{v}.json")["playbook"]
new_play = [c for c in named(cand_pb) if c not in named(shipped_pb)]
new_act = [c for c in named(cand_pb, ("activate",)) if c not in named(shipped_pb, ("activate",))]
stock = load(f"{R}/demo-data/playtest/2026-11-14/{deck}-stock.json")
sh, ca = load(f"{out}/{deck}-shipped.json"), load(f"{out}/{deck}-{v}.json")
def cell(rep, c):
    x = rep["cards"].get(c)
    return f"{x['played']}/{x['drawn']}" if x else "-"
def held(rep, c):
    x = rep["cards"].get(c)
    return str(x["held_at_loss"]) if x else "-"
print(f"{deck}: stock (#26) {stock['result']['wins']} of {stock['result']['games']}; shipped {sh['result']['wins']} of {sh['result']['games']}; {v} {ca['result']['wins']} of {ca['result']['games']}")
print(f"  rules: shipped {len(rules(shipped_pb))}, {v} {len(rules(cand_pb))}; cards newly named by a play rule: {len(new_play)}; by an activate rule: {new_act}")
print("  card: cast/drawn as stock (#26) | shipped | candidate; in hand at a loss shipped -> candidate")
tot = {"stock": [0, 0], "shipped": [0, 0], "cand": [0, 0]}
for c in new_play:
    print(f"    {c}: {cell(stock, c)} | {cell(sh, c)} | {cell(ca, c)}; {held(sh, c)} -> {held(ca, c)}")
    for k, rep in (("stock", stock), ("shipped", sh), ("cand", ca)):
        x = rep["cards"].get(c)
        if x:
            tot[k][0] += x["played"]; tot[k][1] += x["drawn"]
pct = lambda t: f"{t[0]}/{t[1]} ({100 * t[0] / t[1]:.0f}%)" if t[1] else "-"
print(f"  all newly named cards: stock {pct(tot['stock'])} | shipped {pct(tot['shipped'])} | candidate {pct(tot['cand'])}")
def diff(a, b, la, lb, pts=15, mind=20):
    rows = []
    for c, x in b["cards"].items():
        y = a["cards"].get(c)
        if not y or x["drawn"] < mind or y["drawn"] < mind:
            continue
        d = 100 * ((x["played_share"] or 0) - (y["played_share"] or 0))
        if abs(d) >= pts:
            rows.append((d, c, x, y))
    less = sorted((r for r in rows if r[0] < 0), key=lambda r: r[0])
    more = sorted((r for r in rows if r[0] > 0), key=lambda r: -r[0])
    print(f"  {lb} casts LESS than {la} (15 points or more): " + ("; ".join(f"{c} {y['played']}/{y['drawn']} -> {x['played']}/{x['drawn']}" for d, c, x, y in less) or "nothing"))
    print(f"  {lb} casts more than {la}: " + ("; ".join(f"{c} {y['played']}/{y['drawn']} -> {x['played']}/{x['drawn']}" for d, c, x, y in more) or "nothing"))
diff(sh, ca, "shipped", v)
diff(stock, ca, "stock (#26)", v)
