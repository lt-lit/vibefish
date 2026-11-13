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
- `slot.sh`: every command that starts Forge goes behind it, so that the machine never plays more than three games however
  many agents are working. Waiters queue shortest run first (the `-n` of the command), then by arrival: with two slots
  and a plain race, ten agents starved one deck for half an hour and timed out its foreground runs. Create the `locks`
  directory it names; after a container restart empty `locks/queue/`.
- `verify_batch.py DECK NAME`: the candidate `playbook/variants/DECK-NAME.json` against the playbook its validation run
  recorded, then the paired kill turns. `verify_answers.py DECK`: an answers candidate against the shipped playbook (every
  shipped rule kept, in order) and against the playbook each of its local runs recorded. Run them before a candidate goes
  to the tables.
- `finish_candidate.py DECK NAME BASE`: `verify_batch.py`, then the candidate's sibling without an attack block
  (`DECK-NAME-forgeattack.json`, for the side-by-side attack arm at the tables) and the goldfish pair copied into
  `demo-data/goldfish/<date>/`. `save_report.py TASK_ID DECK`: an agent's final report, verbatim from its transcript, into
  `docs/agents/reports/<date>/DECK.md`.
- `reports/<date>/`: the agents' reports as handed back: the audit, the rules, the validation, what the rule format could
  not say, the deck's answers for the second pass, and where the candidate falls short of a person.

Rules that held: one agent a deck, its own seed blocks and scratch directory, no commits and no Java changes while agents
play; deck-writing agents on Opus, artifact fetching on Sonnet, bulk downloads on Haiku; check every candidate file against
its validation run yourself. A container restart kills the agents and their games but not their scratch directories or
transcripts: `SendMessage` to the agent's id resumes it with its context, and it needs telling which runs finished
(2026-11-13: six agents resumed that way).
