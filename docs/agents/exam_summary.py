#!/usr/bin/env python3
"""Read an exam's rollups, join the side arms and print what there is to decide. A session helper, not pipeline code.

    python3 -I docs/agents/exam_summary.py ROLLUPS_DIR [ROLLUPS_DIR ...] [--out demo-data/ab/<date>-ab-vNN]

ROLLUPS_DIR is an unzipped `ab-rollups` artifact of ab-run: one `ab-<deck>/rollup.json` or
`ab-<deck>@<variant>/rollup.json` per request. With --out every rollup is copied there as `<deck>.json` or
`<deck>-<variant>.json`, and for each deck whose rollups share a seed the arms are lined up on the same tables with
`runner/ab.py join` (written as `<deck>-join.json`):

  <deck>@<v> (stock,playbook) + <deck>@<v>-forgeattack (playbook)   -> stock, gowide, forgeattack
  <deck> (stock,playbook) + <deck>@<v> (playbook)                    -> stock, shipped, <v>
  <deck> (playbook) + <deck>@<v> (playbook)                          -> shipped, <v>

Prints one block a deck: wins of the tables played for each arm, and each paired difference with its interval and
the exact test on the discordant pairs. It decides nothing.
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def arm_line(name, a):
    lo, hi = a["win_rate_ci95"]
    return (f"    {name:<12} {a['wins']:>3} of {a['games']}  {a['win_rate'] * 100:5.1f}%  ({lo * 100:.0f} to {hi * 100:.0f})"
            f"   {a.get('avg_turns', 0):.1f} turns, {a.get('draws', 0)} not finished")


def pair_line(name, p):
    a, b = name.split("_vs_")
    lo, hi = p["difference_ci95"]
    return (f"    {a} on {b}: {p['difference'] * 100:+.1f} points ({lo * 100:+.0f} to {hi * 100:+.0f}), "
            f"{p[a + '_only']} against {p[b + '_only']} of the discordant tables, exact test {p['exact_p']:.4f}"
            f" ({p['pairs']} pairs, {p['identical_outcomes']} with the same outcome)")


def block(title, r):
    print(f"\n{title}  seed {r.get('seed')}  pool {r.get('pool')}  {r.get('forge_version')}")
    for arm, a in r["arm_stats"].items():
        print(arm_line(arm, a))
    for name, p in (r.get("paired") or {}).items():
        print(pair_line(name, p))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    found = {}                                       # (deck, variant or None) -> path
    for d in a.dirs:
        for p in sorted(glob.glob(os.path.join(d, "**", "rollup.json"), recursive=True)):
            name = os.path.basename(os.path.dirname(p))
            if not name.startswith("ab-"):
                continue
            deck, _, variant = name[3:].partition("@")
            found[(deck, variant or None)] = p
    if not found:
        raise SystemExit("no ab-*/rollup.json under " + ", ".join(a.dirs))
    if a.out:
        os.makedirs(a.out, exist_ok=True)
    dest = {}
    for (deck, variant), p in sorted(found.items(), key=lambda kv: (kv[0][0], kv[0][1] or "")):
        r = load(p)
        block(f"{deck}{'@' + variant if variant else ''}", r)
        if a.out:
            dest[(deck, variant)] = os.path.join(a.out, f"{deck}{'-' + variant if variant else ''}.json")
            shutil.copyfile(p, dest[(deck, variant)])
    for deck in sorted({d for d, _ in found}):
        mine = {v: load(p) for (d, v), p in found.items() if d == deck}
        paths = {v: (dest.get((deck, v)) or found[(deck, v)]) for v in mine}
        spec = None
        fa = [v for v in mine if v and v.endswith("-forgeattack") and v[:-len("-forgeattack")] in mine]
        cands = [v for v in mine if v and not v.endswith("-forgeattack")]
        if fa:
            base = fa[0][:-len("-forgeattack")]
            if mine[base]["seed"] == mine[fa[0]]["seed"] and "stock" in mine[base]["arm_stats"]:
                spec = ["--against", "gowide", f"stock={paths[base]}:stock", f"gowide={paths[base]}:playbook", f"forgeattack={paths[fa[0]]}:playbook"]
        elif None in mine and cands:
            same = [v for v in cands if mine[v]["seed"] == mine[None]["seed"]]
            if same:
                arms = ([f"stock={paths[None]}:stock"] if "stock" in mine[None]["arm_stats"] else []) + [f"shipped={paths[None]}:playbook"]
                arms += [f"{v}={paths[v]}:playbook" for v in sorted(same)]
                spec = (["--against", "shipped"] if len(arms) > 2 else []) + arms
        if not spec:
            continue
        out = os.path.join(a.out or os.path.dirname(found[(deck, None)] if (deck, None) in found else list(paths.values())[0]), f"{deck}-join.json")
        cmd = [sys.executable, "-I", os.path.join(ROOT, "runner", "ab.py"), "join", "--out", out] + spec
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"\n{deck}: join failed: {res.stderr.strip()[-400:]}")
            continue
        block(f"{deck} joined ({os.path.relpath(out, ROOT) if out.startswith(ROOT) else out})", load(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
