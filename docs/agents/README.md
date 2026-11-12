# docs/agents

What a session hands to the agents that write playbooks, kept here so the next session does not have to write it again.
These files are copies from one session's scratch directory (2026-11-12): the absolute paths in them (`/tmp/claude-0/...`)
are that session's and have to be replaced by the new session's scratch directory before use.

- `deck-playbook-brief.md`: one agent, one deck, from nothing to a candidate playbook and a goldfish pair on 40 seeds it had
  not seen. The agent's prompt names the deck, its file, three seed blocks (audit, tuning, validation) and a scratch
  directory. An Opus agent takes 20 to 35 minutes and 160k to 200k tokens with it (the batch of 2026-11-12, six decks).
- `answer-rules-brief.md`: one agent, one shipped bot, rules for the deck's wipes and removal, written from the games of a
  bot league and tried at local tables of bots. It names a league run's directory in the scratchpad; give it the games of
  the latest league. The four of 2026-11-11 were Fable agents at 630k to 760k tokens each; nothing in the brief needs that.
- `slot.sh`: every command that starts Forge goes behind it, so that the machine never plays more than two games however
  many agents are working (two `flock` files; create the `locks` directory it names).
- `verify_batch.py DECK NAME`: the candidate `playbook/variants/DECK-NAME.json` against the playbook its validation run
  recorded, then the paired kill turns. `verify_answers.py DECK`: an answers candidate against the shipped playbook (every
  shipped rule kept, in order) and against the playbook each of its local runs recorded. Run them before a candidate goes
  to the tables.

Rules that held: one agent a deck, its own seed blocks and scratch directory, no commits and no Java changes while agents
play; deck-writing agents on Opus, artifact fetching on Sonnet, bulk downloads on Haiku; check every candidate file against
its validation run yourself.
