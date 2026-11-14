<!-- The report of the agent that wrote this deck's candidate, as it handed it back (docs/agents/). <scratch> is that session's scratch directory, which does not outlive its container. -->

**Miracle Worker (`miracle-worker`): report**

**1. The audit (12 stock games, seeds 28001 to 28012)**
- **Kill turn:** 13.83 on average (median 13, range 11 to 19).
- **Unspent mana:** 3.1 of 6.2 lands' worth a turn went unspent (50%). 49% of turns ended with a card in hand that the spare mana would have paid for, and on 18% of turns nothing was cast.
- **The commander:** Aminatou was first cast on own turns 3 to 14.
- **Cards it sat on:** answers that have nothing to hit in goldfish, plus Fear of Sleep Paralysis (in hand with the mana for it on 15 turns; drawn in 7 games, cast in 0), Dream Eater (6 games, 0 casts), Phenomenon Investigators (4, 0), Doomwake Giant (3, 0), the Rooms from hand (12, 0) and Entreat the Angels from hand (in hand with the mana on 9 turns).
- **Abilities never used:** Demon of Fate's Design's sacrifice, Prognostic Sphinx's discard. Hall of Heliod's Generosity was used once in 7 turns.
- **Miracle:** stock takes every miracle it is offered, 27 of 27 triggers cast. So the deck's plan already runs under stock AI.
- **Triggers declined:** only Life Insurance's extort, once.
- **Flagged never-cast:** only Timely Ward.

**2. The candidate: `playbook/variants/miracle-worker-veil.json` (version 2)**
1. Sol Ring first.
2. Aminatou the turn she is affordable. Stock lets her wait behind other plays.
3. The mana rocks.
4. The enchantment engine, Sigil of the Empty Throne first, then Secret Arcade (it makes every permanent an enchantment, so every permanent spell feeds Sigil and Mesa), Starfield Mystic, Mesa Enchantress, Soaring Lightbringer, Demon, Ondu, Cellarspawn, One with the Multiverse, Extravagant Replication.
5. Entreat the Angels from hand at maximum X, never below 2. Stock holds it.
6. The Master of Keys at X 2 to 4 while `library >= 40` (it mills twice X).
7. The bodies and Rooms stock never casts.
8. Read the Bones, Diabolic Vision and Ponder while `library >= 30`.
9. Hall of Heliod's Generosity in the second main phase, to put an enchantment card on top for next turn's miracle.
10. Crack Mind Stone or Commander's Sphere late, with an empty hand.

**Triggers:** take Mesa Enchantress's draw while `library >= 25`; take Moon-Blessed Cleric, Ondu Spiritdancer and Solemn Simulacrum.

**Dropped:** a rule to unlock a Room's second door. In Forge an unlock is a static ability (`ST$ UnlockDoor`, not counted as an activated ability), so an `activate` rule never sees it. Forge does unlock doors by itself sometimes. Arvinox is `Mind Flayer, the Shadow` in Forge, so I left it out of the rules.

**3. Validation (seeds 28101 to 28140, 40 games per arm)**

| | finished | kill turn mean | median |
|---|---|---|---|
| stock | 37/40 | 13.97 | 14 |
| playbook | 39/40 | 12.36 | 12 |

- **Paired on 37 seeds:** playbook 1.62 turns faster (95% +1.16 to +2.09). It was faster on 30 seeds, the same on 5 and slower on 2.
- **Unfinished games:** Forge hung until the 900 s clock on seed 28131 in both arms, and on two more seeds under stock.
- **Other measures:** unspent mana fell from 42% to 31%, and the median commander turn from about 6 to 4.5.
- **Changes after seeing validation games:** none. The rules recorded in the validation run match the file; only the `notes` text was edited, before the playbook arm ran.

**4. Which rules fired (validation)**
- Rules 1 to 8 fired: 10, 40, 47, 76, 6, 7, 161 and 31 times.
- Rules 9 (Hall of Heliod's) and 10 (cracking the rocks) never fired. Hall was drawn in 7 games, and Forge's own logic has to agree to its target. Rule 10 fired once in tuning.
- 34 casts were declined by Forge's logic.
- **Triggers:** the Mesa Enchantress rule answered 50 times and the second rule 1,758 times, probably Ondu Spiritdancer being asked about every enchantment that enters once Secret Arcade is out. It answers "yes" each time, and the card itself limits the copy to once a turn.

**5. What the rule format cannot express**
- **The miracle cast itself.** The reveal is a static draw trigger (`confirmTrigger` could answer it), but the cast is an optional Play effect decided by Forge's `confirmAction`, which no rule reaches. Stock always says yes here, so nothing is lost today.
- **Room unlocks:** see item 2.
- **Choices as an effect resolves:** what to keep on top with Brainstorm, Brainstone, Telling Time or the surveils, so that an enchantment is the next draw.
- **Hall of Heliod's at an opponent's end step,** where a person would use it.
- **Cycling Cast Out or Shark Typhoon at instant speed.**

**6. Recommendation:** send it to 200 tables. The gain held on unseen seeds (+1.6 turns, interval clear of zero), and it comes from the commander out on time and from bodies stock never casts, not from tuning to the audit seeds. Stock already runs the miracle engine, so the table result may be modest.

**7. The deck's answers, for the second pass**
- **Terminus:** all creatures to the bottom of their libraries; miracle {W}.
- **Time Wipe:** returns one of your creatures to hand, then destroys all creatures.
- **The Eldest Reborn:** each opponent sacrifices a creature or planeswalker, then discards; chapter III reanimates.
- **Doomwake Giant:** opponents' creatures get -1/-1 whenever an enchantment enters.
- **Swords to Plowshares:** a creature.
- **Utter End:** a nonland permanent.
- **Cast Out:** a nonland permanent; flash, cycling.
- **Return to Dust:** one artifact or enchantment, two in your main phase.
- **Cramped Vents:** 6 damage to an opponent's creature on unlock.
- **Bottomless Pool:** returns a creature to hand on unlock.
- **Dream Eater:** returns an opponent's nonland permanent to hand when it enters.
- **Fear of Sleep Paralysis:** taps and stuns a creature.
- **Bojuka Bog:** exiles a graveyard.
- **Arcane Denial:** counterspell.
- **Inkshield:** fog that makes flying tokens.
- **Sphere of Safety:** attack tax.
- **Flagged never to cast:** none of these. Stock cast none of the spot removal, wipes, counterspell or Inkshield in goldfish, which has no targets for them.

**8. How an owner expects it to play**
Aminatou out on turn four, and every turn's draw set up with surveil, Brainstorm and Hall of Heliod's so an enchantment is miracled cheaply into Sigil of the Empty Throne angels or Enchantress draws. Then flyers take over, and Terminus is miracled for {W} when the board turns against you. The candidate gets the commander, the engine and the bodies down on time. It cannot steer which card sits on top, cannot hold a miracle Terminus for the right moment, and leaves every answer and instant-speed play to Forge.

Files are in `<scratch>/batch/miracle-worker`:
- `miracle-worker-pair.json` (the validation pair)
- `results/` (audit, tuning and validation runs)
- `bin/mir.py` (miracle and per-card counts)
