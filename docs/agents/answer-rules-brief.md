# Brief: answer rules for one shipped bot

You own ONE deck (named in your prompt). Other agents do the same for other decks at the same time on
the same 4-core machine. Your job ends with a candidate playbook file and a short report; the 200-table judgement
happens later in GitHub Actions and is not yours.

## Where things stand, in a dozen lines
Vibefish (`/home/user/vibefish`) plays Commander decks through Forge's AI, headless. A "playbook" is a JSON file of
rules for ONE deck that takes over some of that seat's decisions (which card to cast when and aimed at what, which
optional triggers to take, how to attack); whatever the rules do not cover stays with stock Forge AI. Twelve decks
have a shipped playbook (`runner/leagues/bots-v2.json`). Each plays its own plan. Only three of them play the table:
Hail, Caesar, Goblin Storm and Tricky Terrain carry "answer rules", rules that cast the deck's board wipes and removal,
which Forge's AI mostly keeps in hand or is told never to cast at all (`AI:RemoveDeck:All`). Before those rules the
seats lost holding their answers (`DESIGN.md` section 24, "What the bots hold while they lose"); with them a wipe that
was cast in a fifth to two fifths of the games it was drawn is cast in three fifths to three quarters (section 27,
"What the answer rules cast"), which was worth 9.5 points of win rate to Hail, Caesar, 4 to Goblin Storm, a lean to
Tricky Terrain and nothing to Token Triumph, the deck that led that table. The owner's purpose (section 29): the bots
are opponents for playtesting decks, and an opponent has to react to the table the way a competent person would, so
the answers must be played whether or not they raise this seat's own win rate. On 2026-11-12 the twelve were played
against each other, every seat under its playbook, 600 games (section 28). Those games are your material: when
should this seat use each of its answers, and can the rule format say so.

## Read first
1. `/home/user/vibefish/playbook/README.md` from "`playbook` (Phase 4)" to the end: the rule format. Note in
   particular the conditions about the other side (`opp_creatures`, `opp_power`, `opp_life`, `threat`, and our own
   `power`, `creatures`, `life`), the comparison of two metrics (`"opp_power > power"`), `x` / `x_min` for X spells,
   `activate` with `ability`, and the limits: a spell that needs a target is cast by a rule only if the target is a
   permanent of ours named by the rule, or if Forge's own logic for the card agrees (Forge then picks the targets);
   the rules are read only in the seat's own main phases with an empty stack.
2. Your deck's shipped playbook, the `playbook` object in `/home/user/vibefish/playbook/precons/<deck id>.json`,
   with its `notes`, and as worked examples the answer rules of two shipped bots: the rules about Ruinous Ultimatum,
   Martial Coup and Hour of Reckoning in `/home/user/vibefish/playbook/precons/hail-caesar.json`, and the rules about
   Oblivion Stone, Propaganda and Evacuation in `/home/user/vibefish/playbook/precons/tricky-terrain.json` (their
   `notes` say what each was written from). A candidate file looks like `/home/user/vibefish/playbook/variants/quick-draw-spells.json`
   (keys: schema, deck, variant, of, about, playbook).
3. `/home/user/vibefish/DESIGN.md` section 22, "**Results: Goblin Storm's candidates**": two "lost board" rules cost
   that deck wins. They were judged at tables of stock AI; the new exam is tables of bots, so that verdict does not
   bind you, but its lesson does: a rule written from a post-mortem is a hypothesis, and holding cards for later
   usually loses.

## Your material
- The 600 league games (your deck is in 200 of them), one directory a game:
  `L=/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/league3/2026-11-12-bots-v2-snapshot-2026-11-10-s20261250-bots`
  `$L/shard-N/gNNNNN/run.json` (the decks with their card lists, mana values and the playbook each seat ran) and
  `$L/shard-N/gNNNNN/games/game-001.events.jsonl` (the event stream: schema in `DESIGN.md` section 6; every `turn`
  event has each seat's hand by card name, life, lands and permanent count; `cast`, `attack`, `block`, `damage`,
  `zone`, `lost` events carry the seat).
  `python3 runner/hands.py game <events.jsonl> --deck <deck id>` prints one game turn by turn for your seat.
  `python3 runner/playstyle.py $L --by-deck` prints how the twelve played (slow: it reads 600 games; run it once).
- Card text: Forge's card scripts, unzipped, at
  `/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/cards/all/<first letter>/<name_lowercase_underscores>.txt`
  (`Oracle:` is the text; `AI:RemoveDeck:All` means stock Forge AI never casts the card).
- The rule engine itself, if you need to know exactly what a condition counts:
  `/home/user/vibefish/controller/src/vibefish/PlaybookController.java` and `Playbook.java`. READ ONLY.

