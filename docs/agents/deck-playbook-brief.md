# Brief: write and goldfish-test a candidate playbook for one Commander precon

You own ONE deck (named in your prompt). Three other agents are doing the same for other decks at the same time
on the same 4-core machine. Your job ends with a candidate playbook file and a goldfish measurement of it against
stock Forge AI; the four-player table runs happen later in GitHub Actions and are not yours.

## What this project is, in five lines
Vibefish (`/home/user/vibefish`) plays Commander decks through Forge's AI, headless. Stock Forge AI misplays many
decks. A "playbook" is a small JSON file of rules written for ONE deck that takes over some of that seat's
decisions (which card to cast when and aimed at what, which optional triggers to take, how to attack); everything
the rules do not cover stays Forge's. Four decks have a shipped playbook that beats stock by 7 to 15 points at
tables. What moved them was the deck's own lines, written by hand from reading its games: the commander out at
once, the engine cards used, the cards Forge's AI never casts cast, the "you may" triggers it declines taken.

## Read first (in this order, skim what you do not need)
1. `/home/user/vibefish/playbook/README.md`, the section "`playbook` (Phase 4)" to the end: the rule format
   (`cast` rules play / activate / hold with `when`, `target`, `phase`, `before_land`, `x`; `triggers`; `attack`)
   and the commands under "Writing one". This is the reference; do not guess rule syntax.
2. Two shipped examples, the `playbook` object in each: `/home/user/vibefish/playbook/precons/token-triumph.json`
   and `/home/user/vibefish/playbook/precons/tricky-terrain.json` (read their `notes`: they say why each rule exists).
   A candidate file looks like `/home/user/vibefish/playbook/variants/quick-draw-spells.json`
   (keys: schema, deck, variant, of, about, playbook).
3. `/home/user/vibefish/DESIGN.md` section 21 ("Cast rules") from "**The diagnosis, in goldfish.**" to
   "**Goblin Storm's playbook, version 2**" and the two corrections after it, and section 22 "**Results: a draft is
   not a bot.**" and "**What it says.**". Lessons that cost games to learn: a card-draw rule can deck the seat
   (guard with `library >= 40` or a creature cap); a `play` rule without `times` casts a card once a turn; rules
   that hold cards "for later" usually lose; attack `go_wide` beat the blocker-counting `pressure` on every deck.

## The loop
All commands run from `/home/user/vibefish`. The Forge build is already fetched at `forge/runtime-snapshot`
(do NOT fetch or rebuild anything). Deck files are in `forge/runtime-snapshot/res/quest/commanderprecons/`.
Card text: Forge's card scripts are unzipped at
`/tmp/claude-0/-home-user/2b458bb3-a9c8-5f77-a5b8-a723b31f9b47/scratchpad/cards/all/<first letter>/<card_name_lowercase_underscores>.txt`
(Oracle text is the `Oracle:` line; `AI:RemoveDeck:All` means stock AI never casts the card).

    SLOT=/tmp/claude-0/-home-user/2b458bb3-a9c8-5f77-a5b8-a723b31f9b47/scratchpad/bin/slot
    W=/tmp/claude-0/-home-user/2b458bb3-a9c8-5f77-a5b8-a723b31f9b47/scratchpad/batch/<your deck id>     # your scratch dir
    D="forge/runtime-snapshot/res/quest/commanderprecons/<your deck file>"

1. What Forge's scripts say:
   `python3 runner/playbook.py roles --deck <id> --runtime forge/runtime-snapshot`
   `python3 runner/playbook.py draft --deck <id> --runtime forge/runtime-snapshot`   (writes
   `playbook/variants/<id>-draft.json`; it lists the cards Forge's AI never casts and the deck's optional triggers)
2. The audit, 12 stock goldfish games on your AUDIT seeds:
   `$SLOT runner/goldfish.sh "$D" -n 12 -s <AUDIT_BASE> -i audit-stock -R forge/runtime-snapshot -o $W/results`
   then read them:
   `python3 runner/hands.py held $W/results/audit-stock`          (mana unspent, cards kept with the mana for them)
   `python3 runner/hands.py abilities $W/results/audit-stock --runtime forge/runtime-snapshot`   (abilities never used)
   `python3 runner/hands.py game $W/results/audit-stock/shard-1/games/game-00N.events.jsonl`      (a slow game, turn by turn)
   A playbook seat run with `FORGE_JAVA_OPTS=-Dvibefish.trace=true` prints every optional trigger Forge declines
   into `$W/results/<run>/shard-1.log`; that is where trigger rules come from.
