#!/usr/bin/env python3
"""verify_shards.py EXAM_DIR --seed SEED [--date YYYY-MM-DD] [--pool NAME] [--tables 200] [--shards 5]: every downloaded
shard directory against its name. A session helper.

EXAM_DIR holds unzipped shard artifacts of ab-run workflow runs, each in a directory of its artifact's name (ab-ENTRY-N;
fetch_artifact.sh puts them there). For each: its ab.json has to name the deck and the candidate file the directory's
name says (the shipped playbook for a plain entry), the seed, a start on the date given and the pool; its playbook arm
has to hold the tables of one shard, each with a run.json, and none that another shard of the entry holds. It prints one
line an entry (harness version, shards, tables) and everything that is wrong. Run it before anything is read: on
2026-11-21 it found five directories of the right name that held another run's games (the same deck's shipped arm of the
exam before, on another seed), which a check of the names and the table counts alone had passed.
"""
import argparse, collections, json, os, re, sys


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('exam')
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--date')
    ap.add_argument('--pool')
    ap.add_argument('--tables', type=int, default=200)
    ap.add_argument('--shards', type=int, default=5)
    a = ap.parse_args(argv)
    ok = collections.Counter(); bad = []
    tables = collections.defaultdict(set)
    for name in sorted(os.listdir(a.exam)):
        m = re.fullmatch(r'ab-([a-z-]+?)(?:@([a-z0-9]+))?-(\d+)', name)
        if not m:
            continue
        deck, var = m.group(1), m.group(2)
        p = os.path.join(a.exam, name)
        try:
            j = json.load(open(os.path.join(p, 'ab.json')))
        except Exception as e:
            bad.append((name, f'no ab.json: {e}')); continue
        want = f'playbook/variants/{deck}-{var}.json' if var else f'playbook/precons/{deck}.json'
        probs = []
        if j.get('deck') != deck: probs.append(f"deck {j.get('deck')}")
        if (j.get('data_file') or '') != want: probs.append(f"data_file {j.get('data_file')!r}")
        if j.get('seed') != a.seed: probs.append(f"seed {j.get('seed')}")
        if a.date and not str(j.get('started', '')).startswith(a.date): probs.append(f"started {j.get('started')}")
        if a.pool and j.get('pool') != a.pool: probs.append(f"pool {j.get('pool')}")
        arm = os.path.join(p, 'arm-playbook')
        gs = sorted(os.listdir(arm)) if os.path.isdir(arm) else []
        if len(gs) != a.tables // a.shards: probs.append(f'{len(gs)} tables')
        miss = [g for g in gs if not os.path.exists(os.path.join(arm, g, 'run.json'))]
        if miss: probs.append(f'{len(miss)} tables without run.json')
        entry = deck + ('@' + var if var else '')
        if tables[entry] & set(gs): probs.append(f'{len(tables[entry] & set(gs))} tables repeat another shard')
        tables[entry] |= set(gs)
        if probs: bad.append((name, '; '.join(probs)))
        else: ok[(entry, j.get('vibefish'))] += 1
    whole = 0
    for (entry, v), c in sorted(ok.items()):
        full = c == a.shards and len(tables[entry]) == a.tables
        whole += full
        print(f"{entry:<32} harness {v}  {c} shards  {len(tables[entry])} tables" + ('' if full else '   <-- incomplete'))
    print(f"{whole} entries complete; wrong: {bad if bad else 'none'}")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
