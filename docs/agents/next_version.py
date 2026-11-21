#!/usr/bin/env python3
"""next_version.py DECK --name NAME [--rules VARIANT]... [--finish leader] [--swing] [--open] [--targets] [--block]
[--add-when 'CARD=CONDITION']... [--on DATE]: a deck's next version put together from the parts that passed their exams.
A session helper.

playbook/variants/DECK-NAME.json: the shipped playbook of playbook/precons/DECK.json, its version plus one, with

  the rules of each --rules VARIANT (playbook/variants/DECK-VARIANT.json, a candidate that is the shipped playbook with
  cast rules put in, as docs/agents/add_rules.py writes them): every rule the candidate has and the shipped playbook has
  not goes in before the shipped rule it stood before in the candidate (or after the last one), several candidates'
  rules at the same place in the order the candidates are named; groups a candidate added to `cast.groups` and keys it
  added to the attack block come along. A candidate that changes anything else is refused;

  the hooks asked for, as docs/agents/add_finish.py writes them: `"finish": "leader"`, `"aim": "danger"` (--swing) and
  `"open": true` on the attack block, `"targets": {"triggers": "danger"}` (--targets), `"block": {"survive": true}`;

  --add-when: one more condition on the rule that plays or activates CARD, for a guard decided after an exam (say so
  where the version is recorded).

The notes are the shipped notes with what the version is at the end: the parts by name, the place of each candidate's
rules in this file, each candidate's own account of its rules (its rule numbers are those of its own file), and what
each hook does. It prints the rule list around every insertion, and checks that taking the inserted rules out again
gives the shipped rule list. It decides nothing: what goes in is what the exams' rules let through (CLAUDE.md).
"""
import argparse, copy, importlib.util, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def short(r):
    s = json.dumps(r, ensure_ascii=False)
    return s if len(s) <= 150 else s[:147] + "..."