3. Write the candidate: `playbook/variants/<id>-<short name>.json`. Rules about this deck's own cards only.
   Start from what the audit shows stock leaves undone, in this order of likely worth: the commander's timing, the
   deck's engine (the two or three cards its plan runs through), activated abilities stock never uses, optional
   triggers it declines, cards flagged `AI:RemoveDeck:All`, then curve and mana. Attack: use
   `{"policy": "go_wide", "target": "highest_life", "min_attackers": 3, "safety_margin": 5, "max_reserve": 3, "spread": true}`
   unless the deck clearly wants otherwise (Tricky Terrain uses min_attackers 2 and max_reserve 2). No mulligan rule.
4. Tune on your AUDIT seeds (and up to 20 more TUNING seeds if you need them):
   `$SLOT runner/goldfish.sh "$D" -n 12 -s <AUDIT_BASE> -i tune-1 -R forge/runtime-snapshot -o $W/results -P playbook/variants/<id>-<name>.json`
   `python3 runner/hands.py compare $W/results/audit-stock $W/results/tune-1`
   Read the slow games of the playbook run, fix, repeat a few times. Check in `$W/results/<run>/shard-1/run.json`
   (`games[].playbook_stats`, keys `cast_rule_<n>`, `trigger_accepted`) that your rules actually fire. A rule naming
   a card that is not in the deck stops the harness with exit 2: look in `$W/results/<run>/shard-1.log`.
5. The measurement, on your VALIDATION seeds, which you must not look at before the rules are final:
   40 games stock and 40 under the final candidate, then
   `python3 runner/hands.py compare $W/results/val-stock $W/results/val-playbook --out $W/<id>-pair.json`
   If you change the rules after seeing validation games, say so in the report (the number is then flattered).

## Hard rules
- **CPU.** Prefix EVERY command that starts Forge (`runner/goldfish.sh`, anything calling `controller/vibefish-sim.sh`)
  with `$SLOT`. It waits for one of two machine-wide slots. Never start Forge without it, never run two of your own
  Forge commands at once, and do not run `runner/ab.py` (tables and duels are not part of this job).
  A stock goldfish game takes 10 to 40 s; a deck that makes huge boards can take minutes. `runner/goldfish.sh`
  has `-c CLOCK_S` (default 900) and `-t TURN_CAP` (default 80); leave them alone.
- **Waiting.** A bare `sleep N` in the foreground is blocked. Goldfish runs of 12 games fit in one foreground
  command (give the Bash call a timeout of 600000 ms); for 40 games run it with `run_in_background: true` and
  you will be notified when it ends.
- **Files.** Write only inside your scratch dir `$W` and your own `playbook/variants/<id>-*.json` files. Do not
  edit Java, docs, other decks' files, anything under `playbook/precons/`, `runner/`, `demo-data/` or `.github/`.
  No git commits, no pushes, no GitHub calls.
- **Honesty.** Report what was measured, including nothing. If stock already runs the deck (little unspent mana,
  no idle engine) and your best candidate gains under half a turn on validation, say so and recommend not sending
  it to the tables: two of the six decks tried so far ended that way and that is a useful result.
- If a line of the deck cannot be written with the rule format (for example it needs a choice the rules cannot
  make), do not work around it: list it in the report as a capability the controller lacks.

## Report (your final message; keep it under 500 words plus one small table)
1. The audit in numbers: stock's kill turn, share of mana unspent, the cards it sat on, abilities never used,
   triggers declined, cards flagged never-cast.
2. The candidate: file path, the rules in one line each with the reason, anything you tried and dropped.
3. Validation: games finished in each arm, kill turn stock and playbook, the paired difference with its 95%
   interval, faster/same/slower counts, and whether the rules were changed after validation games were seen.
4. Which rules fired (counts from `playbook_stats`), and any that never did.
5. What the deck needs that the rule format cannot express.
6. Your recommendation: send to 200 tables, or not, and why.
