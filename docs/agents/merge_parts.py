#!/usr/bin/env python3
"""merge_parts.py DECK --name NAME --parts A,B,C [--on DATE] [--allow-remove] [--dry-run]: a deck's next version put
together from candidates that are each the shipped playbook with one change of any kind. A session helper.

docs/agents/next_version.py does this for candidates that put cast rules in and for the six hooks. Since harness 0.4.14
a candidate can differ from the shipped playbook in other places: a key on the cast block (`keep_life`,
`bounce_lands`), a block in `targets` (`counters`, `types`), a cast rule changed where it stands (a `take` block, a
hold without its condition), a trigger rule added. This helper takes each part's difference from the shipped playbook
as it finds it and applies all of them to the shipped playbook:

  playbook/variants/DECK-NAME.json = playbook/precons/DECK.json's playbook, its version plus one, with, for every part
  (playbook/variants/DECK-PART.json): every key the part added or changed in a block (cast, targets, attack, block, ...),
  and in every list of rules (cast.rules, triggers) every rule the part put in, at the place it has there, and every
  rule the part changed, in the place of the shipped rule.

It refuses: a part that is not written against the shipped version (its `playbook.version` is not the shipped version
plus one); two parts that change the same key or the same rule differently; a part that takes a key or a rule away,
unless --allow-remove. Rules two parts put in at the same place go in the order the parts are named.

It checks itself: each part's difference applied alone to the shipped playbook gives that part's playbook again. It
prints every change with the part it came from, and for a rule the rules on either side of it, to be read against the
candidate files (the rule of the exams: put in by hand and read). The notes are the shipped notes, then what the version is
made of, then each part's own account (the tail of its notes after the shipped notes, or its `about`).

It decides nothing: what goes in is what the exams' rules let through (CLAUDE.md, In flight).
"""
import argparse, copy, datetime as dt, difflib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
META = ('version', 'notes', 'on')


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def key(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def short(r, n=170):
    s = json.dumps(r, ensure_ascii=False)
    return s if len(s) <= n else s[:n - 3] + '...'


def rule_list(x):
    return isinstance(x, list) and all(isinstance(e, dict) for e in x)


def diff(base, cand, path=()):
    """The part's changes as operations on the shipped playbook: set/del on a key, ins/repl/rm on a list of rules."""
    ops = []
    if isinstance(base, dict) and isinstance(cand, dict):
        for k in cand:
            if not path and k in META:
                continue
            if k not in base:
                ops.append(('set', path + (k,), cand[k]))
            elif key(base[k]) != key(cand[k]):
                if (isinstance(base[k], dict) and isinstance(cand[k], dict)) or (rule_list(base[k]) and rule_list(cand[k])):
                    ops += diff(base[k], cand[k], path + (k,))
                else:
                    ops.append(('set', path + (k,), cand[k]))
        for k in base:
            if k not in cand and not (not path and k in META):
                ops.append(('del', path + (k,), None))
    else:                                                    # two lists of rules
        sm = difflib.SequenceMatcher(None, [key(x) for x in base], [key(x) for x in cand], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                continue
            if tag == 'insert':
                ops.append(('ins', path, i1, cand[j1:j2]))
            elif tag == 'delete':
                ops.append(('rm', path, i1, i2))
            elif i2 - i1 == j2 - j1:                         # the same number of rules: each changed where it stands
                for d in range(i2 - i1):
                    ops.append(('repl', path, i1 + d, cand[j1 + d]))
            else:                                            # a changed rule beside rules put in: the first ones change, the rest go in after
                n = min(i2 - i1, j2 - j1)
                for d in range(n):
                    ops.append(('repl', path, i1 + d, cand[j1 + d]))
                if j2 - j1 > n:
                    ops.append(('ins', path, i1 + n, cand[j1 + n:j2]))
                if i2 - i1 > n:
                    ops.append(('rm', path, i1 + n, i2))
    return ops


def get(obj, path):
    for k in path:
        obj = obj[k]
    return obj


def apply(base, named_ops, allow_remove=False, say=None):
    """named_ops: [(part, op)] in the order the parts are named. Returns the new playbook; raises SystemExit on a conflict."""
    out = copy.deepcopy(base)
    sets, lists = {}, {}
    for part, op in named_ops:
        if op[0] in ('set', 'del'):
            if op[0] == 'del' and not allow_remove:
                raise SystemExit(f"{part}: takes the key {'.'.join(op[1])} away (--allow-remove if that is the change)")
            prev = sets.get(op[1])
            if prev is not None and key(prev[1][2]) != key(op[2]):
                raise SystemExit(f"{part} and {prev[0]} both set {'.'.join(op[1])}, differently")
            sets[op[1]] = (part, op)
        else:
            L = lists.setdefault(op[1], {'ins': {}, 'repl': {}, 'rm': set()})
            if op[0] == 'ins':
                L['ins'].setdefault(op[2], []).append((part, op[3]))
            elif op[0] == 'repl':
                prev = L['repl'].get(op[2])
                if prev is not None and key(prev[1]) != key(op[3]):
                    raise SystemExit(f"{part} and {prev[0]} both change rule {op[2] + 1} of {'.'.join(op[1])}, differently")
                L['repl'][op[2]] = (part, op[3])
            else:
                if not allow_remove:
                    raise SystemExit(f"{part}: takes rules {op[2] + 1} to {op[3]} of {'.'.join(op[1])} away (--allow-remove if that is the change)")
                L['rm'].update(range(op[2], op[3]))
    for path, (part, op) in sets.items():
        parent = get(out, path[:-1])
        if op[0] == 'del':
            parent.pop(path[-1], None)
            if say:
                say(f"  {part}: {'.'.join(path)} taken away")
        else:
            if say:
                was = parent.get(path[-1], None)
                say(f"  {part}: {'.'.join(path)} = {short(op[2])}" + ('' if was is None else f"   (was {short(was, 90)})"))
            parent[path[-1]] = copy.deepcopy(op[2])
    for path, L in lists.items():
        old = get(base, path)
        new = []
        for i in range(len(old) + 1):
            for part, rules in L['ins'].get(i, []):
                for r in rules:
                    new.append(copy.deepcopy(r))
                    if say:
                        say(f"  {part}: a rule put into {'.'.join(path)} as rule {len(new)}, between shipped rules {i} and {i + 1}:")
                        if i > 0:
                            say(f"      above  {short(old[i - 1])}")
                        say(f"      NEW    {short(r, 400)}")
                        if i < len(old):
                            say(f"      below  {short(old[i])}")
            if i == len(old):
                break
            if i in L['rm']:
                if say:
                    say(f"  shipped rule {i + 1} of {'.'.join(path)} taken away: {short(old[i])}")
                continue
            if i in L['repl']:
                part, r = L['repl'][i]
                new.append(copy.deepcopy(r))
                if say:
                    say(f"  {part}: shipped rule {i + 1} of {'.'.join(path)} changed (rule {len(new)} here):")
                    say(f"      was    {short(old[i], 400)}")
                    say(f"      NOW    {short(r, 400)}")
            else:
                new.append(copy.deepcopy(old[i]))
        parent = get(out, path[:-1])
        parent[path[-1]] = new
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('deck')
    ap.add_argument('--name', required=True)
    ap.add_argument('--parts', required=True, help='comma-separated candidate names, in the order their rules go in at a shared place')
    ap.add_argument('--on', default=dt.date.today().isoformat())
    ap.add_argument('--allow-remove', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args(argv)
    shipped_file = os.path.join(ROOT, 'playbook', 'precons', a.deck + '.json')
    shipped = load(shipped_file)
    base = shipped['playbook']
    v = base['version']
    parts = [p for p in a.parts.split(',') if p]
    named, accounts = [], []
    for part in parts:
        f = os.path.join(ROOT, 'playbook', 'variants', f'{a.deck}-{part}.json')
        c = load(f)
        pb = c['playbook']
        if pb.get('version') != v + 1:
            raise SystemExit(f"{part}: its playbook is version {pb.get('version')}, the shipped one is version {v}: not written against the shipped playbook")
        ops = diff(base, pb)
        if not ops:
            raise SystemExit(f"{part}: no different from the shipped playbook")
        alone = apply(base, [(part, op) for op in ops], a.allow_remove)
        if key({k: x for k, x in alone.items() if k not in META}) != key({k: x for k, x in pb.items() if k not in META}):
            raise SystemExit(f"{part}: its difference applied to the shipped playbook does not give its playbook again (a bug here: do it by hand)")
        named += [(part, op) for op in ops]
        notes = pb.get('notes') or ''
        tail = notes[len(base.get('notes') or ''):].strip() if notes.startswith(base.get('notes') or '') and len(notes) > len(base.get('notes') or '') else (c.get('about') or '').strip()
        accounts.append((part, tail))
    print(f"{a.deck}: version {v + 1} = version {v} with {', '.join(parts)}")
    out = apply(base, named, a.allow_remove, say=print)
    out['version'] = v + 1
    out['on'] = a.on
    made = (f" VERSION {v + 1} ({a.on}) = version {v} with {len(parts)} part{'s' if len(parts) != 1 else ''}, each played alone beside version {v} on the same tables "
            f"and never together until the confirming run: {', '.join(parts)}. ")
    out['notes'] = (base.get('notes') or '').rstrip() + made + ' '.join(f"PART {p}: {t}" for p, t in accounts)
    for k in ('cast', 'triggers'):
        b, n = base.get(k), out.get(k)
        nb = len(b['rules']) if isinstance(b, dict) and 'rules' in b else (len(b) if isinstance(b, list) else 0)
        nn = len(n['rules']) if isinstance(n, dict) and 'rules' in n else (len(n) if isinstance(n, list) else 0)
        print(f"  {k}: {nb} rules shipped, {nn} here")
    doc = {'schema': shipped.get('schema'), 'deck': a.deck, 'variant': a.name, 'of': f"playbook/precons/{a.deck}.json (version {v})",
           'about': f"Version {v + 1}: version {v} with the parts {', '.join(parts)} (docs/agents/merge_parts.py), each a candidate that passed the rule of its exam.",
           'playbook': out}
    dest = os.path.join(ROOT, 'playbook', 'variants', f'{a.deck}-{a.name}.json')
    if a.dry_run:
        print(f"  (dry run: {os.path.relpath(dest, ROOT)} not written)")
        return 0
    if os.path.exists(dest):
        raise SystemExit(f"{os.path.relpath(dest, ROOT)} exists: another name, or remove it first")
    with open(dest, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print(f"  wrote {os.path.relpath(dest, ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