def insertions(shipped, variant, what):
    """[(anchor, rule)]: the variant's rules that are not shipped rules, each with the index of the shipped rule it stood before."""
    out, i = [], 0
    for r in variant:
        if i < len(shipped) and r == shipped[i]:
            i += 1
        else:
            out.append((i, r))
    if i != len(shipped):
        raise SystemExit(f"{what}: its rule list is not the shipped list with rules put in (matched {i} of {len(shipped)} shipped rules in order)")
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--name", required=True)
    ap.add_argument("--rules", action="append", default=[])
    ap.add_argument("--finish", choices=["leader"])
    ap.add_argument("--swing", action="store_true")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--targets", action="store_true")
    ap.add_argument("--block", action="store_true")
    ap.add_argument("--add-when", action="append", default=[])
    ap.add_argument("--on", default="")
    a = ap.parse_args(argv)
    sp = importlib.util.spec_from_file_location("add_finish", os.path.join(ROOT, "docs", "agents", "add_finish.py"))
    add_finish = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(add_finish)

    base = load(os.path.join(ROOT, "playbook", "precons", f"{a.deck}.json"))["playbook"]
    shipped_rules = base["cast"]["rules"]
    attack = dict(base["attack"]) if base.get("attack") else None
    groups = dict(base["cast"].get("groups") or {})
    by_anchor = {}
    accounts = []
    for v in a.rules:
        var = load(os.path.join(ROOT, "playbook", "variants", f"{a.deck}-{v}.json"))["playbook"]
        if var["version"] != base["version"] + 1:
            raise SystemExit(f"{a.deck}-{v}: version {var['version']}, the shipped playbook is version {base['version']}")
        for k in set(base) | set(var):
            if k in ("version", "notes", "on", "cast", "attack"):
                continue
            if base.get(k) != var.get(k):
                raise SystemExit(f"{a.deck}-{v}: `{k}` differs from the shipped playbook; put it in by hand")
        for k in set(base["cast"]) | set(var["cast"]):
            if k not in ("rules", "groups") and base["cast"].get(k) != var["cast"].get(k):
                raise SystemExit(f"{a.deck}-{v}: `cast.{k}` differs from the shipped playbook; put it in by hand")
        for g, cards in (var["cast"].get("groups") or {}).items():
            if g in (base["cast"].get("groups") or {}) and base["cast"]["groups"][g] != cards:
                raise SystemExit(f"{a.deck}-{v}: group `{g}` is changed, not added")
            groups[g] = cards
        if var.get("attack") != base.get("attack"):
            va = var.get("attack") or {}
            ba = base.get("attack") or {"policy": "forge"}
            if any(ba.get(k) != va.get(k) for k in ba):
                raise SystemExit(f"{a.deck}-{v}: its attack block changes a shipped key; put it in by hand")
            attack = dict(attack or {"policy": "forge"})
            attack.update({k: x for k, x in va.items() if k not in ba})
        ins = insertions(shipped_rules, var["cast"]["rules"], f"{a.deck}-{v}")
        if not ins:
            raise SystemExit(f"{a.deck}-{v}: no rule of its own")
        for anchor, r in ins:
            by_anchor.setdefault(anchor, []).append((v, r))
        n = var.get("notes") or ""
        i = n.rfind(f"CANDIDATE `{v}`")
        j = n.find("WHY:", i) if i >= 0 else -1
        accounts.append((v, n[j:].strip() if j >= 0 else ""))

    rules, where = [], {}
    for i in range(len(shipped_rules) + 1):
        for v, r in by_anchor.get(i, []):
            rules.append(copy.deepcopy(r))
            where.setdefault(v, []).append(len(rules))
        if i < len(shipped_rules):
            rules.append(copy.deepcopy(shipped_rules[i]))
    added = [r for lst in by_anchor.values() for _, r in lst]
    left = list(rules)
    for r in added:
        left.remove(r)
    if left != shipped_rules:
        raise SystemExit("taking the inserted rules out again does not give the shipped rule list")

    guards = []
    for spec in a.add_when:
        card, cond = spec.split("=", 1)
        hit = [k for k, r in enumerate(rules) if card in (r.get("play") or []) + (r.get("activate") or []) and r in added]
        if len(hit) != 1:
            raise SystemExit(f"--add-when {card}: {len(hit)} inserted rules name it")
        rules[hit[0]]["when"] = list(rules[hit[0]].get("when") or []) + [cond]
        guards.append((card, cond, hit[0] + 1))

    hooks = add_finish.hook_texts("danger" if a.swing else None, a.open, a.finish or "none", None, "danger" if a.targets else None, "survive" if a.block else None)
    touches_attack = bool(a.finish or a.swing or a.open)
    if touches_attack:
        attack = dict(attack or {"policy": "forge"})
        for k in ("aim", "open", "finish"):
            if attack.get(k):
                raise SystemExit(f"the attack block already has `{k}`")
        if a.swing:
            attack["aim"] = "danger"
        if a.open:
            attack["open"] = True
        if a.finish:
            attack["finish"] = a.finish
    if (a.targets and base.get("targets")) or (a.block and base.get("block")):
        raise SystemExit("the shipped playbook already has that hook")

    pb = {"version": base["version"] + 1}
    if attack:
        pb["attack"] = attack
    if a.targets:
        pb["targets"] = {"triggers": "danger"}
    elif base.get("targets"):
        pb["targets"] = base["targets"]
    if a.block:
        pb["block"] = {"survive": True}
    elif base.get("block"):
        pb["block"] = base["block"]
    cast = {}
    if groups:
        cast["groups"] = groups
    cast.update({k: v for k, v in base["cast"].items() if k not in ("groups", "rules")})
    cast["rules"] = rules
    pb["cast"] = cast
    pb.update({k: v for k, v in base.items() if k not in ("version", "attack", "targets", "block", "cast", "on", "notes")})

    def span(ns):
        runs, s = [], None
        for n in ns:
            if s is not None and n == prev + 1:
                prev = n
                continue
            if s is not None:
                runs.append((s, prev))
            s = prev = n
        runs.append((s, prev))
        return " and ".join(f"rule {x}" if x == y else f"rules {x} to {y}" for x, y in runs)

    parts = []
    for v, _ in accounts:
        parts.append(f"the cast rules of the candidate `{v}` ({span(where[v])} of this file)")
    was = "its own attack (" + base["attack"].get("policy", "go_wide") + ")" if base.get("attack") else "Forge's own attack"
    note = f" VERSION {pb['version']}{' (' + a.on + ')' if a.on else ''}, the candidate `{a.name}`: version {base['version']} with what passed its exam, part by part."
    if parts:
        note += " RULES: " + "; ".join(parts) + "."
    if hooks:
        attack_hooks = hooks[:int(a.swing) + int(a.open) + int(bool(a.finish))]
        other_hooks = hooks[len(attack_hooks):]
        note += " HOOKS: " + (f"after {was} has been declared, " + "; and then ".join(attack_hooks) if attack_hooks else "")
        note += ("; " if attack_hooks and other_hooks else "") + "; ".join(other_hooks) + "."
    for card, cond, k in guards:
        note += f" One condition was added to rule {k} ({card}) after its exam: `{cond}`."
    for v, text in accounts:
        if text:
            note += f" FROM THE CANDIDATE `{v}` (its rule numbers are those of its own file, playbook/variants/{a.deck}-{v}.json): {text}"
    pb["notes"] = (base.get("notes") or "") + note

    out = {"schema": 1, "deck": a.deck, "variant": a.name, "of": f"playbook/precons/{a.deck}.json (version {base['version']})",
           "about": "A candidate playbook for ab-run (deck@variant) and runner/ab.py --data: the shipped playbook with every part that passed its exam (docs/agents/next_version.py; DESIGN.md section 34). Only the playbook object is read.",
           "playbook": pb}
    p = os.path.join(ROOT, "playbook", "variants", f"{a.deck}-{a.name}.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"{p}: version {pb['version']}, {len(rules)} cast rules ({len(shipped_rules)} shipped, {len(added)} added), attack {json.dumps(pb.get('attack'))}, "
          f"targets {json.dumps(pb.get('targets'))}, block {json.dumps(pb.get('block'))}, groups {sorted(groups) if groups else 'none'}")
    for v in where:
        for n in where[v]:
            if n >= 2:
                print(f"    {n - 1:>3}  {short(rules[n - 2])}")
            print(f"  + {n:>3}  {short(rules[n - 1])}    <- {v}")
            if n < len(rules):
                print(f"    {n + 1:>3}  {short(rules[n])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
