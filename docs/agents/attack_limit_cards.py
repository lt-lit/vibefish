#!/usr/bin/env python3
"""attack_limit_cards.py --runtime forge/runtime-snapshot LEAGUE.json...: the cards of a table's decks that limit or tax attacks and blocks. A session helper.

For every deck of the league files given, the cards whose Forge script has a static ability that limits how many creatures may
attack or block (`Mode$ AttackRestrict`, `BlockRestrict`), taxes an attack or a block (`CantAttackUnless`, `CantBlockUnless`) or
forbids one (`CantAttack`). Read it before `runner/mistakes.py` is used at a table it has not counted: the `combat` line's damage
"sure to get through" knows what one creature may do and what an attack costs, and not a limit on the number of attackers. On
2026-11-22 a third of the pool's "winning kills not taken" were turns under Planeswalker Party's Silent Arbiter (DESIGN.md section
36); the cards with `AttackRestrict` are in mistakes.py's ATTACK_LIMITS, and a new one found here goes there.
"""
import argparse, json, os, re, sys, zipfile

PAT = re.compile(r"Mode\$ (AttackRestrict|CantAttackUnless|BlockRestrict|CantBlockUnless|CantAttack\b)")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('leagues', nargs='+')
    ap.add_argument('--runtime', default='forge/runtime-snapshot')
    a = ap.parse_args(argv)
    z = zipfile.ZipFile(os.path.join(a.runtime, 'res', 'cardsfolder', 'cardsfolder.zip'))
    names = set(z.namelist())

    def script(name):
        key = re.sub(r"[^a-z0-9]+", "_", name.split('|')[0].strip().lower().replace("'", "")).strip('_')
        p = f'{key[0]}/{key}.txt' if key else ''
        return z.read(p).decode('utf-8') if p in names else None

    missing = []
    for lf in a.leagues:
        for d in json.load(open(lf, encoding='utf-8'))['decks']:
            hits = []
            for line in open(os.path.join(a.runtime, 'res', 'quest', 'commanderprecons', d['file']), encoding='utf-8'):
                m = re.match(r"^\d+\s+(.+)$", line.strip())
                if not m:
                    continue
                sc = script(m.group(1))
                if sc is None:
                    missing.append(m.group(1).split('|')[0])
                    continue
                hits += [(m.group(1).split('|')[0], l[:240]) for l in sc.split('\n') if l.startswith('S:') and PAT.search(l)]
            if hits:
                print(d['id'])
                for n, l in hits:
                    print(f'    {n} :: {l}')
    print(f'{len(missing)} card names without a script under their plain name (accents, split cards): {", ".join(sorted(set(missing))[:14])}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
