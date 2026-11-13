# Brief: write and goldfish-test a candidate playbook for one Commander precon

You own ONE deck (named in your prompt). Other agents are doing the same for other decks at the same time
on the same 4-core machine. Your job ends with a candidate playbook file and a goldfish measurement of it against
stock Forge AI; the four-player table runs happen later in GitHub Actions and are not yours.

## What this project is, in five lines
Vibefish (`/home/user/vibefish`) plays Commander decks through Forge's AI, headless. Stock Forge AI misplays many
decks. A "playbook" is a small JSON file of rules written for ONE deck that takes over some of that seat's
decisions (which card to cast when and aimed at what, which optional triggers to take, how to attack); everything
the rules do not cover stays Forge's. Twelve decks have a shipped playbook; the best beat their stock pilot by 8 to
13 points at tables of other bots. What moved them was the deck's own lines, written by hand from reading its games: the commander out at
once, the engine cards used, the cards Forge's AI never casts cast, the "you may" triggers it declines taken.

## What this batch is for
These ten decks are the precons the project's owner and the owner's group actually play. Each bot will be used two ways:
as an opponent when the owner playtests a new deck, and as the pilot when the owner simulates this deck itself. So the
aim is the deck played the way a competent person who owns it would play it: its commander out when it should be, its
engine running, its abilities used, its cards cast. A deck that stock Forge AI already plays well is a fine result:
say so, keep the rules few, and do not invent rules to have some.

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
`/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/cards/all/<first letter>/<card_name_lowercase_underscores>.txt`
(Oracle text is the `Oracle:` line; `AI:RemoveDeck:All` means stock AI never casts the card).

    SLOT=/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/bin/slot
    W=/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/batch/<your deck id>     # your scratch dir
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
   triggers it declines, cards flagged `AI:RemoveDeck:All` that advance the deck's own plan, then curve and mana.
   Leave the deck's ANSWERS alone in this pass (board wipes, spot removal, counterspells, fogs): against three
   opponents that do nothing there is no board to answer, so goldfish cannot test a rule for them. List them in
   your report instead (item 7); rules for them are written in a second pass from games at real tables. Attack: use
   `{"policy": "go_wide", "target": "highest_life", "min_attackers": 3, "safety_margin": 5, "max_reserve": 3, "spread": true}`
   unless the deck clearly wants otherwise (a deck that attacks with one or two big creatures wants min_attackers 1
   or 2 and max_reserve 1 or 2). The attack block is there so that goldfish measures the engine; at the tables the
   same rules are also played with Forge's own attack, and which attack the deck keeps is decided there, not by
   you. No mulligan rule.
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
  no idle engine) and your best candidate gains under half a turn on validation, say so plainly: several decks
  tried so far ended that way and that is a useful result. The candidate file is still wanted (the deck will get
  answer rules in the second pass), so leave the best version you have.
- If a line of the deck cannot be written with the rule format (for example it needs a choice the rules cannot
  make), do not work around it: list it in the report as a capability the controller lacks.

## Report (your final message; keep it under 650 words plus one small table)
1. The audit in numbers: stock's kill turn, share of mana unspent, the cards it sat on, abilities never used,
   triggers declined, cards flagged never-cast.
2. The candidate: file path, the rules in one line each with the reason, anything you tried and dropped.
3. Validation: games finished in each arm, kill turn stock and playbook, the paired difference with its 95%
   interval, faster/same/slower counts, and whether the rules were changed after validation games were seen.
4. Which rules fired (counts from `playbook_stats`), and any that never did.
5. What the deck needs that the rule format cannot express.
6. Your recommendation: send to 200 tables, or not, and why.
7. The deck's answers, for the second pass: each board wipe, spot removal spell, counterspell and fog in the list by
   name with what it hits, and which of them Forge's AI is flagged never to cast. One line each; no rules for them.
8. In three or four plain sentences, how a person who owns this deck expects it to play, and where your candidate
   still falls short of that. The owner will read this to judge the bot.
