# docs/agents

What a session hands to the agents that write playbooks, kept here so the next session does not have to write it again.
These files are copies from one session's scratch directory (2026-11-12): the absolute paths in them (`/tmp/claude-0/...`)
are that session's and have to be replaced by the new session's scratch directory before use.

- `deck-playbook-brief.md`: one agent, one deck, from nothing to a candidate playbook and a goldfish pair on 40 seeds it had
  not seen. The agent's prompt names the deck, its file, three seed blocks (audit, tuning, validation) and a scratch
  directory. An Opus agent takes 20 to 35 minutes of its own time and 160k to 200k tokens with it; ten at once on one
  4-core machine took about two hours of wall clock, most of it waiting for a game slot (2026-11-13). This copy is the
  one given to the agents of the owner's ten precons: it says what the batch is for, leaves the deck's answers to a
  second pass and asks for them in the report (items 7 and 8).
- `answer-rules-brief.md`: one agent, one shipped bot, rules for the deck's wipes and removal, written from the games of a
  bot league and tried at a few local tables of bots. This copy points at the league of twelve (`league-run` #3) and the
  pool `bots-v2`; give it the games of the latest league. The four of 2026-11-11 were Fable agents at 630k to 760k tokens
  each; nothing in the brief needs that.
- `answer-rules-brief-exam.md`: the same job for a deck whose engine rules are still a candidate at the tables (the owner's
  ten, 2026-11-14): the material is the deck's own exam games as far as they are in, the base is the candidate file, and
  it asks for eight local tables in one run (sixteen at most), because local tables were what the first batch waited for.
- `slot.sh`: every command that starts Forge goes behind it, so that the machine never plays more than three games however
  many agents are working. Goldfish runs queue shortest first (the `-n` of the command), then by arrival: with two slots
  and a plain race, ten agents starved one deck for half an hour and timed out its foreground runs. Table runs (`ab.py`,
  `league.py`) queue behind the goldfish runs and among themselves by arrival alone: ordered by size, the agents that asked
  for four or six tables kept jumping ahead and two agents that asked for eight had no game in ninety minutes (2026-11-14).
  Nine agents trying rules at local tables get about 23 table games an hour out of three slots between them, so ask for
  few local tables (eight show whether a rule fires) and leave the measuring to Actions. Create the `locks` directory it
  names; after a container restart empty `locks/queue/`.
- `verify_batch.py DECK NAME`: the candidate `playbook/variants/DECK-NAME.json` against the playbook its validation run
  recorded, then the paired kill turns. `verify_answers.py DECK`: an answers candidate against the shipped playbook (every
  shipped rule kept, in order) and against the playbook each of its local runs recorded. Run them before a candidate goes
  to the tables.
- `finish_candidate.py DECK NAME BASE`: `verify_batch.py`, then the candidate's sibling without an attack block
  (`DECK-NAME-forgeattack.json`, for the side-by-side attack arm at the tables) and the goldfish pair copied into
  `demo-data/goldfish/<date>/`. `save_report.py TASK_ID DECK`: an agent's final report, verbatim from its transcript, into
  `docs/agents/reports/<date>/DECK.md`.
- `exam_summary.py ROLLUPS_DIR [--out demo-data/ab/<date>-ab-vNN]`: an unzipped `ab-rollups` artifact read in one step:
  every arm's wins and every paired difference with its interval and exact test, the rollups copied under the names
  `demo-data/ab/` uses, and a deck's side arms (the `-forgeattack` sibling, a candidate played as a playbook-only arm) joined
  on the same tables. It reproduces the figures recorded for `ab-run` #26.
- `ship_candidate.py DECK NAME --attack gowide|forge --tables ... --bot-arm ... --run ... --status ... --summary ...`: the
  mechanical part of shipping: the candidate's playbook (with or without its attack block, checked against the
  `-forgeattack` sibling the tables played) into `playbook/precons/DECK.json` with the date and a note, and the deck's row
  in `playbook/bots.json`. The words are the session's. `add_row.py ROW_FILE` puts one row into
  `playbook/variants/README.md` (a row with the same first cell is replaced).
- `ship_version.py DECK NAME --tables ... --old-arm shipped --new-arm NAME --run ... --status ... --note ...`: the same for
  the next version of a playbook that is already shipped, judged against the shipped arm of its own deck on the same
  tables (the nine pool decks' answer rules, 2026-11-14). It refuses a candidate whose version is not the shipped one plus
  one or whose attack block differs, keeps the row's `tables` (the last measurement against the stock pilot, of the
  earlier version: the status has to say so) and records this exam as `version_tables`.