## What to do
1. List the deck's answer cards from its card list and their scripts: board wipes, one-sided or not; removal aimed at
   opponents' permanents; anything that stops an attack. For each, from the league games: in how many games your seat
   saw it, cast it, and lost with it in hand; and what was happening on the table when it sat there (who was ahead,
   who killed your seat and with what). A few minutes of scripting over the event logs does this.
2. Decide, card by card, when a competent pilot of THIS deck casts it at a table like that one, and write that as
   rules. Typical shapes: a wipe that spares our side is cast as soon as the opponents have a board worth it; a wipe
   that hits us too is cast when we are behind (`opp_power > power`, or `threat` close to our `life`), not when we
   are the one ahead; a rule that needs a number wants one you can defend from the games, not a guess.
   Keep every shipped rule as it is and in its order unless one conflicts with yours (say so if it does). Put the new
   rules where they belong: rules are read top to bottom and the first `play` or `activate` rule that has something
   to do acts, so an answer that should come before the turn's other plays goes above them.
3. Write `playbook/variants/<deck id>-answers.json`: `"variant": "answers"`, `"of": "playbook/precons/<deck id>.json"`,
   the shipped playbook's `triggers` and `cast` with your rules added, its `attack` exactly as shipped (most shipped
   playbooks have none: then yours has none, and Forge attacks; which attack suits the deck is decided at the tables), `"version"` one higher than the
   shipped version, and `notes` that say for each new rule why it is there and what it was written from.
4. Test it at tables of bots, locally, a few games at a time. This is to see that the rules fire when they should and
   do what you meant, not to measure a win rate (the tables in Actions do that; a dozen games cannot):

       SLOT=/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/bin/slot
       W=/tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad/batch/answers-<deck id>
       cd /home/user/vibefish
       $SLOT env FORGE_RUNTIME=$PWD/forge/runtime-snapshot python3 -I runner/ab.py play --deck <deck id> --games 8 \
           --seed <YOUR SEED> --out $W/results/t1 --runtime forge/runtime-snapshot -j 1 --arms playbook \
           --data playbook/variants/<deck id>-answers.json --pool runner/leagues/bots-v2.json --opponent-playbooks
       python3 -I runner/ab.py rollup $W/results/t1 ; python3 runner/losses.py $W/results/t1

   That plays eight tables with your seat under the candidate and the other three seats drawn from the other eleven
   bots, each under its shipped playbook; the games land in `$W/results/t1/arm-playbook/gNNNN/`. Without `--data` the same command
   plays the shipped playbook on the same eight tables, which is your comparison if you want one.
   A game takes one to two minutes (some far longer), so eight games is more than the ten-minute limit of a foreground command: start
   the run with `run_in_background: true` and wait for the notification.
   Read the games: every cast of your answer cards (the `cast` events of your seat), the turn, what was on the table,
   what left the battlefield after it (`zone` events), and the turns on which the card was in hand and stayed there.
   Fix, play again. Aim for 16 local table games in all; 24 is the hard cap (nine agents share two game slots, and
   the 200 tables in Actions are the judgement, not these).
   Do not trust `playbook_stats` here: at a table with several playbook seats the counters are summed over the seats
   and the rule numbers of different playbooks collide. Go by the event log.

## Hard rules
- **CPU.** Every command that starts Forge (anything through `runner/ab.py play`, `runner/goldfish.sh` or
  `controller/vibefish-sim.sh`) goes behind `$SLOT`, with `-j 1`, one such command of yours at a time. No exceptions.
- **Files.** Write only inside your scratch dir `$W` and your own `playbook/variants/<deck id>-answers*.json`.
  Do not edit `playbook/precons/`, Java, docs, `runner/`, `demo-data/`, `.github/` or other decks' files. No git
  commits, no pushes, no GitHub calls. Do not rebuild anything: `controller/` sources must not change while others play.
- **Honesty.** Say what you saw. If a card cannot be driven by the rule format (it needs targets on the other side
  that Forge will not pick, a choice as it resolves, an instant-speed response), do not work around it: write what can
  be written and list the rest precisely, with the evidence. If after testing a rule looks like it does harm, drop it
  and say so. Rules about this deck's own cards only.

## Report (your final message, under 450 words plus one small table)
1. The answer cards and what the league games show for each (seen / cast / in hand at a loss), in a table.
2. The rules you added, one line each with the reason; anything tried and dropped.
3. What the local tables showed: for each answer card, times seen and times cast under the candidate, what the casts
   did, any rule that never fired, anything that backfired. Give the win count of your seat too, labelled as too few
   games to mean anything.
4. What this deck's answers need that the rule format cannot express.
5. The file path, and whether you recommend sending it to 200 tables.
