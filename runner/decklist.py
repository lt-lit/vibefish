#!/usr/bin/env python3
"""A pasted deck list to a Forge .dck, so a list of your own can sit in the focus seat (runner/ab.py --deck-file).

  runner/decklist.py LIST.txt [--name "My Deck"] [--commander "Card Name" ...] [-o "My Deck.dck"] [--keep-sets]
                     [--runtime forge/runtime-snapshot]

LIST.txt is what a deck site exports as text (Moxfield, Archidekt, MTGO, a plain "1 Sol Ring" list): one card a
line with a count in front (`1 Sol Ring`, `1x Sol Ring (C21) 263 *F* [Ramp]`); `-` reads standard input. A line
without a count is a section header: cards under `Commander` are the commanders, cards under `Sideboard`,
`Maybeboard` or `Considering` are left out, everything else is the main deck. A list without a Commander section
names its commander with --commander (once per commander); the card is taken out of the main deck.

Printings are dropped unless --keep-sets is given: Forge picks its default printing for a bare name, and a set code
Forge spells differently would make the card unknown.

With --runtime (or FORGE_RUNTIME set) the written deck is put through the harness's check
(`controller/vibefish-sim.sh check`, half a minute of Forge starting up): cards Forge does not know, cards it cannot
play, the cards its AI is told never to play (a seat under stock AI holds them all game; a playbook rule can cast
them), and whether the list is a legal Commander deck. Deck sites write a double-faced card as "Front // Back"; Forge
knows it by its front face and keeps both halves only for split cards (Fire // Ice), so a "Front // Back" name Forge
does not know is rewritten to its front face and checked again. Without --runtime the list is written as given and
not checked. Standard library only.
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP = {'sideboard', 'maybeboard', 'considering', 'maybe', 'tokens', 'token', 'attractions', 'stickers', 'wishlist'}
COMMANDER = {'commander', 'commanders', 'command zone', 'companion'}
CARD = re.compile(r'^(\d+)\s*[xX]?\s+(.+)$')
SET = re.compile(r'\s+\(([A-Za-z0-9]{2,6})\)(?:\s+[\w★†-]+)?\s*$')


def parse(lines, keep_sets=False):
    section = 'main'
    out = {'commander': collections.OrderedDict(), 'main': collections.OrderedDict()}
    skipped = []
    for raw in lines:
        line = raw.strip().lstrip('﻿')
        if not line or line.startswith('//') or line.startswith('#'):
            continue
        m = CARD.match(line)
        if not m:
            head = re.sub(r'[\[\]:()0-9]', '', line).strip().lower()
            section = 'commander' if head in COMMANDER else 'skip' if head in SKIP else 'main'
            continue
        n, name = int(m.group(1)), m.group(2)
        name = re.sub(r'\s+\*[A-Za-z]+\*', '', name)            # *F* foil, *E* etched
        name = re.sub(r'\s+\[[^\]]*\]', '', name)                # [Category]
        name = re.sub(r'\s+\^[^^]*\^', '', name)                 # ^tag^
        name = re.sub(r'\s+#\S.*$', '', name)                    # #tag
        code = None
        sm = SET.search(name)
        if sm:
            code = sm.group(1).upper(); name = name[:sm.start()]
        name = re.sub(r'\s*/{1,2}\s*', ' // ', name.strip()) if '/' in name else name.strip()
        if section == 'skip':
            skipped.append(name)
            continue
        key = (name, code if keep_sets else None)
        out[section][key] = out[section].get(key, 0) + n
    return out, skipped


def to_dck(name, deck):
    def rows(d):
        return [f"{n} {card}" + (f"|{code}" if code else '') for (card, code), n in d.items()]
    return '\n'.join(['[metadata]', f'Name={name}', '[Commander]'] + rows(deck['commander']) + ['[Main]'] + rows(deck['main'])) + '\n'


def forge_check(path, runtime):
    """The harness's check of one deck file: {requested_count, loaded_count, unknown, unsupported, ai_never, ai_random, conformance, ok}."""
    fd, tmp = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    try:
        subprocess.run([os.path.join(ROOT, 'controller', 'vibefish-sim.sh'), 'check', '--out', tmp, os.path.abspath(path)],
                       env={**os.environ, 'FORGE_RUNTIME': os.path.abspath(runtime)}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with open(tmp, encoding='utf-8') as f:
            res = json.load(f)
    except (OSError, ValueError) as e:
        raise SystemExit(f"the check did not run ({e}); is the Forge runtime at {runtime}? (forge/fetch-forge.sh)")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return res[0] if isinstance(res, list) else res


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('list')
    ap.add_argument('--name')
    ap.add_argument('--commander', action='append', default=[])
    ap.add_argument('-o', '--out')
    ap.add_argument('--keep-sets', action='store_true')
    ap.add_argument('--runtime', default=os.environ.get('FORGE_RUNTIME'), help='a Forge runtime to check the deck with')
    a = ap.parse_args(argv)
    text = sys.stdin.read() if a.list == '-' else open(a.list, encoding='utf-8').read()
    deck, skipped = parse(text.splitlines(), a.keep_sets)
    for want in a.commander:
        hit = [k for k in deck['main'] if k[0].lower() == want.lower()]
        if not hit and not any(k[0].lower() == want.lower() for k in deck['commander']):
            raise SystemExit(f"--commander {want}: not in the list")
        for k in hit:
            deck['commander'][k] = deck['main'].pop(k)
    if not deck['commander']:
        raise SystemExit("no commander: the list has no Commander section, so name it with --commander \"Card Name\"")
    name = a.name or (os.path.splitext(os.path.basename(a.list))[0] if a.list != '-' else 'Deck')
    out = a.out or name + '.dck'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(to_dck(name, deck))
    cmd, main_n = sum(deck['commander'].values()), sum(deck['main'].values())
    print(f"{out}: {', '.join(k[0] for k in deck['commander'])} and {main_n} cards ({cmd + main_n} in all)"
          + (f"; left out {len(skipped)} sideboard or maybeboard line(s)" if skipped else ''), file=sys.stderr)
    if cmd + main_n != 100:
        print(f"note: a Commander deck is 100 cards with its commander; this is {cmd + main_n}", file=sys.stderr)
    if not a.runtime:
        print(f"not checked: add --runtime forge/runtime-snapshot, or run controller/vibefish-sim.sh check \"{out}\"", file=sys.stderr)
        return 0
    res = forge_check(out, a.runtime)
    faces = [n for n in res.get('unknown') or [] if ' // ' in n]
    if faces:                                   # a double-faced card: Forge knows it by its front face
        for sec in ('commander', 'main'):
            deck[sec] = collections.OrderedDict(((k[0].split(' // ')[0], k[1]) if k[0] in faces else k, n) for k, n in deck[sec].items())
        with open(out, 'w', encoding='utf-8') as f:
            f.write(to_dck(name, deck))
        print("written by their front face: " + '; '.join(faces), file=sys.stderr)
        res = forge_check(out, a.runtime)
    print(f"Forge loaded {res.get('loaded_count')} of {res.get('requested_count')} cards.", file=sys.stderr)
    for key, what in (('unknown', "cards Forge does not know (check the spelling; a very new card may not be in this build)"),
                      ('unsupported', "cards Forge cannot play"),
                      ('ai_never', "cards Forge's AI is told never to play (stock AI holds them; a playbook rule can cast them)"),
                      ('ai_random', "cards Forge's AI is told to leave out of decks it builds (it does play them)")):
        if res.get(key):
            print(f"{what}: " + '; '.join(res[key]), file=sys.stderr)
    if res.get('conformance'):
        print("not a legal Commander deck: " + ' '.join(str(res['conformance']).split()), file=sys.stderr)
    return 0 if res.get('ok') else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