- The card check of an exam (what each arm casts, card by card; DESIGN §30): `fetch-shards-brief.md` is the brief of the
  small agent that downloads a run's shard artifacts with `fetch_artifact.sh DEST NAME 'URL'`; `shards.sh DEST ENTRY`
  merges the shards of one request into a run directory for `runner/playtest.py`; then, on the reports of the arms:
  `arm_card_diff.py STOCK.json PLAYBOOK.json` (two arms), `three_way.py STOCK.json BASE.json NEW.json` (the cards a base
  playbook casts less than stock AI and what a third arm does with them: the `forge` rule's trial),
  `pool_check.py DECK VARIANT OUT_DIR [--base-commit=REV]` (a candidate that extends a shipped playbook, beside it and
  beside stock AI: the pool's answer rules; the files in `demo-data/playtest/2026-11-14/pool-answers/` are its output
  with `--base-commit=304db09`, the commit before the nine shipped), and `cast_phase.py RUN_DIR ARM DECK CARD...`
  (whether a seat's casts on its own turn come before or after its attack: the logs have no phase, and this is how
  §30 found that Forge's AI casts most permanents after combat).
- `named_split.py VARIANT.json STOCK.json BASE.json NEW.json`: three arms' casts summed over the cards the playbook
  names above its `forge` rule, the cards it names below it and the cards no rule names: how §32 read what the `forge`
  rule's wait moved from one group to the other. `leader.py DIR...`: which thing a table can see says who goes on to
  win (the seat with the most nonland permanents, the highest life, the most damage dealt, sums of them), turn by turn
  from the event logs; the default of an aim's judgement of danger comes from it (DESIGN §33). `danger_eval.py RUN_DIR...`
  (numpy): the same question on harness 0.4.0 logs with more counts (creatures, their power, lands, hand, damage
  dealt) and a model fitted on half the games and scored on the other half; nothing beat life + 2 x nonland
  permanents (DESIGN §34).
- `add_finish.py DECK [DECK ...] [--finish true|leader|none] [--guard one|table] [--swing danger] [--open]
  [--targets danger] [--block survive] [--name NAME]`: a candidate that is a deck's shipped playbook with a hook on
  its attack (`{"policy": "forge", ...}` for a playbook that leaves the attack to Forge), on its triggers' targets or
  on its blocks: `finish` (the kill no block prevents, harness 0.4.0), `"finish": "leader"` (only from the most
  dangerous opponent down, 0.4.1), `guard` (against dying tapped out to one opponent, or to the table, 0.4.1),
  `targets` (removal triggers aimed by danger, 0.4.2), `block` (the blocks that keep the seat alive, 0.4.3),
  `--swing danger` (`"aim": "danger"` on the attack: the declared attack goes at the most dangerous opponent when it
  is no worse there, 0.4.5) and `--open` (`"open": true`: creatures left home attack an opponent that cannot block,
  0.4.5). Nothing else is changed.
- Reading an exam of a hook that changes one decision (DESIGN §34): `first_difference.py EXAM_RESULTS_DIR VARIANT DECK...`
  reads the two games of every table side by side to the first event that differs and files the table by it: the same
  game to the end, the seat's own attack declaration (the hook's doing; filed further by whether the seat was sure to
  kill its last opponent, the most dangerous of several, a less dangerous one, or nobody), or anything else (Forge's
  own run-to-run differences, which only add noise to the paired count). It is how `ab-run` #45 was found to hold two
  opposite effects. `kill_chances.py RUN_DIR...` counts a seat's sure kills once an opponent instead of once a turn and
  says what became of the opponents let live; `tapped_out.py RUN_DIR...` says what a seat did on its own turn before it
  died tapped out, and how often an attack leaves the attacker open to one opponent; `block_check.py CARDSFOLDER_ZIP
  RUN_DIR...` checks the deaths by a block not made against trample. `hook_exam.py EXAM_DIR ROLLUPS_DIR OUT_DIR --pair
  BASE:CAND [--pair ...] DECK...` puts an exam of attack hooks together: for each pair of arms, deck by deck and over
  all decks, the wins and discordant tables, the seat's mistakes in each arm, the hooks' own counters and the
  first-difference tables. It prints what a rule needs and decides nothing. `other_turns.py RUN_DIR... [--arm ARM] [--focus]`: a seat's instants, other spells
  and activated abilities by whether it was its own turn or another player's (the count behind "what the bots do on
  other players' turns", DESIGN §34). `aimed_at.py RUN_DIR...`: whose permanents a seat's spells, triggers and abilities
  are aimed at (the most dangerous opponent, the widest board, the lowest life, the eventual winner, each beside
  chance), from the `target_ctrl` of the cast lines. `attack_danger.py RUN_DIR... [--arm ARM] [--deck ID]`: the same
  question for attackers, from the `combat` and `attack` lines: the share that goes at the most dangerous opponent
  and at the eventual winner, and for the declarations that sent nothing at the most dangerous opponent what stood
  where (who had the lower life, who had more creatures that could block, where more damage was sure to get
  through). It is the count behind `"aim": "danger"` on an attack and, with `--deck` on the two arms of an exam, the
  measure of what that hook changed.
- `add_forge_rule.py DECK [--base FILE] [--name NAME] [--after commander|top|N] [--wait]`: a variant of a playbook with a
  `forge` rule put in mechanically (after the commander's rule unless told otherwise; `--wait` gives the rule
  `"wait": "main2"`). `playbook_check.sh [RUNTIME_DIR] [FILE...]` parses every playbook file with the harness's own
  loader (`PbCheck.java`): run it after a change to the playbook format and before a candidate goes to the tables.
- `three_arm_check.sh EXAM_DIR DECK VARIANT OUT_DIR`: the card check of a candidate examined with both attacks (the
  requests `DECK@VARIANT` with stock and playbook arms and `DECK@VARIANT-forgeattack`): the playtest report of the three
  arms and what each attack arm casts less or more often than the stock pilot. The second pass of the owner's ten was
  read with it (`demo-data/playtest/2026-11-14/second-pass/`).
- `reports/<date>/`: the agents' reports as handed back: the audit, the rules, the validation, what the rule format could
  not say, the deck's answers for the second pass, and where the candidate falls short of a person.

Rules that held: one agent a deck, its own seed blocks and scratch directory, no commits and no Java changes while agents
play; deck-writing agents on Opus, artifact fetching on Sonnet, bulk downloads on Haiku; check every candidate file against
its validation run yourself. A container restart kills the agents and their games but not their scratch directories or
transcripts: `SendMessage` to the agent's id resumes it with its context, and it needs telling which runs finished
(2026-11-13: six agents resumed that way).
