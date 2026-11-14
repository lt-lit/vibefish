#!/usr/bin/env python3
"""three_way.py STOCK.json BASE.json NEW.json [--label-base gowide --label-new forge] : the cards BASE casts 15 points less often than stock,
and what NEW does with them; then the counts of cards cast less / more than stock (15 points, 20 games drawn) under BASE and NEW."""
import json, sys, argparse
ap = argparse.ArgumentParser(); ap.add_argument("stock"); ap.add_argument("base"); ap.add_argument("new")
ap.add_argument("--label-base", default="base"); ap.add_argument("--label-new", default="new"); ap.add_argument("--top", type=int, default=8)
a = ap.parse_args()
s, b, n = (json.load(open(p)) for p in (a.stock, a.base, a.new))
def share(x): return (x["played_share"] or 0) * 100
def rows(ref, rep, pts=15, mind=20):
    out = []
    for c, x in rep["cards"].items():
        y = ref["cards"].get(c)
        if not y or x["drawn"] < mind or y["drawn"] < mind: continue
        d = share(x) - share(y)
        if abs(d) >= pts: out.append((d, c))
    return out
rb, rn = rows(s, b), rows(s, n)
less_b = sorted(r for r in rb if r[0] < 0)
print(f"{n['deck']}: wins stock {s['result']['wins']}, {a.label_base} {b['result']['wins']}, {a.label_new} {n['result']['wins']} of {n['result']['games']}")
print(f"  cards cast 15+ points less than stock: {a.label_base} {sum(1 for r in rb if r[0] < 0)}, {a.label_new} {sum(1 for r in rn if r[0] < 0)}; more: {a.label_base} {sum(1 for r in rb if r[0] > 0)}, {a.label_new} {sum(1 for r in rn if r[0] > 0)}")
tot = [[0, 0], [0, 0], [0, 0]]
lines = []
for d, c in less_b:
    cells = []
    for i, rep in enumerate((s, b, n)):
        x = rep["cards"].get(c)
        if x:
            tot[i][0] += x["played"]; tot[i][1] += x["drawn"]; cells.append(f"{x['played']}/{x['drawn']}")
        else: cells.append("-")
    lines.append(f"    {c}: {cells[0]} | {cells[1]} | {cells[2]}")
pct = lambda t: f"{t[0]}/{t[1]} ({100*t[0]/t[1]:.0f}%)" if t[1] else "-"
print(f"  the {len(less_b)} cards {a.label_base} casts less than stock, summed (stock | {a.label_base} | {a.label_new}): {pct(tot[0])} | {pct(tot[1])} | {pct(tot[2])}")
for l in lines[:a.top]: print(l)
still = sorted(r for r in rn if r[0] < 0)
print(f"  still cast less than stock under {a.label_new}: " + "; ".join(f"{c} {s['cards'][c]['played']}/{s['cards'][c]['drawn']} -> {n['cards'][c]['played']}/{n['cards'][c]['drawn']}" for d, c in still[:10]) or "nothing")
rbn = rows(b, n)
print(f"  {a.label_new} against {a.label_base}, cast less: " + ("; ".join(f"{c} {b['cards'][c]['played']}/{b['cards'][c]['drawn']} -> {n['cards'][c]['played']}/{n['cards'][c]['drawn']}" for d, c in sorted(r for r in rbn if r[0] < 0)[:8]) or "nothing"))
t = n.get("tempo") or {}
tb = b.get("tempo") or {}
print("  tempo:", {k: (tb.get(k), t.get(k)) for k in list(t.keys())[:8] if not isinstance(t.get(k), (dict, list))})
