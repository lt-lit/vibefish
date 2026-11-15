#!/usr/bin/env python3
"""named_split.py VARIANT.json STOCK.json FORGE.json FORGEWAIT.json: the three arms' cast shares summed over the cards the
playbook's rules name below the forge rule, the cards named above it, and the cards no rule names (nonland, drawn 20+ games)."""
import json, sys
var, s, b, n = (json.load(open(p)) for p in sys.argv[1:5])
pb = var["playbook"]
rules = pb["cast"]["rules"] if isinstance(pb["cast"], dict) else pb["cast"]
fi = next(i for i, r in enumerate(rules) if "forge" in r)
def names(r):
    out = []
    for k in ("play", "activate", "hold"):
        v = r.get(k)
        if isinstance(v, str): out.append(v)
        elif isinstance(v, list): out += [x for x in v if isinstance(x, str)]
    return out
above = {c for r in rules[:fi] for c in names(r)}
below = {c for r in rules[fi + 1:] for c in names(r)}
held = {c for r in rules for c in ([r["hold"]] if isinstance(r.get("hold"), str) else (r.get("hold") or []))}
groups = {"named above the forge rule": [], "named below the forge rule": [], "no rule names it": []}
for c, x in s["cards"].items():
    if x.get("land"): continue
    key = "named above the forge rule" if c in above else "named below the forge rule" if c in below else "no rule names it"
    groups[key].append(c)
print(f"{n['deck']}: forge rule is rule {fi + 1} of {len(rules)}; named above {len(above)}, below {len(below)}")
for g, cs in groups.items():
    t = [[0, 0] for _ in range(3)]
    for c in cs:
        for i, rep in enumerate((s, b, n)):
            x = rep["cards"].get(c)
            if x: t[i][0] += x["played"]; t[i][1] += x["drawn"]
    f = lambda v: f"{v[0]}/{v[1]} ({100 * v[0] / v[1]:.0f}%)" if v[1] else "-"
    print(f"  {g} ({len(cs)} cards): stock {f(t[0])} | forge {f(t[1])} | forgewait {f(t[2])}")
