#!/usr/bin/env python3
"""cmp_rollups.py OFFICIAL_DIR RECORD_DIR: compare the run's own ab-rollups (ab-<entry>/rollup.json) with the
rollups in the record (<entry>.json), ignoring `generated`. Prints one line an entry."""
import json, sys, os
off, rec = sys.argv[1], sys.argv[2]
def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k != 'generated'}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o
def diff(a, b, path=''):
    out = []
    if type(a) != type(b):
        out.append((path, repr(a)[:80], repr(b)[:80])); return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a: out.append((path + '/' + k, '<missing>', repr(b[k])[:80]))
            elif k not in b: out.append((path + '/' + k, repr(a[k])[:80], '<missing>'))
            else: out.extend(diff(a[k], b[k], path + '/' + k))
    elif isinstance(a, list):
        if len(a) != len(b): out.append((path, 'len %d' % len(a), 'len %d' % len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)): out.extend(diff(x, y, '%s[%d]' % (path, i)))
    elif a != b:
        out.append((path, repr(a)[:80], repr(b)[:80]))
    return out
bad = 0
for d in sorted(os.listdir(off)):
    p = os.path.join(off, d, 'rollup.json')
    if not os.path.isfile(p): continue
    entry = d[3:] if d.startswith('ab-') else d
    q = os.path.join(rec, entry.replace('@', '-') + '.json')
    if not os.path.isfile(q):
        print('NO RECORD', entry); bad += 1; continue
    a = strip(json.load(open(p))); b = strip(json.load(open(q)))
    ds = diff(a, b)
    if ds:
        bad += 1
        print('DIFFERS', entry, len(ds), 'fields')
        for x in ds[:12]: print('   ', x)
    else:
        print('same', entry)
print('entries that differ:', bad)
