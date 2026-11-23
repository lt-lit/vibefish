# Brief: read ten games of one deck (DESIGN.md sections 44 and 47)

The brief the game-reading agents were given on 2026-11-23, with DECK set to the deck's id. The printouts are made with `runner/hands.py game EVENTS.jsonl --deck DECK` (eight games the deck lost and two it won, drawn at random from a league), listed in an INDEX.txt with each game's raw event log. Bring the list of what is already counted up to date before using it again.

```
You are reading ten games of one Commander deck played by a bot, to find plays a competent human player of this deck would not make.
Read-only: change nothing in the repository /home/user/vibefish. Put any scripts you write in a new directory SCRATCH/audit-tools-DECK/ (SCRATCH = /tmp/claude-0/-home-user/689e2db2-1b2b-5713-8d65-c6b69bb2badb/scratchpad). Run Python with -I. Do not start any game or build.

What you have
- SCRATCH/audit-DECK/INDEX.txt and game-1.txt ... game-10.txt: ten games of DECK from a 504-game league at a four-player table (every seat a bot under its playbook), eight it lost and two it won. Each printout is the DECK seat's game turn by turn: life, lands, hand at the start of its turn, the land played, casts with their targets, abilities and triggers, attacks. "T7" is the seat's own seventh turn; a game turn number appears in brackets where it matters. INDEX.txt names the raw event log of each game (JSON lines: `turn` lines with every seat's state including hands, then `land`, `cast`, `resolve`, `zone`, `life`, `damage`, `combat`, `attack`, `block`, `lost`), and run.json beside the games directory has every seat's deck list (`decks[].cards`).
- The deck's playbook: /home/user/vibefish/playbook/precons/DECK.json (under "playbook": the `cast` rules in order, `triggers`, `attack`, `block`, `targets`), and the format in /home/user/vibefish/playbook/README.md. Count rule numbers from 1. A rule that has something to do goes first; whatever no rule names is the choice of Forge's stock AI.
- Card texts: Forge's scripts in the zip /home/user/vibefish/forge/runtime-snapshot/res/cardsfolder/cardsfolder.zip (one file a card, the name in lower case with underscores, e.g. grim_poppet.txt; read it with Python's zipfile).
- Already known and counted. Do not report these again: a seat that pays its last life for its own spell (Reanimate at low life, draw spells that cost life); a land that returns a land (Dimir Aqueduct and its kind) kept in hand for want of a basic land; wipe rules that count one opponent's creatures and not the table's. For Death Toll it is known that the seat mills its own library away: do say what mills it and what a person would do about it.

What to find
Decisions in these games that a competent player of THIS deck would not make. Kinds of thing: a card cast at the wrong time or at the wrong target; a card never cast though it was the right play; mana left unspent with a good play in hand; an engine piece or the commander's ability not used; a removal spell or a wipe spent badly or held too long; an attack that throws creatures away; a block not made or made badly; cards discarded to hand size that could have been cast.

For each finding give
1. the game and the turn(s), with the facts from the printout or the raw log;
2. what a competent player would have done, and why;
3. whose decision it was: a rule of the playbook (quote the rule and its number) or Forge's AI (no rule names the card or the choice);
4. how often it occurs in the ten games: count the chances as well as the occurrences;
5. whether the event logs could count it over hundreds of games, and how (which lines, which fields).
Verify each finding in the raw log and in the card's script before you report it, and say plainly which findings you could not verify. Rank the findings by what they cost the deck. End with a short list of what the bot did that a competent player would also do.

Keep the report under 900 words. Suggest nothing that involves contacting anyone or changing Forge itself.
```
